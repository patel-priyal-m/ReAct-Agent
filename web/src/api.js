export async function runWorkflow(){
  const res = await fetch('http://127.0.0.1:8000/run-workflow', {method:'POST'})
  if(!res.ok) throw new Error('Request failed: '+res.status)
  return await res.json()
}

export async function cancelRun(runId){
  const res = await fetch(`http://127.0.0.1:8000/cancel/${runId}`, {method:'POST'})
  if(!res.ok) throw new Error('Cancel failed: '+res.status)
  return await res.json()
}
