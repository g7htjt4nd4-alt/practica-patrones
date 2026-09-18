// Fase 3 — Checklist de las 5 estrategias.
(function () {
  'use strict';

  const S = window.PatronesShared;
  const STORAGE_KEY = 'practica-patrones-fase3-progreso';
  const DATA_URL = 'data/patterns_fase3.json';

  const ETIQUETAS = {
    VV11: 'VV11 (gap + ruptura de canal)',
    SMA_hora: 'S.M.A. — Temporalidad de 1 hora',
    SMA_dia: 'S.M.A. — Temporalidad de Día',
    V10_roja: 'V10 Roja (reversión en canal bajista)',
    Falso_Gap: 'Falso Gap',
    ninguna: 'Ninguna estrategia aplica todavía',
  };

  const statsEl = document.getElementById('f3-stats');
  const btnReset = document.getElementById('f3-btn-reset');
  const contextoEl = document.getElementById('f3-contexto');
  const velaEl = document.getElementById('f3-vela');
  const volumenEl = document.getElementById('f3-volumen');
  const volumenActualEl = document.getElementById('f3-volumen-actual');
  const volumenUmbralEl = document.getElementById('f3-volumen-umbral');
  const volumenTextoEl = document.getElementById('f3-volumen-texto');
  const opcionesEl = document.getElementById('f3-opciones');
  const resultadoEl = document.getElementById('f3-resultado');
  const resultadoTextoEl = document.getElementById('f3-resultado-texto');
  const explicacionEl = document.getElementById('f3-explicacion');
  const btnSiguiente = document.getElementById('f3-btn-siguiente');
  const btnVerReferencia = document.getElementById('f3-btn-ver-referencia');

  const mazo = S.crearMazo();
  let ejemplos = [];
  let actual = null;
  let progreso = S.cargarProgreso(STORAGE_KEY);
  let inicializado = false;

  function renderStats() {
    statsEl.textContent = `Aciertos: ${progreso.aciertos} / ${progreso.intentos}`;
  }

  function siguienteEjemplo() {
    const idx = mazo.siguienteIndice(ejemplos.length);
    actual = ejemplos[idx];
    // Mismo resguardo que en Fase 1/2: un fallo al dibujar no debe impedir
    // que las opciones se actualicen a la pregunta nueva.
    try {
      dibujarEjemplo(actual);
    } catch (e) {
      console.error('Error dibujando el ejemplo (se continúa igual):', e);
    }
    renderOpciones(actual);
    resultadoEl.hidden = true;
  }

  // Dibuja contexto + vela gatillo + volumen sobre un juego de elementos
  // del DOM (reutilizado tal cual por Fase 4 - modo velocidad).
  function dibujarEnElementos(el, ejemplo) {
    if (el.contextoEl) el.contextoEl.textContent = ejemplo.contexto;
    S.dibujarVelaSVG(el.velaEl, ejemplo.vela_gatillo);

    if (ejemplo.volumen) {
      const { actual_pct_avg, umbral_pct_avg } = ejemplo.volumen;
      const maxRef = Math.max(actual_pct_avg, umbral_pct_avg) * 1.2;
      el.volumenActualEl.style.width = `${(actual_pct_avg / maxRef) * 100}%`;
      el.volumenUmbralEl.style.width = `${(umbral_pct_avg / maxRef) * 100}%`;
      el.volumenTextoEl.textContent = `Volumen: ${actual_pct_avg}% del promedio (umbral: ${umbral_pct_avg}%)`;
      el.volumenEl.hidden = false;
    } else {
      el.volumenEl.hidden = true;
    }
  }

  function dibujarEjemplo(ejemplo) {
    dibujarEnElementos(
      { contextoEl, velaEl, volumenEl, volumenActualEl, volumenUmbralEl, volumenTextoEl },
      ejemplo
    );
  }

  function renderOpciones(ejemplo) {
    opcionesEl.innerHTML = '';
    ejemplo.opciones.forEach((opcion) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn btn-opcion';
      btn.textContent = ETIQUETAS[opcion] || opcion;
      btn.dataset.opcion = opcion;
      btn.addEventListener('click', () => elegirOpcion(opcion));
      opcionesEl.appendChild(btn);
    });
  }

  function elegirOpcion(opcionElegida) {
    const correcta = actual.patron_correcto;
    const esCorrecto = opcionElegida === correcta;

    Array.from(opcionesEl.children).forEach((btn) => {
      btn.disabled = true;
      if (btn.dataset.opcion === correcta) {
        btn.classList.add('correcta');
      } else if (btn.dataset.opcion === opcionElegida) {
        btn.classList.add('incorrecta');
      }
    });

    S.registrarIntento(progreso, correcta, esCorrecto);
    S.guardarProgreso(STORAGE_KEY, progreso);
    renderStats();

    resultadoTextoEl.textContent = esCorrecto ? '¡Correcto!' : `Incorrecto. Era: ${ETIQUETAS[correcta] || correcta}`;
    resultadoTextoEl.className = `resultado-texto ${esCorrecto ? 'correcta' : 'incorrecta'}`;
    explicacionEl.textContent = actual.explicacion;
    resultadoEl.hidden = false;
  }

  btnSiguiente.addEventListener('click', siguienteEjemplo);

  btnVerReferencia.addEventListener('click', () => {
    window.Glosario.mostrarModalFicha(actual.patron_correcto);
  });

  btnReset.addEventListener('click', () => {
    const confirmado = window.confirm('¿Reiniciar el progreso guardado de Fase 3? Esta acción no se puede deshacer.');
    if (!confirmado) return;
    localStorage.removeItem(STORAGE_KEY);
    progreso = { aciertos: 0, intentos: 0, porPatron: {} };
    renderStats();
  });

  function activar() {
    if (!inicializado) {
      inicializado = true;
      renderStats();
      fetch(DATA_URL)
        .then((res) => res.json())
        .then((data) => {
          ejemplos = data;
          siguienteEjemplo();
        })
        .catch((err) => {
          contextoEl.textContent = 'No se pudieron cargar los datos de Fase 3.';
          console.error('Error cargando patterns_fase3.json:', err);
        });
    }
  }

  window.Fase3 = {
    activar,
    ETIQUETAS,
    dibujarEnElementos,
    obtenerEjemplos: () => ejemplos,
  };
})();
