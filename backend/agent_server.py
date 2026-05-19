"""
Open Tutor AI - Agentic API Server
==================================
This module serves as the FastAPI REST interface bridging the Open WebUI frontend
with the custom LangGraph multi-agent orchestrator. 

Responsibilities:
- Episodic memory extraction and state management.
- Interception of automated UI background tasks to prevent frontend crashes.
- Sanitization of Python execution outputs for safe HTML rendering.
- Formatting of multi-agent execution steps into UI-compatible JSON responses.
"""

import time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from t2_extension.orchestrator import t2_engine

app = FastAPI()

# 1. Allow Open WebUI to talk to this server securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Identify the Engine to Open WebUI
@app.get("/v1/models")
async def get_models():
    """Returns the custom LangGraph model identity to the frontend."""
    return {
        "data": [{
            "id": "LangGraph-Agent", 
            "object": "model", 
            "created": int(time.time()), 
            "owned_by": "custom"
        }]
    }

# 3. Process the actual chat requests
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Primary endpoint for handling user prompts and routing to LangGraph."""
    try:
        body = await request.json()
    except Exception:
        body = {}
        
    msgs = body.get("messages", [])
    
    # --- NEW: EPISODIC MEMORY EXTRACTION ---
    # We separate the historical raw data from the current user prompt
    if len(msgs) > 1:
        chat_history = msgs[:-1]       # Everything except the very last message
        user_msg = msgs[-1]["content"] # The very last message
    elif len(msgs) == 1:
        chat_history = []
        user_msg = msgs[0]["content"]
    else:
        chat_history = []
        user_msg = ""
        
    msg_lower = user_msg.lower()

    # --- UPGRADED SHIELD FOR OPEN WEBUI BACKGROUND TASKS ---
    meta_triggers = ["title", "summarize", "tags", "generate a concise", "json"]
    
    if any(keyword in msg_lower for keyword in meta_triggers):
        ans = '["Python", "Coding"]' # Give it a safe dummy list so React doesn't crash
    elif msg_lower in ["hello", "hi", "hey", "hello!", "hi!"]:
        # A natural response to the automated greeting ONLY if they type exactly "hello"
        ans = "Hello! I am your Open Tutor AI. What would you like to learn today?"
    else:
        # Run your actual LangGraph Engine
        print(f"🚨 RUNNING AGENT FOR: {user_msg} 🚨")
        try:
            # --- NEW: PASSING MEMORY TO THE GRAPH ---
            # Injecting both the new prompt and the chat history into the Working Memory
            state = t2_engine.invoke({
                "user_prompt": user_msg, 
                "chat_history": chat_history,
                "attempts": 0
            })
            
            # --- NEW: HANDLING MULTI-AGENT OUTPUTS ---
            # Check if the Researcher answered (General Text) or the Coder answered (Code + Sandbox)
            text_response = state.get('final_text_response', '')
            
            if text_response:
                # Route 1: It was a general question handled by the Researcher
                ans = f"🎓 **Researcher Agent:**\n\n{text_response}"
            else:
                # Route 2: It was a coding task handled by the Coder and Sandbox
                c = str(state.get('generated_code', ''))
                r = str(state.get('execution_result', ''))

                # Sanitize the output so it doesn't crash the frontend UI!
                r_safe = r.replace('<', '&lt;').replace('>', '&gt;')
                
                nl = "\n"
                ticks = "```"
                
                # --- CORRECTED: Check if the sandbox succeeded or failed ---
                if "SUCCESS:" in r:
                    ans = f"✅ **Coder Agent Finished!**{nl}{nl}{ticks}python{nl}{c}{nl}{ticks}{nl}{nl}**Sandbox Output:**{nl}{ticks}text{nl}{r_safe}{nl}{ticks}"
                else:
                    ans = f"⚠️ **Execution Failed!**{nl}{nl}I tried to run this code:{nl}{ticks}python{nl}{c}{nl}{ticks}{nl}{nl}But the Sandbox threw this error:{nl}{ticks}text{nl}{r_safe}{nl}{ticks}{nl}{nl}**What should we do?**"
                    
        except Exception as e:
            ans = f"Error: {str(e)}"

    # Return pure, flawless JSON in the exact format Open WebUI demands
    return {
        "id": "chatcmpl-agent",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "LangGraph-Agent",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": ans}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
    }

if __name__ == "__main__":
    print("🚀 Starting LangGraph Standalone Server on port 9099...")
    uvicorn.run(app, host="0.0.0.0", port=9099)