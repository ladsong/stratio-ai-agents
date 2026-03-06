from __future__ import annotations

import logging
import os
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.knowledge.chunker import TextChunker
from core.knowledge.embeddings import StubEmbeddingGenerator
from core.repositories.knowledge_chunk_repo import KnowledgeChunkRepository
from core.repositories.knowledge_document_repo import KnowledgeDocumentRepository


logger = logging.getLogger(__name__)


def get_db_session():
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://nanobot:nanobot@localhost:5432/nanobot"
    )
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def chunk_document_job(document_id: str, generate_embeddings: bool = True) -> dict:
    """
    Chunk a document and optionally generate embeddings.
    This function is executed by the RQ worker.
    
    Args:
        document_id: ID of the document to chunk
        generate_embeddings: Whether to generate embeddings for chunks
        
    Returns:
        Dictionary with job results
    """
    logger.info(f"Starting chunking job for document {document_id}")
    
    db = get_db_session()
    
    try:
        # Get the document
        doc_repo = KnowledgeDocumentRepository(db)
        document = doc_repo.get_by_id(document_id)
        
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        content = document.content
        if not content:
            logger.warning(f"Document {document_id} has no content")
            return {
                "document_id": document_id,
                "chunks_created": 0,
                "status": "no_content"
            }
        
        # Chunk the document
        chunker = TextChunker(chunk_size=800, overlap=150)
        chunks = chunker.chunk(content)
        
        logger.info(f"Created {len(chunks)} chunks for document {document_id}")
        
        # Generate embeddings if requested
        embeddings = None
        if generate_embeddings and chunks:
            embedding_generator = StubEmbeddingGenerator(dimension=1536)
            chunk_texts = [chunk["content"] for chunk in chunks]
            embeddings = embedding_generator.generate(chunk_texts)
            logger.info(f"Generated embeddings for {len(embeddings)} chunks")
        
        # Store chunks
        chunk_repo = KnowledgeChunkRepository(db)
        for i, chunk_data in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            embedding = embeddings[i] if embeddings else None
            
            chunk_repo.create(
                chunk_id=chunk_id,
                document_id=document_id,
                content=chunk_data["content"],
                embedding=embedding,
                meta={
                    "position": chunk_data["position"],
                    "start_char": chunk_data.get("start_char", 0),
                    "end_char": chunk_data.get("end_char", 0),
                    "length": chunk_data["length"],
                    "is_complete": chunk_data.get("is_complete", False)
                }
            )
        
        logger.info(f"Stored {len(chunks)} chunks for document {document_id}")
        
        return {
            "document_id": document_id,
            "chunks_created": len(chunks),
            "embeddings_generated": generate_embeddings,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Chunking job failed for document {document_id}: {e}")
        raise
    
    finally:
        db.close()
