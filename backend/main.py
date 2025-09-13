from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import httpx
import asyncio
import os
from io import BytesIO
import base64
import tempfile
import json
import logging
from datetime import datetime, timedelta
import google.generativeai as genai
from app.core.config import settings
# mains.py
from app.services.voiceService_1 import GeminiVoiceService  # path to your kept class



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ===== MODELS =====
class VoiceRequest(BaseModel):
    text: str
    voice_style: Optional[str] = "friendly"  # friendly, professional, casual
    response_format: Optional[str] = "audio"  # audio or text

class VoiceResponse(BaseModel):
    audio_base64: Optional[str] = None
    text_response: Optional[str] = None
    content_type: str = "audio/wav"

class SpeechToTextRequest(BaseModel):
    audio_base64: str
    prompt: Optional[str] = "Please transcribe this audio accurately."
    include_analysis: Optional[bool] = False

class VoiceInteractionRequest(BaseModel):
    audio_base64: str
    interaction_type: str = "conversation"  # transcription, conversation, event_search
    voice_response: bool = True  # Whether to return audio response

# ===== GEMINI UNIFIED VOICE SERVICE =====
# class GeminiVoiceService:
#     def __init__(self, api_key: str):
#         if not api_key:
#             raise ValueError("Google Gemini API key is required")
#         genai.configure(api_key=api_key)
        
#         # Use Gemini 2.0 Flash for audio capabilities
#         self.model_name = "gemini-2.0-flash-exp"
#         self.generation_config = {
#             "temperature": 0.7,
#             "top_p": 0.8,
#             "top_k": 40,
#             "max_output_tokens": 1024,
#         }
#         logger.info("Gemini Voice Service initialized with audio capabilities")
    
#     async def transcribe_audio(self, 
#                              audio_data: bytes, 
#                              prompt: str = "Transcribe this audio accurately.",
#                              include_analysis: bool = False) -> dict:
#         """Convert audio to text using Gemini 2.0 Flash"""
        
#         try:
#             model = genai.GenerativeModel(
#                 self.model_name, 
#                 generation_config=self.generation_config
#             )
            
#             # Create temporary file for audio
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
#                 temp_file.write(audio_data)
#                 temp_path = temp_file.name
            
#             try:
#                 # Upload audio file
#                 audio_file = genai.upload_file(temp_path)
                
#                 # Wait for processing
#                 while audio_file.state.name == "PROCESSING":
#                     await asyncio.sleep(1)
#                     audio_file = genai.get_file(audio_file.name)
                
#                 if audio_file.state.name == "FAILED":
#                     raise HTTPException(status_code=500, detail="Audio processing failed")
                
#                 # Enhanced prompt for better transcription
#                 if include_analysis:
#                     full_prompt = f"""
#                     {prompt}
                    
#                     Please provide:
#                     1. Accurate transcription
#                     2. Intent analysis (greeting, event_search, question, etc.)
#                     3. Key entities (locations, event types, dates)
#                     4. Sentiment (positive, neutral, negative)
                    
#                     Format as JSON:
#                     {{
#                         "transcript": "exact words",
#                         "intent": "detected intent",
#                         "entities": {{
#                             "locations": ["city names"],
#                             "event_types": ["concerts", "festivals"],
#                             "time_references": ["tonight", "weekend"]
#                         }},
#                         "sentiment": "sentiment",
#                         "confidence": "high/medium/low"
#                     }}
#                     """
#                 else:
#                     full_prompt = prompt
                
#                 # Generate transcription
#                 response = model.generate_content([audio_file, full_prompt])
                
#                 # Clean up uploaded file
#                 genai.delete_file(audio_file.name)
                
#                 return {
#                     "transcript": response.text,
#                     "model_used": self.model_name,
#                     "success": True
#                 }
                
#             finally:
#                 # Clean up temp file
#                 if os.path.exists(temp_path):
#                     os.unlink(temp_path)
                
#         except Exception as e:
#             logger.error(f"Gemini transcription error: {str(e)}")
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Audio transcription failed: {str(e)}"
#             )
    
#     async def generate_voice_response(self, 
#                                     text: str, 
#                                     voice_style: str = "friendly") -> bytes:
#         """Generate audio response using Gemini 2.0 Flash audio generation"""
        
#         try:
#             model = genai.GenerativeModel(self.model_name)
            
#             # Style-aware prompt for better voice generation
#             style_prompts = {
#                 "friendly": "Respond in a warm, friendly, and helpful tone.",
#                 "professional": "Respond in a clear, professional, and informative tone.",
#                 "casual": "Respond in a relaxed, casual, and conversational tone.",
#                 "energetic": "Respond with enthusiasm and energy.",
#                 "calm": "Respond in a calm, soothing tone."
#             }
            
#             voice_prompt = f"""
#             {style_prompts.get(voice_style, style_prompts['friendly'])}
            
#             Please generate an audio response for: "{text}"
            
#             Make it natural and conversational, keeping the response concise and clear.
#             """
            
#             # Generate audio content
#             response = model.generate_content(
#                 voice_prompt,
#                 generation_config={
#                     **self.generation_config,
#                     "response_mime_type": "audio/wav"
#                 }
#             )
            
#             # Return audio data
#             if hasattr(response, 'parts') and response.parts:
#                 for part in response.parts:
#                     if hasattr(part, 'inline_data'):
#                         return base64.b64decode(part.inline_data.data)
            
#             # Fallback: if direct audio generation doesn't work, return text
#             logger.warning("Direct audio generation not available, falling back to text")
#             return text.encode('utf-8')
            
#         except Exception as e:
#             logger.error(f"Gemini voice generation error: {str(e)}")
#             # Fallback to text-only response
#             return text.encode('utf-8')
    
#     async def voice_to_voice_conversation(self, 
#                                         audio_data: bytes, 
#                                         conversation_context: str = "") -> dict:
#         """Complete voice-to-voice interaction using only Gemini"""
        
#         try:
#             model = genai.GenerativeModel(self.model_name)
            
#             # Create temporary file for input audio
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
#                 temp_file.write(audio_data)
#                 temp_path = temp_file.name
            
#             try:
#                 # Upload input audio
#                 audio_file = genai.upload_file(temp_path)
                
#                 # Wait for processing
#                 while audio_file.state.name == "PROCESSING":
#                     await asyncio.sleep(1)
#                     audio_file = genai.get_file(audio_file.name)
                
#                 if audio_file.state.name == "FAILED":
#                     raise HTTPException(status_code=500, detail="Audio processing failed")
                
#                 # Comprehensive prompt for voice-to-voice
#                 conversation_prompt = f"""
#                 You are a helpful event assistant. Listen to this audio message and respond naturally.
                
#                 Context: {conversation_context if conversation_context else "User is asking about events, concerts, festivals, or entertainment."}
                
#                 Please:
#                 1. Understand what the user is asking
#                 2. Provide a helpful, natural response
#                 3. If they're asking about events, acknowledge their request and offer to help find specific events
#                 4. Keep responses conversational and under 100 words
#                 5. Generate your response as audio
                
#                 Respond naturally as if having a conversation.
#                 """
                
#                 # Generate voice response directly
#                 response = model.generate_content(
#                     [audio_file, conversation_prompt],
#                     generation_config={
#                         **self.generation_config,
#                         "response_mime_type": "audio/wav"
#                     }
#                 )
                
#                 # Clean up uploaded file
#                 genai.delete_file(audio_file.name)
                
#                 # Extract audio and text response
#                 audio_response = None
#                 text_response = response.text if response.text else "I heard your request."
                
#                 if hasattr(response, 'parts') and response.parts:
#                     for part in response.parts:
#                         if hasattr(part, 'inline_data') and part.inline_data:
#                             audio_response = base64.b64encode(
#                                 base64.b64decode(part.inline_data.data)
#                             ).decode('utf-8')
                
#                 return {
#                     "text_response": text_response,
#                     "audio_response": audio_response,
#                     "model_used": self.model_name,
#                     "success": True
#                 }
                
#             finally:
#                 if os.path.exists(temp_path):
#                     os.unlink(temp_path)
                
#         except Exception as e:
#             logger.error(f"Voice-to-voice conversation error: {str(e)}")
#             return {
#                 "text_response": "I'm sorry, I couldn't process that audio message.",
#                 "audio_response": None,
#                 "success": False,
#                 "error": str(e)
#             }

# ===== PREDICTHQ SERVICE (UNCHANGED) =====
class PredictHQService:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.predicthq.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json"
        } if api_token else {}
    
    async def search_events(self, params: dict) -> dict:
        """Search events using PredictHQ API"""
        if not self.api_token:
            return {
                "success": False,
                "count": 0,
                "results": [],
                "error": "PredictHQ token not configured"
            }
        
        try:
            search_params = {
                "limit": 20,
                "start": datetime.now().isoformat(),
                "end": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            # Extract search parameters from voice analysis
            if params.get("search_query"):
                search_params["q"] = params["search_query"]
            if params.get("location"):
                search_params["location"] = params["location"]
            if params.get("category"):
                category_mapping = {
                    "concert": "performing-arts",
                    "music": "performing-arts", 
                    "sports": "sports",
                    "festival": "festivals",
                    "theater": "performing-arts",
                    "comedy": "performing-arts"
                }
                mapped_category = category_mapping.get(
                    params["category"].lower(), params["category"]
                )
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

# ===== RESPONSE GENERATORS =====
class EventResponseGenerator:
    @staticmethod
    def generate_natural_response(search_result: dict, voice_params: dict) -> str:
        """Generate natural language response for events"""
        
        if not search_result.get("success"):
            return "I couldn't search for events right now. Please try again."
        
        count = search_result.get("count", 0)
        location = voice_params.get("location", "your area")
        category = voice_params.get("category", "events")
        
        if count == 0:
            return f"I didn't find any {category} in {location}. Try a different location or event type."
        
        if count == 1:
            response = f"Perfect! I found 1 {category} event in {location}."
        elif count <= 5:
            response = f"Great! I found {count} {category} events in {location}."
        elif count <= 20:
            response = f"Awesome! I found {count} {category} events in {location}."
        else:
            response = f"Wow! {location} is really busy with {count} {category} events!"
        
        # Add specific event details
        results = search_result.get("results", [])
        if results:
            top_event = results[0]
            event_title = top_event.get("title", "")
            if event_title and len(event_title) < 50:
                response += f" One highlight is {event_title}."
        
        return response

# ===== SERVICE INITIALIZATION =====

load_dotenv()
# gemini_voice_service = settings.gemini_api_key
gemini_voice_service = GeminiVoiceService(settings.gemini_api_key)
predicthq_service  = os.getenv("PREDICTHQ_TOKEN")
# predicthq_service = settings.predicthq_token


# Temporary fix to get server running
# try:
#     gemini_api_key = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
#     if gemini_api_key:
#         gemini_voice_service = GeminiVoiceService(gemini_api_key)
#     else:
#         print("WARNING: No Gemini API key found - voice services disabled")
#         gemini_voice_service = None
# except Exception as e:
#     print(f"WARNING: Failed to initialize Gemini service: {e}")
#     gemini_voice_service = None

# ===== ENDPOINTS =====
@app.get("/")
async def root():
    return {"message": "Gemini Voice Assistant API", "version": "2.0"}

@app.post("/transcribe")
async def transcribe_audio(request: SpeechToTextRequest):
    """Transcribe audio to text using Gemini"""
    
    try:
        audio_data = base64.b64decode(request.audio_base64)
        
        result = await gemini_voice_service.transcribe_audio(
            audio_data=audio_data,
            prompt=request.prompt,
            include_analysis=request.include_analysis
        )
        
        return {
            "transcript": result["transcript"],
            "model_used": result["model_used"],
            "success": result["success"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

@app.post("/generate-voice")
async def generate_voice_response(request: VoiceRequest):
    """Generate voice response using Gemini"""
    
    try:
        if request.response_format == "text":
            return VoiceResponse(text_response=request.text, audio_base64=None)
        
        # Generate audio using Gemini
        audio_data = await gemini_voice_service.generate_voice_response(
            text=request.text,
            voice_style=request.voice_style
        )
        
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return VoiceResponse(
            audio_base64=audio_base64,
            text_response=request.text,
            content_type="audio/wav"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice generation error: {str(e)}")

@app.post("/voice-interaction")
async def voice_interaction(request: VoiceInteractionRequest):
    """
    Main voice interaction endpoint - handles all voice interaction types:
    - transcription: Just convert speech to text
    - conversation: Natural voice-to-voice chat
    - event_search: Voice query to event search with voice response
    """
    
    try:
        audio_data = base64.b64decode(request.audio_base64)
        
        if request.interaction_type == "transcription":
            # Simple transcription
            result = await gemini_voice_service.transcribe_audio(
                audio_data=audio_data,
                prompt="Transcribe this audio accurately."
            )
            
            return {
                "type": "transcription",
                "transcript": result["transcript"],
                "success": True
            }
        
        elif request.interaction_type == "conversation":
            # Natural voice-to-voice conversation
            result = await gemini_voice_service.voice_to_voice_conversation(
                audio_data=audio_data,
                conversation_context="General conversation with event assistant"
            )
            
            response = {
                "type": "conversation",
                "text_response": result["text_response"],
                "success": result["success"]
            }
            
            if request.voice_response and result["audio_response"]:
                response["audio_response"] = result["audio_response"]
                response["content_type"] = "audio/wav"
            
            return response
        
        elif request.interaction_type == "event_search":
            # Voice query to event search pipeline
            
            # Step 1: Transcribe and analyze for event search
            transcription_result = await gemini_voice_service.transcribe_audio(
                audio_data=audio_data,
                prompt="""
                Transcribe this audio and extract event search information.
                Return JSON with:
                {
                    "transcript": "exact words",
                    "search_query": "keywords for search",
                    "location": "mentioned location",
                    "category": "event type",
                    "intent": "search_events or other"
                }
                """,
                include_analysis=True
            )
            
            # Parse the analysis
            try:
                voice_params = json.loads(transcription_result["transcript"])
            except json.JSONDecodeError:
                voice_params = {
                    "transcript": transcription_result["transcript"],
                    "intent": "search_events",
                    "search_query": "events",
                    "location": "",
                    "category": ""
                }
            
            # Step 2: Search events if intent is correct
            if voice_params.get("intent") == "search_events":
                search_result = await predicthq_service.search_events(voice_params)
                response_text = EventResponseGenerator.generate_natural_response(
                    search_result, voice_params
                )
            else:
                response_text = f"I heard: '{voice_params.get('transcript', '')}'. How can I help you find events?"
            
            # Step 3: Generate voice response
            response = {
                "type": "event_search",
                "user_transcript": voice_params.get("transcript", ""),
                "voice_analysis": voice_params,
                "response_text": response_text,
                "success": True
            }
            
            if request.voice_response:
                audio_data = await gemini_voice_service.generate_voice_response(
                    text=response_text,
                    voice_style="friendly"
                )
                response["audio_response"] = base64.b64encode(audio_data).decode('utf-8')
                response["content_type"] = "audio/wav"
            
            return response
        
        else:
            raise HTTPException(status_code=400, detail="Invalid interaction_type")
    
    except Exception as e:
        logger.error(f"Voice interaction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice interaction failed: {str(e)}")

@app.post("/upload-voice-file")
async def upload_voice_file(
    file: UploadFile = File(...),
    interaction_type: str = "transcription",
    voice_response: bool = False
):
    """Handle uploaded voice files"""
    
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        # Read file content
        audio_data = await file.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Use the main voice interaction endpoint
        request = VoiceInteractionRequest(
            audio_base64=audio_base64,
            interaction_type=interaction_type,
            voice_response=voice_response
        )
        
        result = await voice_interaction(request)
        result["filename"] = file.filename
        result["file_content_type"] = file.content_type
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")

@app.get("/health")
async def health_check():
    """Check service health"""
    
    health_status = {
        "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "missing_key",
        "predicthq": "configured" if os.getenv("PREDICTHQ_TOKEN") else "missing_key"
    }
    
    return {
        "status": "healthy" if all("missing" not in v for v in health_status.values()) else "degraded",
        "services": health_status,
        "voice_provider": "Google Gemini 2.0 Flash"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)