/**
 * Approval Flow Example
 * 
 * Demonstrates the approval workflow:
 * 1. Create a thread
 * 2. Create a run with a graph that requires approval
 * 3. Poll until waiting_approval
 * 4. Show approval UI to user
 * 5. Submit approval or rejection
 * 6. Poll until completed
 * 7. Get the final artifact
 */

const API_BASE = 'http://localhost:8000/api/v1';
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your-token-here'
};

async function approvalWorkflow(userRequest, onApprovalNeeded) {
  console.log('Starting approval workflow...');
  
  // Step 1: Create a thread
  const thread = await fetch(`${API_BASE}/threads`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ 
      meta: { 
        user_id: 'user123',
        workflow: 'approval_demo'
      } 
    })
  }).then(r => r.json());

  console.log('Thread created:', thread.id);

  // Step 2: Create a run with strategy_synthesis graph (requires approval)
  const run = await fetch(`${API_BASE}/runs`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      thread_id: thread.id,
      graph_name: 'strategy_synthesis',
      meta: {
        messages: [
          { role: 'user', content: userRequest }
        ]
      }
    })
  }).then(r => r.json());

  console.log('Run created:', run.id);

  // Step 3: Poll until waiting_approval or completed/failed
  let state;
  let pollCount = 0;
  do {
    await new Promise(r => setTimeout(r, 1000));
    state = await fetch(`${API_BASE}/runs/${run.id}/state`, { headers })
      .then(r => r.json());
    
    pollCount++;
    console.log(`Poll ${pollCount}: Status = ${state.status}`);
  } while (
    state.status !== 'waiting_approval' && 
    state.status !== 'completed' && 
    state.status !== 'failed'
  );

  // Step 4: Handle approval if needed
  if (state.status === 'waiting_approval') {
    console.log('Approval required!');
    
    const approvalRequest = state.approval_request;
    console.log('Approval request:', approvalRequest);

    // Step 5: Call the approval callback (implement your own UI)
    const userDecision = await onApprovalNeeded({
      run_id: run.id,
      request: approvalRequest,
      payload: approvalRequest.payload
    });

    if (userDecision.approved) {
      // Submit approval
      console.log('Submitting approval...');
      await fetch(`${API_BASE}/runs/${run.id}/approve`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          response: { 
            approved: true,
            feedback: userDecision.feedback || 'Approved'
          }
        })
      });

      // Step 6: Poll until completed
      do {
        await new Promise(r => setTimeout(r, 1000));
        state = await fetch(`${API_BASE}/runs/${run.id}/state`, { headers })
          .then(r => r.json());
        
        pollCount++;
        console.log(`Poll ${pollCount}: Status = ${state.status}`);
      } while (state.status === 'running');
    } else {
      // Submit rejection
      console.log('Submitting rejection...');
      await fetch(`${API_BASE}/runs/${run.id}/reject`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          reason: userDecision.reason || 'Rejected by user'
        })
      });
      
      return {
        approved: false,
        rejected: true,
        reason: userDecision.reason
      };
    }
  }

  // Check final status
  if (state.status === 'failed') {
    throw new Error(state.error || 'Run failed');
  }

  // Step 7: Get final artifact
  const artifacts = await fetch(`${API_BASE}/runs/${run.id}/artifacts`, { headers })
    .then(r => r.json());

  console.log('Workflow completed!');

  return {
    approved: true,
    thread_id: thread.id,
    run_id: run.id,
    artifact: artifacts[0],
    all_artifacts: artifacts
  };
}

// Example approval UI callback
async function exampleApprovalUI(approvalData) {
  console.log('\n=== APPROVAL REQUIRED ===');
  console.log('Run ID:', approvalData.run_id);
  console.log('Request:', JSON.stringify(approvalData.request, null, 2));
  console.log('Payload:', JSON.stringify(approvalData.payload, null, 2));
  console.log('========================\n');

  // In a real application, you would show a UI and wait for user input
  // For this example, we'll auto-approve
  return {
    approved: true,
    feedback: 'Looks good! Proceeding with the strategy.'
  };
}

// Usage example
async function main() {
  try {
    const result = await approvalWorkflow(
      'Create a comprehensive product strategy for Q1 2026 focusing on AI features',
      exampleApprovalUI
    );
    
    if (result.approved) {
      console.log('\n=== Result ===');
      console.log('Thread ID:', result.thread_id);
      console.log('Run ID:', result.run_id);
      console.log('Artifact Type:', result.artifact?.artifact_type);
      console.log('Content:', result.artifact?.content?.substring(0, 200) + '...');
    } else {
      console.log('\n=== Rejected ===');
      console.log('Reason:', result.reason);
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
  module.exports = { approvalWorkflow, exampleApprovalUI };
}
