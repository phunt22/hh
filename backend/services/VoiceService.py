from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
from typing import Optional
import os
from io import BytesIO
import base64

app = FastAPI()

class VoiceRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"  # Default Rachel voice
    model_id: Optional[str] = "eleven_monolingual_v1"
    voice_settings: Optional[dict] = None

class VoiceResponse(BaseModel):
    audio_base64: str
    content_type: str = "audio/mpeg"

class ElevenLabsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
    
    async def text_to_speech(self, 
                           text: str, 
                           voice_id: str = "21m00Tcm4TlvDq8ikWAM",
                           model_id: str = "eleven_monolingual_v1") -> bytes:
        """Convert text to speech using ElevenLabs API"""
        
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        data = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=self.headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"ElevenLabs API error: {response.text}"
                )
            
            return response.content
    
    async def get_voices(self):
        """Get available voices from ElevenLabs"""
        url = f"{self.base_url}/voices"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers={
                "xi-api-key": self.api_key
            })
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch voices"
                )

# Initialize service
elevenlabs_service = ElevenLabsService(os.getenv("ELEVENLABS_API_KEY"))

@app.post("/generate-voice", response_model=VoiceResponse)
async def generate_voice(request: VoiceRequest):
    """Generate voice from text using ElevenLabs"""
    try:
        # Generate audio
        audio_bytes = await elevenlabs_service.text_to_speech(
            text=request.text,
            voice_id=request.voice_id,
            model_id=request.model_id
        )
        
        # Convert to base64 for JSON response
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return VoiceResponse(audio_base64=audio_base64)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voices")
async def get_available_voices():
    """Get available ElevenLabs voices"""
    return await elevenlabs_service.get_voices()

# Event response templates for different scenarios
class EventResponseGenerator:
    @staticmethod
    def generate_summary(event_count: int, location: str, category: str = None) -> str:
        """Generate natural response for event queries"""
        
        if event_count == 0:
            return f"No events found in {location} for your criteria."
        
        category_text = f"{category} " if category else ""
        
        if event_count == 1:
            return f"Found 1 {category_text}event in {location}."
        elif event_count < 10:
            return f"Showing {event_count} {category_text}events in {location}."
        elif event_count < 50:
            return f"Found {event_count} {category_text}events across {location}."
        else:
            return f"Displaying {event_count} {category_text}events. {location} is quite busy!"
    
    @staticmethod
    def generate_filter_response(filter_type: str, value: str) -> str:
        """Generate response for filter applications"""
        return f"Filtered by {filter_type}: {value}. Check the globe for updates."
    
    @staticmethod
    def generate_error_response() -> str:
        """Generate response for errors"""
        return "Sorry, I couldn't process that request. Please try again."

@app.post("/respond-to-query")
async def respond_to_query(
    event_count: int,
    location: str,
    category: Optional[str] = None,
    voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"
):
    """Generate voice response for event query results"""
    
    # Generate natural language summary
    response_text = EventResponseGenerator.generate_summary(
        event_count, location, category
    )
    
    # Convert to speech
    try:
        audio_bytes = await elevenlabs_service.text_to_speech(
            text=response_text,
            voice_id=voice_id
        )
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return {
            "text": response_text,
            "audio_base64": audio_base64,
            "content_type": "audio/mpeg"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)