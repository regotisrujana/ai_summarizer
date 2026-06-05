import json
import math
import os
import re
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DOCUMENTS_PATH = DATA_DIR / "rag_documents.json"
EVAL_PATH = DATA_DIR / "rag_eval.json"

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "how", "in", "is", "it", "of", "on", "or", "that", "the", "this",
    "to", "what", "when", "where", "which", "why", "with",
}


def _load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _tokenize(text):
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in STOP_WORDS and len(token) > 1
    ]


class RAGEngine:
    def __init__(self, documents=None):
        self.documents = documents or _load_json(DOCUMENTS_PATH)
        self.doc_tokens = [
            _tokenize(f"{doc['title']} {doc['category']} {doc['text']}")
            for doc in self.documents
        ]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.average_doc_length = sum(self.doc_lengths) / max(len(self.doc_lengths), 1)
        self.term_frequencies = [Counter(tokens) for tokens in self.doc_tokens]
        self.document_frequencies = Counter()
        for tokens in self.doc_tokens:
            self.document_frequencies.update(set(tokens))

    def search(self, question, top_k=3):
        query_tokens = _tokenize(question)
        scored = [
            (self._bm25_score(query_tokens, index), doc)
            for index, doc in enumerate(self.documents)
        ]
        ranked = sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]
        return [
            {
                "id": doc["id"],
                "title": doc["title"],
                "category": doc["category"],
                "text": doc["text"],
                "score": round(score, 4),
            }
            for score, doc in ranked
            if score > 0
        ]

    def answer(self, question, top_k=3):
        sources = self.search(question, top_k=top_k)
        if not sources:
            return {
                "answer": "I do not know from the available AI summarization and RAG sources.",
                "sources": [],
            }
        return {"answer": _generate_answer(question, sources), "sources": sources}

    def evaluate(self, top_k=3):
        eval_items = _load_json(EVAL_PATH)
        results = []
        top1_hits = 0
        topk_hits = 0
        reciprocal_ranks = []
        answer_f1_scores = []

        for item in eval_items:
            sources = self.search(item["question"], top_k=top_k)
            ranked_ids = [source["id"] for source in sources]
            expected = set(item["expected_doc_ids"])
            top1_hit = bool(ranked_ids and ranked_ids[0] in expected)
            topk_hit = any(doc_id in expected for doc_id in ranked_ids)
            rank = next(
                (idx + 1 for idx, doc_id in enumerate(ranked_ids) if doc_id in expected),
                None,
            )
            reciprocal_rank = 1 / rank if rank else 0
            generated = _extractive_answer(item["question"], sources)
            answer_f1 = _token_f1(generated, item["reference_answer"])

            top1_hits += int(top1_hit)
            topk_hits += int(topk_hit)
            reciprocal_ranks.append(reciprocal_rank)
            answer_f1_scores.append(answer_f1)
            results.append(
                {
                    "question": item["question"],
                    "expected_doc_ids": item["expected_doc_ids"],
                    "retrieved_doc_ids": ranked_ids,
                    "top1_hit": top1_hit,
                    "topk_hit": topk_hit,
                    "reciprocal_rank": round(reciprocal_rank, 3),
                    "answer_f1": round(answer_f1, 3),
                }
            )

        total = len(eval_items) or 1
        return {
            "document_count": len(self.documents),
            "question_count": len(eval_items),
            "top1_accuracy": round(top1_hits / total, 3),
            "topk_accuracy": round(topk_hits / total, 3),
            "mean_reciprocal_rank": round(sum(reciprocal_ranks) / total, 3),
            "answer_quality_f1": round(sum(answer_f1_scores) / total, 3),
            "results": results,
        }

    def _bm25_score(self, query_tokens, doc_index):
        score = 0.0
        k1 = 1.5
        b = 0.75
        doc_length = self.doc_lengths[doc_index] or 1
        frequencies = self.term_frequencies[doc_index]
        total_docs = len(self.documents)

        for token in query_tokens:
            if token not in frequencies:
                continue
            docs_with_token = self.document_frequencies[token]
            idf = math.log(1 + (total_docs - docs_with_token + 0.5) / (docs_with_token + 0.5))
            term_frequency = frequencies[token]
            denominator = term_frequency + k1 * (
                1 - b + b * doc_length / self.average_doc_length
            )
            score += idf * (term_frequency * (k1 + 1)) / denominator
        return score


def _generate_answer(question, sources):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return _extractive_answer(question, sources)

    from groq import Groq

    context = "\n\n".join(
        f"[{source['id']}] {source['title']}: {source['text']}"
        for source in sources
    )
    prompt = f"""You are a domain-specific RAG chatbot for AI summarization and retrieval systems.
Use only the provided sources. If the sources do not answer the question, say you do not know.
Cite source ids in square brackets.

Sources:
{context}

Question: {question}

Answer:"""
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=450,
    )
    return response.choices[0].message.content.strip()


def _extractive_answer(question, sources):
    if not sources:
        return "I do not know from the available AI summarization and RAG sources."

    useful_sentences = []
    query_terms = set(_tokenize(question))
    for source in sources:
        sentences = re.split(r"(?<=[.!?])\s+", source["text"])
        best_sentence = max(
            sentences,
            key=lambda sentence: len(query_terms.intersection(_tokenize(sentence))),
        )
        useful_sentences.append(f"{best_sentence} [{source['id']}]")
    return " ".join(useful_sentences)


def _token_f1(answer, reference):
    answer_tokens = _tokenize(answer)
    reference_tokens = _tokenize(reference)
    if not answer_tokens or not reference_tokens:
        return 0.0

    answer_counts = Counter(answer_tokens)
    reference_counts = Counter(reference_tokens)
    overlap = sum((answer_counts & reference_counts).values())
    if overlap == 0:
        return 0.0

    precision = overlap / len(answer_tokens)
    recall = overlap / len(reference_tokens)
    return 2 * precision * recall / (precision + recall)


rag_engine = RAGEngine()
