/* ============================================================
   BEE HEALTH DETECTOR - DASHBOARD
   Fuente de datos: localStorage del navegador
   ============================================================ */

const STORAGE_KEY = "beeHealthAnalysisHistory";

let allAnalyses = [];

/* ------------------------------------------------------------
   UTILIDADES
   ------------------------------------------------------------ */

function getHistory() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);

        if (!raw) {
            return [];
        }

        const data = JSON.parse(raw);

        if (!Array.isArray(data)) {
            return [];
        }

        return data
            .filter(item => item && typeof item === "object")
            .sort(
                (a, b) =>
                    new Date(b.timestamp || 0) -
                    new Date(a.timestamp || 0)
            );

    } catch (error) {
        console.error(
            "❌ No fue posible leer el historial:",
            error
        );

        return [];
    }
}


/* ------------------------------------------------------------
   FORMATO DE DATOS
   ------------------------------------------------------------ */

function number(value, fallback = 0) {

    const n = Number(value);

    return Number.isFinite(n)
        ? n
        : fallback;
}


function formatInteger(value) {

    return number(value).toLocaleString("es-CO");
}


function formatPercent(value, decimals = 1) {

    return `${number(value).toLocaleString("es-CO", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    })}%`;
}


function formatDate(timestamp) {

    if (!timestamp) {
        return "—";
    }

    const date = new Date(timestamp);

    if (Number.isNaN(date.getTime())) {
        return "—";
    }

    return date.toLocaleString("es-CO", {

        day: "2-digit",
        month: "2-digit",
        year: "numeric",

        hour: "2-digit",
        minute: "2-digit"

    });
}


function escapeHtml(value) {

    return String(value ?? "")

        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function getResult(item) {

    const result =
        String(item.result || "").toUpperCase();

    return result === "HIGH"
        ? "HIGH"
        : "LOW";
}


/* ------------------------------------------------------------
   KPIs
   ------------------------------------------------------------ */

function updateKPIs(data) {

    const total = data.length;

    const high =
        data.filter(
            item => getResult(item) === "HIGH"
        ).length;

    const low =
        data.filter(
            item => getResult(item) === "LOW"
        ).length;


    const confidenceValues = data

        .map(
            item =>
                number(
                    item.confidence,
                    NaN
                )
        )

        .filter(
            value =>
                Number.isFinite(value)
        );


    const avgConfidence =
        confidenceValues.length

            ? confidenceValues.reduce(
                (sum, value) =>
                    sum + value,
                0
            ) / confidenceValues.length

            : 0;


    const totalSegments =
        data.reduce(

            (sum, item) =>
                sum +
                number(
                    item.totalSegments
                ),

            0
        );


    const highPercent =
        total
            ? (high / total) * 100
            : 0;


    const lowPercent =
        total
            ? (low / total) * 100
            : 0;


    const totalAudios =
        document.getElementById(
            "totalAudios"
        );

    const totalHigh =
        document.getElementById(
            "totalHigh"
        );

    const totalLow =
        document.getElementById(
            "totalLow"
        );

    const avgConfidenceElement =
        document.getElementById(
            "avgConfidence"
        );

    const totalSegmentsElement =
        document.getElementById(
            "totalSegments"
        );


    if (totalAudios) {

        totalAudios.textContent =
            formatInteger(total);
    }


    if (totalHigh) {

        totalHigh.textContent =
            formatInteger(high);
    }


    if (totalLow) {

        totalLow.textContent =
            formatInteger(low);
    }


    if (avgConfidenceElement) {

        avgConfidenceElement.textContent =
            formatPercent(
                avgConfidence
            );
    }


    if (totalSegmentsElement) {

        totalSegmentsElement.textContent =
            formatInteger(
                totalSegments
            );
    }


    /* Porcentaje HIGH */

    const highCard =
        document
            .getElementById("totalHigh")
            ?.closest(".kpi-card");


    const lowCard =
        document
            .getElementById("totalLow")
            ?.closest(".kpi-card");


    const highSmall =
        highCard?.querySelector(
            "small"
        );


    const lowSmall =
        lowCard?.querySelector(
            "small"
        );


    if (highSmall) {

        highSmall.textContent =
            `${formatPercent(
                highPercent
            )} del total`;
    }


    if (lowSmall) {

        lowSmall.textContent =
            `${formatPercent(
                lowPercent
            )} del total`;
    }
}


/* ------------------------------------------------------------
   GRÁFICO DONUT
   ------------------------------------------------------------ */

function updateDonut(data) {

    const total =
        data.length;


    const high =
        data.filter(
            item =>
                getResult(item) === "HIGH"
        ).length;


    const low =
        data.filter(
            item =>
                getResult(item) === "LOW"
        ).length;


    const highPercent =
        total
            ? (high / total) * 100
            : 0;


    const donut =
        document.querySelector(
            ".donut-chart"
        );


    if (donut) {

        donut.style.background =
            total

                ? `conic-gradient(
                    var(--red, #ef4444)
                    0% ${highPercent}%,

                    var(--green, #22c55e)
                    ${highPercent}% 100%
                  )`

                : "conic-gradient(#e5e7eb 0% 100%)";
    }


    const centerStrong =
        document.querySelector(
            ".donut-center strong"
        );


    const centerSpan =
        document.querySelector(
            ".donut-center span"
        );


    if (centerStrong) {

        centerStrong.textContent =
            formatInteger(total);
    }


    if (centerSpan) {

        centerSpan.textContent =
            "análisis";
    }


    const legendItems =
        document.querySelectorAll(
            ".legend-item"
        );


    if (legendItems.length >= 2) {

        legendItems[0]
            .querySelector("strong")
            .textContent =
                formatInteger(high);


        legendItems[0]
            .querySelector("small")
            .textContent =
                formatPercent(
                    highPercent
                );


        legendItems[1]
            .querySelector("strong")
            .textContent =
                formatInteger(low);


        legendItems[1]
            .querySelector("small")
            .textContent =
                formatPercent(
                    total
                        ? (low / total) * 100
                        : 0
                );
    }
}


/* ------------------------------------------------------------
   EVOLUCIÓN DE ANÁLISIS
   ------------------------------------------------------------ */

function updateEvolution(data) {

    const chart =
        document.querySelector(
            ".bar-chart"
        );


    if (!chart) {
        return;
    }


    chart.innerHTML = "";


    if (!data.length) {

        chart.innerHTML = `

            <div style="
                width:100%;
                min-height:120px;
                display:flex;
                align-items:center;
                justify-content:center;
                opacity:.65;
                font-size:.9rem;
            ">

                No hay análisis registrados todavía.

            </div>

        `;

        return;
    }


    const byDate = {};


    data.forEach(item => {

        const date =
            new Date(
                item.timestamp || 0
            );


        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return;
        }


        const key =
            date.toLocaleDateString(
                "es-CO",
                {
                    day: "2-digit",
                    month: "2-digit"
                }
            );


        byDate[key] =
            (byDate[key] || 0) + 1;
    });


    const entries =
        Object.entries(byDate)
            .slice(-8);


    const max =
        Math.max(
            ...entries.map(
                ([, value]) =>
                    value
            ),
            1
        );


    entries.forEach(
        ([label, count]) => {

            const height =
                Math.max(
                    (count / max) * 100,
                    4
                );


            const group =
                document.createElement(
                    "div"
                );


            group.className =
                "bar-group";


            group.innerHTML = `

                <div
                    class="bar"
                    style="height:${height}%"
                    title="${count} análisis"
                ></div>

                <span>
                    ${escapeHtml(label)}
                </span>

            `;


            chart.appendChild(
                group
            );
        }
    );
}


/* ------------------------------------------------------------
   RESULTADOS POR COLMENA
   ------------------------------------------------------------ */

function updateHives(data) {

    const container =
        document.querySelector(
            ".hive-list"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (!data.length) {

        container.innerHTML = `

            <div style="
                padding:20px;
                opacity:.65;
            ">

                No hay datos de colmenas todavía.

            </div>

        `;

        return;
    }


    const hives = {};


    data.forEach(item => {

        const hive =
            item.hive ||
            "SIN COLMENA";


        if (!hives[hive]) {

            hives[hive] = {

                total: 0,
                high: 0

            };
        }


        hives[hive].total++;


        if (
            getResult(item) === "HIGH"
        ) {

            hives[hive].high++;
        }
    });


    const entries =
        Object.entries(hives)

            .sort(
                (a, b) =>
                    b[1].total -
                    a[1].total
            )

            .slice(0, 8);


    entries.forEach(
        ([hive, stats]) => {

            const highPercent =
                stats.total

                    ? (
                        stats.high /
                        stats.total
                    ) * 100

                    : 0;


            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "hive-row";


            row.innerHTML = `

                <div>

                    <strong>
                        ${escapeHtml(hive)}
                    </strong>

                    <small>
                        ${formatInteger(
                            stats.total
                        )}
                        análisis
                    </small>

                </div>


                <div class="hive-bar">

                    <span
                        style="width:${highPercent}%"
                    ></span>

                </div>


                <strong>
                    ${formatPercent(
                        highPercent,
                        0
                    )}
                </strong>

            `;


            container.appendChild(
                row
            );
        }
    );
}


/* ------------------------------------------------------------
   PROCESAMIENTO ACÚSTICO
   ------------------------------------------------------------ */

function updateProcessing(data) {

    const miniStats =
        document.querySelectorAll(
            ".processing-grid .mini-stat"
        );


    if (
        miniStats.length < 4
    ) {
        return;
    }


    const totalSegments =
        data.reduce(

            (sum, item) =>
                sum +
                number(
                    item.totalSegments
                ),

            0
        );


    const lowSegments =
        data.reduce(

            (sum, item) =>
                sum +
                number(
                    item.lowSegments
                ),

            0
        );


    const highSegments =
        data.reduce(

            (sum, item) =>
                sum +
                number(
                    item.highSegments
                ),

            0
        );


    const avgSegments =
        data.length

            ? totalSegments /
              data.length

            : 0;


    miniStats[0]
        .querySelector("strong")
        .textContent =
            formatInteger(
                totalSegments
            );


    miniStats[1]
        .querySelector("strong")
        .textContent =
            formatInteger(
                lowSegments
            );


    miniStats[2]
        .querySelector("strong")
        .textContent =
            formatInteger(
                highSegments
            );


    miniStats[3]
        .querySelector("strong")
        .textContent =
            formatInteger(
                Math.round(
                    avgSegments
                )
            );
}


/* ------------------------------------------------------------
   GRÁFICO DE CONFIANZA
   ------------------------------------------------------------ */

function updateConfidenceChart(data) {

    const pointsContainer =
        document.querySelector(
            ".confidence-points"
        );


    const confidenceValue =
        document.querySelector(
            ".confidence-value"
        );


    if (!pointsContainer) {
        return;
    }


    pointsContainer.innerHTML = "";


    const values =
        data
            .slice()
            .reverse()

            .map(
                item =>
                    number(
                        item.confidence,
                        NaN
                    )
            )

            .filter(
                value =>
                    Number.isFinite(value)
            )

            .slice(-8);


    values.forEach(
        value => {

            const point =
                document.createElement(
                    "span"
                );


            point.style.bottom =
                `${Math.max(
                    5,
                    Math.min(
                        95,
                        value
                    )
                )}%`;


            point.title =
                formatPercent(
                    value
                );


            pointsContainer.appendChild(
                point
            );
        }
    );


    const allConfidence =
        data

            .map(
                item =>
                    number(
                        item.confidence,
                        NaN
                    )
            )

            .filter(
                value =>
                    Number.isFinite(value)
            );


    const globalAvg =
        allConfidence.length

            ? allConfidence.reduce(
                (sum, value) =>
                    sum + value,
                0
            ) /
              allConfidence.length

            : 0;


    if (confidenceValue) {

        confidenceValue.textContent =
            formatPercent(
                globalAvg
            );


        confidenceValue.title =
            values.length

                ? `Últimos ${values.length} análisis`

                : "Sin datos";
    }
}


/* ------------------------------------------------------------
   HISTORIAL
   ------------------------------------------------------------ */

function renderHistory(data) {

    const tbody =
        document.getElementById(
            "historyTable"
        );


    if (!tbody) {
        return;
    }


    tbody.innerHTML = "";


    if (!data.length) {

        const row =
            document.createElement(
                "tr"
            );


        row.innerHTML = `

            <td
                colspan="8"
                style="
                    text-align:center;
                    padding:30px;
                    opacity:.65;
                "
            >

                No hay análisis registrados
                en este navegador.

            </td>

        `;


        tbody.appendChild(
            row
        );


        return;
    }


    data.forEach(item => {

        const result =
            getResult(item);


        const confidence =
            number(
                item.confidence
            );


        const totalSegments =
            number(
                item.totalSegments
            );


        const lowSegments =
            number(
                item.lowSegments
            );


        const highSegments =
            number(
                item.highSegments
            );


        const row =
            document.createElement(
                "tr"
            );


        row.innerHTML = `

            <td>

                ${escapeHtml(
                    formatDate(
                        item.timestamp
                    )
                )}

            </td>


            <td
                title="${escapeHtml(
                    item.filename || ""
                )}"
            >

                ${escapeHtml(
                    item.filename ||
                    "audio"
                )}

            </td>


            <td>

                ${escapeHtml(
                    item.hive ||
                    "—"
                )}

            </td>


            <td>

                ${formatInteger(
                    totalSegments
                )}

            </td>


            <td>

                ${formatInteger(
                    lowSegments
                )}

            </td>


            <td>

                ${formatInteger(
                    highSegments
                )}

            </td>


            <td>

                <span
                    class="result-badge ${result.toLowerCase()}"
                >

                    ${result}

                </span>

            </td>


            <td>

                ${formatPercent(
                    confidence
                )}

            </td>

        `;


        tbody.appendChild(
            row
        );
    });
}


/* ------------------------------------------------------------
   FILTROS
   ------------------------------------------------------------ */

function applyFilters() {

    const filter =
        document.getElementById(
            "resultFilter"
        )?.value ||
        "ALL";


    const search =
        (
            document.getElementById(
                "searchInput"
            )?.value ||
            ""
        )
            .trim()
            .toLowerCase();


    const filtered =
        allAnalyses.filter(
            item => {

                const result =
                    getResult(item);


                if (
                    filter !== "ALL" &&
                    result !== filter
                ) {

                    return false;
                }


                if (search) {

                    const filename =
                        String(
                            item.filename ||
                            ""
                        ).toLowerCase();


                    const hive =
                        String(
                            item.hive ||
                            ""
                        ).toLowerCase();


                    const diagnosis =
                        String(
                            item.diagnosis ||
                            ""
                        ).toLowerCase();


                    if (

                        !filename.includes(
                            search
                        )

                        &&

                        !hive.includes(
                            search
                        )

                        &&

                        !diagnosis.includes(
                            search
                        )

                    ) {

                        return false;
                    }
                }


                return true;
            }
        );


    renderHistory(
        filtered
    );
}


/* ------------------------------------------------------------
   ACTUALIZACIÓN COMPLETA
   ------------------------------------------------------------ */

function updateDashboard() {

    allAnalyses =
        getHistory();


    updateKPIs(
        allAnalyses
    );


    updateDonut(
        allAnalyses
    );


    updateEvolution(
        allAnalyses
    );


    updateHives(
        allAnalyses
    );


    updateProcessing(
        allAnalyses
    );


    updateConfidenceChart(
        allAnalyses
    );


    applyFilters();


    console.log(
        `📊 Dashboard actualizado: ${allAnalyses.length} análisis`
    );
}


/* ------------------------------------------------------------
   EVENTOS
   ------------------------------------------------------------ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const resultFilter =
            document.getElementById(
                "resultFilter"
            );


        const searchInput =
            document.getElementById(
                "searchInput"
            );


        if (resultFilter) {

            resultFilter.addEventListener(
                "change",
                applyFilters
            );
        }


        if (searchInput) {

            searchInput.addEventListener(
                "input",
                applyFilters
            );
        }


        updateDashboard();


        /*
         * Si se realiza un análisis
         * desde otra pestaña del mismo
         * origen, el dashboard se
         * actualiza automáticamente.
         */

        window.addEventListener(
            "storage",
            event => {

                if (
                    event.key ===
                    STORAGE_KEY
                ) {

                    updateDashboard();
                }
            }
        );
    }
);


/* ------------------------------------------------------------
   FUNCIONES DISPONIBLES DESDE CONSOLA
   ------------------------------------------------------------ */

window.refreshBeeHealthDashboard =
    updateDashboard;


window.getBeeHealthHistory =
    getHistory;