/**
 * Basic Conversation Example
 * 
 * Demonstrates the simplest workflow:
 * 1. Create a thread
 * 2. Create a run with a user message
 * 3. Poll until completed
 * 4. Get the response
 */

const API_BASE = 'http://localhost:8000/api/v1';
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your-token-here'
};

async function basicConversation(userMessage) {
  console.log('Starting conversation...');
  
  // Step 1: Create a thread
  const thread = await fetch(`${API_BASE}/threads`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ 
      meta: { 
        user_id: 'user123',
        session_id: Date.now().toString()
      } 
    })
  }).then(r => r.json());

  console.log('Thread created:', thread.id);

  // Step 2: Create a run with the user message
  const run = await fetch(`${API_BASE}/runs`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      thread_id: thread.id,
      graph_name: 'conversation_router',
      meta: {
        messages: [
          { role: 'user', content: userMessage }
        ]
      }
    })
  }).then(r => r.json());

  console.log('Run created:', run.id);

  // Step 3: Poll until completed
  let state;
  let pollCount = 0;
  do {
    await new Promise(r => setTimeout(r, 1000)); // Wait 1 second
    state = await fetch(`${API_BASE}/runs/${run.id}/state`, { headers })
      .then(r => r.json());
    
    pollCount++;
    console.log(`Poll ${pollCount}: Status = ${state.status}`);
  } while (state.status === 'queued' || state.status === 'running');

  // Step 4: Check for errors
  if (state.status === 'failed') {
    throw new Error(state.error || 'Run failed');
  }

  // Step 5: Get artifacts (the response)
  const artifacts = await fetch(`${API_BASE}/runs/${run.id}/artifacts`, { headers })
    .then(r => r.json());

  console.log('Run completed!');

  return {
    thread_id: thread.id,
    run_id: run.id,
    response: artifacts[0]?.content || 'No response',
    artifacts
  };
}

// Usage example
async function main() {
  try {
    const result = await basicConversation('Help me create a product strategy for Q1 2026');
    
    console.log('\n=== Result ===');
    console.log('Thread ID:', result.thread_id);
    console.log('Run ID:', result.run_id);
    console.log('Response:', result.response);
    console.log('Artifacts:', result.artifacts.length);
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
  module.exports = { basicConversation };
}
