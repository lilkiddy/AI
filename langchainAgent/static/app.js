let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let audioPlayer = new Audio(); // Reusable audio player for TTS playback

const micBtn = document.getElementById("micBtn");
const status = document.getElementById("status");
const userText = document.getElementById("userText");
const aiText = document.getElementById("aiText");

async function toggleRecording() {
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                await sendAudioToServer(audioBlob);
            };

            mediaRecorder.start();
            isRecording = true;
            micBtn.classList.add("recording");
            micBtn.innerText = "⏹️";
            status.innerText = "Listening... Click to stop";
        } catch (err) {
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
    const formData = new FormData();
    formData.append("file", blob, "recording.wav");

    try {
        const response = await fetch("/transcribe", {
            method: "POST",
            body: formData
        });

        if (!response.ok) throw new Error("Server error " + response.status);

        const data = await response.json();
        userText.innerText = data.transcription || "(No speech detected)";
        aiText.innerText = data.ai_response || "(No response)";
        status.innerText = "🔊 Speaking response...";

        // Play AI response as audio via Edge-TTS
        if (data.ai_response) {
            await playTTS(data.ai_response);
        }
        status.innerText = "Ready! Click microphone to reply.";
    } catch (error) {
        status.innerText = "Error processing voice request";
        aiText.innerText = "Failed: " + error.message;
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
        await audioPlayer.play();

        // Wait for audio to finish playing before returning
        await new Promise(resolve => {
            audioPlayer.onended = resolve;
            audioPlayer.onerror = resolve;
        });

        // Clean up the blob URL to free memory
        URL.revokeObjectURL(audioUrl);
    } catch (err) {
        console.error("TTS playback failed:", err);
    }
}

async function endSession() {
    try {
        status.innerText = "Analyzing memory and saving profile...";
        const res = await fetch("/end-session", { method: "POST" });
        await res.json();
        status.innerText = "Memory saved successfully! Session reset.";
        userText.innerText = "Waiting for your voice...";
        aiText.innerText = "AI is ready.";
    } catch (e) {
        status.innerText = "Could not save memory.";
    }
}
