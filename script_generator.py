import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

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

    response = model.generate_content(prompt)
    script = response.text.strip()
    if not script:
        raise ValueError("Gemini returned an empty script")
    return script
