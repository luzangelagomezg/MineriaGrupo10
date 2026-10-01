// Gráficas de la dimensión territorial (Integrante 2)
(() => {
  const elementoDatos = document.getElementById("territorial-chart-data");
  const datos = elementoDatos ? JSON.parse(elementoDatos.textContent) : null;
  if (!datos || !window.Chart) return;

  Chart.defaults.color = "#b9bfd8";
  Chart.defaults.font.family = '"Space Grotesk", sans-serif';

  const rejilla = { color: "rgba(255, 255, 255, 0.08)" };
  const azul = "rgba(91, 140, 255, 0.8)";
  const verde = "#19f28c";

  // Barras horizontales: departamentos y municipios
  const crearBarras = (id, serie, colores) => {
    const lienzo = document.getElementById(id);
    if (!lienzo) return;
    new Chart(lienzo, {
      type: "bar",
      data: {
        labels: serie.etiquetas,
        datasets: [{ data: serie.valores, backgroundColor: colores, borderRadius: 5, maxBarThickness: 26 }]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (c) => ` ${c.parsed.x.toLocaleString("es-CO")} víctimas` } }
        },
        scales: {
          x: { beginAtZero: true, grid: rejilla, ticks: { precision: 0 } },
          y: { grid: { display: false }, ticks: { autoSkip: false } }
        }
      }
    });
  };

  // 1. Departamentos: el primero (o el elegido en el filtro) se resalta en verde
  const deptos = datos.departamentos;
  crearBarras(
    "grafica-departamentos",
    deptos,
    deptos.etiquetas.map((d, i) =>
      (deptos.seleccionado !== "Todos" ? d === deptos.seleccionado : i === 0) ? verde : azul
    )
  );

  // 2. Municipios: el primero se resalta en verde
  crearBarras(
    "grafica-municipios",
    datos.municipios,
    datos.municipios.valores.map((_, i) => (i === 0 ? verde : azul))
  );

  // 3. Zona del hecho por departamento (barras apiladas al 100 %)
  const colores = {
    "Parte rural": verde,
    "Centro poblado": "#a78bfa",
    "Cabecera municipal": azul,
    "Sin información": "#4b5563"
  };
  const zonas = document.getElementById("grafica-zonas");
  if (zonas) {
    new Chart(zonas, {
      type: "bar",
      data: {
        labels: datos.zonas.etiquetas,
        datasets: datos.zonas.series.map((s) => ({
          label: s.nombre,
          data: s.valores,
          backgroundColor: colores[s.nombre]
        }))
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 12 } },
          tooltip: { callbacks: { label: (c) => ` ${c.dataset.label}: ${c.parsed.x.toLocaleString("es-CO")} %` } }
        },
        scales: {
          x: { stacked: true, max: 100, grid: rejilla, ticks: { callback: (v) => `${v} %` } },
          y: { stacked: true, grid: { display: false }, ticks: { autoSkip: false, font: { size: 11 } } }
        }
      }
    });
  }
})();
