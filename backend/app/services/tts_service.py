from app.core.config import settings


class TextToSpeechError(RuntimeError):
    pass


async def synthesize_speech(text: str) -> bytes:
    if not settings.elevenlabs_api_key:
        raise TextToSpeechError("ElevenLabs API key is not configured")

    try:
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=settings.elevenlabs_voice_id,
            model_id=settings.elevenlabs_model_id,
            output_format=settings.elevenlabs_output_format,
        )
        if isinstance(audio, bytes):
            return audio
        return b"".join(audio)
    except Exception as exc:
        raise TextToSpeechError("ElevenLabs text-to-speech request failed") from exc
