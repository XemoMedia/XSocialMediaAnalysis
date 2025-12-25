"""
LLM-backed helper service for language, intent, toxicity, sarcasm, and topic/entity extraction.
"""
from __future__ import annotations

from typing import List, Sequence, Tuple
from transformers import pipeline

# Cache heavy pipelines at module scope
language_pipe = None
intent_pipe = None
toxicity_pipe = None
sarcasm_pipe = None
ner_pipe = None


class InsightLLMService:
    """Wraps transformers pipelines to derive higher-level insights from text."""

    INTENT_LABELS = ["complaint", "question", "request", "praise", "statement"]
    TOPIC_LABELS = [
        "product issue",
        "pricing",
        "usability",
        "support",
        "delivery",
        "feature request",
        "praise",
        "other",
    ]

    def __init__(self) -> None:
        global language_pipe, intent_pipe, toxicity_pipe, sarcasm_pipe, ner_pipe

        if language_pipe is None:
            language_pipe = pipeline(
                "text-classification",
                model="papluca/xlm-roberta-base-language-detection",
                truncation=True,
            )
        if intent_pipe is None:
            intent_pipe = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                truncation=True,
            )
        if toxicity_pipe is None:
            toxicity_pipe = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                truncation=True,
            )
        if sarcasm_pipe is None:
            sarcasm_pipe = pipeline(
                "text-classification",
                model="helinivan/english-sarcasm-detector",
                truncation=True,
            )
        if ner_pipe is None:
            ner_pipe = pipeline(
                "token-classification",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple",
            )

        self.language_pipe = language_pipe
        self.intent_pipe = intent_pipe
        self.toxicity_pipe = toxicity_pipe
        self.sarcasm_pipe = sarcasm_pipe
        self.ner_pipe = ner_pipe

    @staticmethod
    def _prepare_texts(texts: Sequence[str]) -> Tuple[List[str], List[str], List[int]]:
        sanitized = [text or "" for text in texts]
        valid_indices = [idx for idx, text in enumerate(sanitized) if text.strip()]
        truncated = [sanitized[idx][:512] for idx in valid_indices]
        return sanitized, truncated, valid_indices

    @staticmethod
    def _first_result(result):
        if isinstance(result, list):
            return result[0]
        return result

    def detect_language(self, text: str) -> str:
        if not text:
            return "unknown"
        result = self.language_pipe(text[:512])[0]
        return result["label"].lower()

    def detect_languages(self, texts: Sequence[str], batch_size: int = 32) -> List[str]:
        if not texts:
            return []

        sanitized, valid_texts, valid_indices = self._prepare_texts(texts)
        languages = ["unknown"] * len(sanitized)
        if not valid_indices:
            return languages

        outputs = self.language_pipe(
            valid_texts,
            batch_size=batch_size,
            truncation=True,
        )

        for output_idx, original_idx in enumerate(valid_indices):
            result = self._first_result(outputs[output_idx])
            languages[original_idx] = result["label"].lower()

        return languages

    def classify_intent(self, text: str) -> Tuple[str, float]:
        if not text:
            return "unknown", 0.0
        result = self.intent_pipe(
            sequences=text[:512],
            candidate_labels=self.INTENT_LABELS,
            multi_label=False,
        )
        return result["labels"][0], float(result["scores"][0])

    def classify_intents(
        self,
        texts: Sequence[str],
        batch_size: int = 8,
    ) -> List[Tuple[str, float]]:
        if not texts:
            return []

        sanitized, valid_texts, valid_indices = self._prepare_texts(texts)
        intents: List[Tuple[str, float]] = [("unknown", 0.0) for _ in sanitized]
        if not valid_indices:
            return intents

        outputs = self.intent_pipe(
            sequences=valid_texts,
            candidate_labels=self.INTENT_LABELS,
            multi_label=False,
            batch_size=batch_size,
        )

        for output_idx, original_idx in enumerate(valid_indices):
            result = outputs[output_idx]
            intents[original_idx] = (
                result["labels"][0].lower(),
                float(result["scores"][0]),
            )

        return intents

    def detect_toxicity(self, text: str) -> Tuple[str, float]:
        if not text:
            return "safe", 0.0
        result = self.toxicity_pipe(text[:512])[0]
        label = result["label"].lower()
        if label in {"toxic", "LABEL_1"}:
            return "toxic", float(result["score"])
        return "safe", 1.0 - float(result["score"])

    def detect_toxicity_bulk(
        self,
        texts: Sequence[str],
        batch_size: int = 32,
    ) -> List[Tuple[str, float]]:
        if not texts:
            return []

        sanitized, valid_texts, valid_indices = self._prepare_texts(texts)
        toxicity: List[Tuple[str, float]] = [("safe", 0.0) for _ in sanitized]
        if not valid_indices:
            return toxicity

        outputs = self.toxicity_pipe(
            valid_texts,
            batch_size=batch_size,
            truncation=True,
        )

        for output_idx, original_idx in enumerate(valid_indices):
            result = self._first_result(outputs[output_idx])
            label = result["label"].lower()
            if label in {"toxic", "label_1"}:
                toxicity[original_idx] = ("toxic", float(result["score"]))
            else:
                toxicity[original_idx] = ("safe", 1.0 - float(result["score"]))

        return toxicity

    def detect_sarcasm(self, text: str) -> Tuple[str, float]:
        if not text:
            return "not_sarcastic", 0.0
        result = self.sarcasm_pipe(text[:512])[0]
        label = "sarcastic" if "sarcasm" in result["label"].lower() else "not_sarcastic"
        return label, float(result["score"])

    def detect_sarcasm_bulk(
        self,
        texts: Sequence[str],
        batch_size: int = 32,
    ) -> List[Tuple[str, float]]:
        if not texts:
            return []

        sanitized, valid_texts, valid_indices = self._prepare_texts(texts)
        sarcasm: List[Tuple[str, float]] = [("not_sarcastic", 0.0) for _ in sanitized]
        if not valid_indices:
            return sarcasm

        outputs = self.sarcasm_pipe(
            valid_texts,
            batch_size=batch_size,
            truncation=True,
        )

        for output_idx, original_idx in enumerate(valid_indices):
            result = self._first_result(outputs[output_idx])
            label = "sarcastic" if "sarcasm" in result["label"].lower() else "not_sarcastic"
            sarcasm[original_idx] = (label, float(result["score"]))

        return sarcasm

    def extract_topics_and_entities(self, text: str) -> Tuple[List[str], List[str]]:
        if not text:
            return [], []

        topic_result = self.intent_pipe(
            sequences=text[:512],
            candidate_labels=self.TOPIC_LABELS,
            multi_label=True,
        )
        topics = [
            label
            for label, score in zip(topic_result["labels"], topic_result["scores"])
            if score >= 0.25
        ]

        ner_result = self.ner_pipe(text[:512])
        entities = []
        for item in ner_result:
            entity = item.get("word")
            if entity:
                cleaned = entity.replace("##", "")
                if cleaned not in entities:
                    entities.append(cleaned)

        return topics, entities

    def extract_topics_and_entities_bulk(
        self,
        texts: Sequence[str],
        batch_size: int = 8,
    ) -> List[Tuple[List[str], List[str]]]:
        if not texts:
            return []

        sanitized, valid_texts, valid_indices = self._prepare_texts(texts)
        results: List[Tuple[List[str], List[str]]] = [([], []) for _ in sanitized]
        if not valid_indices:
            return results

        topic_outputs = self.intent_pipe(
            sequences=valid_texts,
            candidate_labels=self.TOPIC_LABELS,
            multi_label=True,
            batch_size=batch_size,
        )
        ner_outputs = self.ner_pipe(
            valid_texts,
            batch_size=batch_size,
        )

        for output_idx, original_idx in enumerate(valid_indices):
            topic_result = topic_outputs[output_idx]
            topics = [
                label.lower()
                for label, score in zip(topic_result["labels"], topic_result["scores"])
                if score >= 0.25
            ]

            entity_result = ner_outputs[output_idx]
            entities: List[str] = []
            for item in entity_result:
                entity = item.get("word")
                if entity:
                    cleaned = entity.replace("##", "")
                    if cleaned not in entities:
                        entities.append(cleaned)

            results[original_idx] = (topics, entities)

        return results

