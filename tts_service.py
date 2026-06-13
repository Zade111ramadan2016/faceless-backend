import os
from google.cloud import texttospeech


def generate_audio(script: str, output_path: str) -> None:
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=script)

    # Using a natural WaveNet voice — free tier supports these
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Wavenet-D",  # Deep male voice, great for reels
        ssml_gender=texttospeech.SsmlVoiceGender.MALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.05,   # Slightly faster — works better for short-form video
        pitch=0.0,
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    with open(output_path, "wb") as f:
        f.write(response.audio_content)

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise ValueError("TTS returned empty audio file")
