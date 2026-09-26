// Interacciones comunes a todas las páginas
document.addEventListener("DOMContentLoaded", () => {
  const navbar = document.querySelector(".navbar-grupo");
  const btnSubir = document.querySelector(".btn-subir");

  // Barra de navegación compacta y botón "subir" al hacer scroll
  const alDesplazar = () => {
    const bajo = window.scrollY > 40;
    navbar?.classList.toggle("con-scroll", bajo);
    btnSubir?.classList.toggle("visible", window.scrollY > 400);
  };
  window.addEventListener("scroll", alDesplazar, { passive: true });
  alDesplazar();

  btnSubir?.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

  // Elementos con clase .aparecer se animan al entrar en pantalla
  const observador = new IntersectionObserver((entradas) => {
    entradas.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add("visible");
        observador.unobserve(e.target);
      }
    });
  }, { threshold: 0.15 });
  document.querySelectorAll(".aparecer").forEach((el) => observador.observe(el));

  // Brillo de las tarjetas siguiendo el cursor
  document.querySelectorAll(".tarjeta").forEach((t) => {
    t.addEventListener("mousemove", (ev) => {
      const r = t.getBoundingClientRect();
      t.style.setProperty("--mx", `${ev.clientX - r.left}px`);
      t.style.setProperty("--my", `${ev.clientY - r.top}px`);
    });
  });

  // Contadores animados: <span data-contar="125284">0</span>
  const formato = new Intl.NumberFormat("es-CO");
  const contar = (el) => {
    const fin = Number(el.dataset.contar);
    const inicio = performance.now();
    const duracion = 1600;
    const paso = (ahora) => {
      const p = Math.min((ahora - inicio) / duracion, 1);
      el.textContent = formato.format(Math.round(fin * (1 - Math.pow(1 - p, 3))));
      if (p < 1) requestAnimationFrame(paso);
    };
    requestAnimationFrame(paso);
  };
  const observadorCifras = new IntersectionObserver((entradas) => {
    entradas.forEach((e) => {
      if (e.isIntersecting) {
        contar(e.target);
        observadorCifras.unobserve(e.target);
      }
    });
  }, { threshold: 0.6 });
  document.querySelectorAll("[data-contar]").forEach((el) => observadorCifras.observe(el));
});
