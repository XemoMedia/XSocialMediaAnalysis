"""
Repository abstraction for the media_analysis_analytics table.
"""
from datetime import datetime, timezone
import json
from typing import Iterable, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.media_analysis_analytic_model import MediaAnalysisAnalytic
from app.schemas.social_comment_analysis_schemas import SocialCommentInsight


class MediaAnalysisAnalyticRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_from_insight(self, insight: SocialCommentInsight) -> MediaAnalysisAnalytic:
        entity = self._upsert_without_commit(insight)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def bulk_upsert_from_insights(self, insights: Iterable[SocialCommentInsight]) -> None:
        last_entity: Optional[MediaAnalysisAnalytic] = None
        for insight in insights:
            last_entity = self._upsert_without_commit(insight)
        self.db.commit()
        if last_entity is not None:
            self.db.refresh(last_entity)

    def _upsert_without_commit(self, insight: SocialCommentInsight) -> MediaAnalysisAnalytic:
        entity: Optional[MediaAnalysisAnalytic] = (
            self.db.query(MediaAnalysisAnalytic)
            .filter(MediaAnalysisAnalytic.social_comment_analysis_id == insight.id)
            .one_or_none()
        )

        topics_payload = json.dumps(insight.topics) if insight.topics else None
        entities_payload = json.dumps(insight.entities) if insight.entities else None
        metadata_payload = json.dumps(
            {
                "sentiment_score": insight.sentiment_score,
                "polarity": insight.polarity,
                "intent_confidence": insight.intent_confidence,
                "toxicity_score": insight.toxicity_score,
                "sarcasm_score": insight.sarcasm_score,
            }
        )
        now = datetime.now(timezone.utc)

        if entity:
            entity.language = insight.language
            entity.sentiment = insight.sentiment
            entity.intent = insight.intent
            entity.toxicity = insight.toxicity
            entity.emotion = insight.emotion
            entity.sarcasm = insight.sarcasm
            entity.risk_index = insight.risk_index
            entity.topics = topics_payload
            entity.entities = entities_payload
            entity.notes = metadata_payload
            entity.last_modified_date = now
        else:
            entity = MediaAnalysisAnalytic(
                id=str(uuid4()),
                social_comment_analysis_id=insight.id,
                language=insight.language,
                sentiment=insight.sentiment,
                intent=insight.intent,
                toxicity=insight.toxicity,
                emotion=insight.emotion,
                sarcasm=insight.sarcasm,
                risk_index=insight.risk_index,
                topics=topics_payload,
                entities=entities_payload,
                notes=metadata_payload,
                created_date=now,
                last_modified_date=now,
            )
            self.db.add(entity)

        return entity

