"""
AI Content Summarizer API — single POST /summarize endpoint.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from pydantic import BaseModel

from database import save_summary
from rag import rag_engine
from scraper import scrape_url

load_dotenv()

app = FastAPI(title="AI Content Summarizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq on-demand tier: ~6000 tokens per request (input + output combined)
_GROQ_CHARS_PER_TOKEN = 1.7
_GROQ_MAX_REQUEST_TOKENS = 5800
_GROQ_OUTPUT_TOKENS = 800
_MAX_CHUNK_CHARS = int(
    (_GROQ_MAX_REQUEST_TOKENS - 200 - _GROQ_OUTPUT_TOKENS)
    / _GROQ_CHARS_PER_TOKEN
    * 0.72
)

_EXTRACT_PROMPT = """Read the content below and list ALL important points as bullet points.
- Include every main idea, key fact, argument, and conclusion.
- Do not skip topics. One clear bullet per point (start each line with "- ").
- Be concise per bullet but thorough overall.

Content:
{content}

Important points:"""

_MERGE_PROMPT = """Combine the bullet lists below into ONE final list.
- Remove duplicates and merge similar points.
- Keep every unique important idea.
- Use "- " for each bullet.

{parts}

Final important points:"""


class SummarizeRequest(BaseModel):
    text: str = ""
    url: str = ""


class ChatRequest(BaseModel):
    question: str
    top_k: int = 3


@app.get("/")
def health():
    return {"status": "ok", "features": ["summarization", "rag_chatbot"]}


@app.post("/summarize")
def summarize(request: SummarizeRequest):
    url_used = ""
    content = ""

    if request.url and request.url.strip():
        try:
            url_used = request.url.strip()
            content = scrape_url(url_used)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"URL scraping failed: {exc}",
            ) from exc
    elif request.text and request.text.strip():
        content = request.text.strip()
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide article text or a URL to summarize.",
        )

    try:
        summary = generate_summary(content)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI summarization failed: {exc}",
        ) from exc

    try:
        save_summary(
            original_text=content[:8000],
            url=url_used,
            summary=summary,
            length="key_points",
        )
    except Exception as exc:
        print(f"MongoDB save warning: {exc}")

    return {"summary": summary}


@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    top_k = min(max(request.top_k, 1), 5)
    return rag_engine.answer(question, top_k=top_k)


@app.get("/rag/evaluate")
def evaluate_rag():
    return rag_engine.evaluate(top_k=3)


def _truncate_chunk(text: str) -> str:
    text = text.strip()
    if len(text) <= _MAX_CHUNK_CHARS:
        return text
    portion = (_MAX_CHUNK_CHARS - 40) // 2
    return (
        text[:portion]
        + "\n\n[...]\n\n"
        + text[-portion:]
    )


def _groq_complete(prompt: str, max_tokens: int = _GROQ_OUTPUT_TOKENS) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def _extract_points(content: str) -> str:
    chunk = _truncate_chunk(content)
    return _groq_complete(_EXTRACT_PROMPT.format(content=chunk), max_tokens=500)


def generate_summary(content: str) -> str:
    """
    Return all important points as a bullet list.
    Long content: extract from start + end, then merge (stays under Groq token limits).
    """
    content = content.strip()

    if len(content) <= _MAX_CHUNK_CHARS:
        return _extract_points(content)

    # Long video/article: summarize beginning and ending sections, then merge
    portion = _MAX_CHUNK_CHARS - 40
    start = content[:portion]
    end = content[-portion:]

    points_start = _extract_points(start)
    points_end = _extract_points(end)

    parts = f"From the beginning:\n{points_start}\n\nFrom the ending:\n{points_end}"
    return _groq_complete(
        _MERGE_PROMPT.format(parts=parts),
        max_tokens=_GROQ_OUTPUT_TOKENS,
    )
