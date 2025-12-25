"""
Service that reads social_comment_analysis records and enriches them with ML-derived insights.
"""
from typing import List, Optional

from app.repositories.media_analysis_analytic_repository import MediaAnalysisAnalyticRepository
from app.repositories.social_comment_analysis_repository import SocialCommentAnalysisRepository
from app.services.sentiment_service import SentimentService
from app.services.insight_llm_service import InsightLLMService
from app.schemas.social_comment_analysis_schemas import (
    SocialCommentAnalysisResponse,
    SocialCommentInsight,
    EmotionScore,
)


class SocialCommentAnalysisService:
    """Business logic for deriving insights from uploaded social comments."""

    def __init__(
        self,
        repository: SocialCommentAnalysisRepository,
        media_repository: MediaAnalysisAnalyticRepository,
        sentiment_service: SentimentService,
        insight_service: InsightLLMService,
    ):
        self.repository = repository
        self.media_repository = media_repository
        self.sentiment_service = sentiment_service
        self.insight_service = insight_service

    def analyze_social_comments(self, limit: Optional[int] = None) -> SocialCommentAnalysisResponse:
        records = self.repository.find_all(limit)
        insights: List[SocialCommentInsight] = []

        for record in records:
            text = record.comment or ""
            sentiment = self.sentiment_service.analyze_text(text)

            intent, intent_confidence = self.insight_service.classify_intent(text)
            language = self.insight_service.detect_language(text)
            toxicity_label, toxicity_score = self.insight_service.detect_toxicity(text)
            sarcasm_label, sarcasm_score = self.insight_service.detect_sarcasm(text)
            topics, entities = self.insight_service.extract_topics_and_entities(text)
            risk_index = self._calculate_risk_index(
                sentiment_score=float(sentiment.get("sentiment_score", 0.0)),
                polarity=float(sentiment.get("polarity", 0.0)),
                toxicity_score=float(sentiment.get("toxicity_score", 0.0)),
                intent=intent,
                sarcasm=sarcasm_label,
                sarcasm_score=sarcasm_score,
            )

            insight = SocialCommentInsight(
                id=record.id,
                username=record.username,
                platform=record.platform,
                brand=record.brand,
                comment=text,
                sentiment=sentiment.get("sentiment", "neutral"),
                sentiment_score=float(sentiment.get("sentiment_score", 0.0)),
                polarity=float(sentiment.get("polarity", 0.0)),
                emotion=sentiment.get("emotion", "neutral"),
                emotion_scores=[
                    EmotionScore(emotion=item["emotion"], score=item["score"])
                    for item in sentiment.get("emotion_scores", [])
                ],
                intent=intent,
                intent_confidence=round(intent_confidence, 3),
                language=language,
                toxicity=toxicity_label,
                toxicity_score=round(toxicity_score, 3),
                sarcasm=sarcasm_label,
                sarcasm_score=round(sarcasm_score, 3),
                topics=topics,
                entities=entities,
                risk_index=round(risk_index, 4),
            )
            insights.append(insight)
            self.media_repository.upsert_from_insight(insight)

        return SocialCommentAnalysisResponse(
            total_records=len(records),
            analyzed_records=len(insights),
            results=insights,
        )

    def _calculate_risk_index(
        self,
        sentiment_score: float,
        polarity: float,
        toxicity_score: float,
        intent: str,
        sarcasm: str,
        sarcasm_score: float,
    ) -> float:
        sentiment_risk = max(0.0, -polarity)
        toxicity_risk = max(0.0, min(toxicity_score, 1.0))
        sarcasm_risk = sarcasm_score if (sarcasm or "").lower() == "sarcastic" else 0.0
        intent_weight = self._intent_weight(intent)

        risk = (
            0.4 * sentiment_risk
            + 0.3 * toxicity_risk
            + 0.2 * intent_weight
            + 0.1 * sarcasm_risk
        )
        return min(max(risk, 0.0), 1.0)

    def _intent_weight(self, intent: Optional[str]) -> float:
        normalized = (intent or "").lower()
        if normalized == "complaint":
            return 1.0
        if normalized == "request":
            return 0.8
        if normalized == "question":
            return 0.6
        if normalized == "praise":
            return 0.3
        return 0.4

    # legacy heuristic helpers removed in favor of transformer-based InsightLLMService

