import os
from openai import OpenAI
import openai
import sys
import subprocess
import json
from pydantic import BaseModel, Field, field_validator

# Configuration Variables
MAX_HISTORY_LENGTH = 20
OLLAMA_MODEL_NAME = "phi3:latest"

# Pydantic Schemas for Tools
class RunTerminalCommandSchema(BaseModel):
    """Schema defining the structure and constraints for the terminal command tool."""
    cmd: str = Field(
        ...,
        description="The exact bash command to run (e.g., 'ls -la' or 'pwd'). Do NOT include interactive commands like 'nano', 'vim', or 'top' that require human input to exit."
    )

    @field_validator('cmd')
    @classmethod
    def check_dangerous_commands(cls, value: str) -> str:
        """Validates command string against a blacklist to prevent destructive actions."""
        forbidden = ["rm", "reboot", "sudo"]
        words = value.strip().split()
        for word in words:
            clean_word = word.split('/')[-1]
            if clean_word in forbidden:
                raise ValueError(f"Dangerous command '{clean_word}' detected. Execution blocked.")
        return value

def get_clean_schema(model_class):
    """Strips UI-specific metadata from Pydantic schemas to optimize token usage for the LLM."""
    schema = model_class.model_json_schema()
    schema.pop("title", None)
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)
    return schema

# Tool definitions mapped to Pydantic schemas
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_terminal_command",
            "description": "Executes a bash command on the user's Linux terminal. Use this to check system status, files, or run scripts.",
            "parameters": get_clean_schema(RunTerminalCommandSchema)
        }
    }
]

def execute_tool(tool_name, arguments_json):
    """Routes tool execution requests, validates arguments, and captures standard output/error."""
    if tool_name == "run_terminal_command":
        try:
            validated_args = RunTerminalCommandSchema.model_validate_json(arguments_json)
            cmd = validated_args.cmd
            print(f"\n[TOOL RUNNING] -> {cmd}")
            
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            output = result.stdout
            if result.stderr:
                output += "\nError: " + result.stderr
            return output if output else "Command executed successfully with no output."
        except Exception as e:
            return f"Error executing command (Validation Failed): {e}"
    return "Tool not recognized."

def summarize_conversation(client, model_name, messages_to_summarize):
    """Calls the LLM to generate a highly compressed, token-efficient summary of the provided message history."""
    try:
        summary_response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": f"Create a maximally token-efficient, highly compressed summary of the following history (including system context). Retain only critical entities, facts, and user preferences. Omit all conversational filler, grammar, titles, and markdown. Use comma-separated keywords or extremely short fragments to save tokens: {messages_to_summarize}"}]
        )
        return summary_response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] Failed to summarize: {e}")
        return "Could not generate summary."

def save_summary_to_file(summary_text, filename="state_management"):
    """Persists the latest conversation summary to disk for session continuity."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(summary_text.strip() + "\n")
    print(f"\n[INFO] Conversation summary saved to {filename}!")

def load_summary_from_file(filename="state_management"):
    """Retrieves a persisted conversation summary from disk if it exists."""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                print(f"[INFO] Loaded previous conversation history from {filename}!")
                return content
        except Exception as e:
            print(f"[ERROR] Failed to read history file: {e}")
    return None

def setup_client(mode):
    """Initializes the appropriate OpenAI client instance based on the execution mode (local vs cloud)."""
    if mode == "api":
        print("[INFO] Connecting to OpenRouter API...")
        api_key = <API_token>
        return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key), "minimax/minimax-m2.5:free"
    else:
        print(f"[INFO] Connecting to local Ollama (Model: {OLLAMA_MODEL_NAME})...")
        return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama-local"), OLLAMA_MODEL_NAME

def main():
    mode = "ollama"
    if len(sys.argv) > 1 and sys.argv[1].lower() == "api":
        mode = "api"
        
    client, current_model = setup_client(mode)

    print("=================================================")
    print(" Welcome to the Chatbot! Type 'exit' to stop.")
    print("=================================================")
    
    messages_history = []
    
    # Initialize conversation context from persistent storage
    past_summary = load_summary_from_file()
    if past_summary:
        messages_history.append({"role": "system", "content": f"Background context from previous session: {past_summary}"})

    # Main user interaction loop
    while True:
        user_question = input("\nWhat's on your mind...? ")
        
        if user_question.strip() == "":
            continue
            
        # Graceful exit handling and final state persistence
        if user_question.strip().lower() == 'exit':
            if len(messages_history) > 0:
                print("\n[INFO] Generating final summary before exiting...")
                final_summary = summarize_conversation(client, current_model, messages_history)
                if final_summary != "Could not generate summary.":
                    save_summary_to_file(final_summary)
            print("Goodbye!")
            break

        messages_history.append({"role": "user", "content": user_question})

        # Tool orchestration loop
        try:
            while True:
                # Inject core system instructions dynamically to enforce schema compliance
                api_messages = [{"role": "system", "content": "You are a helpful AI. You have access to tools. Only use tools if the user explicitly asks you to interact with the system or check files. NEVER output raw JSON tool schemas in your normal text responses."}] + messages_history
                
                response_stream = client.chat.completions.create(
                    model=current_model,
                    messages=api_messages,
                    tools=TOOLS,
                    stream=True,
                    stream_options={"include_usage": True} 
                )

                print("\nBot: ", end="", flush=True)
                bot_full_answer = ""
                tool_calls_buffer = {}

                # Stream processing block: handles text output and buffers tool call JSON chunks
                for chunk in response_stream:
                    if not chunk.choices: continue
                    delta = chunk.choices[0].delta
                    
                    if delta.content is not None:
                        content = delta.content
                        bot_full_answer += content
                        print(content, end="", flush=True)
                    
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": ""}}
                            if tc.function.arguments:
                                tool_calls_buffer[idx]["function"]["arguments"] += tc.function.arguments

                # Tool execution block: evaluates buffered tool requests and feeds results back to the LLM
                if tool_calls_buffer:
                    tool_calls_list = list(tool_calls_buffer.values())
                    
                    messages_history.append({
                        "role": "assistant",
                        "content": bot_full_answer if bot_full_answer else None,
                        "tool_calls": tool_calls_list
                    })
                    
                    for tc in tool_calls_list:
                        tool_result = execute_tool(tc["function"]["name"], tc["function"]["arguments"])
                        messages_history.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": tc["function"]["name"],
                            "content": tool_result
                        })
                    
                    continue 
                else:
                    messages_history.append({"role": "assistant", "content": bot_full_answer})
                    break

            # Context window management: compresses historical context when threshold is exceeded
            if len(messages_history) > MAX_HISTORY_LENGTH:
                 print("\n\n[DEBUG] History limit reached. Summarizing old messages in the background...")
                 
                 summary_text = summarize_conversation(client, current_model, messages_history[0:4])
                 
                 if summary_text != "Could not generate summary.":
                     del messages_history[0:4] 
                     messages_history.insert(0, {"role": "system", "content": f"Background context: {summary_text}"})
                 print("[DEBUG] Summarization complete! Ready for next question.")

        except openai.RateLimitError:
            print("\n[ERROR] OpenRouter's free tier is currently overloaded! Please wait a few seconds and try again.")
            messages_history.pop()
        except Exception as e:
            print(f"\n[ERROR] An unexpected error occurred: {e}")
            messages_history.pop()

if __name__ == "__main__":
    main()
