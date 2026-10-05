// Gráficas de la dimensión temporal (Integrante 3)
(() => {
  const elementoDatos = document.getElementById("temporal-chart-data");
  const datos = elementoDatos ? JSON.parse(elementoDatos.textContent) : null;
  if (!datos || !window.Chart) return;

  Chart.defaults.color = "#b9bfd8";
  Chart.defaults.font.family = '"Space Grotesk", sans-serif';

  const rejilla = { color: "rgba(255, 255, 255, 0.08)" };
  const tooltip = {
    callbacks: {
      label: (context) => ` ${context.parsed.y.toLocaleString("es-CO")} víctimas`
    }
  };

  // 1. Evolución anual (línea)
  const anual = document.getElementById("grafica-anual");
  if (anual) {
    new Chart(anual, {
      type: "line",
      data: {
        labels: datos.anual.etiquetas,
        datasets: [{
          data: datos.anual.valores,
          borderColor: "#19f28c",
          backgroundColor: "rgba(25, 242, 140, 0.15)",
          pointBackgroundColor: "#19f28c",
          pointRadius: 4,
          tension: 0.25,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, grid: rejilla, ticks: { precision: 0 } }
        }
      }
    });
  }

  // 2 y 3. Barras por mes y por día de la semana
  const crearBarras = (id, serie, color) => {
    const lienzo = document.getElementById(id);
    if (!lienzo) return;
    const maximo = Math.max(...serie.valores);
    new Chart(lienzo, {
      type: "bar",
      data: {
        labels: serie.etiquetas,
        datasets: [{
          data: serie.valores,
          // La barra más alta se resalta en verde
          backgroundColor: serie.valores.map((v) => (v === maximo ? "#19f28c" : color)),
          borderRadius: 5,
          maxBarThickness: 42
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip },
        scales: {
          x: { grid: { display: false }, ticks: { maxRotation: 45, minRotation: 0 } },
          y: { beginAtZero: true, grid: rejilla, ticks: { precision: 0 } }
        }
      }
    });
  };

  crearBarras("grafica-mensual", datos.mensual, "rgba(91, 140, 255, 0.8)");
  crearBarras("grafica-semanal", datos.semanal, "rgba(91, 140, 255, 0.8)");
})();
