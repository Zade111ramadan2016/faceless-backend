import os
import re
import requests

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"

STYLE_PROMPT_TEMPLATES = {
    "anime": "anime style, {topic}, cinematic, vibrant colors, detailed background, studio ghibli inspired, no text, no watermark",
    "cartoon": "cartoon style, {topic}, colorful, fun, pixar inspired, bright lighting, no text, no watermark",
    "comic": "comic book style, {topic}, bold ink outlines, halftone dots, dramatic shadows, marvel inspired, no text, no watermark",
}


def fetch_style_images(topic: str, style: str, script: str, clips_dir: str) -> None:
    sentences = _split_script(script)
    template = STYLE_PROMPT_TEMPLATES.get(style, STYLE_PROMPT_TEMPLATES["anime"])

    for i, sentence in enumerate(sentences[:8]):
        prompt_text = template.format(topic=f"{topic}, {_keywords(sentence)}")
        encoded = requests.utils.quote(prompt_text)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true"

        dest = os.path.join(clips_dir, f"frame_{i:02d}.jpg")
        _download(url, dest)


def _split_script(script: str) -> list:
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 10]


def _keywords(sentence: str) -> str:
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "and", "or",
                 "but", "in", "on", "at", "to", "for", "of", "with", "you",
                 "your", "this", "that", "it", "its", "be", "have", "has"}
    words = re.findall(r'\b\w+\b', sentence.lower())
    keywords = [w for w in words if w not in stopwords and len(w) > 3]
    return " ".join(keywords[:5])


def _download(url: str, dest: str) -> None:
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
    except Exception as e:
        raise ValueError(f"Failed to download image from Pollinations: {e}")
