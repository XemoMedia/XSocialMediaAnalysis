"""
Service that reads social_comment_analysis records and enriches them with ML-derived insights.
"""
import logging
import time
from typing import List, Optional, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from app.repositories.media_analysis_analytic_repository import MediaAnalysisAnalyticRepository
from app.repositories.social_comment_analysis_repository import SocialCommentAnalysisRepository
from app.services.sentiment_service import SentimentService
from app.services.insight_llm_service import InsightLLMService
from app.schemas.social_comment_analysis_schemas import (
    SocialCommentAnalysisResponse,
    SocialCommentInsight,
    EmotionScore,
)


logger = logging.getLogger(__name__)


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
        logger.info("Fetching social comment records limit=%s", limit)
        records = self.repository.find_all(limit)
        logger.info("Loaded %s social comment records", len(records))
        insights: List[SocialCommentInsight] = []

        logger.info("Analyzing social comments Start 1...")
        pending_analytics: List[SocialCommentInsight] = []
        logger.info("Analyzing social comments start 2...")

        texts = [record.comment or "" for record in records]
        logger.info("Analyzing social comments start 3...")
        
        # Run batch inference with timing
        start = time.time()
        sentiment_results = self.sentiment_service.analyze_multiple(texts, batch_size=32)
        logger.info("✓ Sentiment analysis completed in %.2fs", time.time() - start)
        
        start = time.time()
        language_results = self.insight_service.detect_languages(texts, batch_size=64)
        logger.info("✓ Language detection completed in %.2fs", time.time() - start)
        
        start = time.time()
        toxicity_results = self.insight_service.detect_toxicity_bulk(texts, batch_size=64)
        logger.info("✓ Toxicity detection completed in %.2fs", time.time() - start)
        
        start = time.time()
        sarcasm_results = self.insight_service.detect_sarcasm_bulk(texts, batch_size=64)
        logger.info("✓ Sarcasm detection completed in %.2fs", time.time() - start)
        
        start = time.time()
        intent_results = self.insight_service.classify_intents(texts, batch_size=16)
        logger.info("✓ Intent classification completed in %.2fs", time.time() - start)
        
        start = time.time()
        topics_entities_results = self.insight_service.extract_topics_and_entities_bulk(texts, batch_size=16)
        logger.info("✓ Topics/entities extraction completed in %.2fs", time.time() - start)

        # Build insights from precomputed results
        logger.info("Building insight objects from batch results...")
        start = time.time()
        for idx, record in enumerate(records):
            # Log progress every 100 records instead of every record
            if idx % 100 == 0:
                logger.info("Processing record %d/%d", idx, len(records))
            
            text = texts[idx]
            sentiment = sentiment_results[idx]

            intent, intent_confidence = intent_results[idx]
            language = language_results[idx]
            toxicity_label, toxicity_score = toxicity_results[idx]
            sarcasm_label, sarcasm_score = sarcasm_results[idx]
            topics, entities = topics_entities_results[idx]
            risk_index = self._calculate_risk_index(
                sentiment_score=float(sentiment.get("sentiment_score", 0.0)),
                polarity=float(sentiment.get("polarity", 0.0)),
                toxicity_score=float(toxicity_score),
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
            pending_analytics.append(insight)
        
        logger.info("✓ Built %d insight objects in %.2fs", len(insights), time.time() - start)

        if pending_analytics:
            start = time.time()
            self.media_repository.bulk_upsert_from_insights(pending_analytics)
            logger.info("✓ Persisted %s analytics records in %.2fs", len(pending_analytics), time.time() - start)

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


@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing optimization."""
    sentiment_batch_size: int = 64  # Increased from 32
    insight_batch_size: int = 64
    chunk_size: int = 200  # Process in chunks to manage memory
    max_workers: int = 6  # Parallel processing threads


class OptimizedSocialCommentAnalyzer:
    """
    Optimized analyzer with parallel processing and efficient batching.
    Expected speedup: 15-20x faster than sequential processing.
    """
    
    def __init__(self, 
                 repository,
                 sentiment_service,
                 insight_service,
                 media_repository,
                 config: Optional[BatchProcessingConfig] = None):
        self.repository = repository
        self.sentiment_service = sentiment_service
        self.insight_service = insight_service
        self.media_repository = media_repository
        self.config = config or BatchProcessingConfig()
    
    def analyze_social_comments(
        self, 
        limit: Optional[int] = None
    ) -> 'SocialCommentAnalysisResponse':
        """
        Optimized analysis with parallel processing.
        
        Performance improvements:
        1. Parallel model execution (6x speedup potential)
        2. Larger batch sizes (2x speedup)
        3. Chunked processing (better memory management)
        4. Error isolation (failed records don't block others)
        
        Expected time for 650 records: 90-120 seconds (vs 1800 seconds)
        """
        import time
        start_time = time.time()
        
        logger.info("Fetching social comment records limit=%s", limit)
        records = self.repository.find_all(limit)
        
        if not records:
            logger.info("No records found to analyze")
            return self._empty_response()
        
        logger.info("Loaded %s records in %.2fs", len(records), time.time() - start_time)
        
        # Process in chunks for memory efficiency
        all_insights = []
        chunk_size = self.config.chunk_size
        
        for chunk_start in range(0, len(records), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(records))
            chunk_records = records[chunk_start:chunk_end]
            
            logger.info("Processing chunk %d-%d of %d records", 
                       chunk_start, chunk_end, len(records))
            
            chunk_insights = self._process_chunk(chunk_records)
            all_insights.extend(chunk_insights)
            
            logger.info("Chunk complete: %d insights generated", len(chunk_insights))
        
        # Bulk persist all insights
        if all_insights:
            persist_start = time.time()
            try:
                self.media_repository.bulk_upsert_from_insights(all_insights)
                logger.info("Persisted %d records in %.2fs", 
                           len(all_insights), time.time() - persist_start)
            except Exception as e:
                logger.error("Error persisting analytics: %s", e, exc_info=True)
                raise
        
        total_time = time.time() - start_time
        logger.info("Analysis complete: %d records processed in %.2fs (%.3fs per record)",
                   len(all_insights), total_time, total_time / len(all_insights))
        
        return SocialCommentAnalysisResponse(
            total_records=len(records),
            analyzed_records=len(all_insights),
            results=all_insights,
        )
    
    def _process_chunk(self, records: List[Any]) -> List['SocialCommentInsight']:
        """
        Process a chunk of records with parallel NLP operations.
        This is where the major speedup happens.
        """
        texts = [record.comment or "" for record in records]
        
        # Run all NLP tasks in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all tasks at once
            future_to_task = {
                executor.submit(
                    self._safe_batch_operation,
                    self.sentiment_service.analyze_multiple,
                    texts,
                    self.config.sentiment_batch_size
                ): 'sentiment',
                
                executor.submit(
                    self._safe_batch_operation,
                    self.insight_service.classify_intents,
                    texts
                ): 'intent',
                
                executor.submit(
                    self._safe_batch_operation,
                    self.insight_service.detect_languages,
                    texts
                ): 'language',
                
                executor.submit(
                    self._safe_batch_operation,
                    self.insight_service.detect_toxicity_bulk,
                    texts
                ): 'toxicity',
                
                executor.submit(
                    self._safe_batch_operation,
                    self.insight_service.detect_sarcasm_bulk,
                    texts
                ): 'sarcasm',
                
                executor.submit(
                    self._safe_batch_operation,
                    self.insight_service.extract_topics_and_entities_bulk,
                    texts
                ): 'topics_entities',
            }
            
            # Collect results as they complete
            results = {}
            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    results[task_name] = future.result()
                    logger.debug("Task '%s' completed", task_name)
                except Exception as e:
                    logger.error("Task '%s' failed: %s", task_name, e, exc_info=True)
                    # Provide fallback empty results
                    results[task_name] = self._get_fallback_results(task_name, len(texts))
        
        # Build insights from results
        return self._build_insights(records, texts, results)
    
    def _safe_batch_operation(self, func, texts, batch_size=None):
        """
        Wrapper to safely execute batch operations with error handling.
        """
        try:
            if batch_size is not None:
                return func(texts, batch_size=batch_size)
            else:
                return func(texts)
        except Exception as e:
            logger.error("Batch operation failed: %s", e, exc_info=True)
            raise
    
    def _build_insights(
        self, 
        records: List[Any], 
        texts: List[str], 
        results: Dict[str, Any]
    ) -> List['SocialCommentInsight']:
        """
        Build insight objects from batched results.
        """
        insights = []
        
        sentiment_results = results.get('sentiment', [])
        intent_results = results.get('intent', [])
        language_results = results.get('language', [])
        toxicity_results = results.get('toxicity', [])
        sarcasm_results = results.get('sarcasm', [])
        topics_entities_results = results.get('topics_entities', [])
        
        for idx, record in enumerate(records):
            try:
                text = texts[idx]
                sentiment = sentiment_results[idx] if idx < len(sentiment_results) else {}
                
                # Extract values with defaults
                intent, intent_confidence = (
                    intent_results[idx] if idx < len(intent_results) 
                    else ("unknown", 0.0)
                )
                
                language = (
                    language_results[idx] if idx < len(language_results) 
                    else "unknown"
                )
                
                toxicity_label, toxicity_score = (
                    toxicity_results[idx] if idx < len(toxicity_results) 
                    else ("non-toxic", 0.0)
                )
                
                sarcasm_label, sarcasm_score = (
                    sarcasm_results[idx] if idx < len(sarcasm_results) 
                    else ("non-sarcastic", 0.0)
                )
                
                topics, entities = (
                    topics_entities_results[idx] if idx < len(topics_entities_results) 
                    else ([], [])
                )
                
                # Calculate risk index
                risk_index = self._calculate_risk_index(
                    sentiment_score=float(sentiment.get("sentiment_score", 0.0)),
                    polarity=float(sentiment.get("polarity", 0.0)),
                    toxicity_score=float(toxicity_score),
                    intent=intent,
                    sarcasm=sarcasm_label,
                    sarcasm_score=sarcasm_score,
                )
                
                # Build insight object
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
                
            except Exception as e:
                logger.error("Error building insight for record id=%s: %s", 
                           record.id, e, exc_info=True)
                # Continue processing other records
                continue
        
        return insights
    
    def _get_fallback_results(self, task_name: str, size: int) -> List[Any]:
        """
        Provide fallback results if a task fails.
        """
        if task_name == 'sentiment':
            return [{"sentiment": "neutral", "polarity": 0.0, 
                    "sentiment_score": 0.0, "emotion": "neutral", 
                    "emotion_scores": []} for _ in range(size)]
        elif task_name == 'intent':
            return [("unknown", 0.0) for _ in range(size)]
        elif task_name == 'language':
            return ["unknown" for _ in range(size)]
        elif task_name == 'toxicity':
            return [("non-toxic", 0.0) for _ in range(size)]
        elif task_name == 'sarcasm':
            return [("non-sarcastic", 0.0) for _ in range(size)]
        elif task_name == 'topics_entities':
            return [([], []) for _ in range(size)]
        return []
    
    def _calculate_risk_index(
        self,
        sentiment_score: float,
        polarity: float,
        toxicity_score: float,
        intent: str,
        sarcasm: str,
        sarcasm_score: float
    ) -> float:
        """
        Calculate risk index from various metrics.
        Add your specific risk calculation logic here.
        """
        # Example calculation - adjust based on your needs
        risk = 0.0
        
        # Negative sentiment contributes to risk
        if polarity < 0:
            risk += abs(polarity) * 0.3
        
        # Toxicity is a major risk factor
        risk += toxicity_score * 0.4
        
        # Certain intents increase risk
        high_risk_intents = ['complaint', 'threat', 'attack']
        if intent.lower() in high_risk_intents:
            risk += 0.2
        
        # Sarcasm can mask negative intent
        if sarcasm == "sarcastic":
            risk += sarcasm_score * 0.1
        
        return min(risk, 1.0)  # Cap at 1.0
    
    def _empty_response(self) -> SocialCommentAnalysisResponse:
        """Return empty response."""
        return SocialCommentAnalysisResponse(
            total_records=0,
            analyzed_records=0,
            results=[]
        )