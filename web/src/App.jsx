import React, {useState} from 'react'
import { runWorkflow } from './api'

export default function App(){
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [streaming, setStreaming] = useState(false)
  const [logs, setLogs] = useState([])
  const [runId, setRunId] = useState(null)

  async function handleRun(){
    setRunning(true)
    setResult(null)
    try{
      const res = await runWorkflow()
      setResult(res)
    }catch(e){
      setResult({error: String(e)})
    }finally{
      setRunning(false)
    }
  }

  // Streamed run using SSE
  function handleStreamRun(){
    setLogs([])
    setStreaming(true)
    const es = new EventSource('http://127.0.0.1:8000/stream-workflow')
    es.onmessage = (ev) => {
      try{
        const data = JSON.parse(ev.data)
        setLogs((l)=>[...l, data])
        if(data.type === 'started'){
          setRunId(data.run_id)
        }
        if(data.type === 'done' || data.type === 'error'){
          es.close()
          setStreaming(false)
          // also set the final result for convenience
          if(data.type === 'done') setResult(data.result)
        }
      }catch(err){
        setLogs((l)=>[...l, {type:'parse_error', raw: ev.data}])
      }
    }
    es.onerror = (e)=>{
      setLogs((l)=>[...l, {type:'sse_error', error: String(e)}])
      es.close()
      setStreaming(false)
    }
  }

  async function handleCancel(){
    if(!runId) return
    try{
      setLogs((l)=>[...l, {type:'client', msg:`Requesting cancel for ${runId}`}])
      const res = await fetch(`http://127.0.0.1:8000/cancel/${runId}`, {method:'POST'})
      const body = await res.json()
      setLogs((l)=>[...l, {type:'cancel_response', body}])
    }catch(e){
      setLogs((l)=>[...l, {type:'cancel_error', error: String(e)}])
    }
  }

  return (
    <div style={{fontFamily:'sans-serif', padding:20}}>
      <h2>Hybrid Agent Demo</h2>
      <p>Click to run the example hybrid workflow (uses mock LLM by default).</p>
      <button onClick={handleRun} disabled={running}>{running? 'Running...' : 'Run Workflow'}</button>

      <h3>Result</h3>
      {result ? (
        <pre style={{whiteSpace:'pre-wrap', background:'#f5f5f5', padding:10}}>{JSON.stringify(result, null, 2)}</pre>
      ) : (
        <p>No results yet.</p>
      )}

      <h3>Streamed Logs</h3>
  <button onClick={handleStreamRun} disabled={streaming}>{streaming? 'Streaming...':'Stream Run'}</button>
  <button onClick={handleCancel} disabled={!runId} style={{marginLeft:8}}>{runId? `Cancel ${runId}` : 'Cancel'}</button>
      <div style={{maxHeight:300, overflow:'auto', background:'#fafafa', padding:8, marginTop:8}}>
        {logs.length===0? <p>No logs</p> : logs.map((ev, idx)=> (
          <div key={idx} style={{borderBottom:'1px solid #eee', padding:6}}>
            <b>{ev.type}</b> {ev.iteration? `(iter ${ev.iteration})`:''}
            <pre style={{whiteSpace:'pre-wrap', margin:4}}>{JSON.stringify(ev, null, 2)}</pre>
          </div>
        ))}
      </div>
    </div>
  )
}
