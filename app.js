(function () {
  'use strict';

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

  let mazo = [];
  let ejemplos = [];
  let actual = null;
  let progreso = cargarProgreso();

  const chart = LightweightCharts.createChart(chartContainer, {
    layout: {
      background: { color: '#161c2c' },
      textColor: '#b8bfd1',
    },
    grid: {
      vertLines: { color: '#1f2740' },
      horzLines: { color: '#1f2740' },
    },
    rightPriceScale: { borderColor: '#2d3650' },
    timeScale: { borderColor: '#2d3650' },
  });

  const serie = chart.addCandlestickSeries({
    upColor: '#2f9e5f',
    downColor: '#e5534b',
    borderUpColor: '#2f9e5f',
    borderDownColor: '#e5534b',
    wickUpColor: '#2f9e5f',
    wickDownColor: '#e5534b',
  });

  function ajustarTamano() {
    chart.applyOptions({ width: chartContainer.clientWidth, height: chartContainer.clientHeight });
  }
  window.addEventListener('resize', ajustarTamano);
  ajustarTamano();

  function cargarProgreso() {
    try {
      const guardado = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (guardado && typeof guardado.aciertos === 'number') {
        return guardado;
      }
    } catch (e) {
      /* localStorage vacío o corrupto: se ignora y se parte de cero */
    }
    return { aciertos: 0, intentos: 0, porPatron: {} };
  }

  function guardarProgreso() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progreso));
  }

  function renderStats() {
    statsEl.textContent = `Aciertos: ${progreso.aciertos} / ${progreso.intentos}`;
  }

  function barajar(arr) {
    const copia = arr.slice();
    for (let i = copia.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copia[i], copia[j]] = [copia[j], copia[i]];
    }
    return copia;
  }

  function siguienteEjemplo() {
    if (mazo.length === 0) {
      mazo = barajar(ejemplos.map((_, idx) => idx));
    }
    const idx = mazo.pop();
    actual = ejemplos[idx];
    dibujarEjemplo(actual);
    renderOpciones(actual);
    resultadoEl.hidden = true;
  }

  function dibujarEjemplo(ejemplo) {
    const baseTime = 1700000000;
    const datos = ejemplo.velas.map((vela, i) => ({
      time: baseTime + i * 86400,
      open: vela.o,
      high: vela.h,
      low: vela.l,
      close: vela.c,
    }));

    const idxObjetivo = ejemplo.vela_objetivo_idx;
    datos[idxObjetivo] = {
      ...datos[idxObjetivo],
      borderColor: '#f5c542',
    };

    serie.setData(datos);
    serie.setMarkers([
      {
        time: datos[idxObjetivo].time,
        position: 'aboveBar',
        color: '#f5c542',
        shape: 'arrowDown',
        text: 'Vela a identificar',
      },
    ]);
    chart.timeScale().fitContent();
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

    registrarIntento(correcta, esCorrecto);

    resultadoTextoEl.textContent = esCorrecto ? '¡Correcto!' : `Incorrecto. Era: ${ETIQUETAS[correcta] || correcta}`;
    resultadoTextoEl.className = `resultado-texto ${esCorrecto ? 'correcta' : 'incorrecta'}`;
    explicacionEl.textContent = actual.explicacion;
    resultadoEl.hidden = false;
  }

  function registrarIntento(patron, esCorrecto) {
    progreso.intentos += 1;
    if (esCorrecto) progreso.aciertos += 1;

    if (!progreso.porPatron[patron]) {
      progreso.porPatron[patron] = { aciertos: 0, intentos: 0 };
    }
    progreso.porPatron[patron].intentos += 1;
    if (esCorrecto) progreso.porPatron[patron].aciertos += 1;

    guardarProgreso();
    renderStats();
  }

  btnSiguiente.addEventListener('click', siguienteEjemplo);

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
})();
