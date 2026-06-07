# Native Python AI Agent Orchestrator

## The Objective
As the industry rushes to adopt AI orchestration frameworks like LangChain and LangGraph, I wanted to understand the actual engine running underneath them before treating them as black boxes. 

Coming from a systems engineering and DevOps background, I built this autonomous AI agent entirely from scratch using raw Python. The goal of this project is to manually engineer the core tool-execution loop, manage persistent memory, and implement strict action-validation to protect the host operating system. By building this without abstractions, the architecture maps perfectly to what modern frameworks are doing under the hood.

## Core Architecture vs. Framework Abstractions

This agent relies on six fundamental engineering pillars, ordered by their impact on the application's capability:

### 1. Parallel Tool Execution
* **The Framework Way:** Advanced agents support parallel function calling, allowing the AI to request multiple actions simultaneously before providing a final answer.
* **The Raw Python Way:** Instead of limiting the AI to one action per turn, my streaming loop utilizes a dynamic buffer (`tool_calls_buffer`). If the LLM determines it needs to check the current directory (`pwd`), list the files (`ls -la`), and read a log (`cat error.log`) all at once, the code successfully captures the multi-tool JSON array, executes every command sequentially, and feeds all outputs back to the LLM in a single consolidated context window.

### 2. The Orchestration Engine (LangGraph Equivalent)
* **The Framework Way:** LangGraph uses cyclic graphs and nodes to manage state, routing between an LLM and tools until a condition is met.
* **The Raw Python Way:** This agent uses a continuous `while True` execution loop. When the LLM streams a tool-call request, the script pauses generation, executes the requested command on the local system, appends the raw terminal output back into the conversation history, and instantly re-prompts the LLM. It acts as a manual, single-node state machine.

### 3. Action Validation Guardrails (LangChain `@tool` Equivalent)
* **The Framework Way:** LangChain uses `@tool` decorators and complex guardrail libraries to prevent destructive AI actions.
* **The Raw Python Way:** Giving an AI direct access to a system terminal introduces massive security risks via command injection. I implemented a native security layer using **Pydantic `@field_validator`**. Before any LLM-generated command reaches the OS, the code intercepts it:
  * It strips path prefixes to prevent bypasses (e.g., converting `/bin/rm` to `rm`).
  * It checks the core command against a strict blacklist (blocking `rm`, `sudo`, `reboot`, etc.).
  * If a threat is detected, it intercepts the execution, throws a `ValueError`, and feeds that error string directly back into the LLM's context, forcing the model to learn and try a safer approach.

### 4. Persistent Sliding-Window Memory & Zero-Latency UX
* **The Framework Way:** Frameworks utilize built-in memory classes (`ConversationSummaryMemory`) that automatically prune or summarize old messages to manage context limits.
* **The Raw Python Way:** To prevent the agent from overflowing its token window, I built a background summarization pipeline. Once the history array exceeds `MAX_HISTORY_LENGTH`, the oldest messages are compressed into a token-efficient summary string, saved to disk, and injected as a system prompt for the next API call. 
* **The Engineering UX:** Crucially, this memory maintenance triggers strictly *after* the AI has fully streamed its answer to the user. While the user is reading the response, the script handles the API summarization call during that natural downtime. This prevents blocking and ensures the user never experiences artificial latency while the context window is being managed.

### 5. Stream Parsing & Token Optimization
* **The Framework Way:** Frameworks handle asynchronous API streaming under the hood and pass bloated default JSON schemas to the model.
* **The Raw Python Way:** The code manually parses the OpenAI `delta` stream in real-time, buffering JSON tool-call fragments while printing conversational text to the terminal. Furthermore, a custom `get_clean_schema()` function intercepts the Pydantic schema and strips out unnecessary metadata (like `title` tags) to optimize token usage. Finally, dynamic anti-hallucination prompts are injected per-call to prevent smaller local models from leaking raw JSON syntax to the user.

### 6. Hybrid Deployment (Local & Cloud Versatility)
* **The Framework Way:** Many introductory tutorials tightly couple their logic to a single provider, requiring code rewrites to test local open-source models.
* **The Raw Python Way:** This agent is built for complete environment versatility. The SDK is dynamically configured to route traffic either to a local Ollama instance (for secure, free, offline testing) or to a cloud endpoint like OpenRouter (for accessing massive foundation models). You can switch between local and cloud execution with a single command-line argument (`python native_agent.py` vs `python native_agent.py api`), proving the architecture is completely agnostic to the LLM provider.

## Generated Files & State Management
When running this agent, it dynamically generates the following file in your root directory to handle memory:
* `state_management` - This file is automatically created and overwritten whenever the conversation exceeds the `MAX_HISTORY_LENGTH`. When the application initializes, it immediately checks for this file and loads the context if present. This guarantees **persisted state even after closing the app and starting it again**. Crucially, it does not save a verbatim transcript of everything you typed. Instead, it stores a highly compressed, token-efficient summary of the entire conversation. This allows the AI to retain long-term background context across sessions without bloating the API token limit. To completely reset the AI's memory, simply delete this file.

## Tech Stack
* **Python 3.x**
* **OpenAI SDK** (Configured dynamically for OpenRouter API or local Ollama endpoints)
* **Pydantic** (For strict schema generation and pre-execution validation)
* **Subprocess** (For local OS tool execution)

## How to Run It

```bash
# ==========================================
# STEP 1: Clone and Install
# ==========================================
git clone [https://github.com/lilkiddy/AI.git](https://github.com/lilkiddy/AI.git)
cd AI/Native_AI_Agent

# Install the required packages 
pip install -r requirements.txt

# ==========================================
# STEP 2: Configure Your AI Engine
# ==========================================
# OPTION A: Local Execution via Ollama (Default)
# 1. Install Ollama from [https://ollama.com/](https://ollama.com/)
# 2. Pull the required model:
ollama pull phi3:latest
# (To use a different model, update the OLLAMA_MODEL_NAME variable in native_agent.py)

# OPTION B: Cloud API via OpenRouter
# 1. Get an API key from [https://openrouter.ai/](https://openrouter.ai/)
# 2. Open native_agent.py and replace <API_token> with your actual key string.

# ==========================================
# STEP 3: Execute the Agent
# ==========================================
# To run locally (Ollama):
python native_agent.py

# To run via Cloud API (OpenRouter):
python native_agent.py api