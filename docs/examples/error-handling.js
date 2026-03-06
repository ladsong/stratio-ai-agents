/**
 * Error Handling Example
 * 
 * Demonstrates robust error handling patterns:
 * 1. Retry logic with exponential backoff
 * 2. Timeout handling
 * 3. Error response parsing
 * 4. Graceful degradation
 */

const API_BASE = 'http://localhost:8000/api/v1';
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your-token-here'
};

/**
 * Fetch with retry logic and exponential backoff
 */
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      
      // Parse error response if not OK
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(errorData.detail || `HTTP ${response.status}`);
        error.status = response.status;
        error.data = errorData;
        throw error;
      }
      
      return await response.json();
    } catch (error) {
      // Don't retry on client errors (4xx)
      if (error.status >= 400 && error.status < 500) {
        throw error;
      }
      
      // Last attempt - throw error
      if (i === maxRetries - 1) {
        throw error;
      }
      
      // Exponential backoff: 1s, 2s, 4s
      const delay = Math.pow(2, i) * 1000;
      console.log(`Retry ${i + 1}/${maxRetries} after ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}

/**
 * Fetch with timeout
 */
async function fetchWithTimeout(url, options, timeoutMs = 30000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeoutMs}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

/**
 * Safe API call wrapper with comprehensive error handling
 */
async function safeApiCall(url, options = {}) {
  try {
    return {
      success: true,
      data: await fetchWithRetry(url, options)
    };
  } catch (error) {
    console.error('API Error:', error.message);
    
    return {
      success: false,
      error: {
        message: error.message,
        status: error.status,
        data: error.data
      }
    };
  }
}

/**
 * Create thread with error handling
 */
async function createThreadSafe(meta = {}) {
  const result = await safeApiCall(`${API_BASE}/threads`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ meta })
  });

  if (!result.success) {
    console.error('Failed to create thread:', result.error);
    return null;
  }

  return result.data;
}

/**
 * Create run with error handling
 */
async function createRunSafe(threadId, graphName, meta = {}) {
  const result = await safeApiCall(`${API_BASE}/runs`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      thread_id: threadId,
      graph_name: graphName,
      meta
    })
  });

  if (!result.success) {
    console.error('Failed to create run:', result.error);
    return null;
  }

  return result.data;
}

/**
 * Poll run status with timeout and error handling
 */
async function pollRunStatus(runId, maxPollSeconds = 60) {
  const startTime = Date.now();
  const pollInterval = 1000; // 1 second
  
  while ((Date.now() - startTime) < maxPollSeconds * 1000) {
    try {
      const state = await fetchWithTimeout(
        `${API_BASE}/runs/${runId}/state`,
        { headers },
        5000 // 5 second timeout per request
      );

      // Terminal states
      if (state.status === 'completed') {
        return { success: true, state };
      }
      
      if (state.status === 'failed') {
        return { 
          success: false, 
          error: state.error || 'Run failed',
          state 
        };
      }

      // Continue polling for non-terminal states
      if (state.status === 'queued' || 
          state.status === 'running' || 
          state.status === 'waiting_approval') {
        await new Promise(r => setTimeout(r, pollInterval));
        continue;
      }

      // Unknown status
      console.warn('Unknown run status:', state.status);
      await new Promise(r => setTimeout(r, pollInterval));
      
    } catch (error) {
      console.error('Error polling run status:', error.message);
      
      // Continue polling on transient errors
      await new Promise(r => setTimeout(r, pollInterval));
    }
  }

  return {
    success: false,
    error: `Polling timeout after ${maxPollSeconds} seconds`
  };
}

/**
 * Complete conversation workflow with comprehensive error handling
 */
async function robustConversation(userMessage) {
  console.log('Starting robust conversation...');
  
  // Step 1: Create thread
  const thread = await createThreadSafe({ 
    user_id: 'user123',
    timestamp: Date.now()
  });
  
  if (!thread) {
    return {
      success: false,
      error: 'Failed to create thread'
    };
  }

  console.log('Thread created:', thread.id);

  // Step 2: Create run
  const run = await createRunSafe(thread.id, 'conversation_router', {
    messages: [{ role: 'user', content: userMessage }]
  });

  if (!run) {
    return {
      success: false,
      error: 'Failed to create run',
      thread_id: thread.id
    };
  }

  console.log('Run created:', run.id);

  // Step 3: Poll for completion
  const pollResult = await pollRunStatus(run.id, 60);

  if (!pollResult.success) {
    return {
      success: false,
      error: pollResult.error,
      thread_id: thread.id,
      run_id: run.id
    };
  }

  console.log('Run completed');

  // Step 4: Get artifacts
  const artifactsResult = await safeApiCall(
    `${API_BASE}/runs/${run.id}/artifacts`,
    { headers }
  );

  if (!artifactsResult.success) {
    return {
      success: false,
      error: 'Failed to fetch artifacts',
      thread_id: thread.id,
      run_id: run.id
    };
  }

  return {
    success: true,
    thread_id: thread.id,
    run_id: run.id,
    response: artifactsResult.data[0]?.content || 'No response',
    artifacts: artifactsResult.data
  };
}

/**
 * Error recovery example
 */
async function conversationWithRecovery(userMessage) {
  let attempts = 0;
  const maxAttempts = 3;

  while (attempts < maxAttempts) {
    attempts++;
    console.log(`Attempt ${attempts}/${maxAttempts}`);

    const result = await robustConversation(userMessage);

    if (result.success) {
      return result;
    }

    console.error(`Attempt ${attempts} failed:`, result.error);

    // Don't retry on certain errors
    if (result.error?.includes('Invalid') || 
        result.error?.includes('not found')) {
      return result;
    }

    // Wait before retry
    if (attempts < maxAttempts) {
      await new Promise(r => setTimeout(r, 2000));
    }
  }

  return {
    success: false,
    error: `Failed after ${maxAttempts} attempts`
  };
}

// Usage example
async function main() {
  try {
    console.log('=== Testing Error Handling ===\n');

    // Test 1: Successful conversation
    console.log('Test 1: Successful conversation');
    const result1 = await robustConversation('Hello, how are you?');
    console.log('Result:', result1.success ? 'Success' : 'Failed');
    if (result1.success) {
      console.log('Response:', result1.response.substring(0, 100) + '...');
    } else {
      console.log('Error:', result1.error);
    }

    console.log('\n---\n');

    // Test 2: Invalid graph name (should fail gracefully)
    console.log('Test 2: Invalid graph name');
    const thread = await createThreadSafe({ user_id: 'user123' });
    if (thread) {
      const result2 = await createRunSafe(thread.id, 'invalid_graph_name', {
        messages: [{ role: 'user', content: 'Test' }]
      });
      console.log('Result:', result2 ? 'Created' : 'Failed (expected)');
    }

    console.log('\n---\n');

    // Test 3: Conversation with recovery
    console.log('Test 3: Conversation with recovery');
    const result3 = await conversationWithRecovery('Help me with product strategy');
    console.log('Result:', result3.success ? 'Success' : 'Failed');
    if (result3.success) {
      console.log('Response received');
    } else {
      console.log('Error:', result3.error);
    }

  } catch (error) {
    console.error('Unexpected error:', error);
  }
}

// Run if this is the main module
if (typeof require !== 'undefined' && require.main === module) {
  main();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    fetchWithRetry,
    fetchWithTimeout,
    safeApiCall,
    createThreadSafe,
    createRunSafe,
    pollRunStatus,
    robustConversation,
    conversationWithRecovery
  };
}
