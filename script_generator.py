import os
import time
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

PLATFORM_HINTS = {
    "tiktok":    "fast-paced, punchy sentences, trending Gen-Z energy, max 60 words",
    "youtube":   "informative, slightly longer sentences, educational tone, max 120 words",
    "instagram": "aspirational, lifestyle-focused, motivational, max 80 words",
    "general":   "conversational, energetic, broad audience, max 100 words",
}

STYLE_HINTS = {
    "cinematic":  "dramatic, epic, cinematic narration style",
    "realistic":  "grounded, factual, documentary tone",
    "anime":      "adventurous, passionate, anime-inspired energy",
    "cartoon":    "fun, playful, lighthearted and upbeat",
    "comic":      "bold, punchy, comic book narrator style — short dramatic sentences",
}


def generate_script(topic: str, platform: str = "general", style: str = "cinematic") -> str:
    platform_hint = PLATFORM_HINTS.get(platform, PLATFORM_HINTS["general"])
    style_hint = STYLE_HINTS.get(style, STYLE_HINTS["cinematic"])

    prompt = f"""You are a professional short-form video scriptwriter.
Write a faceless reel script about: {topic}

Platform: {platform} — {platform_hint}
Visual style: {style} — {style_hint}

Rules:
- Hook in the first 3 seconds — start with a bold statement or question
- Spoken words only — no stage directions, no scene descriptions, no emojis
- This will be read by a text-to-speech voice
- End with a strong call to action (like, follow, share, comment)
- Write only the script text, nothing else"""

    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-pro",
    ]

    last_error = None
    for model_name in models_to_try:
        for attempt in range(3):
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                script = response.text.strip()
                if script:
                    return script
            except Exception as e:
                last_error = str(e)
                if "429" in str(e):
                    time.sleep(10)
                    continue
                break

    raise ValueError(f"All Gemini models failed. Last error: {last_error}")
