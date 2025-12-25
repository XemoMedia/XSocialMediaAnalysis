"""
Sentiment analysis service using Hugging Face transformers.
Uses pre-trained models for accurate sentiment and emotion analysis.
"""
from transformers import pipeline
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Global pipelines (loaded once on service initialization)
sentiment_pipe: Optional[pipeline] = None
emotion_pipe: Optional[pipeline] = None


class SentimentService:
    """
    Service for performing sentiment analysis on text.
    Uses Hugging Face transformers models:
    - siebert/sentiment-roberta-large-english for sentiment
    - j-hartmann/emotion-english-distilroberta-base for emotions
    """
    
    def __init__(self):
        """
        Initialize the service and load models if not already loaded.
        """
        global sentiment_pipe, emotion_pipe
        
        if sentiment_pipe is None:
            logger.info("Loading sentiment model...")
            sentiment_pipe = pipeline(
                "sentiment-analysis",
                model="siebert/sentiment-roberta-large-english"
            )
            logger.info("Sentiment model loaded successfully")
        
        if emotion_pipe is None:
            logger.info("Loading emotion model...")
            emotion_pipe = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None  # Returns all scores (replaces deprecated return_all_scores=True)
            )
            logger.info("Emotion model loaded successfully")
        
        self.sentiment_pipe = sentiment_pipe
        self.emotion_pipe = emotion_pipe

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "sentiment": "neutral",
            "polarity": 0.0,
            "sentiment_score": 0.0,
            "emotion": "neutral",
            "emotion_scores": []
        }

    def _build_result(
        self,
        sentiment_result: Dict[str, Any],
        emotion_result: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        sentiment_label = sentiment_result["label"].lower()
        sentiment_score = float(sentiment_result["score"])

        if sentiment_label == "positive":
            sentiment = "positive"
            polarity = sentiment_score
        elif sentiment_label == "negative":
            sentiment = "negative"
            polarity = -sentiment_score
        else:
            sentiment = "neutral"
            polarity = 0.0

        emotion_scores: List[Dict[str, Any]] = []
        top_emotion = "neutral"
        if emotion_result:
            sorted_emotions = sorted(emotion_result, key=lambda item: item["score"], reverse=True)
            top_emotion = sorted_emotions[0]["label"].lower()
            emotion_scores = [
                {"emotion": item["label"].lower(), "score": round(float(item["score"]), 4)}
                for item in sorted_emotions
            ]

        return {
            "sentiment": sentiment,
            "polarity": round(polarity, 3),
            "sentiment_score": round(sentiment_score, 4),
            "emotion": top_emotion,
            "emotion_scores": emotion_scores,
        }

    @staticmethod
    def _first_result(output: Any) -> Dict[str, Any]:
        if isinstance(output, list):
            return output[0] if output else {}
        return output or {}

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment and emotion of a single text.
        """
        if not text or not text.strip():
            return self._empty_result()

        try:
            sentiment_result = self.sentiment_pipe(text[:512])[0]
            emotion_result = self.emotion_pipe(text[:512])[0]
            return self._build_result(sentiment_result, emotion_result)
        except Exception as exc:  # pragma: no cover
            logger.error("Error analyzing text: %s", exc, exc_info=True)
            return self._empty_result()

    def analyze_multiple(self, texts: List[str], batch_size: int = 16) -> List[Dict[str, Any]]:
        """
        Analyze sentiment and emotion of multiple texts leveraging batched transformer calls.
        """
        if not texts:
            return []

        sanitized = [text or "" for text in texts]
        results = [self._empty_result() for _ in sanitized]

        valid_indices = [idx for idx, text in enumerate(sanitized) if text.strip()]
        if not valid_indices:
            return results

        valid_texts = [sanitized[idx][:512] for idx in valid_indices]

        try:
            sentiment_outputs = self.sentiment_pipe(
                valid_texts,
                batch_size=batch_size,
                truncation=True,
            )
            emotion_outputs = self.emotion_pipe(
                valid_texts,
                batch_size=batch_size,
                truncation=True,
            )
        except Exception as exc:
            logger.error("Error running batched sentiment analysis: %s", exc, exc_info=True)
            return results

        for output_idx, original_idx in enumerate(valid_indices):
            try:
                sentiment_output = self._first_result(sentiment_outputs[output_idx])
                if not sentiment_output:
                    raise ValueError("empty sentiment output")
                emotion_result = emotion_outputs[output_idx]
                results[original_idx] = self._build_result(sentiment_output, emotion_result)
            except Exception as exc:  # pragma: no cover
                logger.error("Error post-processing batched sentiment result: %s", exc, exc_info=True)
                results[original_idx] = self._empty_result()

        return results
    
    def save_analysis_result(
        self,
        repository,
        source_id: str,
        source_type: str,
        text: str,
        analysis_result: Dict[str, Any]
    ) -> Any:
        """
        Save sentiment analysis result to the database.
        
        Args:
            repository: SentimentAnalysisRepository instance
            source_id: ID of the source (Post, Comment, or Reply ID) as string
            source_type: Type of source (POST, COMMENT, or REPLY)
            text: The analyzed text
            analysis_result: Result from analyze_text() method
            
        Returns:
            Saved SentimentAnalysis entity
        """
        from app.models.sentiment_analysis_model import SentimentAnalysis
        from decimal import Decimal
        
        try:
            # Create sentiment analysis record
            sentiment_analysis = SentimentAnalysis(
                source_id=source_id,
                source_type=source_type.upper(),  # Ensure uppercase
                sentiment=analysis_result.get("sentiment", "neutral"),
                sentiment_score=Decimal(str(analysis_result.get("sentiment_score", 0.0))),
                top_emotion=analysis_result.get("emotion", "neutral"),
                emotion_scores=analysis_result.get("emotion_scores", []),
                analyzed_text=text
            )
            
            # Save to database
            saved_record = repository.save(sentiment_analysis)
            logger.info(f"Saved sentiment analysis for {source_type} ID {source_id}")
            return saved_record
            
        except Exception as e:
            logger.error(f"Error saving sentiment analysis: {e}", exc_info=True)
            raise

