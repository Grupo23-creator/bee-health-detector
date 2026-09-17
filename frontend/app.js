console.log("🐝 Bee Health Detector - app.js cargado");


// ============================================================================
// CONFIGURACIÓN
// ============================================================================

// Backend local utilizado durante desarrollo
const API_URL = "http://127.0.0.1:8000/api/v1/predict";


// ============================================================================
// ELEMENTOS DE LA INTERFAZ
// ============================================================================

const recordBtn = document.getElementById("recordBtn");

const stopBtn = document.getElementById("stopBtn");

const statusText = document.getElementById("status");

const resultCard = document.getElementById("resultCard");

const resultBadge = document.getElementById("resultBadge");

const diagnosisText = document.getElementById("diagnosisText");

const confidenceText = document.getElementById("confidenceText");

const lowProbability = document.getElementById("lowProbability");

const highProbability = document.getElementById("highProbability");

const lowBar = document.getElementById("lowBar");

const highBar = document.getElementById("highBar");

const totalSegments = document.getElementById("totalSegments");

const lowSegments = document.getElementById("lowSegments");

const highSegments = document.getElementById("highSegments");

const visualizer = document.getElementById("visualizer");


// ============================================================================
// VARIABLES DE GRABACIÓN
// ============================================================================

let mediaRecorder = null;

let audioChunks = [];

let currentStream = null;


// ============================================================================
// OBTENER FORMATO COMPATIBLE
// ============================================================================

function getSupportedMimeType() {

    const mimeTypes = [

        "audio/webm;codecs=opus",

        "audio/webm",

        "audio/ogg;codecs=opus"

    ];


    for (const mimeType of mimeTypes) {

        if (
            MediaRecorder.isTypeSupported(
                mimeType
            )
        ) {

            return mimeType;
        }
    }


    return "";
}


// ============================================================================
// INICIAR GRABACIÓN
// ============================================================================

recordBtn.onclick = async () => {

    console.log("🎙️ Solicitando acceso al micrófono...");


    try {

        currentStream =
            await navigator
                .mediaDevices
                .getUserMedia({
                    audio: true
                });


        const mimeType =
            getSupportedMimeType();


        if (mimeType) {

            mediaRecorder =
                new MediaRecorder(
                    currentStream,
                    {
                        mimeType:
                            mimeType
                    }
                );

        } else {

            mediaRecorder =
                new MediaRecorder(
                    currentStream
                );
        }


        audioChunks = [];


        // ------------------------------------------------------------
        // AUDIO DISPONIBLE
        // ------------------------------------------------------------

        mediaRecorder.ondataavailable =
            (event) => {

                if (
                    event.data &&
                    event.data.size > 0
                ) {

                    audioChunks.push(
                        event.data
                    );
                }
            };


        // ------------------------------------------------------------
        // GRABACIÓN TERMINADA
        // ------------------------------------------------------------

        mediaRecorder.onstop =
            async () => {

                await processRecording();

            };


        // ------------------------------------------------------------
        // COMENZAR
        // ------------------------------------------------------------

        mediaRecorder.start();


        recordBtn.disabled = true;

        stopBtn.disabled = false;


        visualizer.classList.add(
            "recording"
        );


        statusText.textContent =
            "Grabando audio…";


        resultCard.classList.add(
            "hidden"
        );


        console.log(
            "🎙️ Grabación iniciada"
        );

    }

    catch (error) {

        console.error(
            "❌ Error accediendo al micrófono:",
            error
        );


        statusText.textContent =
            "No fue posible acceder al micrófono.";


        alert(
            "No se pudo acceder al micrófono. " +
            "Verifica los permisos del navegador."
        );
    }
};


// ============================================================================
// DETENER GRABACIÓN
// ============================================================================

stopBtn.onclick = () => {

    console.log(
        "⏹️ Deteniendo grabación..."
    );


    if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
    ) {

        mediaRecorder.stop();
    }


    if (currentStream) {

        currentStream
            .getTracks()
            .forEach(
                track => track.stop()
            );
    }


    recordBtn.disabled = false;

    stopBtn.disabled = true;


    visualizer.classList.remove(
        "recording"
    );


    statusText.textContent =
        "Preparando audio…";
};


// ============================================================================
// PROCESAR GRABACIÓN
// ============================================================================

async function processRecording() {

    try {

        if (audioChunks.length === 0) {

            throw new Error(
                "No se capturó audio."
            );
        }


        statusText.textContent =
            "Procesando audio…";


        console.log(
            "📦 Creando archivo de audio..."
        );


        const audioBlob =
            new Blob(
                audioChunks,
                {
                    type:
                        audioChunks[0].type ||
                        "audio/webm"
                }
            );


        console.log(
            "📦 Tamaño:",
            audioBlob.size,
            "bytes"
        );


        // ------------------------------------------------------------
        // FORM DATA
        // ------------------------------------------------------------

        const formData =
            new FormData();


        formData.append(
            "file",
            audioBlob,
            "audio.webm"
        );


        // ------------------------------------------------------------
        // ENVIAR AL BACKEND
        // ------------------------------------------------------------

        console.log(
            "📤 Enviando audio al backend..."
        );


        const response =
            await fetch(
                API_URL,
                {
                    method: "POST",
                    body: formData
                }
            );


        console.log(
            "📥 HTTP:",
            response.status
        );


        // ------------------------------------------------------------
        // RESPUESTA
        // ------------------------------------------------------------

        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Error HTTP " +
                response.status
            );
        }


        console.log(
            "✅ Respuesta:",
            data
        );


        // ------------------------------------------------------------
        // MOSTRAR RESULTADO
        // ------------------------------------------------------------

        displayResult(
            data
        );


        statusText.textContent =
            "Análisis completado ✓";

    }

    catch (error) {

        console.error(
            "❌ Error procesando audio:",
            error
        );


        statusText.textContent =
            "Error procesando el audio";


        alert(
            "No fue posible procesar el audio.\n\n" +
            error.message
        );
    }

    finally {

        recordBtn.disabled = false;

        stopBtn.disabled = true;

        visualizer.classList.remove(
            "recording"
        );
    }
}


// ============================================================================
// MOSTRAR RESULTADO
// ============================================================================

function displayResult(data) {

    const level =
        data.varroa_level;


    const confidence =
        Number(
            data.confidence_percentage
        );


    const low =
        Number(
            data.probabilities?.LOW || 0
        );


    const high =
        Number(
            data.probabilities?.HIGH || 0
        );


    const total =
        data.segments?.total || 0;


    const lowCount =
        data.segments?.LOW || 0;


    const highCount =
        data.segments?.HIGH || 0;


    // ------------------------------------------------------------
    // DIAGNÓSTICO
    // ------------------------------------------------------------

    diagnosisText.textContent =
        data.diagnosis ||
        level ||
        "Resultado desconocido";


    confidenceText.textContent =
        `Confianza estimada del modelo: ${confidence.toFixed(2)}%`;


    // ------------------------------------------------------------
    // BADGE
    // ------------------------------------------------------------

    resultBadge.textContent =
        level || "—";


    resultBadge.classList.remove(
        "high",
        "low"
    );


    if (level === "HIGH") {

        resultBadge.classList.add(
            "high"
        );

    } else if (level === "LOW") {

        resultBadge.classList.add(
            "low"
        );
    }


    // ------------------------------------------------------------
    // PROBABILIDADES
    // ------------------------------------------------------------

    lowProbability.textContent =
        `${low.toFixed(2)}%`;


    highProbability.textContent =
        `${high.toFixed(2)}%`;


    // Reiniciar barras
    lowBar.style.width = "0%";

    highBar.style.width = "0%";


    // Pequeño retraso para permitir animación
    setTimeout(() => {

        lowBar.style.width =
            `${low}%`;

        highBar.style.width =
            `${high}%`;

    }, 50);


    // ------------------------------------------------------------
    // SEGMENTOS
    // ------------------------------------------------------------

    totalSegments.textContent =
        total;


    lowSegments.textContent =
        lowCount;


    highSegments.textContent =
        highCount;


    // ------------------------------------------------------------
    // MOSTRAR TARJETA
    // ------------------------------------------------------------

    resultCard.classList.remove(
        "hidden"
    );


    // Desplazar suavemente hacia el resultado
    setTimeout(() => {

        resultCard.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }, 100);
}