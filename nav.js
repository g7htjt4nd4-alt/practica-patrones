// Navegación entre las 4 fases: solo muestra/oculta secciones, cada fase
// mantiene su propio estado y progreso en memoria y en localStorage.
(function () {
  'use strict';

  const botones = document.querySelectorAll('.tab-btn');
  const paneles = {
    velas: document.getElementById('tab-velas'),
    canales: document.getElementById('tab-canales'),
    estrategias: document.getElementById('tab-estrategias'),
    velocidad: document.getElementById('tab-velocidad'),
    glosario: document.getElementById('tab-glosario'),
    backtesting: document.getElementById('tab-backtesting'),
  };
  const activadores = {
    velas: () => window.Fase1.activar(),
    canales: () => window.Fase2.activar(),
    estrategias: () => window.Fase3.activar(),
    velocidad: () => window.Fase4.activar(),
    glosario: () => window.Glosario.activar(),
    backtesting: () => window.Backtesting.activar(),
  };

  function mostrarTab(nombre) {
    Object.entries(paneles).forEach(([clave, panel]) => {
      panel.hidden = clave !== nombre;
    });
    botones.forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.tab === nombre);
    });
    activadores[nombre]();
  }

  botones.forEach((btn) => {
    btn.addEventListener('click', () => mostrarTab(btn.dataset.tab));
  });
})();
