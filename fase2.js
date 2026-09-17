// Fase 2 — Canales y rupturas.
(function () {
  'use strict';

  const S = window.PatronesShared;
  const STORAGE_KEY = 'practica-patrones-fase2-progreso';
  const DATA_URL = 'data/patterns_fase2.json';

  const ETIQUETAS = {
    canal_bajista_valido_con_ruptura: 'Canal bajista válido, con ruptura',
    canal_bajista_valido_sin_ruptura: 'Canal bajista válido, sin ruptura',
    canal_alcista_valido_con_ruptura: 'Canal alcista válido, con ruptura',
    canal_alcista_valido_sin_ruptura: 'Canal alcista válido, sin ruptura',
    canal_invalido: 'Canal inválido (solo 1 toque)',
    ninguno: 'Ninguno / rango lateral',
  };

  const statsEl = document.getElementById('f2-stats');
  const btnReset = document.getElementById('f2-btn-reset');
  const chartContainer = document.getElementById('f2-chart');
  const opcionesEl = document.getElementById('f2-opciones');
  const resultadoEl = document.getElementById('f2-resultado');
  const resultadoTextoEl = document.getElementById('f2-resultado-texto');
  const explicacionEl = document.getElementById('f2-explicacion');
  const btnSiguiente = document.getElementById('f2-btn-siguiente');

  let mazo = [];
  let ejemplos = [];
  let actual = null;
  let progreso = S.cargarProgreso(STORAGE_KEY);
  let grafico = null;
  let lineaSerie = null;
  let inicializado = false;

  function renderStats() {
    statsEl.textContent = `Aciertos: ${progreso.aciertos} / ${progreso.intentos}`;
  }

  function siguienteEjemplo() {
    if (mazo.length === 0) {
      mazo = S.barajar(ejemplos.map((_, idx) => idx));
    }
    const idx = mazo.pop();
    actual = ejemplos[idx];
    dibujarEjemplo(actual);
    renderOpciones(actual);
    resultadoEl.hidden = true;
  }

  function calcularLineaExtendida(ejemplo) {
    const { punto_inicio, punto_fin } = ejemplo.linea;
    const nVelas = ejemplo.velas.length;
    const pendiente = (punto_fin.valor - punto_inicio.valor) / (punto_fin.idx - punto_inicio.idx);
    const valorInicio = punto_inicio.valor - pendiente * punto_inicio.idx;
    const valorFinal = valorInicio + pendiente * (nVelas - 1);
    return { valorInicio, valorFinal };
  }

  // Dibuja velas + línea de canal (si aplica) sobre `graficoDestino`.
  // `lineaSerieActual` es la serie de línea previamente creada en ESE
  // gráfico (o null); devuelve la nueva serie de línea (o null) para que
  // el caller la recuerde y la pase de vuelta la próxima vez.
  function dibujarEnGrafico(graficoDestino, ejemplo, lineaSerieActual) {
    const datos = S.velasATiempo(ejemplo.velas);
    graficoDestino.serie.setData(datos);

    if (lineaSerieActual) {
      graficoDestino.chart.removeSeries(lineaSerieActual);
      lineaSerieActual = null;
    }

    if (ejemplo.linea) {
      const { valorInicio, valorFinal } = calcularLineaExtendida(ejemplo);
      lineaSerieActual = graficoDestino.chart.addLineSeries({
        color: S.COLOR_DESTACADO,
        lineWidth: 2,
        crosshairMarkerVisible: false,
        lastValueVisible: false,
        priceLineVisible: false,
      });
      lineaSerieActual.setData([
        { time: datos[0].time, value: valorInicio },
        { time: datos[datos.length - 1].time, value: valorFinal },
      ]);

      const posicionMarcador = ejemplo.linea.tipo === 'alcista' ? 'belowBar' : 'aboveBar';
      graficoDestino.serie.setMarkers(
        ejemplo.indices_toque.map((idx) => ({
          time: datos[idx].time,
          position: posicionMarcador,
          color: S.COLOR_DESTACADO,
          shape: 'circle',
        }))
      );
    } else {
      graficoDestino.serie.setMarkers([]);
    }

    graficoDestino.chart.timeScale().fitContent();
    return lineaSerieActual;
  }

  function dibujarEjemplo(ejemplo) {
    lineaSerie = dibujarEnGrafico(grafico, ejemplo, lineaSerie);
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

  btnReset.addEventListener('click', () => {
    const confirmado = window.confirm('¿Reiniciar el progreso guardado de Fase 2? Esta acción no se puede deshacer.');
    if (!confirmado) return;
    localStorage.removeItem(STORAGE_KEY);
    progreso = { aciertos: 0, intentos: 0, porPatron: {} };
    renderStats();
  });

  function activar() {
    if (!inicializado) {
      inicializado = true;
      grafico = S.crearGraficoVelas(chartContainer);
      renderStats();
      fetch(DATA_URL)
        .then((res) => res.json())
        .then((data) => {
          ejemplos = data;
          siguienteEjemplo();
        })
        .catch((err) => {
          chartContainer.textContent = 'No se pudieron cargar los datos de Fase 2.';
          console.error('Error cargando patterns_fase2.json:', err);
        });
      return;
    }
    grafico.ajustarTamano();
    grafico.chart.timeScale().fitContent();
  }

  window.Fase2 = {
    activar,
    ETIQUETAS,
    dibujarEnGrafico,
    obtenerEjemplos: () => ejemplos,
  };
})();
