from __future__ import annotations

import re
from typing import Any


class TextChunker:
    """Simple text chunker that splits documents into overlapping chunks."""
    
    def __init__(self, chunk_size: int = 800, overlap: int = 150):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str) -> list[dict[str, Any]]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: The text to chunk
            
        Returns:
            List of chunk dictionaries with content, position, and metadata
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Clean the text
        text = text.strip()
        
        # If text is shorter than chunk size, return as single chunk
        if len(text) <= self.chunk_size:
            return [{
                "content": text,
                "position": 0,
                "length": len(text),
                "is_complete": True
            }]
        
        chunks = []
        position = 0
        chunk_index = 0
        
        while position < len(text):
            # Calculate end position
            end_position = min(position + self.chunk_size, len(text))
            
            # Try to break at sentence boundary if not at end
            if end_position < len(text):
                # Look for sentence endings near the chunk boundary
                search_start = max(position, end_position - 100)
                search_text = text[search_start:end_position + 50]
                
                # Find last sentence ending
                sentence_endings = [m.end() for m in re.finditer(r'[.!?]\s+', search_text)]
                if sentence_endings:
                    # Adjust end position to last sentence ending
                    last_ending = sentence_endings[-1]
                    end_position = search_start + last_ending
            
            # Extract chunk
            chunk_text = text[position:end_position].strip()
            
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "position": chunk_index,
                    "start_char": position,
                    "end_char": end_position,
                    "length": len(chunk_text),
                    "is_complete": end_position >= len(text)
                })
                chunk_index += 1
            
            # Move position forward, accounting for overlap
            position = end_position - self.overlap
            
            # Prevent infinite loop
            if position <= end_position - self.chunk_size:
                position = end_position
        
        return chunks
