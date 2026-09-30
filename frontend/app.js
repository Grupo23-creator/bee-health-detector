console.log("🐝 Bee Health Detector - app.js cargado");


// ============================================================================
// CONFIGURACIÓN
// ============================================================================

const API_URL =
    "https://bee-health-api.onrender.com/api/v1/predict";

const STORAGE_KEY =
    "beeHealthAnalysisHistory";


// ============================================================================
// ELEMENTOS DE LA INTERFAZ
// ============================================================================

const recordBtn =
    document.getElementById("recordBtn");

const stopBtn =
    document.getElementById("stopBtn");

const statusText =
    document.getElementById("status");

const resultCard =
    document.getElementById("resultCard");

const resultBadge =
    document.getElementById("resultBadge");

const diagnosisText =
    document.getElementById("diagnosisText");

const confidenceText =
    document.getElementById("confidenceText");

const lowProbability =
    document.getElementById("lowProbability");

const highProbability =
    document.getElementById("highProbability");

const lowBar =
    document.getElementById("lowBar");

const highBar =
    document.getElementById("highBar");

const totalSegments =
    document.getElementById("totalSegments");

const lowSegments =
    document.getElementById("lowSegments");

const highSegments =
    document.getElementById("highSegments");

const visualizer =
    document.getElementById("visualizer");


// ============================================================================
// ELEMENTOS DE COLMENA
// ============================================================================

const hiveSelect =
    document.getElementById("hiveSelect");

const customHiveGroup =
    document.getElementById("customHiveGroup");

const customHive =
    document.getElementById("customHive");


// ============================================================================
// VARIABLES DE GRABACIÓN
// ============================================================================

let mediaRecorder = null;

let audioChunks = [];

let currentStream = null;


// Colmena asociada a la grabación actual.
// Se captura cuando comienza la grabación para evitar
// que un cambio posterior del selector altere el registro.
let currentHive = null;


// ============================================================================
// INICIALIZACIÓN
// ============================================================================

initializeHiveSelector();


// ============================================================================
// SELECTOR DE COLMENA
// ============================================================================

function initializeHiveSelector() {

    if (!hiveSelect) {

        console.warn(
            "No se encontró el selector de colmena."
        );

        return;
    }


    hiveSelect.addEventListener(
        "change",
        handleHiveChange
    );


    // Estado inicial
    updateRecordingAvailability();
}


// ============================================================================
// CAMBIO DE COLMENA
// ============================================================================

function handleHiveChange() {

    const value =
        hiveSelect.value;


    // ------------------------------------------------------------
    // OTRA / NUEVA COLMENA
    // ------------------------------------------------------------

    if (value === "OTHER") {

        customHiveGroup.classList.remove(
            "hidden"
        );

        customHive.focus();

    } else {

        customHiveGroup.classList.add(
            "hidden"
        );

        customHive.value = "";
    }


    updateRecordingAvailability();
}


// ============================================================================
// OBTENER COLMENA SELECCIONADA
// ============================================================================

function getSelectedHive() {

    if (!hiveSelect) {

        return null;
    }


    const selected =
        hiveSelect.value;


    // No seleccionada
    if (!selected) {

        return null;
    }


    // Nueva colmena
    if (selected === "OTHER") {

        const customValue =
            customHive
                ? customHive.value.trim()
                : "";


        if (!customValue) {

            return null;
        }


        return normalizeHiveCode(
            customValue
        );
    }


    return selected;
}


// ============================================================================
// NORMALIZAR CÓDIGO DE COLMENA
// ============================================================================

function normalizeHiveCode(value) {

    if (!value) {

        return "";
    }


    let hive =
        value
            .trim()
            .toUpperCase();


    // Si el usuario escribe solamente 3700,
    // lo convertimos en HIVE-3700.
    if (
        /^\d+$/.test(hive)
    ) {

        hive =
            `HIVE-${hive}`;
    }


    // Si escribe HIVE 3700
    // lo convertimos en HIVE-3700.
    hive =
        hive.replace(
            /^HIVE\s+/i,
            "HIVE-"
        );


    return hive;
}


// ============================================================================
// HABILITAR / DESHABILITAR GRABACIÓN
// ============================================================================

function updateRecordingAvailability() {

    if (!recordBtn) {

        return;
    }


    const hive =
        getSelectedHive();


    // Si no hay colmena seleccionada,
    // no permitimos iniciar grabación.
    if (!hive) {

        recordBtn.disabled = true;

        if (statusText) {

            statusText.textContent =
                "Selecciona una colmena para comenzar.";
        }

        return;
    }


    // Solo habilitamos si no estamos grabando.
    if (
        !mediaRecorder ||
        mediaRecorder.state === "inactive"
    ) {

        recordBtn.disabled = false;

        if (statusText) {

            statusText.textContent =
                `Colmena seleccionada: ${hive}. Lista para grabar.`;
        }
    }
}


// ============================================================================
// OBTENER FORMATO COMPATIBLE
// ============================================================================

function getSupportedMimeType() {

    const mimeTypes = [

        "audio/webm;codecs=opus",

        "audio/webm",

        "audio/ogg;codecs=opus"

    ];


    for (
        const mimeType of mimeTypes
    ) {

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

    console.log(
        "🎙️ Solicitando acceso al micrófono..."
    );


    // ------------------------------------------------------------
    // VALIDAR COLMENA
    // ------------------------------------------------------------

    const selectedHive =
        getSelectedHive();


    if (!selectedHive) {

        alert(
            "Selecciona una colmena antes de iniciar la grabación."
        );

        return;
    }


    // Guardamos la colmena de esta grabación.
    currentHive =
        selectedHive;


    console.log(
        "🐝 Colmena seleccionada:",
        currentHive
    );


    try {

        // --------------------------------------------------------
        // MICRÓFONO
        // --------------------------------------------------------

        if (
            !navigator.mediaDevices ||
            !navigator.mediaDevices.getUserMedia
        ) {

            throw new Error(
                "El navegador no permite acceder al micrófono."
            );
        }


        currentStream =
            await navigator
                .mediaDevices
                .getUserMedia({
                    audio: true
                });


        // --------------------------------------------------------
        // FORMATO
        // --------------------------------------------------------

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


        // --------------------------------------------------------
        // LIMPIAR AUDIO ANTERIOR
        // --------------------------------------------------------

        audioChunks = [];


        // --------------------------------------------------------
        // AUDIO DISPONIBLE
        // --------------------------------------------------------

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


        // --------------------------------------------------------
        // GRABACIÓN TERMINADA
        // --------------------------------------------------------

        mediaRecorder.onstop =
            async () => {

                await processRecording();

            };


        // --------------------------------------------------------
        // MANEJO DE ERROR
        // --------------------------------------------------------

        mediaRecorder.onerror =
            (event) => {

                console.error(
                    "❌ Error del MediaRecorder:",
                    event
                );
            };


        // --------------------------------------------------------
        // COMENZAR
        // --------------------------------------------------------

        mediaRecorder.start();


        recordBtn.disabled = true;

        stopBtn.disabled = false;


        visualizer.classList.add(
            "recording"
        );


        statusText.textContent =
            `Grabando audio de ${currentHive}…`;


        resultCard.classList.add(
            "hidden"
        );


        console.log(
            "🎙️ Grabación iniciada para:",
            currentHive
        );

    }

    catch (error) {

        console.error(
            "❌ Error accediendo al micrófono:",
            error
        );


        // Liberar stream si algo falló
        if (currentStream) {

            currentStream
                .getTracks()
                .forEach(
                    track => track.stop()
                );

            currentStream = null;
        }


        recordBtn.disabled = false;

        stopBtn.disabled = true;


        statusText.textContent =
            "No fue posible acceder al micrófono.";


        alert(
            "No se pudo acceder al micrófono.\n\n" +
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

        currentStream = null;
    }


    recordBtn.disabled = true;

    stopBtn.disabled = true;


    visualizer.classList.remove(
        "recording"
    );


    statusText.textContent =
        `Preparando audio de ${currentHive || "la colmena"}…`;
};


// ============================================================================
// PROCESAR GRABACIÓN
// ============================================================================

async function processRecording() {

    try {

        // --------------------------------------------------------
        // VALIDAR AUDIO
        // --------------------------------------------------------

        if (
            audioChunks.length === 0
        ) {

            throw new Error(
                "No se capturó audio."
            );
        }


        if (!currentHive) {

            throw new Error(
                "No se pudo identificar la colmena de la grabación."
            );
        }


        statusText.textContent =
            `Procesando audio de ${currentHive}…`;


        console.log(
            "📡 Creando archivo de audio..."
        );


        // --------------------------------------------------------
        // CREAR BLOB
        // --------------------------------------------------------

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
            "📡 Tamaño del audio:",
            audioBlob.size,
            "bytes"
        );


        // --------------------------------------------------------
        // FORM DATA
        // --------------------------------------------------------

        const formData =
            new FormData();


        formData.append(
            "file",
            audioBlob,
            "audio.webm"
        );


        // --------------------------------------------------------
        // ENVIAR AL BACKEND
        // --------------------------------------------------------

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


        // --------------------------------------------------------
        // RESPUESTA
        // --------------------------------------------------------

        let data;


        try {

            data =
                await response.json();

        }

        catch (jsonError) {

            throw new Error(
                "El servidor devolvió una respuesta que no pudo ser interpretada."
            );
        }


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Error HTTP " +
                response.status
            );
        }


        console.log(
            "✅ Respuesta del backend:",
            data
        );


        // --------------------------------------------------------
        // MOSTRAR RESULTADO
        // --------------------------------------------------------

        displayResult(
            data
        );


        // --------------------------------------------------------
        // GUARDAR HISTORIAL
        // --------------------------------------------------------

        saveAnalysis(
            data
        );


        statusText.textContent =
            `Análisis completado para ${currentHive} ✓`;


        console.log(
            "💾 Análisis guardado en historial:",
            currentHive
        );

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


        // Limpiar stream por seguridad
        if (currentStream) {

            currentStream
                .getTracks()
                .forEach(
                    track => track.stop()
                );

            currentStream = null;
        }


        // Mantener la colmena seleccionada
        // para el siguiente análisis.
        updateRecordingAvailability();
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
            data.confidence_percentage || 0
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
        Number(
            data.segments?.total || 0
        );


    const lowCount =
        Number(
            data.segments?.LOW || 0
        );


    const highCount =
        Number(
            data.segments?.HIGH || 0
        );


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

    }

    else if (level === "LOW") {

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
    lowBar.style.width =
        "0%";

    highBar.style.width =
        "0%";


    // Animación
    setTimeout(
        () => {

            lowBar.style.width =
                `${Math.min(Math.max(low, 0), 100)}%`;

            highBar.style.width =
                `${Math.min(Math.max(high, 0), 100)}%`;

        },
        50
    );


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
    // MOSTRAR COLMENA EN CONSOLA
    // ------------------------------------------------------------

    console.log(
        "🐝 Resultado asociado a:",
        currentHive
    );


    // ------------------------------------------------------------
    // MOSTRAR TARJETA
    // ------------------------------------------------------------

    resultCard.classList.remove(
        "hidden"
    );


    // ------------------------------------------------------------
    // DESPLAZAR HACIA RESULTADO
    // ------------------------------------------------------------

    setTimeout(
        () => {

            resultCard.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        },
        100
    );
}


// ============================================================================
// GUARDAR ANÁLISIS
// ============================================================================

function saveAnalysis(data, hiveOverride = null) {

    try {

        // --------------------------------------------------------
        // OBTENER HISTORIAL EXISTENTE
        // --------------------------------------------------------

        let history = [];


        const stored =
            localStorage.getItem(
                STORAGE_KEY
            );


        if (stored) {

            try {

                const parsed =
                    JSON.parse(stored);


                if (
                    Array.isArray(parsed)
                ) {

                    history =
                        parsed;
                }

            }

            catch (parseError) {

                console.warn(
                    "El historial existente no pudo ser leído. Se creará uno nuevo."
                );

                history = [];
            }
        }


        // --------------------------------------------------------
        // DATOS DEL RESULTADO
        // --------------------------------------------------------

        const level =
            data.varroa_level ||
            "";


        const confidence =
            Number(
                data.confidence_percentage || 0
            );


        const total =
            Number(
                data.segments?.total || 0
            );


        const lowCount =
            Number(
                data.segments?.LOW || 0
            );


        const highCount =
            Number(
                data.segments?.HIGH || 0
            );


        // --------------------------------------------------------
        // REGISTRO
        // --------------------------------------------------------

        const analysis = {

            id:
                `${Date.now()}-${Math.random()
                    .toString(36)
                    .substring(2, 9)}`,

            timestamp:
                new Date().toISOString(),

            filename:
                data.filename ||
                "audio.webm",

            hive:
                currentHive ||
                "SIN-COLMENA",

            result:
                level,

            confidence:
                confidence,

            totalSegments:
                total,

            lowSegments:
                lowCount,

            highSegments:
                highCount,

            diagnosis:
                data.diagnosis ||
                "",

            samplingRate:
                data.audio_specs?.sampling_rate ||
                "",

            segmentDuration:
                data.audio_specs?.segment_duration ||
                "",

            window:
                data.audio_specs?.window ||
                "",

            mfccCoefficients:
                data.audio_specs?.mfcc_coefficients ||
                0,

            probabilities: {

                LOW:
                    Number(
                        data.probabilities?.LOW || 0
                    ),

                HIGH:
                    Number(
                        data.probabilities?.HIGH || 0
                    )
            }
        };


        // --------------------------------------------------------
        // AGREGAR AL INICIO
        // --------------------------------------------------------

        history.unshift(
            analysis
        );


        // --------------------------------------------------------
        // LIMITAR HISTORIAL
        // --------------------------------------------------------

        if (
            history.length > 500
        ) {

            history =
                history.slice(
                    0,
                    500
                );
        }


        // --------------------------------------------------------
        // GUARDAR
        // --------------------------------------------------------

        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify(history)
        );


        console.log(
            "💾 Historial actualizado:",
            analysis
        );

    }

    catch (error) {

        console.error(
            "❌ No fue posible guardar el análisis:",
            error
        );
    }
}


// ============================================================================
// FUNCIÓN AUXILIAR: OBTENER HISTORIAL
// ============================================================================

function getAnalysisHistory() {

    try {

        const stored =
            localStorage.getItem(
                STORAGE_KEY
            );


        if (!stored) {

            return [];
        }


        const history =
            JSON.parse(
                stored
            );


        return Array.isArray(history)
            ? history
            : [];

    }

    catch (error) {

        console.error(
            "❌ Error leyendo historial:",
            error
        );

        return [];
    }
}


// ============================================================================
// INFORMACIÓN DE DEPURACIÓN
// ============================================================================

console.log(
    "🐝 Bee Health Detector inicializado"
);

console.log(
    "🌐 API:",
    API_URL
);

console.log(
    "💾 Historial:",
    STORAGE_KEY
);

// ============================================================================
// ANÁLISIS MASIVO DE AUDIOS
// ============================================================================

console.log("📁 Inicializando módulo de análisis masivo...");

const bulkAudioInput = document.getElementById("bulkAudioInput");
const selectBulkBtn = document.getElementById("selectBulkBtn");
const analyzeBulkBtn = document.getElementById("analyzeBulkBtn");
const clearBulkBtn = document.getElementById("clearBulkBtn");
const bulkSelectedCount = document.getElementById("bulkSelectedCount");
const bulkProgressWrap = document.getElementById("bulkProgressWrap");
const bulkProgressText = document.getElementById("bulkProgressText");
const bulkProgressPercent = document.getElementById("bulkProgressPercent");
const bulkProgressBar = document.getElementById("bulkProgressBar");
const bulkCurrentFile = document.getElementById("bulkCurrentFile");
const bulkFileList = document.getElementById("bulkFileList");

const MAX_BULK_FILES = 50;
let bulkFiles = [];

function getHiveFromFilename(filename) {
    if (!filename) return null;
    const match = filename.match(/HIVE[-_\s]?(\d{3,6})/i);
    if (!match) return null;
    return normalizeHiveCode(`HIVE-${match[1]}`);
}

function getBulkHive(filename) {
    const filenameHive = getHiveFromFilename(filename);
    if (filenameHive) return filenameHive;
    return getSelectedHive();
}

function updateBulkControls() {
    const count = bulkFiles.length;

    if (bulkSelectedCount) {
        bulkSelectedCount.textContent =
            `${count} archivo${count === 1 ? "" : "s"} seleccionado${count === 1 ? "" : "s"}`;
    }

    if (analyzeBulkBtn) analyzeBulkBtn.disabled = count === 0;
    if (clearBulkBtn) clearBulkBtn.disabled = count === 0;
}

function renderBulkFileList() {
    if (!bulkFileList) return;

    bulkFileList.innerHTML = "";

    if (bulkFiles.length === 0) {
        bulkFileList.classList.remove("active");
        return;
    }

    bulkFileList.classList.add("active");

    bulkFiles.forEach((file, index) => {
        const row = document.createElement("div");
        row.className = "bulk-file-row";

        const name = document.createElement("span");
        name.className = "bulk-file-name";
        name.title = file.name;
        name.textContent = `${index + 1}. ${file.name}`;

        const status = document.createElement("span");
        status.className = "bulk-file-status pending";
        status.id = `bulk-status-${index}`;
        status.textContent = "Pendiente";

        row.appendChild(name);
        row.appendChild(status);
        bulkFileList.appendChild(row);
    });
}

function updateBulkFileStatus(index, status, text) {
    const element = document.getElementById(`bulk-status-${index}`);
    if (!element) return;

    element.className = `bulk-file-status ${status}`;
    element.textContent = text;
}

if (selectBulkBtn && bulkAudioInput) {
    selectBulkBtn.addEventListener("click", () => {
        bulkAudioInput.click();
    });

    bulkAudioInput.addEventListener("change", () => {
        const selected = Array.from(bulkAudioInput.files || []);

        if (selected.length === 0) return;

        if (selected.length > MAX_BULK_FILES) {
            alert(
                `Puedes seleccionar máximo ${MAX_BULK_FILES} audios por lote.\n\n` +
                `Se conservarán los primeros ${MAX_BULK_FILES}.`
            );
        }

        bulkFiles = selected.slice(0, MAX_BULK_FILES);

        renderBulkFileList();
        updateBulkControls();

        console.log("📁 Audios seleccionados:", bulkFiles.length);
    });
}

if (clearBulkBtn) {
    clearBulkBtn.addEventListener("click", () => {
        bulkFiles = [];

        if (bulkAudioInput) bulkAudioInput.value = "";
        if (bulkProgressWrap) bulkProgressWrap.classList.remove("active");
        if (bulkProgressBar) bulkProgressBar.style.width = "0%";
        if (bulkProgressPercent) bulkProgressPercent.textContent = "0%";
        if (bulkProgressText) bulkProgressText.textContent = "Preparando...";
        if (bulkCurrentFile) bulkCurrentFile.textContent = "—";

        renderBulkFileList();
        updateBulkControls();

        console.log("🧹 Selección masiva limpiada.");
    });
}

async function analyzeBulkFile(file) {
    const formData = new FormData();
    formData.append("file", file, file.name);

    const response = await fetch(API_URL, {
        method: "POST",
        body: formData
    });

    let data;

    try {
        data = await response.json();
    } catch (error) {
        throw new Error("El servidor devolvió una respuesta no válida.");
    }

    if (!response.ok) {
        throw new Error(data.detail || `Error HTTP ${response.status}`);
    }

    return data;
}

if (analyzeBulkBtn) {
    analyzeBulkBtn.addEventListener("click", async () => {
        if (!bulkFiles || bulkFiles.length === 0) {
            alert("Selecciona al menos un archivo de audio.");
            return;
        }

        const filesToProcess = [...bulkFiles];
        let successful = 0;
        let failed = 0;

        analyzeBulkBtn.disabled = true;
        if (selectBulkBtn) selectBulkBtn.disabled = true;
        if (clearBulkBtn) clearBulkBtn.disabled = true;
        if (recordBtn) recordBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = true;

        if (bulkProgressWrap) bulkProgressWrap.classList.add("active");
        if (bulkProgressBar) bulkProgressBar.style.width = "0%";
        if (bulkProgressPercent) bulkProgressPercent.textContent = "0%";
        if (bulkProgressText) {
            bulkProgressText.textContent =
                `Preparando ${filesToProcess.length} audios...`;
        }

        console.log(
            `🚀 Iniciando análisis masivo de ${filesToProcess.length} audios.`
        );

        for (let i = 0; i < filesToProcess.length; i++) {
            const file = filesToProcess[i];
            const percentage = Math.round((i / filesToProcess.length) * 100);

            if (bulkProgressBar) bulkProgressBar.style.width = `${percentage}%`;
            if (bulkProgressPercent) bulkProgressPercent.textContent = `${percentage}%`;
            if (bulkProgressText) {
                bulkProgressText.textContent =
                    `Procesando ${i + 1} de ${filesToProcess.length}`;
            }
            if (bulkCurrentFile) bulkCurrentFile.textContent = file.name;

            updateBulkFileStatus(i, "processing", "Procesando...");

            const hive = getBulkHive(file.name);

            if (!hive) {
                failed++;
                updateBulkFileStatus(i, "error", "Sin colmena");
                console.warn("⚠️ No se pudo identificar la colmena:", file.name);
                continue;
            }

            try {
                console.log(
                    `📤 [${i + 1}/${filesToProcess.length}]`,
                    file.name,
                    "→",
                    hive
                );

                const data = await analyzeBulkFile(file);
                saveAnalysis(data, hive);
                successful++;

                const result = String(data.varroa_level || "").toUpperCase();
                const confidence = Number(data.confidence_percentage || 0);

                updateBulkFileStatus(
                    i,
                    "success",
                    `${result || "OK"} · ${confidence.toFixed(1)}%`
                );

                console.log(
                    `✅ [${i + 1}/${filesToProcess.length}]`,
                    file.name,
                    data
                );
            } catch (error) {
                failed++;
                updateBulkFileStatus(i, "error", "Error");
                console.error(
                    `❌ [${i + 1}/${filesToProcess.length}]`,
                    file.name,
                    error
                );
            }
        }

        if (bulkProgressBar) bulkProgressBar.style.width = "100%";
        if (bulkProgressPercent) bulkProgressPercent.textContent = "100%";
        if (bulkProgressText) {
            bulkProgressText.textContent = "Análisis masivo completado";
        }
        if (bulkCurrentFile) {
            bulkCurrentFile.textContent =
                `${successful} procesados correctamente · ${failed} con error`;
        }

        console.log("🏁 Análisis masivo terminado:", {
            total: filesToProcess.length,
            successful: successful,
            failed: failed
        });

        alert(
            "Análisis masivo completado.\n\n" +
            `Audios seleccionados: ${filesToProcess.length}\n` +
            `Procesados correctamente: ${successful}\n` +
            `Con error: ${failed}\n\n` +
            "Los resultados exitosos fueron guardados en el historial."
        );

        analyzeBulkBtn.disabled = false;
        if (selectBulkBtn) selectBulkBtn.disabled = false;
        if (clearBulkBtn) clearBulkBtn.disabled = false;
        if (recordBtn) updateRecordingAvailability();
    });
}

updateBulkControls();

console.log("📁 Módulo de análisis masivo disponible.");
console.log("📁 Límite máximo de archivos:", MAX_BULK_FILES);
