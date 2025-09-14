import asyncio
from typing import List, Optional
import numpy as np
from app.core.config import settings
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


client = genai.Client(api_key=settings.gemini_api_key)

class EmbeddingService:
    def __init__(self):
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension
        logger.debug(f"EmbeddingService initialized with model: {self.model}, dimension: {self.dimension}")

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        logger.info(f"Generating embedding for text: {text[:50]}{'...' if len(text) > 50 else ''}")
        try:
            # Clean and prepare text
            clean_text = self._clean_text(text)
            logger.debug(f"Cleaned text: {clean_text[:50]}{'...' if len(clean_text) > 50 else ''}")
            if not clean_text:
                logger.warning("Input text is empty after cleaning. Returning zero vector.")
                return [0.1] * self.dimension
            
            # Generate embedding using Gemini
            logger.debug(f"Requesting embedding from OpenAI for model: {self.model}, dimension: {self.dimension}")
            response = await asyncio.to_thread(
                client.models.embed_content,
                model=self.model,
                contents=clean_text,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimension,
                    task_type="SEMANTIC_SIMILARITY"
                ),
            )
            logger.info("Received embedding response from Gemini.")
            
            # Validate embedding values
            embedding_values = response.embeddings[0].values
            if not embedding_values or len(embedding_values) == 0:
                logger.warning("Received empty embedding, returning zero vector")
                return [0.1] * self.dimension
            
            # Check for NaN or infinite values
            embedding_array = np.array(embedding_values)
            if np.any(np.isnan(embedding_array)) or np.any(np.isinf(embedding_array)):
                logger.warning("Received embedding with NaN or infinite values, returning zero vector")
                return [0.1] * self.dimension
            
            return embedding_values
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            # Return zero vector on error
            return [0.1] * self.dimension

    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently"""
        logger.info(f"Generating batch embeddings for {len(texts)} texts.")
        try:
            # Clean texts
            clean_texts = [self._clean_text(text) for text in texts]
            logger.debug(f"Cleaned texts: {[t[:30] + ('...' if len(t) > 30 else '') for t in clean_texts]}")
            
            # Filter out empty texts and keep track of indices
            valid_texts = []
            valid_indices = []
            
            for i, text in enumerate(clean_texts):
                if text:
                    valid_texts.append(text)
                    valid_indices.append(i)
            
            logger.debug(f"Valid texts count: {len(valid_texts)} / {len(texts)}")
            if not valid_texts:
                logger.warning("No valid texts after cleaning. Returning zero vectors.")
                return [[0.0] * self.dimension] * len(texts)
            
            # Generate embeddings in batch
            logger.debug(f"Requesting batch embeddings from OpenAI for {len(valid_texts)} valid texts.")
            response = await asyncio.to_thread(
                client.models.embed_content,
                model=self.model,
                contents=valid_texts,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimension,
                    task_type="SEMANTIC_SIMILARITY"
                )
            )
            logger.info("Received batch embedding response from OpenAI.")
            
            # Map results back to original order with validation
            embeddings = [[0.0] * self.dimension] * len(texts)
            for i, valid_idx in enumerate(valid_indices):
                embedding_values = response.embeddings[i].values
                
                # Validate embedding values
                if not embedding_values or len(embedding_values) == 0:
                    logger.warning(f"Received empty embedding for index {valid_idx}, using zero vector")
                    embeddings[valid_idx] = [0.0] * self.dimension
                else:
                    # Check for NaN or infinite values
                    embedding_array = np.array(embedding_values)
                    if np.any(np.isnan(embedding_array)) or np.any(np.isinf(embedding_array)):
                        logger.warning(f"Received embedding with NaN/inf values for index {valid_idx}, using zero vector")
                        embeddings[valid_idx] = [0.0] * self.dimension
                    else:
                        embeddings[valid_idx] = embedding_values
                
                logger.debug(f"Embedding for index {valid_idx} set.")
            
            return embeddings
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
            return [[0.0] * self.dimension] * len(texts)

    def _clean_text(self, text: str) -> str:
        """Clean and prepare text for embedding"""
        logger.debug(f"Cleaning text: {text[:50]}{'...' if text and len(text) > 50 else ''}")
        if not text:
            logger.debug("Input text is None or empty.")
            return ""
        
        # Basic cleaning
        text = str(text).strip()
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate if too long (OpenAI has token limits)
        if len(text) > 8000:  # Conservative limit
            logger.warning("Text length exceeds 8000 characters. Truncating.")
            text = text[:8000]
        
        logger.debug(f"Cleaned text result: {text[:50]}{'...' if len(text) > 50 else ''}")
        return text

    def prepare_event_text(self, title: str, description: str) -> str:
        """Prepare combined text for event embedding"""
        logger.debug(f"Preparing event text. Title: {title[:30] if title else ''}, Description: {description[:30] if description else ''}")
        title = title or ""
        description = description.replace("Sourced from predicthq.com", "") or ""
        
        # Combine title and description with appropriate weighting
        combined = f"Title: {title}"
        if description:
            combined += f" Description: {description}"
        
        result = combined.strip()
        logger.debug(f"Prepared event text: {result[:80]}{'...' if len(result) > 80 else ''}")
        return result

    @staticmethod
    def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        logger.debug("Calculating cosine similarity between two embeddings.")
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            logger.debug(f"Vector 1 norm: {np.linalg.norm(vec1)}, Vector 2 norm: {np.linalg.norm(vec2)}")
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                logger.warning("One or both embeddings are zero vectors. Returning similarity 0.0.")
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Handle NaN values that can occur in similarity calculations
            if np.isnan(similarity):
                logger.warning("NaN similarity calculated, returning 0.0")
                return 0.0
                
            logger.info(f"Cosine similarity calculated: {similarity}")
            return float(similarity)
        
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}", exc_info=True)
            return 0.0


# Global instance
logger.debug("Creating global EmbeddingService instance.")
embedding_service = EmbeddingService()