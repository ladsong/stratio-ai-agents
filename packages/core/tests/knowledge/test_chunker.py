"""Tests for TextChunker."""
import pytest
from core.knowledge.chunker import TextChunker


@pytest.mark.unit
def test_chunker_basic(sample_text):
    """Test basic text chunking."""
    chunker = TextChunker(chunk_size=200, overlap=50)
    
    chunks = chunker.chunk(sample_text)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, dict) for chunk in chunks)
    assert all('content' in chunk for chunk in chunks)
    assert all('position' in chunk for chunk in chunks)


@pytest.mark.unit
def test_chunker_empty_text():
    """Test chunking empty text."""
    chunker = TextChunker(chunk_size=200, overlap=50)
    
    chunks = chunker.chunk("")
    
    assert len(chunks) == 0


@pytest.mark.unit
def test_chunker_short_text():
    """Test chunking text shorter than chunk size."""
    chunker = TextChunker(chunk_size=1000, overlap=100)
    
    chunks = chunker.chunk("Short text")
    
    assert len(chunks) == 1
    assert chunks[0]['content'] == "Short text"
    assert chunks[0]['is_complete'] is True


@pytest.mark.unit
def test_chunker_metadata():
    """Test chunk metadata."""
    chunker = TextChunker(chunk_size=100, overlap=20)
    
    chunks = chunker.chunk("A" * 250)
    
    assert all('length' in chunk for chunk in chunks)
    assert all('position' in chunk for chunk in chunks)
    assert chunks[0]['position'] == 0
    if len(chunks) > 1:
        assert chunks[1]['position'] == 1
