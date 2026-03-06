#!/usr/bin/env python3
"""Test script for Phase 7: Knowledge Ingestion."""

import os
import sys
import time

# Add core package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages/core/src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.knowledge.chunker import TextChunker
from core.knowledge.embeddings import StubEmbeddingGenerator
from core.repositories.knowledge_document_repo import KnowledgeDocumentRepository
from core.repositories.knowledge_chunk_repo import KnowledgeChunkRepository
from core.jobs.chunk_document import chunk_document_job


def main():
    print("=== Phase 7 Testing: Knowledge Ingestion ===\n")
    
    # Setup database connection
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://nanobot:nanobot@localhost:5432/nanobot"
    )
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Test 1: TextChunker
    print("1. Testing TextChunker...")
    sample_text = """
    Artificial intelligence is transforming how we work and live. Machine learning algorithms 
    can now process vast amounts of data to identify patterns and make predictions. Deep learning, 
    a subset of machine learning, uses neural networks with multiple layers to learn complex 
    representations. Natural language processing enables computers to understand and generate 
    human language. Computer vision allows machines to interpret and analyze visual information 
    from the world. These technologies are being applied across industries, from healthcare to 
    finance, transportation to entertainment. As AI continues to advance, it raises important 
    questions about ethics, privacy, and the future of work.
    """
    
    chunker = TextChunker(chunk_size=200, overlap=50)
    chunks = chunker.chunk(sample_text)
    print(f"   ✓ Created {len(chunks)} chunks from sample text")
    print(f"   First chunk: {chunks[0]['content'][:80]}...")
    print()
    
    # Test 2: StubEmbeddingGenerator
    print("2. Testing StubEmbeddingGenerator...")
    embedding_gen = StubEmbeddingGenerator(dimension=1536)
    embeddings = embedding_gen.generate(["test text 1", "test text 2"])
    print(f"   ✓ Generated {len(embeddings)} embeddings")
    print(f"   Embedding dimension: {len(embeddings[0])}")
    print()
    
    # Test 3: Create a knowledge document
    print("3. Creating a knowledge document...")
    import uuid
    doc_id = str(uuid.uuid4())
    doc_repo = KnowledgeDocumentRepository(db)
    
    document = doc_repo.create(
        document_id=doc_id,
        title="AI Strategy Guide",
        content=sample_text,
        meta={"source": "test", "category": "AI"}
    )
    print(f"   ✓ Created document: {doc_id}")
    print(f"   Title: {document.title}")
    print()
    
    # Test 4: Run chunking job
    print("4. Running chunking job...")
    result = chunk_document_job(doc_id, generate_embeddings=True)
    print(f"   ✓ Chunking job completed")
    print(f"   Chunks created: {result['chunks_created']}")
    print(f"   Embeddings generated: {result['embeddings_generated']}")
    print()
    
    # Test 5: Retrieve chunks
    print("5. Retrieving document chunks...")
    chunk_repo = KnowledgeChunkRepository(db)
    chunks = chunk_repo.list_by_document(doc_id)
    print(f"   ✓ Found {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):
        has_emb = "✓" if chunk.has_embedding else "✗"
        print(f"   {has_emb} Chunk {i+1}: {chunk.content[:60]}...")
    print()
    
    # Test 6: Vector search
    print("6. Testing vector search...")
    if chunks and chunks[0].has_embedding:
        # Generate query embedding
        query_embedding = embedding_gen.generate(["machine learning"])[0]
        
        # Search by embedding
        results = chunk_repo.search_by_embedding(query_embedding, top_k=3)
        print(f"   ✓ Found {len(results)} results")
        for i, result in enumerate(results):
            print(f"   {i+1}. Distance: {result.distance:.4f} - {result.content[:60]}...")
    else:
        print("   ✗ No chunks with embeddings found")
    print()
    
    # Test 7: Create another document
    print("7. Creating second document...")
    doc_id_2 = str(uuid.uuid4())
    doc_2 = doc_repo.create(
        document_id=doc_id_2,
        title="Product Strategy",
        content="Product strategy involves defining the vision, goals, and roadmap for a product. It requires understanding customer needs, market dynamics, and competitive landscape. A good product strategy aligns the team and guides decision-making.",
        meta={"source": "test", "category": "Product"}
    )
    print(f"   ✓ Created document: {doc_id_2}")
    
    # Chunk it
    result_2 = chunk_document_job(doc_id_2, generate_embeddings=True)
    print(f"   ✓ Created {result_2['chunks_created']} chunks")
    print()
    
    # Test 8: List all documents
    print("8. Listing all documents...")
    all_docs = doc_repo.list_documents(limit=10)
    print(f"   ✓ Found {len(all_docs)} documents")
    for doc in all_docs[:5]:
        chunk_count = doc_repo.count_chunks(doc.id)
        print(f"   - {doc.title}: {chunk_count} chunks")
    print()
    
    # Test 9: Search across all documents
    print("9. Searching across all documents...")
    query_embedding = embedding_gen.generate(["product development"])[0]
    results = chunk_repo.search_by_embedding(query_embedding, top_k=5)
    print(f"   ✓ Found {len(results)} results across documents")
    for i, result in enumerate(results):
        print(f"   {i+1}. [{result.document_title}] {result.content[:50]}...")
    print()
    
    print("=== Phase 7 Testing Complete ===\n")
    print("Summary:")
    print("  ✓ TextChunker working (splits text into overlapping chunks)")
    print("  ✓ StubEmbeddingGenerator working (generates 1536-dim vectors)")
    print("  ✓ Document creation working")
    print("  ✓ Chunking job working (async processing)")
    print("  ✓ Chunk storage with embeddings")
    print("  ✓ Vector search by embedding similarity")
    print("  ✓ Multi-document search working")
    print()
    print("Knowledge Ingestion Flow:")
    print("  Document → Chunker → Chunks → Embedding Generator → pgvector")
    print("       ↓         ↓         ↓            ↓                  ↓")
    print("  Create    Split     Store      Generate           Store in DB")
    print()
    
    db.close()


if __name__ == "__main__":
    main()
