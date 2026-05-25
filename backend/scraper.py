"""
Extract text from URLs: YouTube transcripts or article pages (newspaper3k).
"""

import re
from urllib.parse import parse_qs, urlparse

import nltk
from newspaper import Article
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    IpBlocked,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
)

# newspaper3k needs NLTK tokenizers (first run downloads them)
for resource in ("punkt", "punkt_tab"):
    try:
        nltk.data.find(f"tokenizers/{resource}")
    except LookupError:
        nltk.download(resource, quiet=True)

# English first, then common languages (auto-captions are often non-English)
EN_LANGS = ["en", "en-US", "en-GB", "en-IN", "en-AU", "en-CA"]
FALLBACK_LANGS = [
    "hi",
    "te",
    "ta",
    "es",
    "fr",
    "de",
    "pt",
    "ja",
    "ko",
    "zh",
    "zh-Hans",
    "zh-Hant",
    "ar",
    "ru",
    "it",
]


def _is_youtube_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().replace("www.", "")
    return host in ("youtube.com", "youtu.be", "m.youtube.com")


def _youtube_video_id(url: str) -> str:
    """Parse video ID from common YouTube URL formats."""
    parsed = urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")

    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif "/shorts/" in parsed.path:
        video_id = parsed.path.split("/shorts/")[-1].split("/")[0]
    elif "/embed/" in parsed.path:
        video_id = parsed.path.split("/embed/")[-1].split("/")[0]
    else:
        query = parse_qs(parsed.query)
        video_id = query.get("v", [None])[0]

    if not video_id or not re.fullmatch(r"[\w-]{11}", video_id):
        raise ValueError("Could not read YouTube video ID from this URL.")
    return video_id


def _text_from_fetched(fetched) -> str:
    text = " ".join(snippet.text for snippet in fetched.snippets).strip()
    if len(text) < 50:
        raise ValueError(
            "Transcript is too short to summarize. Paste more content instead."
        )
    return text


def _scrape_youtube(url: str) -> str:
    """Fetch captions/transcript from a YouTube video (any available language)."""
    video_id = _youtube_video_id(url)
    api = YouTubeTranscriptApi()

    try:
        transcript_list = api.list(video_id)
    except TranscriptsDisabled as exc:
        raise ValueError(
            "Transcripts are disabled for this video. Paste the text instead."
        ) from exc
    except VideoUnavailable as exc:
        raise ValueError("YouTube video not found or is private.") from exc
    except VideoUnplayable as exc:
        raise ValueError(
            "This video cannot be played (removed, restricted, or blocked)."
        ) from exc
    except (RequestBlocked, IpBlocked) as exc:
        raise ValueError(
            "YouTube blocked the request. Wait a minute and retry, or paste the transcript."
        ) from exc
    except CouldNotRetrieveTranscript as exc:
        raise ValueError(f"Could not load YouTube captions: {exc}") from exc

    manual = list(transcript_list._manually_created_transcripts.keys())
    generated = list(transcript_list._generated_transcripts.keys())
    all_available = manual + [code for code in generated if code not in manual]

    if not all_available:
        raise ValueError(
            "This video has no captions. On YouTube: ⋮ → Show transcript, or "
            "enable CC/subtitles, then try again. You can also paste text below."
        )

    # 1) English (manual + auto-generated)
    for finder_name in ("find_transcript", "find_generated_transcript"):
        finder = getattr(transcript_list, finder_name)
        try:
            return _text_from_fetched(finder(EN_LANGS).fetch())
        except NoTranscriptFound:
            pass
        except Exception:
            pass

    # 2) Any language YouTube lists for this video
    try:
        return _text_from_fetched(
            transcript_list.find_transcript(all_available).fetch()
        )
    except NoTranscriptFound:
        pass
    except Exception:
        pass

    # 3) Common languages (e.g. auto Hindi captions)
    try:
        return _text_from_fetched(
            transcript_list.find_transcript(FALLBACK_LANGS).fetch()
        )
    except NoTranscriptFound:
        pass
    except Exception:
        pass

    # 4) First transcript that actually downloads
    for transcript in transcript_list:
        try:
            return _text_from_fetched(transcript.fetch())
        except Exception:
            continue

    # 5) Translate any track to English
    for transcript in transcript_list:
        if transcript.is_translatable:
            try:
                return _text_from_fetched(transcript.translate("en").fetch())
            except Exception:
                continue

    raise ValueError(
        "Could not download captions for this video. Make sure subtitles/CC are "
        "turned on in YouTube, or paste the transcript in the text box."
    )


def _scrape_article(url: str) -> str:
    """Download and parse a normal web article."""
    article = Article(url)
    article.download()
    article.parse()

    text = (article.text or "").strip()
    if len(text) < 50:
        raise ValueError(
            "Could not extract enough text from this URL. "
            "Try pasting the article text instead."
        )
    return text


def scrape_url(url: str) -> str:
    """Route YouTube URLs to transcript API; everything else to newspaper3k."""
    if _is_youtube_url(url):
        return _scrape_youtube(url)
    return _scrape_article(url)
