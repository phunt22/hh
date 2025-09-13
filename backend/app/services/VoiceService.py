from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import httpx
import asyncio
from typing import Optional
import os
from io import BytesIO
import base64
import tempfile
import json
import logging
import google.generativeai as genai
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ===== EXISTING MODELS =====
class VoiceRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"  # Default Rachel voice
    model_id: Optional[str] = "eleven_monolingual_v1"
    voice_settings: Optional[dict] = None

class VoiceResponse(BaseModel):
    audio_base64: str
    content_type: str = "audio/mpeg"

# ===== NEW MODELS =====
class SpeechToTextRequest(BaseModel):
    audio_base64: str
    prompt: Optional[str] = "Please transcribe this audio accurately."
    model: Optional[str] = "gemini-2.0-flash-exp"

class VoicePipelineRequest(BaseModel):
    audio_base64: str
    voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"

# ===== EXISTING ELEVENLABS SERVICE =====
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

# ===== NEW GEMINI STT SERVICE =====
class GeminiSTTService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Google Gemini API key is required")
        genai.configure(api_key=api_key)
        self.model_name = "gemini-2.0-flash-exp"
        logger.info("Gemini STT service initialized")
    
    async def transcribe_and_analyze(self, 
                                   audio_data: bytes, 
                                   analysis_prompt: str) -> dict:
        """Convert audio to text and analyze using Gemini 2.0 Flash"""
        
        try:
            model = genai.GenerativeModel(self.model_name)
            
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Upload the audio file
                audio_file = genai.upload_file(temp_path)
                
                # Wait for processing
                while audio_file.state.name == "PROCESSING":
                    await asyncio.sleep(1)
                    audio_file = genai.get_file(audio_file.name)
                
                if audio_file.state.name == "FAILED":
                    raise HTTPException(status_code=500, detail="Audio processing failed")
                
                # Generate transcription and analysis
                response = model.generate_content([audio_file, analysis_prompt])
                
                # Clean up
                genai.delete_file(audio_file.name)
                
                return {
                    "analysis": response.text,
                    "model_used": self.model_name
                }
                
            finally:
                # Clean up temp file
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Gemini STT error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Gemini audio transcription error: {str(e)}"
            )

# ===== NEW PREDICTHQ SERVICE =====
class PredictHQService:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.predicthq.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json"
        } if api_token else {}
    
    async def search_events(self, params: dict) -> dict:
        """Search events using PredictHQ API with voice-extracted parameters"""
        if not self.api_token:
            return {
                "success": False,
                "count": 0,
                "results": [],
                "error": "PredictHQ token not configured"
            }
        
        try:
            # Build search parameters
            search_params = {
                "limit": 20,
                "start": datetime.now().isoformat(),
                "end": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            if params.get("search_query"):
                search_params["q"] = params["search_query"]
            if params.get("location"):
                search_params["location"] = params["location"]
            if params.get("category"):
                # Map categories to PredictHQ categories
                category_mapping = {
                    "concert": "performing-arts",
                    "music": "performing-arts", 
                    "sports": "sports",
                    "festival": "festivals",
                    "theater": "performing-arts",
                    "comedy": "performing-arts"
                }
                mapped_category = category_mapping.get(params["category"].lower(), params["category"])
                search_params["category"] = mapped_category
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/events/",
                    headers=self.headers,
                    params=search_params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "count": data.get("count", 0),
                        "results": data.get("results", []),
                        "search_params": search_params
                    }
                else:
                    return {
                        "success": False,
                        "count": 0,
                        "results": [],
                        "error": f"API error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"PredictHQ search error: {str(e)}")
            return {
                "success": False,
                "count": 0,
                "results": [],
                "error": str(e)
            }

# ===== SERVICE INITIALIZATIONS =====
# Initialize existing service
elevenlabs_service = ElevenLabsService(os.getenv("ELEVENLABS_API_KEY"))

# Initialize new services - Using GEMINI_API_KEYS as you specified
gemini_stt_service = GeminiSTTService(os.getenv("GEMINI_API_KEYS"))
predicthq_service = PredictHQService(os.getenv("PREDICTHQ_TOKEN"))

# ===== EXISTING EVENT RESPONSE TEMPLATES =====
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

# ===== NEW ENHANCED EVENT RESPONSE GENERATOR =====
class EnhancedEventResponseGenerator:
    @staticmethod
    def generate_detailed_response(search_result: dict, voice_params: dict) -> str:
        """Generate detailed natural language response from voice search"""
        
        if not search_result.get("success"):
            return "Sorry, I couldn't search for events right now. Please try again."
        
        count = search_result.get("count", 0)
        location = voice_params.get("location", "your area")
        category = voice_params.get("category", "events")
        
        if count == 0:
            return f"I didn't find any {category} in {location}. Try a different location or event type."
        
        # Build response with specific event details
        if count == 1:
            response = f"I found 1 {category} event in {location}."
        elif count <= 5:
            response = f"I found {count} {category} events in {location}."
        elif count <= 20:
            response = f"Great! I found {count} {category} events in {location}."
        else:
            response = f"Wow! {location} is busy with {count} {category} events coming up!"
        
        # Add details about top events
        results = search_result.get("results", [])
        if results:
            top_events = results[:2]  # Get top 2 events
            event_names = []
            
            for event in top_events:
                title = event.get("title", "Unnamed event")
                if len(title) > 50:
                    title = title[:47] + "..."
                event_names.append(title)
            
            if len(event_names) == 1:
                response += f" The main event is {event_names[0]}."
            elif len(event_names) == 2:
                response += f" Top events include {event_names[0]} and {event_names[1]}."
        
        return response

# ===== EXISTING ENDPOINTS =====
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

# ===== NEW ENDPOINTS =====
@app.post("/transcribe-audio")
async def transcribe_audio(request: SpeechToTextRequest):
    """Transcribe audio to text using Gemini 2.0 Flash"""
    
    try:
        # Decode base64 audio
        audio_data = base64.b64decode(request.audio_base64)
        
        # Transcribe audio using Gemini
        result = await gemini_stt_service.transcribe_and_analyze(
            audio_data=audio_data,
            analysis_prompt=request.prompt
        )
        
        return {
            "transcript": result["analysis"],
            "model_used": result["model_used"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

@app.post("/transcribe-audio-file")
async def transcribe_audio_file(
    file: UploadFile = File(...),
    prompt: str = "Please transcribe this audio accurately."
):
    """Transcribe uploaded audio file using Gemini"""
    
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        # Read file content
        audio_data = await file.read()
        
        # Transcribe using Gemini
        result = await gemini_stt_service.transcribe_and_analyze(
            audio_data=audio_data,
            analysis_prompt=prompt
        )
        
        return {
            "filename": file.filename,
            "transcript": result["analysis"],
            "model_used": result["model_used"],
            "content_type": file.content_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File transcription error: {str(e)}")

@app.post("/voice-pipeline")
async def complete_voice_pipeline(request: VoicePipelineRequest):
    """
    Complete voice interaction pipeline:
    1. Gemini Speech-to-Text
    2. Extract search parameters
    3. Search PredictHQ API
    4. Generate natural response
    5. ElevenLabs Text-to-Speech
    """
    
    pipeline_start = datetime.now()
    logger.info("Starting voice pipeline")
    
    try:
        # Step 1: Transcribe and analyze speech
        logger.info("Step 1: Transcribing speech with Gemini")
        audio_data = base64.b64decode(request.audio_base64)
        
        analysis_prompt = """
        Transcribe this audio and extract event search information.
        
        Return valid JSON with:
        {
            "transcript": "exact words spoken",
            "intent": "search_events|greeting|help|unclear",
            "search_query": "main keywords for event search",
            "location": "city or venue mentioned",
            "category": "concert|sports|festival|theater|comedy|music",
            "time_frame": "tonight|weekend|this_week|next_month",
            "confidence": "high|medium|low"
        }
        """
        
        analysis_result = await gemini_stt_service.transcribe_and_analyze(
            audio_data=audio_data,
            analysis_prompt=analysis_prompt
        )
        
        # Parse analysis result
        try:
            voice_params = json.loads(analysis_result["analysis"])
        except json.JSONDecodeError:
            # Fallback parsing
            logger.warning("JSON parsing failed, using fallback")
            voice_params = {
                "transcript": analysis_result["analysis"][:200],
                "intent": "search_events",
                "search_query": "events",
                "location": "",
                "category": "",
                "confidence": "low"
            }
        
        transcript = voice_params.get("transcript", "")
        intent = voice_params.get("intent", "search_events")
        
        logger.info(f"Transcription: '{transcript}', Intent: {intent}")
        
        if not transcript:
            response_text = "I didn't catch what you said. Could you please speak again?"
        
        elif intent == "greeting":
            response_text = "Hello! I'm your event assistant. Tell me what events you're looking for and where!"
            
        elif intent == "help":
            response_text = "I can help you find concerts, festivals, sports events, and more. Just tell me what you want and where!"
            
        elif intent == "search_events" or "event" in transcript.lower():
            # Step 2: Search for events
            logger.info("Step 2: Searching events with PredictHQ")
            search_result = await predicthq_service.search_events(voice_params)
            
            # Step 3: Generate response
            logger.info("Step 3: Generating response")
            response_text = EnhancedEventResponseGenerator.generate_detailed_response(
                search_result, voice_params
            )
            
        else:
            response_text = f"I heard: '{transcript}'. I'm designed to help find events. What events are you looking for?"
        
        # Step 4: Convert to speech using existing service
        logger.info("Step 4: Converting response to speech")
        audio_bytes = await elevenlabs_service.text_to_speech(
            text=response_text,
            voice_id=request.voice_id
        )
        
        pipeline_duration = (datetime.now() - pipeline_start).total_seconds()
        logger.info(f"Pipeline completed in {pipeline_duration:.2f} seconds")
        
        return {
            "success": True,
            "user_transcript": transcript,
            "voice_analysis": voice_params,
            "response_text": response_text,
            "response_audio_base64": base64.b64encode(audio_bytes).decode('utf-8'),
            "content_type": "audio/mpeg",
            "processing_time_seconds": pipeline_duration
        }
        
    except Exception as e:
        logger.error(f"Voice pipeline error: {str(e)}")
        
        # Generate error response with voice
        error_response = "Sorry, I couldn't process that request. Please try again."
        try:
            audio_bytes = await elevenlabs_service.text_to_speech(
                error_response, request.voice_id
            )
            error_audio = base64.b64encode(audio_bytes).decode('utf-8')
        except:
            error_audio = ""
        
        return {
            "success": False,
            "error": str(e),
            "response_text": error_response,
            "response_audio_base64": error_audio,
            "content_type": "audio/mpeg"
        }

@app.post("/analyze-voice-intent")
async def analyze_voice_intent(
    audio_base64: str,
    analysis_prompt: str = None
):
    """Transcribe and analyze audio for event-related intent using Gemini"""
    
    try:
        audio_data = base64.b64decode(audio_base64)
        
        # Custom analysis for event queries
        if not analysis_prompt:
            analysis_prompt = """
            Transcribe this audio and analyze it for event-related queries.
            
            Respond in JSON format with:
            - transcript: exact words spoken
            - intent: what the user wants (search_events, get_info, greeting, etc.)
            - location: any mentioned places (city, venue, etc.)
            - event_type: type of event mentioned (concert, festival, sports, etc.)
            - time_frame: any time references (tonight, weekend, next month, etc.)
            - sentiment: user's mood/tone (excited, neutral, urgent)
            - keywords: important search terms for event APIs
            """
        
        result = await gemini_stt_service.transcribe_and_analyze(
            audio_data=audio_data,
            analysis_prompt=analysis_prompt
        )
        
        return {
            "analysis": result["analysis"],
            "model_used": result["model_used"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.get("/health/voice-services")
async def voice_services_health():
    """Check health of all voice services"""
    health_status = {
        "elevenlabs": "configured" if os.getenv("ELEVENLABS_API_KEY") else "missing_key",
        "gemini": "configured" if os.getenv("GEMINI_API_KEYS") else "missing_key", 
        "predicthq": "configured" if os.getenv("PREDICTHQ_TOKEN") else "missing_key"
    }
    
    # Test ElevenLabs connection
    try:
        voices = await elevenlabs_service.get_voices()
        health_status["elevenlabs"] = f"healthy ({len(voices.get('voices', []))} voices)"
    except Exception as e:
        health_status["elevenlabs"] = f"error: {str(e)}"
    
    return {
        "status": "healthy" if all("error" not in v for v in health_status.values()) else "degraded",
        "services": health_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)