(() => {
  const elementoDatos = document.getElementById("poblacional-chart-data");
  const datos = elementoDatos ? JSON.parse(elementoDatos.textContent) : null;
  if (!datos || !window.Chart) return;

  Chart.defaults.color = "#b9bfd8";
  Chart.defaults.font.family = '"Space Grotesk", sans-serif';

  const crearGrafica = (id, serie, color, horizontal = false) => {
    const lienzo = document.getElementById(id);
    if (!lienzo) return;

    new Chart(lienzo, {
      type: "bar",
      data: {
        labels: serie.etiquetas,
        datasets: [{
          data: serie.valores,
          backgroundColor: color,
          borderColor: color,
          borderWidth: 1,
          borderRadius: 5,
          maxBarThickness: horizontal ? 18 : 42
        }]
      },
      options: {
        indexAxis: horizontal ? "y" : "x",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => {
                const index = context.dataIndex;
                const cantidad = serie.cantidades_texto[index];
                const porcentaje = serie.porcentajes_texto[index];
                return ` ${cantidad} víctimas (${porcentaje} %)`;
              }
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            grid: { color: "rgba(255, 255, 255, 0.08)" },
            ticks: { color: "#b9bfd8", precision: 0 }
          },
          y: {
            beginAtZero: true,
            grid: { display: horizontal, color: "rgba(255, 255, 255, 0.08)" },
            ticks: {
              color: "#b9bfd8",
              autoSkip: !horizontal,
              maxRotation: horizontal ? 0 : 45,
              minRotation: 0
            }
          }
        }
      }
    });
  };

  crearGrafica("grafica-sexo", datos.sexo, ["#19f28c", "#5b8cff", "#b9bfd8"]);
  crearGrafica("grafica-edad", datos.edad, "rgba(25, 242, 140, 0.75)", true);
  crearGrafica("grafica-ciclo-vital", datos.ciclo_vital, "rgba(91, 140, 255, 0.8)", true);
})();