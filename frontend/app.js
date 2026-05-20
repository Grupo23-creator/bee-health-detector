console.log("app.js cargado");

let mediaRecorder;
let audioChunks = [];

const recordBtn = document.getElementById("recordBtn");
const stopBtn = document.getElementById("stopBtn");
const statusText = document.getElementById("status");
const resultText = document.getElementById("result");

recordBtn.onclick = async () => {
    console.log("🎙️ Grabando...");

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm"
    });

    audioChunks = [];

    mediaRecorder.ondataavailable = e => {
        audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
        try {
            statusText.textContent = "Procesando audio…";

            const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
            const formData = new FormData();
            formData.append("file", audioBlob, "audio.webm");

            console.log("📤 Enviando audio al backend...");

            const response = await fetch("/predict-audio", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                throw new Error("Error HTTP " + response.status);
            }

            const data = await response.json();
            console.log("✅ Respuesta backend:", data);

            resultText.textContent = "Resultado: " + data.prediction;
            statusText.textContent = "Listo ✅";

        } catch (err) {
            console.error("❌ Error:", err);
            statusText.textContent = "Error procesando audio";
        }
    };

    mediaRecorder.start();

    recordBtn.disabled = true;
    stopBtn.disabled = false;
    statusText.textContent = "Grabando…";
};

stopBtn.onclick = () => {
    console.log("⏹️ Grabación detenida");
    mediaRecorder.stop();

    recordBtn.disabled = false;
    stopBtn.disabled = true;
};
