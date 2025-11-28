"""
Sentiment analysis service using Hugging Face transformers.
Uses pre-trained models for accurate sentiment and emotion analysis.
"""
from transformers import pipeline
from typing import Dict, List, Optional
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
    
    def analyze_text(self, text: str) -> Dict[str, any]:
        """
        Analyze sentiment and emotion of a single text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with 'sentiment' (label), 'polarity' (score), 'emotion', and 'emotion_scores'
        """
        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "polarity": 0.0,
                "emotion": "neutral",
                "emotion_scores": []
            }
        
        try:
            # Analyze sentiment using RoBERTa model
            sentiment_result = self.sentiment_pipe(text)[0]
            sentiment_label = sentiment_result['label'].lower()
            sentiment_score = sentiment_result['score']
            
            # Convert sentiment label to standard format and calculate polarity
            if sentiment_label == 'positive':
                sentiment = "positive"
                polarity = sentiment_score  # 0.0 to 1.0
            elif sentiment_label == 'negative':
                sentiment = "negative"
                polarity = -sentiment_score  # -1.0 to 0.0
            else:
                sentiment = "neutral"
                polarity = 0.0
            
            # Analyze emotion using emotion model
            emotion_result = self.emotion_pipe(text)[0]
            
            # Get all emotions with scores
            emotion_scores = []
            top_emotion = "neutral"
            
            if emotion_result and len(emotion_result) > 0:
                # Sort by score (descending) to get top emotion first
                sorted_emotions = sorted(emotion_result, key=lambda x: x['score'], reverse=True)
                top_emotion = sorted_emotions[0]['label'].lower()
                
                # Create list of all emotions with scores
                emotion_scores = [
                    {
                        "emotion": item['label'].lower(),
                        "score": round(float(item['score']), 4)
                    }
                    for item in sorted_emotions
                ]
            
            return {
                "sentiment": sentiment,
                "polarity": round(polarity, 3),
                "sentiment_score": round(float(sentiment_score), 4),  # Score from 0-1
                "emotion": top_emotion,
                "emotion_scores": emotion_scores
            }
        except Exception as e:
            logger.error(f"Error analyzing text: {e}", exc_info=True)
            return {
                "sentiment": "neutral",
                "polarity": 0.0,
                "sentiment_score": 0.0,
                "emotion": "neutral",
                "emotion_scores": []
            }
    
    def analyze_multiple(self, texts: List[str]) -> List[Dict[str, any]]:
        """
        Analyze sentiment and emotion of multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of sentiment analysis results
        """
        return [self.analyze_text(text) for text in texts]
    
    def save_analysis_result(
        self,
        repository,
        source_id: str,
        source_type: str,
        text: str,
        analysis_result: Dict[str, any]
    ) -> any:
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

