import base64
from typing import Any
from google import genai
from google.genai import types
from app.core.config import settings
import wave
import io


class TTSService:
    def __init__(self) -> None:
        self.client = genai.Client(api_key = settings.gemini_api_key)
        self.model_name = "gemini-2.5-flash-preview-tts"
        self.web_search_model = "gemini-2.0-flash"
    
    def pcm_to_wav_base64(self, pcm_bytes: bytes, sample_rate: int = 24000, channels: int = 1) -> str:
        """
        Convert raw PCM bytes to WAV format and encode as base64 data URL
        """
        with io.BytesIO() as buf:
            with wave.open(buf, 'wb') as wav_file:
                wav_file.setnchannels(channels)        # mono or stereo
                wav_file.setsampwidth(2)               # 16-bit PCM (2 bytes)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_bytes)
            wav_bytes = buf.getvalue()
        
        b64_str = base64.b64encode(wav_bytes).decode('ascii')
        data_url = f"data:audio/wav;base64,{b64_str}"
        return data_url

    def explain_search(self, events: Any):
        """
        Extracts the title and description from all events and joins them into a single string.
        """
        
        voice_config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Kore',
                    )
                )
            ),
        )

        audio_response = self.client.models.generate_content(
            model=self.model_name,
            contents=f"Using a friendly tone, explain these events only telling relevant information: {events}",
            config=voice_config
        )

        data = audio_response.candidates[0].content.parts[0].inline_data.data
        data_uri = self.pcm_to_wav_base64(data) if data is not None else None
        return data_uri


tts_service = TTSService()