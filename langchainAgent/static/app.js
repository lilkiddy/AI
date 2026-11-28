let mediaRecorder;
let activeStream = null;
let audioChunks = [];
let isRecording = false;
let isProcessing = false;
let audioPlayer = new Audio(); // Reusable audio player for TTS playback

const loginScreen = document.getElementById("loginScreen");
const agentScreen = document.getElementById("agentScreen");
const loginStatus = document.getElementById("loginStatus");
const startSessionBtn = document.getElementById("startSessionBtn");
const micBtn = document.getElementById("micBtn");
const status = document.getElementById("status");
const userText = document.getElementById("userText");
const aiText = document.getElementById("aiText");
const userIdInput = document.getElementById("userIdInput");
const profileBadge = document.getElementById("profileBadge");
const stopAudioBtn = document.getElementById("stopAudioBtn");

// Allow pressing Enter in the username box to start session
userIdInput.addEventListener("keydown", event => {
    if (event.key === "Enter") selectUser();
});

function switchUserScreen() {
    if (isProcessing || isRecording) return;
    audioPlayer.pause();
    audioPlayer.currentTime = 0;
    agentScreen.classList.add("hidden");
    loginScreen.classList.remove("hidden");
    loginStatus.innerText = "Enter a username to switch profiles";
    userIdInput.focus();
}

async function selectUser() {
    if (isProcessing || isRecording) return;
    const rawName = userIdInput.value.trim();
    if (!rawName) {
        loginStatus.innerText = "Please enter a username first.";
        userIdInput.focus();
        return;
    }

    isProcessing = true;
    startSessionBtn.disabled = true;
    loginStatus.innerText = `Loading profile "${rawName}"...`;

    try {
        const res = await fetch("/select-user", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: rawName })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Failed to load user");

        const factLabel = `${data.facts_count} saved fact${data.facts_count === 1 ? "" : "s"}`;
        profileBadge.innerText = data.is_new_user
            ? `✨ ${data.user_id} (new profile)`
            : `👤 ${data.user_id} • ${factLabel}`;
        userText.innerText = "Waiting for your voice...";
        aiText.innerText = data.is_new_user
            ? `New profile "${data.user_id}" created. Say hello!`
            : `Welcome back, ${data.user_id}!`;
        status.innerText = "Click microphone to speak";

        // Transition from Login Screen to Voice Agent Screen
        loginScreen.classList.add("hidden");
        agentScreen.classList.remove("hidden");
    } catch (err) {
        loginStatus.innerText = "Could not load profile: " + err.message;
    } finally {
        isProcessing = false;
        startSessionBtn.disabled = false;
    }
}

function releaseMicStream() {
    if (activeStream) {
        activeStream.getTracks().forEach(track => track.stop());
        activeStream = null;
    }
}

function getFileExtension(mimeType) {
    const mime = (mimeType || "").toLowerCase();
    if (mime.includes("ogg")) return "ogg";
    if (mime.includes("mp4")) return "mp4";
    if (mime.includes("wav")) return "wav";
    return "webm";
}

async function toggleRecording() {
    if (isProcessing) return;

    if (!isRecording) {
        // Stop any ongoing TTS playback if user starts speaking again
        audioPlayer.pause();
        audioPlayer.currentTime = 0;

        try {
            activeStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(activeStream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const mimeType = mediaRecorder.mimeType || "audio/webm";
                releaseMicStream();
                const audioBlob = new Blob(audioChunks, { type: mimeType });
                await sendAudioToServer(audioBlob);
            };

            mediaRecorder.start();
            isRecording = true;
            micBtn.classList.add("recording");
            micBtn.innerText = "⏹️";
            status.innerText = "Listening... Click to stop";
        } catch (err) {
            releaseMicStream();
            alert("Microphone permission denied: " + err.message);
        }
    } else {
        mediaRecorder.stop();
        isRecording = false;
        micBtn.classList.remove("recording");
        micBtn.innerText = "🎙️";
        status.innerText = "Transcribing & Thinking...";
    }
}

async function sendAudioToServer(blob) {
    isProcessing = true;
    micBtn.disabled = true;

    const ext = getFileExtension(blob.type);
    const formData = new FormData();
    formData.append("file", blob, `recording.${ext}`);

    let aiResponse = "";
    try {
        const response = await fetch("/transcribe", {
            method: "POST",
            body: formData
        });

        if (!response.ok) throw new Error("Server error " + response.status);

        const data = await response.json();
        userText.innerText = data.transcription || "(No speech detected)";
        aiText.innerText = data.ai_response || "(No response)";
        aiResponse = data.ai_response || "";
    } catch (error) {
        status.innerText = "Error processing voice request";
        aiText.innerText = "Failed: " + error.message;
        return;
    } finally {
        isProcessing = false;
        micBtn.disabled = false;
    }

    // Play AI response as audio via Edge-TTS
    if (aiResponse) {
        status.innerText = "🔊 Speaking response...";
        await playTTS(aiResponse);
    }
    if (!isRecording && !isProcessing) {
        status.innerText = "Ready! Click microphone to reply.";
    }
}

function stopTTS() {
    audioPlayer.pause();
    audioPlayer.currentTime = 0;
    stopAudioBtn.classList.add("hidden");
    if (!isRecording && !isProcessing) {
        status.innerText = "Audio stopped. Click microphone to reply.";
    }
}

async function playTTS(text) {
    try {
        // Stop any currently playing audio
        audioPlayer.pause();
        audioPlayer.currentTime = 0;

        // Fetch MP3 audio from the /synthesize endpoint
        const response = await fetch("/synthesize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok) throw new Error("TTS error " + response.status);

        // Convert response to a playable audio blob
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);

        audioPlayer.src = audioUrl;
        stopAudioBtn.classList.remove("hidden");
        await audioPlayer.play();

        // Wait for audio to finish, fail, or be stopped/paused
        await new Promise(resolve => {
            audioPlayer.onended = resolve;
            audioPlayer.onerror = resolve;
            audioPlayer.onpause = resolve;
        });

        stopAudioBtn.classList.add("hidden");

        // Clean up the blob URL to free memory
        URL.revokeObjectURL(audioUrl);
    } catch (err) {
        stopAudioBtn.classList.add("hidden");
        console.error("TTS playback failed:", err);
    }
}

async function endSession() {
    if (isProcessing) return;
    try {
        status.innerText = "Analyzing memory and saving profile...";
        const res = await fetch("/end-session", { method: "POST" });
        await res.json();
        const infoRes = await fetch("/session-info");
        if (infoRes.ok) {
            const info = await infoRes.json();
            profileBadge.innerText = `👤 ${info.user_id} • ${info.facts_count} saved fact${info.facts_count === 1 ? "" : "s"}`;
        }
        status.innerText = "Memory saved successfully! Session reset.";
        userText.innerText = "Waiting for your voice...";
        aiText.innerText = "AI is ready.";
    } catch (e) {
        status.innerText = "Could not save memory.";
    }
}
