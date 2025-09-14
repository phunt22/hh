import os
import tempfile
import asyncio
import base64
import json
import logging
from typing import Dict, Optional, List, Union
from fastapi import HTTPException
import google.generativeai as genai
from typing import Any

from google import genai as ai
from google.genai import types


logger = logging.getLogger(__name__)

class GeminiVoiceService:
    """
    Unified Gemini service for all voice operations:
    - Speech-to-Text (STT)
    - Text-to-Speech (TTS) 
    - Voice-to-Voice conversations
    - Audio analysis and understanding
    """
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Google Gemini API key is required")
        
        genai.configure(api_key=api_key)
        self.model_name = "gemini-2.0-flash-exp"
        
        # Configuration for different use cases
        self.configs = {
            "transcription": genai.GenerationConfig(
                temperature=0.1,  # Low temperature for accurate transcription
                top_p=0.8,
                max_output_tokens=1024,
            ),
            "conversation": genai.GenerationConfig(
                temperature=0.7,  # Higher temperature for natural conversation
                top_p=0.9,
                max_output_tokens=512,
            ),
            "analysis": genai.GenerationConfig(
                temperature=0.3,  # Medium temperature for structured analysis
                top_p=0.8,
                max_output_tokens=1024,
            )
        }
        
        logger.info(f"GeminiVoiceService initialized with model: {self.model_name}")
    
    async def _upload_and_process_audio(self, audio_data: bytes, suffix: str = ".wav") -> Any:
        """Helper method to upload audio file to Gemini and wait for processing"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            # Upload to Gemini
            audio_file = genai.upload_file(temp_path)
            
            # Wait for processing with timeout
            max_wait = 30  # seconds
            waited = 0
            while audio_file.state.name == "PROCESSING" and waited < max_wait:
                await asyncio.sleep(1)
                audio_file = genai.get_file(audio_file.name)
                waited += 1
            
            if audio_file.state.name == "FAILED":
                raise HTTPException(status_code=500, detail="Audio file processing failed")
            
            if audio_file.state.name == "PROCESSING":
                raise HTTPException(status_code=408, detail="Audio processing timeout")
            
            return audio_file
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    async def transcribe_audio(self, 
                             audio_data: bytes, 
                             prompt: str = "Transcribe this audio accurately.",
                             language: str = "en") -> Dict[str, Union[str, bool]]:
        """
        Basic audio transcription using Gemini
        
        Args:
            audio_data: Raw audio bytes
            prompt: Custom prompt for transcription
            language: Expected language (for optimization)
        
        Returns:
            Dictionary with transcript and metadata
        """
        
        try:
            model = genai.GenerativeModel(
                self.model_name, 
                generation_config=self.configs["transcription"]
            )
            
            # Upload and process audio
            audio_file = await self._upload_and_process_audio(audio_data)
            
            try:
                # Enhanced transcription prompt
                enhanced_prompt = f"""
                {prompt}
                
                Instructions:
                - Provide accurate word-for-word transcription
                - Use proper punctuation and capitalization
                - If audio quality is poor, indicate [unclear] for unclear sections
                - Language: {language}
                
                Audio content:
                """
                
                # Generate transcription
                response = model.generate_content([audio_file, enhanced_prompt])
                
                if not response.text:
                    raise HTTPException(status_code=500, detail="No transcription generated")
                
                return {
                    "transcript": response.text.strip(),
                    "model_used": self.model_name,
                    "language": language,
                    "success": True
                }
                
            finally:
                # Clean up uploaded file
                genai.delete_file(audio_file.name)
                
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Audio transcription failed: {str(e)}"
            )
    
    async def analyze_voice_intent(self, 
                                 audio_data: bytes, 
                                 context: str = "event search") -> Dict[str, Union[str, Dict, bool]]:
        """
        Transcribe audio and analyze for intent, entities, and context
        
        Args:
            audio_data: Raw audio bytes
            context: Context for analysis (event_search, general, support)
        
        Returns:
            Dictionary with transcript, intent analysis, and extracted entities
        """
        
        try:
            model = genai.GenerativeModel(
                self.model_name, 
                generation_config=self.configs["analysis"]
            )
            
            # Upload and process audio
            audio_file = await self._upload_and_process_audio(audio_data)
            
            try:
                # Context-specific analysis prompts
                analysis_prompts = {
                    "event_search": """
                    Transcribe this audio and analyze it for event-related queries.
                    
                    Return valid JSON with:
                    {
                        "transcript": "exact words spoken",
                        "intent": "search_events|get_info|greeting|help|unclear",
                        "confidence": "high|medium|low",
                        "entities": {
                            "locations": ["city names", "venue names"],
                            "event_types": ["concerts", "festivals", "sports"],
                            "time_references": ["tonight", "weekend", "next month"],
                            "artists_performers": ["band names", "artist names"]
                        },
                        "search_params": {
                            "query": "main search keywords",
                            "location": "primary location mentioned",
                            "category": "main event category",
                            "timeframe": "when they want events"
                        },
                        "sentiment": "excited|neutral|frustrated|urgent",
                        "clarity": "clear|somewhat_clear|unclear"
                    }
                    """,
                    
                    "general": """
                    Transcribe this audio and analyze the user's intent.
                    
                    Return JSON with:
                    {
                        "transcript": "exact words",
                        "intent": "question|request|greeting|complaint|compliment",
                        "topic": "main subject discussed",
                        "sentiment": "positive|neutral|negative",
                        "urgency": "high|medium|low",
                        "entities": ["key terms mentioned"]
                    }
                    """,
                    
                    "support": """
                    Transcribe and analyze for customer support context.
                    
                    Return JSON with:
                    {
                        "transcript": "exact words",
                        "intent": "technical_issue|billing|feature_request|feedback",
                        "urgency": "high|medium|low",
                        "sentiment": "frustrated|confused|satisfied|angry",
                        "issue_category": "main problem category"
                    }
                    """
                }
                
                prompt = analysis_prompts.get(context, analysis_prompts["general"])
                
                # Generate analysis
                response = model.generate_content([audio_file, prompt])
                
                if not response.text:
                    raise HTTPException(status_code=500, detail="No analysis generated")
                
                # Try to parse JSON response
                try:
                    analysis_data = json.loads(response.text)
                    return {
                        "analysis": analysis_data,
                        "raw_response": response.text,
                        "model_used": self.model_name,
                        "context": context,
                        "success": True
                    }
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    logger.warning("Failed to parse analysis as JSON")
                    return {
                        "analysis": {
                            "transcript": response.text,
                            "intent": "unclear",
                            "confidence": "low"
                        },
                        "raw_response": response.text,
                        "model_used": self.model_name,
                        "context": context,
                        "success": True,
                        "json_parse_failed": True
                    }
                
            finally:
                # Clean up uploaded file
                genai.delete_file(audio_file.name)
                
        except Exception as e:
            logger.error(f"Voice intent analysis error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Voice intent analysis failed: {str(e)}"
            )
    
    async def generate_audio_response(self, 
                                    text: str, 
                                    voice_style: str = "friendly",
                                    response_length: str = "medium") -> bytes:
        """
        Generate audio response from text using Gemini 2.0 Flash
        
        Args:
            text: Text to convert to speech
            voice_style: Style of voice (friendly, professional, energetic, calm)
            response_length: Length preference (short, medium, long)
        
        Returns:
            Audio data as bytes
        """
        
        try:
            model = genai.GenerativeModel(
                self.model_name,
                generation_config=self.configs["conversation"]
            )
            
            # Voice style configurations
            style_configs = {
                "friendly": {
                    "tone": "warm, welcoming, and helpful",
                    "pace": "moderate",
                    "energy": "upbeat but not overwhelming"
                },
                "professional": {
                    "tone": "clear, authoritative, and informative", 
                    "pace": "steady and measured",
                    "energy": "confident and composed"
                },
                "energetic": {
                    "tone": "enthusiastic and dynamic",
                    "pace": "slightly faster",
                    "energy": "high and engaging"
                },
                "calm": {
                    "tone": "soothing and reassuring",
                    "pace": "slower and deliberate", 
                    "energy": "peaceful and relaxed"
                },
                "casual": {
                    "tone": "relaxed and conversational",
                    "pace": "natural and flowing",
                    "energy": "laid-back and approachable"
                }
            }
            
            # Length preferences
            length_configs = {
                "short": "Keep it concise, under 30 words",
                "medium": "Provide a complete but not lengthy response, 30-80 words",
                "long": "Give a detailed and comprehensive response, 80+ words"
            }
            
            style_config = style_configs.get(voice_style, style_configs["friendly"])
            length_config = length_configs.get(response_length, length_configs["medium"])
            
            # Audio generation prompt
            audio_prompt = f"""
            Generate an audio response with the following characteristics:
            - Tone: {style_config['tone']}
            - Pace: {style_config['pace']}
            - Energy: {style_config['energy']}
            - Length: {length_config}
            
            Text to speak: "{text}"
            
            Make the audio sound natural and conversational, as if speaking directly to the user.
            """
            
            # Attempt to generate audio response
            try:
                response = model.generate_content(
                    audio_prompt,
                    generation_config=genai.GenerationConfig(
                        **self.configs["conversation"].__dict__,
                        response_mime_type="audio/wav"
                    )
                )
                
                # Extract audio data
                if hasattr(response, 'parts') and response.parts:
                    for part in response.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            return base64.b64decode(part.inline_data.data)
                
                # If no audio data found, log and fallback
                logger.warning("No audio data in Gemini response, using text fallback")
                
            except Exception as audio_error:
                logger.warning(f"Direct audio generation failed: {audio_error}")
            
            # Fallback: Return text as bytes (client can handle TTS if needed)
            logger.info("Using text fallback for audio generation")
            return text.encode('utf-8')
            
        except Exception as e:
            logger.error(f"Audio generation error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Audio generation failed: {str(e)}"
            )
    
    async def voice_to_voice_conversation(self, 
                                        audio_data: bytes,
                                        conversation_context: str = "",
                                        voice_style: str = "friendly",
                                        max_response_length: int = 100) -> Dict[str, Union[str, bytes, bool]]:
        """
        Complete voice-to-voice conversation using only Gemini
        
        Args:
            audio_data: Input audio bytes
            conversation_context: Context for the conversation
            voice_style: Style for audio response
            max_response_length: Max words in response
        
        Returns:
            Dictionary with text and audio response
        """
        
        try:
            model = genai.GenerativeModel(
                self.model_name,
                generation_config=self.configs["conversation"]
            )
            
            # Upload and process input audio
            audio_file = await self._upload_and_process_audio(audio_data)
            
            try:
                # Conversation prompt
                context_text = conversation_context if conversation_context else "You are a helpful assistant for finding events and entertainment."
                
                conversation_prompt = f"""
                {context_text}
                
                Listen to this audio message and respond naturally in a conversational way.
                
                Guidelines:
                - Keep response under {max_response_length} words
                - Be helpful and engaging
                - If they ask about events, offer to help find specific ones
                - Match their energy level appropriately
                - Be natural and human-like in your response
                
                Respond as if you're having a friendly conversation.
                """
                
                # Generate text response first
                text_response = model.generate_content([audio_file, conversation_prompt])
                
                if not text_response.text:
                    text_response_content = "I heard your message. How can I help you?"
                else:
                    text_response_content = text_response.text.strip()
                
                # Generate audio response
                audio_response_data = await self.generate_audio_response(
                    text=text_response_content,
                    voice_style=voice_style,
                    response_length="medium"
                )
                
                return {
                    "text_response": text_response_content,
                    "audio_response": audio_response_data,
                    "voice_style": voice_style,
                    "model_used": self.model_name,
                    "success": True
                }
                
            finally:
                # Clean up uploaded file
                genai.delete_file(audio_file.name)
                
        except Exception as e:
            logger.error(f"Voice-to-voice conversation error: {str(e)}")
            return {
                "text_response": "I'm sorry, I couldn't process that audio message.",
                "audio_response": b"I'm sorry, I couldn't process that audio message.",
                "success": False,
                "error": str(e)
            }
    
    async def batch_process_audio(self, 
                                audio_files: List[bytes],
                                process_type: str = "transcription") -> List[Dict]:
        """
        Process multiple audio files efficiently
        
        Args:
            audio_files: List of audio data bytes
            process_type: Type of processing (transcription, analysis, conversation)
        
        Returns:
            List of processing results
        """
        
        results = []
        
        for i, audio_data in enumerate(audio_files):
            try:
                if process_type == "transcription":
                    result = await self.transcribe_audio(audio_data)
                elif process_type == "analysis":
                    result = await self.analyze_voice_intent(audio_data)
                elif process_type == "conversation":
                    result = await self.voice_to_voice_conversation(audio_data)
                else:
                    result = {"error": f"Unknown process_type: {process_type}"}
                
                results.append({
                    "index": i,
                    "result": result,
                    "success": result.get("success", False)
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    async def get_service_info(self) -> Dict[str, Union[str, bool, Dict]]:
        """Get information about the service capabilities"""
        
        return {
            "service_name": "GeminiVoiceService",
            "model": self.model_name,
            "capabilities": {
                "speech_to_text": True,
                "text_to_speech": True,
                "voice_to_voice": True,
                "intent_analysis": True,
                "batch_processing": True,
                "multi_language": True
            },
            "supported_formats": ["wav", "mp3", "m4a", "ogg"],
            "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh"],
            "voice_styles": ["friendly", "professional", "energetic", "calm", "casual"],
            "max_audio_duration": "10 minutes",
            "api_provider": "Google Gemini 2.0 Flash"
        }

class VoiceInteractionPipeline:
    """
    High-level pipeline for managing complex voice interactions
    """
    
    def __init__(self, gemini_service: GeminiVoiceService):
        self.gemini_service = gemini_service
        self.conversation_history = []
        
    async def process_voice_query(self, 
                                audio_data: bytes,
                                query_type: str = "auto_detect",
                                context: Optional[Dict] = None) -> Dict:
        """
        Process a voice query with automatic intent detection and appropriate response
        
        Args:
            audio_data: Input audio bytes
            query_type: Type of query (auto_detect, event_search, general_chat)
            context: Additional context for processing
        
        Returns:
            Complete processing result
        """
        
        try:
            context = context or {}
            
            # Step 1: Analyze intent if auto-detection is enabled
            if query_type == "auto_detect":
                intent_analysis = await self.gemini_service.analyze_voice_intent(
                    audio_data, context="event_search"
                )
                
                detected_intent = intent_analysis["analysis"].get("intent", "unclear")
                
                if detected_intent in ["search_events", "get_info"]:
                    query_type = "event_search"
                elif detected_intent in ["greeting", "help"]:
                    query_type = "general_chat"
                else:
                    query_type = "conversation"
                    
                context["intent_analysis"] = intent_analysis
            
            # Step 2: Process based on detected/specified query type
            if query_type == "event_search":
                result = await self._handle_event_search(audio_data, context)
            elif query_type == "general_chat":
                result = await self._handle_general_chat(audio_data, context)
            else:
                result = await self._handle_conversation(audio_data, context)
            
            # Step 3: Add to conversation history
            self.conversation_history.append({
                "timestamp": genai.generativeai.time.now(),
                "query_type": query_type,
                "result": result
            })
            
            # Keep history manageable
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return {
                "query_type": query_type,
                "result": result,
                "conversation_length": len(self.conversation_history)
            }
            
        except Exception as e:
            logger.error(f"Voice query processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query_type": query_type
            }
    
    async def _handle_event_search(self, audio_data: bytes, context: Dict) -> Dict:
        """Handle event search specific processing"""
        
        # Analyze for event search parameters
        analysis = await self.gemini_service.analyze_voice_intent(
            audio_data, context="event_search"
        )
        
        return {
            "type": "event_search",
            "analysis": analysis,
            "success": True
        }
    
    async def _handle_general_chat(self, audio_data: bytes, context: Dict) -> Dict:
        """Handle general conversation"""
        
        result = await self.gemini_service.voice_to_voice_conversation(
            audio_data, 
            conversation_context="Friendly assistant for events and general help"
        )
        
        return {
            "type": "general_chat",
            "conversation": result,
            "success": result["success"]
        }
    
    async def _handle_conversation(self, audio_data: bytes, context: Dict) -> Dict:
        """Handle open-ended conversation"""
        
        result = await self.gemini_service.voice_to_voice_conversation(
            audio_data,
            conversation_context="Open conversation with helpful assistant"
        )
        
        return {
            "type": "conversation", 
            "conversation": result,
            "success": result["success"]
        }