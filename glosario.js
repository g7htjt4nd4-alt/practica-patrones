// Glosario visual de referencia: pestaña con 3 secciones (Velas, Canales,
// Estrategias) + modales reutilizados desde Fase 1/2 (imagen) y Fase 3
// (ficha de texto) para mostrar la referencia del patrón correcto.
(function () {
  'use strict';

  const URL_VELAS = 'data/glosario/glosario_fase1.json';
  const URL_CANALES = 'data/glosario_fase2/glosario_fase2.json';
  const URL_ESTRATEGIAS = 'data/glosario_fase3.json';

  const listaVelasEl = document.getElementById('glosario-lista');
  const listaCanalesEl = document.getElementById('glosario-lista-canales');
  const listaEstrategiasEl = document.getElementById('glosario-lista-estrategias');

  const modalEl = document.getElementById('modal-referencia');
  const modalImagenEl = document.getElementById('modal-imagen');
  const modalTituloEl = document.getElementById('modal-titulo');
  const modalDefinicionEl = document.getElementById('modal-definicion');
  const modalCerrarEl = document.getElementById('modal-cerrar');

  const modalFichaEl = document.getElementById('modal-ficha');
  const modalFichaContenidoEl = document.getElementById('modal-ficha-contenido');
  const modalFichaCerrarEl = document.getElementById('modal-ficha-cerrar');

  const subtabBotones = document.querySelectorAll('.subtab-btn');
  const subtabPaneles = {
    velas: document.getElementById('glosario-velas'),
    canales: document.getElementById('glosario-canales'),
    estrategias: document.getElementById('glosario-estrategias'),
  };

  let porPatronVelas = {};
  let porPatronCanales = {};
  let porPatronEstrategias = {};

  function renderListaImagenes(contenedor, entradas, carpeta, patronesSinLinea) {
    contenedor.innerHTML = '';
    entradas.forEach((entrada) => {
      const card = document.createElement('div');
      card.className = 'glosario-card';
      const badge =
        patronesSinLinea && patronesSinLinea.has(entrada.patron)
          ? '<span class="glosario-card-badge">Sin línea (intencional)</span>'
          : '';
      card.innerHTML = `
        <img src="${carpeta}/${entrada.archivo}" alt="${entrada.titulo}" loading="lazy" />
        <h3>${entrada.titulo}</h3>
        ${badge}
        <p>${entrada.definicion}</p>
      `;
      contenedor.appendChild(card);
    });
  }

  const PATRONES_CANAL_SIN_LINEA = new Set(['canal_invalido', 'ninguno']);

  function claseDireccion(direccion) {
    if (direccion.includes('CALL')) return 'ficha-direccion-call';
    if (direccion.includes('PUT')) return 'ficha-direccion-put';
    return 'ficha-direccion-neutral';
  }

  // Marcado de una ficha de estrategia: se usa tanto en el grid del
  // Glosario como dentro del modal de "Ver referencia" de Fase 3.
  function renderFichaHTML(ficha) {
    return `
      <h3>${ficha.titulo}</h3>
      <span class="ficha-direccion ${claseDireccion(ficha.direccion)}">${ficha.direccion}</span>
      <p class="ficha-campo"><strong>Temporalidad:</strong> ${ficha.temporalidad}</p>
      <ul class="ficha-checklist">
        ${ficha.checklist.map((item) => `<li>${item}</li>`).join('')}
      </ul>
      <p class="ficha-campo"><strong>Señal de ruptura:</strong> ${ficha.senal_ruptura}</p>
      <p class="ficha-definicion">${ficha.definicion}</p>
    `;
  }

  function renderListaFichas(contenedor, fichas) {
    contenedor.innerHTML = '';
    fichas.forEach((ficha) => {
      const card = document.createElement('div');
      card.className = 'ficha-card';
      card.innerHTML = renderFichaHTML(ficha);
      contenedor.appendChild(card);
    });
  }

  fetch(URL_VELAS)
    .then((res) => res.json())
    .then((entradas) => {
      porPatronVelas = Object.fromEntries(entradas.map((e) => [e.patron, e]));
      renderListaImagenes(listaVelasEl, entradas, 'data/glosario');
    })
    .catch((err) => {
      listaVelasEl.textContent = 'No se pudo cargar el glosario de Velas.';
      console.error('Error cargando glosario_fase1.json:', err);
    });

  fetch(URL_CANALES)
    .then((res) => res.json())
    .then((entradas) => {
      porPatronCanales = Object.fromEntries(entradas.map((e) => [e.patron, e]));
      renderListaImagenes(listaCanalesEl, entradas, 'data/glosario_fase2', PATRONES_CANAL_SIN_LINEA);
    })
    .catch((err) => {
      listaCanalesEl.textContent = 'No se pudo cargar el glosario de Canales.';
      console.error('Error cargando glosario_fase2.json:', err);
    });

  fetch(URL_ESTRATEGIAS)
    .then((res) => res.json())
    .then((data) => {
      const fichas = data.fichas || [];
      porPatronEstrategias = Object.fromEntries(fichas.map((f) => [f.patron, f]));
      renderListaFichas(listaEstrategiasEl, fichas);
    })
    .catch((err) => {
      listaEstrategiasEl.textContent = 'No se pudo cargar el glosario de Estrategias.';
      console.error('Error cargando glosario_fase3.json:', err);
    });

  function mostrarModalImagen(entrada, carpeta) {
    if (!entrada) return;
    modalImagenEl.src = `${carpeta}/${entrada.archivo}`;
    modalImagenEl.alt = entrada.titulo;
    modalTituloEl.textContent = entrada.titulo;
    modalDefinicionEl.textContent = entrada.definicion;
    modalEl.hidden = false;
  }

  function mostrarModal(patron) {
    mostrarModalImagen(porPatronVelas[patron], 'data/glosario');
  }

  function mostrarModalCanal(patron) {
    mostrarModalImagen(porPatronCanales[patron], 'data/glosario_fase2');
  }

  function mostrarModalFicha(patron) {
    const ficha = porPatronEstrategias[patron];
    if (!ficha) return;
    modalFichaContenidoEl.innerHTML = renderFichaHTML(ficha);
    modalFichaEl.hidden = false;
  }

  function ocultarModal() {
    modalEl.hidden = true;
  }

  function ocultarModalFicha() {
    modalFichaEl.hidden = true;
  }

  modalCerrarEl.addEventListener('click', ocultarModal);
  modalEl.addEventListener('click', (evento) => {
    if (evento.target === modalEl) ocultarModal();
  });

  modalFichaCerrarEl.addEventListener('click', ocultarModalFicha);
  modalFichaEl.addEventListener('click', (evento) => {
    if (evento.target === modalFichaEl) ocultarModalFicha();
  });

  document.addEventListener('keydown', (evento) => {
    if (evento.key !== 'Escape') return;
    if (!modalEl.hidden) ocultarModal();
    if (!modalFichaEl.hidden) ocultarModalFicha();
  });

  function mostrarSubtab(nombre) {
    Object.entries(subtabPaneles).forEach(([clave, panel]) => {
      panel.hidden = clave !== nombre;
    });
    subtabBotones.forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.subtab === nombre);
    });
  }

  subtabBotones.forEach((btn) => {
    btn.addEventListener('click', () => mostrarSubtab(btn.dataset.subtab));
  });

  function activar() {
    /* Las listas se llenan solas en cuanto terminan los fetch; no hay quiz que iniciar. */
  }

  window.Glosario = {
    activar,
    mostrarModal,
    mostrarModalCanal,
    mostrarModalFicha,
    ocultarModal,
    ocultarModalFicha,
  };
})();
