// Gráficas de la dimensión relacional y multivariada (Integrante 4)
(() => {
  const elementoDatos = document.getElementById("multivariada-chart-data");
  const datos = elementoDatos ? JSON.parse(elementoDatos.textContent) : null;
  if (!datos || !window.Chart) return;

  Chart.defaults.color = "#b9bfd8";
  Chart.defaults.font.family = '"Space Grotesk", sans-serif';

  const rejilla = { color: "rgba(255, 255, 255, 0.08)" };
  const numero = (v) => Number(v).toLocaleString("es-CO");

  // Mismos colores que la dimensión territorial
  const colores = {
    "Arma de fuego": "rgba(91, 140, 255, 0.85)",
    "Arma cortopunzante": "#19f28c",
    "Contundente": "#a78bfa",
    "Asfixia": "#ff6b8b",
    "Explosivo": "#fbbf24",
    "Otro / por determinar": "#4b5563",
    "Otros mecanismos": "#4b5563",
    "Hombre": "rgba(91, 140, 255, 0.85)",
    "Mujer": "#19f28c"
  };

  // 1. Mecanismo según sexo y escenario (barras apiladas al 100 %)
  const g1 = datos.sexo_escenario;
  const lienzo1 = document.getElementById("grafica-sexo-escenario");
  if (lienzo1) {
    new Chart(lienzo1, {
      type: "bar",
      data: {
        labels: g1.etiquetas,
        datasets: g1.series.map((s) => ({ label: s.nombre, data: s.valores, backgroundColor: colores[s.nombre] }))
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 12 } },
          tooltip: {
            callbacks: {
              label: (c) => ` ${c.dataset.label}: ${numero(c.parsed.x)} %`,
              footer: (items) => `Víctimas en el grupo: ${numero(g1.totales[items[0].dataIndex])}`
            }
          }
        },
        scales: {
          x: { stacked: true, max: 100, grid: rejilla, ticks: { callback: (v) => `${v} %` } },
          y: { stacked: true, grid: { display: false }, ticks: { autoSkip: false } }
        }
      }
    });
  }

  // 2. % asesinado en la vivienda por ciclo vital y sexo (barras agrupadas)
  const g2 = datos.ciclo_vivienda;
  const lienzo2 = document.getElementById("grafica-ciclo-vivienda");
  if (lienzo2) {
    new Chart(lienzo2, {
      type: "bar",
      data: {
        labels: g2.etiquetas,
        datasets: g2.series.map((s) => ({
          label: s.nombre,
          data: s.valores,
          backgroundColor: colores[s.nombre],
          borderRadius: 5,
          maxBarThickness: 34
        }))
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 12 } },
          tooltip: {
            callbacks: {
              label: (c) => ` ${c.dataset.label}: ${numero(c.parsed.y)} % en la vivienda`,
              afterLabel: (c) => ` Víctimas del grupo: ${numero(g2.series[c.datasetIndex].casos[c.dataIndex])}`
            }
          }
        },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, max: 100, grid: rejilla, ticks: { callback: (v) => `${v} %` } }
        }
      }
    });
  }

  // 3. Víctimas por día de la semana y mecanismo (barras apiladas)
  const g3 = datos.dias;
  const lienzo3 = document.getElementById("grafica-dias");
  if (lienzo3) {
    new Chart(lienzo3, {
      type: "bar",
      data: {
        labels: g3.etiquetas,
        datasets: g3.series.map((s) => ({ label: s.nombre, data: s.valores, backgroundColor: colores[s.nombre] }))
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 12 } },
          tooltip: {
            callbacks: {
              label: (c) => ` ${c.dataset.label}: ${numero(c.parsed.y)} víctimas`,
              footer: (items) => `Cortopunzante: ${numero(g3.pct_corto[items[0].dataIndex])} % del día`
            }
          }
        },
        scales: {
          x: { stacked: true, grid: { display: false } },
          y: { stacked: true, beginAtZero: true, grid: rejilla, ticks: { precision: 0 } }
        }
      }
    });
  }
})();
