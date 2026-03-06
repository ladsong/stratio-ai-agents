from __future__ import annotations

import random
from abc import ABC, abstractmethod


class EmbeddingGenerator(ABC):
    """Abstract base class for embedding generators."""
    
    @abstractmethod
    def generate(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        pass


class StubEmbeddingGenerator(EmbeddingGenerator):
    """Stub embedding generator that returns random vectors for MVP."""
    
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        random.seed(42)  # Consistent random vectors for testing
    
    def generate(self, texts: list[str]) -> list[list[float]]:
        """Generate random embeddings for texts."""
        embeddings = []
        for text in texts:
            # Generate deterministic random vector based on text hash
            seed = hash(text) % (2**32)
            random.seed(seed)
            embedding = [random.random() for _ in range(self.dimension)]
            embeddings.append(embedding)
        return embeddings
    
    def get_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        return self.dimension
