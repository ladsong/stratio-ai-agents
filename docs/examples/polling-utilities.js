/**
 * Polling Utilities
 * 
 * Reusable utilities for polling run status and handling common patterns.
 */

const API_BASE = 'http://localhost:8000/api/v1';
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your-token-here'
};

/**
 * Poll a run until it reaches a terminal state or specific status
 * 
 * @param {string} runId - The run ID to poll
 * @param {string|string[]} targetStatus - Status to wait for (or array of statuses)
 * @param {Object} options - Polling options
 * @returns {Promise<Object>} Final state
 */
async function pollUntil(runId, targetStatus, options = {}) {
  const {
    interval = 1000,        // Poll every 1 second
    timeout = 60000,        // Timeout after 60 seconds
    onProgress = null,      // Callback for progress updates
  } = options;

  const targetStatuses = Array.isArray(targetStatus) ? targetStatus : [targetStatus];
  const terminalStatuses = ['completed', 'failed', ...targetStatuses];
  
  const startTime = Date.now();
  let pollCount = 0;

  while ((Date.now() - startTime) < timeout) {
    pollCount++;
    
    const state = await fetch(`${API_BASE}/runs/${runId}/state`, { headers })
      .then(r => r.json());

    // Call progress callback if provided
    if (onProgress) {
      onProgress({
        pollCount,
        status: state.status,
        elapsed: Date.now() - startTime
      });
    }

    // Check if we've reached target status
    if (targetStatuses.includes(state.status)) {
      return state;
    }

    // Check if we've reached a terminal status
    if (terminalStatuses.includes(state.status)) {
      return state;
    }

    // Wait before next poll
    await new Promise(r => setTimeout(r, interval));
  }

  throw new Error(`Polling timeout after ${timeout}ms`);
}

/**
 * Poll until completed with automatic error handling
 */
async function pollUntilCompleted(runId, options = {}) {
  const state = await pollUntil(runId, 'completed', options);
  
  if (state.status === 'failed') {
    throw new Error(state.error || 'Run failed');
  }
  
  return state;
}

/**
 * Poll until waiting_approval
 */
async function pollUntilApproval(runId, options = {}) {
  return pollUntil(runId, 'waiting_approval', options);
}

/**
 * Smart poller that handles all states automatically
 */
async function smartPoll(runId, callbacks = {}) {
  const {
    onQueued = null,
    onRunning = null,
    onApproval = null,
    onCompleted = null,
    onFailed = null,
    interval = 1000,
    timeout = 60000
  } = callbacks;

  const startTime = Date.now();
  let lastStatus = null;

  while ((Date.now() - startTime) < timeout) {
    const state = await fetch(`${API_BASE}/runs/${runId}/state`, { headers })
      .then(r => r.json());

    // Call callbacks on status change
    if (state.status !== lastStatus) {
      lastStatus = state.status;

      switch (state.status) {
        case 'queued':
          if (onQueued) onQueued(state);
          break;
        case 'running':
          if (onRunning) onRunning(state);
          break;
        case 'waiting_approval':
          if (onApproval) return await onApproval(state);
        case 'completed':
          if (onCompleted) onCompleted(state);
          return state;
        case 'failed':
          if (onFailed) onFailed(state);
          throw new Error(state.error || 'Run failed');
      }
    }

    await new Promise(r => setTimeout(r, interval));
  }

  throw new Error(`Polling timeout after ${timeout}ms`);
}

/**
 * Batch poll multiple runs
 */
async function pollMultiple(runIds, options = {}) {
  const results = await Promise.allSettled(
    runIds.map(id => pollUntilCompleted(id, options))
  );

  return results.map((result, i) => ({
    run_id: runIds[i],
    success: result.status === 'fulfilled',
    state: result.status === 'fulfilled' ? result.value : null,
    error: result.status === 'rejected' ? result.reason.message : null
  }));
}

/**
 * Progress tracker for long-running operations
 */
class ProgressTracker {
  constructor(runId) {
    this.runId = runId;
    this.startTime = Date.now();
    this.pollCount = 0;
    this.statusHistory = [];
  }

  update(status) {
    this.pollCount++;
    this.statusHistory.push({
      status,
      timestamp: Date.now(),
      elapsed: Date.now() - this.startTime
    });
  }

  getProgress() {
    return {
      run_id: this.runId,
      poll_count: this.pollCount,
      elapsed_ms: Date.now() - this.startTime,
      current_status: this.statusHistory[this.statusHistory.length - 1]?.status,
      history: this.statusHistory
    };
  }

  log() {
    const progress = this.getProgress();
    console.log(`[${progress.run_id}] Poll ${progress.poll_count}: ${progress.current_status} (${progress.elapsed_ms}ms)`);
  }
}

/**
 * Adaptive polling with backoff
 */
async function adaptivePoll(runId, options = {}) {
  const {
    initialInterval = 500,
    maxInterval = 5000,
    backoffMultiplier = 1.5,
    timeout = 60000
  } = options;

  const startTime = Date.now();
  let interval = initialInterval;
  let pollCount = 0;

  while ((Date.now() - startTime) < timeout) {
    pollCount++;
    
    const state = await fetch(`${API_BASE}/runs/${runId}/state`, { headers })
      .then(r => r.json());

    // Terminal states
    if (state.status === 'completed' || state.status === 'failed') {
      return state;
    }

    // Increase interval with backoff
    interval = Math.min(interval * backoffMultiplier, maxInterval);
    
    console.log(`Poll ${pollCount}: ${state.status} (next poll in ${Math.round(interval)}ms)`);
    
    await new Promise(r => setTimeout(r, interval));
  }

  throw new Error(`Polling timeout after ${timeout}ms`);
}

// Usage examples
async function examples() {
  const runId = 'some-run-id';

  // Example 1: Simple poll until completed
  console.log('Example 1: Simple poll');
  try {
    const state = await pollUntilCompleted(runId);
    console.log('Completed:', state);
  } catch (error) {
    console.error('Failed:', error.message);
  }

  // Example 2: Poll with progress callback
  console.log('\nExample 2: Poll with progress');
  await pollUntil(runId, 'completed', {
    interval: 1000,
    timeout: 30000,
    onProgress: (progress) => {
      console.log(`Poll ${progress.pollCount}: ${progress.status}`);
    }
  });

  // Example 3: Smart poll with callbacks
  console.log('\nExample 3: Smart poll');
  await smartPoll(runId, {
    onQueued: (state) => console.log('Run queued'),
    onRunning: (state) => console.log('Run started'),
    onApproval: async (state) => {
      console.log('Approval needed');
      // Handle approval
      return state;
    },
    onCompleted: (state) => console.log('Run completed'),
    onFailed: (state) => console.error('Run failed:', state.error)
  });

  // Example 4: Progress tracker
  console.log('\nExample 4: Progress tracker');
  const tracker = new ProgressTracker(runId);
  await pollUntil(runId, 'completed', {
    onProgress: (progress) => {
      tracker.update(progress.status);
      tracker.log();
    }
  });
  console.log('Final progress:', tracker.getProgress());

  // Example 5: Batch polling
  console.log('\nExample 5: Batch polling');
  const results = await pollMultiple(['run-1', 'run-2', 'run-3']);
  results.forEach(result => {
    console.log(`${result.run_id}: ${result.success ? 'Success' : 'Failed'}`);
  });

  // Example 6: Adaptive polling
  console.log('\nExample 6: Adaptive polling');
  await adaptivePoll(runId, {
    initialInterval: 500,
    maxInterval: 5000,
    backoffMultiplier: 1.5
  });
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    pollUntil,
    pollUntilCompleted,
    pollUntilApproval,
    smartPoll,
    pollMultiple,
    ProgressTracker,
    adaptivePoll
  };
}
