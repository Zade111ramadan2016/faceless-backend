import os
import requests

GOOGLE_TTS_API_KEY = os.environ["GOOGLE_TTS_API_KEY"]
TTS_URL = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_TTS_API_KEY}"


def generate_audio(script: str, output_path: str) -> None:
    payload = {
        "input": {"text": script},
        "voice": {
            "languageCode": "en-US",
            "name": "en-US-Wavenet-D",
            "ssmlGender": "MALE"
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": 1.05,
            "pitch": 0.0
        }
    }

    response = requests.post(TTS_URL, json=payload, timeout=30)

    if response.status_code != 200:
        raise ValueError(f"TTS API error {response.status_code}: {response.text}")

    data = response.json()
    audio_content = data.get("audioContent")

    if not audio_content:
        raise ValueError("TTS returned empty audio content")

    import base64
    audio_bytes = base64.b64decode(audio_content)

    with open(output_path, "wb") as f:
        f.write(audio_bytes)

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise ValueError("TTS output file is empty")
