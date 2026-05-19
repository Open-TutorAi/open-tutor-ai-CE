"""
Open Tutor AI - Multi-Agent Orchestrator
========================================
This module defines the core LangGraph state machine (The "Brain") for the application.

Agents & Workflow:
- Traffic Cop (Router): Evaluates intent and directs prompts to the appropriate agent.
- Coder Agent: Generates raw, executable Python code.
- Execution Sandbox: Safely runs generated code in an isolated /tmp/ environment.
- Verifier Agent: Analyzes stack traces to autonomously rewrite and fix broken code.
- Researcher Agent: Queries the local ChromaDB vector database (RAG) for factual context.
"""

import os
import subprocess
from typing import TypedDict

import chromadb
from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, START, END

# --- 1. Security Initialization ---
load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- 2. The Graph State (Working Memory) ---
class T2GraphState(TypedDict):
    """The shared state dictionary passed between all agents in the graph."""
    user_prompt: str
    chat_history: list  # The Episodic Memory Bucket
    generated_code: str
    execution_result: str
    attempts: int
    final_text_response: str

# ---------------------------------------------------------
# 3. THE AGENT NODES
# ---------------------------------------------------------

def coder_node(state: T2GraphState):
    """Generates Python code based on the prompt and episodic memory context."""
    print("🤖 Coder: Writing the script with memory context...")
    
    system_prompt = (
        "You are an elite Python Coder. Write a script to solve the user's prompt. "
        "Output ONLY valid, raw Python code. Do not use markdown blocks (like ```python). "
        "No explanations. Use the provided chat history to understand the context if the "
        "user asks for modifications."
    )
    
    # Injecting the Episodic Memory into the LLM context
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(state.get("chat_history", []))
    messages.append({"role": "user", "content": state["user_prompt"]})
    
    response = client.chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile",
        temperature=0.1, 
    )
    
    raw_code = response.choices[0].message.content.strip()
    clean_code = raw_code.replace("```python", "").replace("```", "")
    
    return {"generated_code": clean_code}

def sandbox_node(state: T2GraphState):
    """Executes the generated Python code securely and captures the output/errors."""
    current_attempt = state.get("attempts", 0) + 1
    print(f"🛠️ Sandbox: Executing code (Attempt {current_attempt}/3)...")
    
    temp_file = "/tmp/temp_run.py"
    with open(temp_file, "w") as f:
        f.write(state["generated_code"])
        
    try:
        process = subprocess.run(
            ["python", temp_file], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if process.returncode == 0:
            result = f"SUCCESS:\n{process.stdout}"
        else:
            result = f"ERROR:\n{process.stderr}"
    except Exception as e:
        result = f"FATAL ERROR:\n{str(e)}"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
    return {"execution_result": result, "attempts": current_attempt}

def verifier_node(state: T2GraphState):
    """Self-healing loop: Analyzes stack traces and rewrites failing code."""
    print("🕵️ Verifier: Error detected! Analyzing the stack trace and fixing the code...")
    
    prompt = f"""
    The following Python code crashed:
    {state['generated_code']}
    
    Here is the Error Trace:
    {state['execution_result']}
    
    Rewrite the code to perfectly fix this error. Output ONLY raw Python code. No markdown.
    """
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.1
    )
    
    raw_code = response.choices[0].message.content.strip()
    clean_code = raw_code.replace("```python", "").replace("```", "")
    
    return {"generated_code": clean_code}

def researcher_node(state: T2GraphState):
    """Queries ChromaDB for semantic context and answers non-coding questions."""
    print("🎓 Researcher: Searching Semantic Memory (ChromaDB) for context...")
    
    # Connect to the database
    chroma_client = chromadb.PersistentClient(path="./t2_extension/chroma_db")
    collection = chroma_client.get_collection(name="course_materials")
    
    # The Retrieval Tool: Search the DB using the user's prompt
    db_results = collection.query(
        query_texts=[state["user_prompt"]],
        n_results=1  # Get the most relevant document
    )
    
    # Extract the retrieved knowledge
    retrieved_knowledge = db_results['documents'][0][0]
    print(f"🔍 Retrieved Knowledge: {retrieved_knowledge}")
    
    # Build the System Prompt with the injected knowledge
    system_prompt = f"""You are a highly intelligent educational AI tutor. 
    Answer the user's question clearly and concisely. Do NOT write executable python scripts. 
    
    IMPORTANT: You must base your answer on the following retrieved course rule:
    "{retrieved_knowledge}"
    """
    
    # Inject Episodic Memory (Chat History) + Semantic Memory (System Prompt)
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(state.get("chat_history", []))
    messages.append({"role": "user", "content": state["user_prompt"]})
    
    # Generate the final answer
    response = client.chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile",
        temperature=0.3, 
    )
    
    return {"final_text_response": response.choices[0].message.content.strip()}

# ---------------------------------------------------------
# 4. WIRING THE GRAPH (The Routers)
# ---------------------------------------------------------

def initial_router(state: T2GraphState):
    """The Traffic Cop: Determines whether to code or research."""
    prompt = state["user_prompt"].lower()
    
    code_triggers = [
        "write", "code", "script", "function", "calculate", "python", 
        "debug", "loop", "print", "change", "update", "fix"
    ]
    
    if any(trigger in prompt for trigger in code_triggers):
        print("🚥 Coordinator: Coding task detected. Routing to Coder.")
        return "coder"
    else:
        print("🚥 Coordinator: General question detected. Routing to Researcher.")
        return "researcher"

def check_result(state: T2GraphState):
    """Evaluates sandbox execution to dictate routing."""
    if "SUCCESS:" in state["execution_result"]:
        return "success"
    elif state["attempts"] >= 2:
        return "max_retries"
    else:
        return "error"

# --- Build the LangGraph Engine ---
workflow = StateGraph(T2GraphState)

workflow.add_node("coder", coder_node)
workflow.add_node("sandbox", sandbox_node)
workflow.add_node("verifier", verifier_node)
workflow.add_node("researcher", researcher_node)

workflow.add_conditional_edges(START, initial_router, {"coder": "coder", "researcher": "researcher"})
workflow.add_edge("coder", "sandbox")
workflow.add_conditional_edges("sandbox", check_result, {"success": END, "max_retries": END, "error": "verifier"})
workflow.add_edge("verifier", "sandbox")
workflow.add_edge("researcher", END)

t2_engine = workflow.compile()