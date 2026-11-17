import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Configuration
MEMORY_DIR = Path("memory")
MAX_SHORT_TERM_TURNS = 20     # Sliding window: keep SystemMessage + last N turns in RAM
MAX_MEMORY_FACTS = 30         # Compaction threshold: when facts exceed this limit...
TARGET_COMPACT_FACTS = 15     # ...consolidate down to this number


# =====================================================================
# LONG-TERM MEMORY ENGINE (Native JSON Array Storage)
# =====================================================================
def get_user_memory_path(user_id: str) -> Path:
    """Returns path to the user's JSON memory file."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    return MEMORY_DIR / f"{user_id}.json"


def load_user_facts(user_id: str) -> list[str]:
    """Loads user facts directly as a native Python list."""
    mem_path = get_user_memory_path(user_id)
    if mem_path.exists():
        try:
            return json.loads(mem_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_user_facts(user_id: str, facts: list[str]) -> None:
    """Saves user facts directly as a JSON array."""
    mem_path = get_user_memory_path(user_id)
    mem_path.write_text(json.dumps(facts, indent=2), encoding="utf-8")


def compact_memory(llm, user_id: str, facts: list[str]) -> list[str]:
    """
    Consolidates memory when it exceeds MAX_MEMORY_FACTS.
    Merges related facts, preserves core identity, and drops trivial details.
    """
    print(f"\n⚡ Memory limit reached ({len(facts)} facts). Running Memory Compaction...")

    compaction_prompt = f"""You are a memory consolidation engine. The user's profile has grown too long ({len(facts)} facts).
Synthesize, merge, and compress these into the top {TARGET_COMPACT_FACTS} most essential permanent facts.

Rules:
1. ALWAYS RETAIN core identity: Name, chosen alias/persona, primary role, key technical stack, long-term goals.
2. MERGE related or overlapping skills into single concise points.
3. REMOVE outdated, redundant, or minor trivial details.
4. Respond ONLY with a valid JSON array of strings containing at most {TARGET_COMPACT_FACTS} points.
Example: ["Identifies as baki / boxxer", "Linux Android STB Developer with 7 years experience"]

Current Facts:
{json.dumps(facts, indent=2)}
"""

    try:
        response = llm.invoke([HumanMessage(content=compaction_prompt)])
        raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        compacted = json.loads(raw_text)

        if isinstance(compacted, list) and compacted:
            save_user_facts(user_id, compacted)
            print(f"🧹 Compaction complete! Reduced from {len(facts)} to {len(compacted)} core facts.")
            return compacted
    except Exception as e:
        print(f"(Compaction skipped: {e})")

    return facts


def update_memory_from_session(llm, user_id: str, session_history: list) -> None:
    """
    1. Extracts new facts from today's chat (deliberately excluding SystemMessage).
    2. Appends new unique facts natively to the JSON list.
    3. Runs compaction if count exceeds MAX_MEMORY_FACTS.
    """
    # Only process if user actually sent messages
    human_messages = [m for m in session_history if isinstance(m, HumanMessage)]
    if not human_messages:
        return

    existing_facts = load_user_facts(user_id)

    # Transcript of ONLY today's chat (Human & AI messages — NO SystemMessage)
    # Step 1 (for m in session_history): Python grabs the message m.
    # Step 2 (if not isinstance(m, SystemMessage)): Python tests if it is a SystemMessage, Step 2 (if not isinstance(m, SystemMessage)): Python tests if it is a SystemMessage
    # Step 3 (The top expression): Only if Step 2 passed, Python formats the string: f"{'User'...}: {m.content}".
    # Step 4 ("\n".join(...)): Once all messages are processed, Python joins all the generated lines with newlines.
    transcript = "\n".join(
    f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content}" # ➡️ Step 3: Build the string
    for m in session_history                                          # ➡️ Step 1: Pick an item from list
    if not isinstance(m, SystemMessage)                               # ➡️ Step 2: Test condition (filter)
)
    extraction_prompt = f"""You are an analytical memory extractor.
Analyze today's conversation transcript and identify any NEW, enduring facts about the USER.(e.g. preferences, role, projects, tools, habits).

Capture:
1. Chosen identity, alias, nickname, or persona (e.g. if the user calls themselves fictional or non fictonal character.).
2. Professional background, skills, experience, tools, projects, and learning goals.
3. Personal preferences, traits, habits, and self-descriptions.

Already Known Facts (DO NOT duplicate these):
{json.dumps(existing_facts, indent=2)}

Today's Conversation Transcript:
{transcript}

Rules:
1. Capture self-identities, titles, aliases, or personas even if playful, fictional, or metaphorical (e.g. "Identifies as Gojo / Sorcerer by night, Developer by day") enduring facts about the user..
2. Do NOT re-extract or rephrase already known facts.
3. Do NOT record temporary questions or conversational chatter.
4. Respond ONLY with a valid JSON array of strings, e.g. ["Uses Ubuntu Linux", "Prefers JSON storage"].
5. If no new enduring facts were learned today, return [].
"""

    try:
        response = llm.invoke([HumanMessage(content=extraction_prompt)])
        raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        new_facts = json.loads(raw_text)

        if isinstance(new_facts, list) and new_facts:
            added_facts = []
            lower_existing = {f.lower() for f in existing_facts}

            for fact in new_facts:
                if fact.lower() not in lower_existing:
                    existing_facts.append(fact)
                    lower_existing.add(fact.lower())
                    added_facts.append(fact)

            if added_facts:
                print(f"\n🧠 Learned {len(added_facts)} new fact(s) today:")
                for f in added_facts:
                    print(f"   • {f}")

                save_user_facts(user_id, existing_facts)

                # Trigger compaction if threshold exceeded
                if len(existing_facts) > MAX_MEMORY_FACTS:
                    compact_memory(llm, user_id, existing_facts)

    except Exception as e:
        print(f"\n(Memory update skipped: {e})")


def build_system_message(user_id: str) -> SystemMessage:
    """Builds SystemMessage with user facts directly injected."""
    facts = load_user_facts(user_id)

    if facts:
        print(f"🧠 Loaded {len(facts)} persistent fact(s).")
        facts_text = "\n".join(f"- {f}" for f in facts)
        memory_section = f"\nWhat you remember about this user across previous interactions:\n{facts_text}\n"
    else:
        print("🧠 Starting with clean slate (no previous memory).")
        memory_section = "\nNo previous memory recorded yet."

    prompt = f"""You are a helpful, knowledgeable AI assistant. Be concise, friendly, and natural.
{memory_section}
Use this knowledge naturally when relevant. If the user has an alias, nickname, persona, or title, warmly acknowledge and respect that identity in conversation! Do not force it unless it adds genuine value."""

    return SystemMessage(content=prompt)


# =====================================================================
# MAIN APPLICATION LOOP
# =====================================================================
def main():
    load_dotenv(override=True)
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not google_api_key:
        raise EnvironmentError("Please provide the GOOGLE_API_KEY in the .env file")

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=google_api_key,
    )

    user_id = "praveen"
    memory_file = get_user_memory_path(user_id)

    print(f"👤 User: {user_id}")
    print(f"📄 Memory File: {memory_file}")

    # In-memory ephemeral session (lives ONLY in RAM)
    system_msg = build_system_message(user_id)
    messages = [system_msg]

    print("\n🤖 Agent initialized! Type 'exit' or 'quit' to stop.\n" + "-" * 55)

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nEnding session and analyzing memory...")
                break

            # Append user message to in-RAM history
            messages.append(HumanMessage(content=user_input))

            # Sliding window: keep SystemMessage (messages[0]) + last N conversation turns
            active_context = [messages[0]] + messages[-MAX_SHORT_TERM_TURNS:]

            # Stream response token-by-token in real time
            print("\nAI: ", end="", flush=True)
            full_response = ""

            for chunk in llm.stream(active_context):
                token = chunk.text
                print(token, end="", flush=True)
                full_response += token

            print()  # Newline after stream finishes

            # Append full AI reply to in-RAM memory
            messages.append(AIMessage(content=full_response))

        except KeyboardInterrupt:
            print("\nSession interrupted.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            continue

    # Update persistent JSON memory
    update_memory_from_session(llm, user_id, messages)

    print(f"📁 Updated {memory_file}")
    print("🗑️  In-RAM session cleared. Goodbye!")


if __name__ == "__main__":
    main()
