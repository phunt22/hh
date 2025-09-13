import openai
import asyncio
from typing import List, Optional
import numpy as np
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai.api_key = settings.openai_api_key


class EmbeddingService:
    def __init__(self):
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            # Clean and prepare text
            clean_text = self._clean_text(text)
            if not clean_text:
                return [0.0] * self.dimension
            
            # Generate embedding using OpenAI
            response = await asyncio.to_thread(
                openai.embeddings.create,
                model=self.model,
                input=clean_text
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector on error
            return [0.0] * self.dimension

    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently"""
        try:
            # Clean texts
            clean_texts = [self._clean_text(text) for text in texts]
            
            # Filter out empty texts and keep track of indices
            valid_texts = []
            valid_indices = []
            
            for i, text in enumerate(clean_texts):
                if text:
                    valid_texts.append(text)
                    valid_indices.append(i)
            
            if not valid_texts:
                return [[0.0] * self.dimension] * len(texts)
            
            # Generate embeddings in batch
            response = await asyncio.to_thread(
                openai.embeddings.create,
                model=self.model,
                input=valid_texts
            )
            
            # Map results back to original order
            embeddings = [[0.0] * self.dimension] * len(texts)
            for i, valid_idx in enumerate(valid_indices):
                embeddings[valid_idx] = response.data[i].embedding
            
            return embeddings
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [[0.0] * self.dimension] * len(texts)

    def _clean_text(self, text: str) -> str:
        """Clean and prepare text for embedding"""
        if not text:
            return ""
        
        # Basic cleaning
        text = str(text).strip()
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate if too long (OpenAI has token limits)
        if len(text) > 8000:  # Conservative limit
            text = text[:8000]
        
        return text

    def prepare_event_text(self, title: str, description: str) -> str:
        """Prepare combined text for event embedding"""
        title = title or ""
        description = description or ""
        
        # Combine title and description with appropriate weighting
        combined = f"Title: {title}"
        if description:
            combined += f" Description: {description}"
        
        return combined

    @staticmethod
    def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0


# Global instance
embedding_service = EmbeddingService()