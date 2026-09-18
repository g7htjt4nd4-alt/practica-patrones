(function () {
  'use strict';

  const S = window.PatronesShared;
  const STORAGE_KEY = 'practica-patrones-progreso';
  const DATA_URL = 'data/patterns_fase1.json';

  const ETIQUETAS = {
    martillo: 'Martillo',
    gancho: 'Gancho',
    marubozu: 'Marubozu',
    doji: 'Doji',
    envolvente_alcista: 'Envolvente alcista',
    envolvente_bajista: 'Envolvente bajista',
    ninguno: 'Ninguno',
  };

  const statsEl = document.getElementById('stats-aciertos');
  const btnReset = document.getElementById('btn-reset');
  const chartContainer = document.getElementById('chart');
  const opcionesEl = document.getElementById('opciones');
  const resultadoEl = document.getElementById('resultado');
  const resultadoTextoEl = document.getElementById('resultado-texto');
  const explicacionEl = document.getElementById('explicacion');
  const btnSiguiente = document.getElementById('btn-siguiente');
  const btnVerReferencia = document.getElementById('btn-ver-referencia');

  const mazo = S.crearMazo();
  let ejemplos = [];
  let actual = null;
  let progreso = S.cargarProgreso(STORAGE_KEY);

  const grafico = S.crearGraficoVelas(chartContainer);
  const chart = grafico.chart;
  const serie = grafico.serie;

  function renderStats() {
    statsEl.textContent = `Aciertos: ${progreso.aciertos} / ${progreso.intentos}`;
  }

  function siguienteEjemplo() {
    const idx = mazo.siguienteIndice(ejemplos.length);
    actual = ejemplos[idx];
    // Si el gráfico falla al dibujar (ej. una excepción intermitente de
    // lightweight-charts), igual debe avanzar la pregunta: que un problema
    // visual no deje la pantalla congelada en el ejemplo anterior.
    try {
      dibujarEjemplo(actual);
    } catch (e) {
      console.error('Error dibujando el gráfico (se continúa igual):', e);
    }
    renderOpciones(actual);
    resultadoEl.hidden = true;
  }

  function dibujarEnGrafico(graficoDestino, ejemplo) {
    const datos = S.velasATiempo(ejemplo.velas);

    const idxObjetivo = ejemplo.vela_objetivo_idx;
    datos[idxObjetivo] = {
      ...datos[idxObjetivo],
      borderColor: S.COLOR_DESTACADO,
    };

    graficoDestino.serie.setData(datos);
    graficoDestino.serie.setMarkers([
      {
        time: datos[idxObjetivo].time,
        position: 'aboveBar',
        color: S.COLOR_DESTACADO,
        shape: 'arrowDown',
        text: 'Vela a identificar',
      },
    ]);
    graficoDestino.chart.timeScale().fitContent();
  }

  function dibujarEjemplo(ejemplo) {
    dibujarEnGrafico(grafico, ejemplo);
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
    window.Glosario.mostrarModal(actual.patron_correcto);
  });

  btnReset.addEventListener('click', () => {
    const confirmado = window.confirm('¿Reiniciar todo el progreso guardado? Esta acción no se puede deshacer.');
    if (!confirmado) return;
    localStorage.removeItem(STORAGE_KEY);
    progreso = { aciertos: 0, intentos: 0, porPatron: {} };
    renderStats();
  });

  fetch(DATA_URL)
    .then((res) => res.json())
    .then((data) => {
      ejemplos = data;
      renderStats();
      siguienteEjemplo();
    })
    .catch((err) => {
      chartContainer.textContent = 'No se pudieron cargar los datos. Revisa que estés usando un servidor local (ver README).';
      console.error('Error cargando patterns_fase1.json:', err);
    });

  window.Fase1 = {
    ETIQUETAS,
    dibujarEnGrafico,
    obtenerEjemplos: () => ejemplos,
    activar: () => {
      grafico.ajustarTamano();
      chart.timeScale().fitContent();
    },
  };
})();
