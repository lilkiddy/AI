# Change Log — Voice AI Agent

Detailed engineering notes for major updates—explaining **what changed**, **why it was needed**, and **how it works** so every commit stays easy to understand later.

---

## Upgrade: Non-Blocking Async Gateway, In-Memory STT, Pydantic Memory & Mic Fixes

### 1. [agent.py](file:///home/prvn/ai/experiments/AI/langchainAgent/agent.py)
* **Fixed duplicate `SystemMessage` in sliding window (`_get_active_context`):**
  * **Before:** `[self.messages[0]] + self.messages[-MAX_SHORT_TERM_TURNS:]` included `messages[0]` (`SystemMessage`) twice whenever total messages were `<= 20`.
  * **Now:** `[self.messages[0]] + self.messages[1:][-MAX_SHORT_TERM_TURNS:]` always pins `SystemMessage` once at index `0` and slices only the rolling conversation turns (`messages[1:]`).
* **Unified streaming (`chat_stream`) & CLI loop:**
  * Added `VoiceAgent.chat_stream()` with rollback protection (`self.messages.pop()` if streaming fails or returns empty) and updated CLI `main()` to iterate over it instead of duplicating `llm.stream()` logic.
* **Pydantic Structured Outputs (`FactList`):**
  * Replaced brittle `.replace("```json", "")` + `json.loads()` parsing with `FactList(BaseModel)` and `llm.with_structured_output(FactList)` in both `update_memory_from_session()` and `compact_memory()`.

---

### 2. [server.py](file:///home/prvn/ai/experiments/AI/langchainAgent/server.py)
* **Unblocked FastAPI's Main Event Loop (`asyncio.to_thread`):**
  * `transcribe_audio()`, `agent.chat()`, and `agent.end_session()` are blocking synchronous functions. Running them directly inside `async def` routes froze the entire FastAPI event loop until they finished.
  * Wrapping them in `await asyncio.to_thread(...)` offloads them to a background worker thread so other requests (like `GET /` or `/synthesize`) remain responsive.
* **Protected Shared Agent State (`agent_lock = asyncio.Lock()`):**
  * Because `agent` is a single shared object in RAM and worker threads can run concurrently, `async with agent_lock:` ensures only one request mutates `agent.messages` at a time (preventing race conditions between `/transcribe` and `/end-session`).

---

### 3. [stt_service.py](file:///home/prvn/ai/experiments/AI/langchainAgent/stt_service.py)
* **Zero-Disk In-Memory STT (`io.BytesIO`):**
  * **Before:** Every voice turn wrote a temporary `.wav` file to disk (`tempfile.NamedTemporaryFile`) and deleted it after transcription.
  * **Now:** Wraps `audio_data` directly in `io.BytesIO(audio_data)` and passes the in-memory stream to Faster-Whisper, avoiding disk I/O and temp-file cleanup. Empty audio returns `""` immediately.

---

### 4. [static/app.js](file:///home/prvn/ai/experiments/AI/langchainAgent/static/app.js)
* **Fixed Microphone Hardware Leak (`releaseMicStream`):**
  * `mediaRecorder.stop()` stops recording chunks, but leaves the OS microphone handle open (red mic icon stays on in Chrome). Calling `track.stop()` on every stream track in `onstop` (and on setup error) releases the mic immediately.
* **Real Container MIME Type instead of fake `.wav`:**
  * Browsers record `audio/webm` (Opus), not uncompressed WAV. Now uses `mediaRecorder.mimeType || "audio/webm"` and a matching extension (`webm`, `ogg`, `mp4`, `wav`) in `FormData`.
* **Interruptible TTS & Double-Click Guard:**
  * Disables `micBtn` only while `/transcribe` is in-flight, re-enabling it before `playTTS()` starts, and resolves `audioPlayer` on `onpause` so clicking the mic mid-speech stops TTS and starts recording immediately.

---

### 5. [requirements.txt](file:///home/prvn/ai/experiments/AI/langchainAgent/requirements.txt) & Docs
* Removed unused `pandas` and `langchain-huggingface`; explicitly listed `pydantic>=2.0.0`.
* Updated [README.md](file:///home/prvn/ai/experiments/AI/langchainAgent/README.md) and [BUILD_AND_RUN.md](file:///home/prvn/ai/experiments/AI/langchainAgent/BUILD_AND_RUN.md) to reflect browser-native `WebM/Opus` streamed in-memory.
* Added **Section 7 (Why `async` Over `sync`)** to [docs/FRONTEND_AND_COMMUNICATION.md](file:///home/prvn/ai/experiments/AI/langchainAgent/docs/FRONTEND_AND_COMMUNICATION.md) explaining the main event loop, `await`, `asyncio.to_thread`, and `asyncio.Lock`.
