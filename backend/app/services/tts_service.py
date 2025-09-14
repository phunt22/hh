import base64
from typing import Any
from google import genai
from google.genai import types
from app.core.config import settings


class TTSService:
    def __init__(self) -> None:
        self.client = genai.Client(api_key = settings.gemini_api_key)
        self.model_name = "gemini-2.5-flash-preview-tts"
        self.web_search_model = "gemini-2.0-flash"

    def explain_search(self, events: Any):
        """
        Extracts the title and description from all events and joins them into a single string.
        """
        if not events:
            return ""

        event_strings = []
        for event in events:
            # Try both dict and object access
            title = ""
            description = ""
            if isinstance(event, dict):
                title = event.get("title", "")
                description = event.get("description", "")
            else:
                title = getattr(event, "title", "")
                description = getattr(event, "description", "")
            event_strings.append(f"{title}: {description}")

        web_query = " ".join(event_strings)
        
        
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

        print(audio_response)

        data = audio_response.candidates[0].content.parts[0].inline_data.data
        # Encode to base64
        b64_bytes = base64.b64encode(data)

        # Convert to string (utf-8)
        b64_string = b64_bytes.decode('utf-8')

        # Optionally make a data URI so browsers/clients can play it easily
        mime_type = audio_response.candidates[0].content.parts[0].inline_data.mime_type
        data_uri = f"data:{mime_type};base64,{b64_string}"
        return data_uri


tts_service = TTSService()