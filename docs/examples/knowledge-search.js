/**
 * Knowledge Search Example
 * 
 * Demonstrates the knowledge ingestion and search workflow:
 * 1. Upload a document
 * 2. Wait for chunking to complete
 * 3. Verify chunks were created
 * 4. Use knowledge in a conversation
 * 5. Check if knowledge was retrieved
 */

const API_BASE = 'http://localhost:8000/api/v1';
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your-token-here'
};

async function uploadDocument(title, content, meta = {}) {
  console.log('Uploading document...');
  
  const doc = await fetch(`${API_BASE}/knowledge/documents`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      title,
      content,
      meta
    })
  }).then(r => r.json());

  console.log('Document uploaded:', doc.id);
  return doc;
}

async function waitForChunking(documentId, maxWaitSeconds = 10) {
  console.log('Waiting for document to be chunked...');
  
  const startTime = Date.now();
  let chunks = [];
  
  while ((Date.now() - startTime) < maxWaitSeconds * 1000) {
    await new Promise(r => setTimeout(r, 1000));
    
    chunks = await fetch(`${API_BASE}/knowledge/documents/${documentId}/chunks`, { headers })
      .then(r => r.json());
    
    if (chunks.length > 0) {
      console.log(`Document chunked into ${chunks.length} pieces`);
      return chunks;
    }
  }
  
  console.log('Chunking not completed within timeout');
  return chunks;
}

async function searchKnowledge(query) {
  console.log('Searching knowledge base...');
  
  // Create a thread
  const thread = await fetch(`${API_BASE}/threads`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ meta: { user_id: 'user123' } })
  }).then(r => r.json());

  // Create a run that will use vector_search_tool
  const run = await fetch(`${API_BASE}/runs`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      thread_id: thread.id,
      graph_name: 'conversation_router',
      meta: {
        messages: [
          { role: 'user', content: query }
        ]
      }
    })
  }).then(r => r.json());

  // Poll until completed
  let state;
  do {
    await new Promise(r => setTimeout(r, 1000));
    state = await fetch(`${API_BASE}/runs/${run.id}/state`, { headers })
      .then(r => r.json());
  } while (state.status === 'queued' || state.status === 'running');

  if (state.status === 'failed') {
    throw new Error(state.error || 'Run failed');
  }

  // Get tool calls to see if knowledge was used
  const toolCalls = await fetch(`${API_BASE}/runs/${run.id}/tool-calls`, { headers })
    .then(r => r.json());

  // Get artifacts (response)
  const artifacts = await fetch(`${API_BASE}/runs/${run.id}/artifacts`, { headers })
    .then(r => r.json());

  return {
    run_id: run.id,
    tool_calls: toolCalls,
    knowledge_used: toolCalls.some(tc => tc.tool_name === 'vector_search'),
    response: artifacts[0]?.content || 'No response',
    artifacts
  };
}

async function knowledgeWorkflow(documentTitle, documentContent, searchQuery) {
  console.log('Starting knowledge workflow...');
  
  // Step 1: Upload document
  const doc = await uploadDocument(documentTitle, documentContent, {
    source: 'api_upload',
    category: 'user_content'
  });

  // Step 2: Wait for chunking
  const chunks = await waitForChunking(doc.id, 10);

  if (chunks.length === 0) {
    console.warn('No chunks created - document may be too short or chunking failed');
  }

  // Step 3: Search using the knowledge
  const searchResult = await searchKnowledge(searchQuery);

  console.log('Workflow completed!');

  return {
    document_id: doc.id,
    document_title: doc.title,
    chunks_created: chunks.length,
    chunks_with_embeddings: chunks.filter(c => c.has_embedding).length,
    search_result: searchResult,
    knowledge_used: searchResult.knowledge_used
  };
}

// Usage example
async function main() {
  try {
    const documentContent = `
      Product Requirements Document: AI-Powered Analytics Dashboard
      
      Overview:
      We are building an AI-powered analytics dashboard that helps product managers
      make data-driven decisions. The system will analyze user behavior, predict
      trends, and provide actionable insights.
      
      Key Features:
      1. Real-time data visualization
      2. Predictive analytics using machine learning
      3. Automated report generation
      4. Natural language query interface
      5. Integration with existing data sources
      
      Technical Requirements:
      - React frontend with TypeScript
      - Python backend with FastAPI
      - PostgreSQL database with pgvector for embeddings
      - Redis for caching
      - Docker for containerization
      
      Success Metrics:
      - 90% user satisfaction score
      - 50% reduction in time to insights
      - 100k+ data points processed per day
    `;

    const result = await knowledgeWorkflow(
      'AI Analytics Dashboard PRD',
      documentContent,
      'What are the key technical requirements for the analytics dashboard?'
    );
    
    console.log('\n=== Result ===');
    console.log('Document ID:', result.document_id);
    console.log('Chunks Created:', result.chunks_created);
    console.log('Chunks with Embeddings:', result.chunks_with_embeddings);
    console.log('Knowledge Used:', result.knowledge_used);
    console.log('Response:', result.search_result.response);
    console.log('\nTool Calls:', result.search_result.tool_calls.length);
    
    if (result.knowledge_used) {
      const vectorSearchCalls = result.search_result.tool_calls
        .filter(tc => tc.tool_name === 'vector_search');
      console.log('Vector Search Calls:', vectorSearchCalls.length);
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Run if this is the main module
if (typeof require !== 'undefined' && require.main === module) {
  main();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { 
    uploadDocument, 
    waitForChunking, 
    searchKnowledge, 
    knowledgeWorkflow 
  };
}
