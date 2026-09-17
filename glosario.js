// Glosario visual de referencia: pestaña propia + modal reutilizado
// desde Fase 1 para mostrar la imagen del patrón correcto.
(function () {
  'use strict';

  const DATA_URL = 'data/glosario/glosario_fase1.json';

  const listaEl = document.getElementById('glosario-lista');
  const modalEl = document.getElementById('modal-referencia');
  const modalImagenEl = document.getElementById('modal-imagen');
  const modalTituloEl = document.getElementById('modal-titulo');
  const modalDefinicionEl = document.getElementById('modal-definicion');
  const modalCerrarEl = document.getElementById('modal-cerrar');

  let porPatron = {};

  function renderLista(entradas) {
    listaEl.innerHTML = '';
    entradas.forEach((entrada) => {
      const card = document.createElement('div');
      card.className = 'glosario-card';
      card.innerHTML = `
        <img src="data/glosario/${entrada.archivo}" alt="${entrada.titulo}" loading="lazy" />
        <h3>${entrada.titulo}</h3>
        <p>${entrada.definicion}</p>
      `;
      listaEl.appendChild(card);
    });
  }

  fetch(DATA_URL)
    .then((res) => res.json())
    .then((entradas) => {
      porPatron = Object.fromEntries(entradas.map((e) => [e.patron, e]));
      renderLista(entradas);
    })
    .catch((err) => {
      listaEl.textContent = 'No se pudo cargar el glosario.';
      console.error('Error cargando glosario_fase1.json:', err);
    });

  function mostrarModal(patron) {
    const entrada = porPatron[patron];
    if (!entrada) return;
    modalImagenEl.src = `data/glosario/${entrada.archivo}`;
    modalImagenEl.alt = entrada.titulo;
    modalTituloEl.textContent = entrada.titulo;
    modalDefinicionEl.textContent = entrada.definicion;
    modalEl.hidden = false;
  }

  function ocultarModal() {
    modalEl.hidden = true;
  }

  modalCerrarEl.addEventListener('click', ocultarModal);
  modalEl.addEventListener('click', (evento) => {
    if (evento.target === modalEl) ocultarModal();
  });
  document.addEventListener('keydown', (evento) => {
    if (evento.key === 'Escape' && !modalEl.hidden) ocultarModal();
  });

  function activar() {
    /* La lista se llena sola en cuanto termina el fetch; no hay quiz que iniciar. */
  }

  window.Glosario = { activar, mostrarModal, ocultarModal };
})();
