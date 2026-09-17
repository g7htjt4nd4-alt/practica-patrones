// Fase 4 — Modo velocidad: mezcla ejemplos de las Fases 1-3 contra reloj.
(function () {
  'use strict';

  const S = window.PatronesShared;
  const HISTORIAL_KEY = 'practica-patrones-fase4-historial';

  // Constantes fáciles de ajustar.
  const TIEMPO_POR_PREGUNTA_MS = 12000;
  const PREGUNTAS_POR_RONDA = 15;
  const PAUSA_TRAS_RESPONDER_MS = 1500;
  const MIN_INTENTOS_PARA_DEBIL = 3;

  const progresoEl = document.getElementById('f4-progreso-ronda');
  const inicioEl = document.getElementById('f4-inicio');
  const btnEmpezar = document.getElementById('f4-btn-empezar');
  const juegoEl = document.getElementById('f4-juego');
  const cronometroBarraEl = document.getElementById('f4-cronometro-barra');
  const cronometroTextoEl = document.getElementById('f4-cronometro-texto');
  const chartContainer = document.getElementById('f4-chart');
  const fase3AreaEl = document.getElementById('f4-fase3-area');
  const contextoEl = document.getElementById('f4-contexto');
  const velaEl = document.getElementById('f4-vela');
  const volumenEl = document.getElementById('f4-volumen');
  const volumenActualEl = document.getElementById('f4-volumen-actual');
  const volumenUmbralEl = document.getElementById('f4-volumen-umbral');
  const volumenTextoEl = document.getElementById('f4-volumen-texto');
  const opcionesEl = document.getElementById('f4-opciones');
  const resultadoEl = document.getElementById('f4-resultado');
  const resultadoTextoEl = document.getElementById('f4-resultado-texto');
  const explicacionEl = document.getElementById('f4-explicacion');
  const resumenEl = document.getElementById('f4-resumen');
  const resumenAciertosEl = document.getElementById('f4-resumen-aciertos');
  const resumenPromedioEl = document.getElementById('f4-resumen-promedio');
  const resumenDebilEl = document.getElementById('f4-resumen-debil');
  const btnOtraRonda = document.getElementById('f4-btn-otra-ronda');

  let inicializado = false;
  let grafico = null;
  let lineaSerieActual = null;
  let pool = [];

  let rondaActiva = [];
  let indiceActual = 0;
  let aciertosRonda = 0;
  let tiemposRespuesta = [];
  let respondida = false;
  let timerInterval = null;
  let inicioPreguntaTs = 0;
  let avanceTimeoutId = null;

  function etiquetasDe(item) {
    if (item.fase === 1) return window.Fase1.ETIQUETAS;
    if (item.fase === 2) return window.Fase2.ETIQUETAS;
    return window.Fase3.ETIQUETAS;
  }

  function renderPreguntaVisual(item) {
    if (item.fase === 3) {
      chartContainer.hidden = true;
      fase3AreaEl.hidden = false;
      if (lineaSerieActual) {
        grafico.chart.removeSeries(lineaSerieActual);
        lineaSerieActual = null;
      }
      window.Fase3.dibujarEnElementos(
        { contextoEl, velaEl, volumenEl, volumenActualEl, volumenUmbralEl, volumenTextoEl },
        item.datos
      );
      return;
    }

    chartContainer.hidden = false;
    fase3AreaEl.hidden = true;

    if (item.fase === 2) {
      lineaSerieActual = window.Fase2.dibujarEnGrafico(grafico, item.datos, lineaSerieActual);
    } else {
      if (lineaSerieActual) {
        grafico.chart.removeSeries(lineaSerieActual);
        lineaSerieActual = null;
      }
      window.Fase1.dibujarEnGrafico(grafico, item.datos);
    }
  }

  function renderOpciones(item) {
    opcionesEl.innerHTML = '';
    const etiquetas = etiquetasDe(item);
    item.datos.opciones.forEach((opcion) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn btn-opcion';
      btn.textContent = etiquetas[opcion] || opcion;
      btn.dataset.opcion = opcion;
      btn.addEventListener('click', () => responder(opcion));
      opcionesEl.appendChild(btn);
    });
  }

  function actualizarProgreso() {
    progresoEl.textContent = `Pregunta ${indiceActual + 1} / ${rondaActiva.length} · Aciertos: ${aciertosRonda}`;
  }

  function iniciarCronometro() {
    inicioPreguntaTs = performance.now();
    clearInterval(timerInterval);
    actualizarCronometro();
    timerInterval = setInterval(actualizarCronometro, 100);
  }

  function detenerCronometro() {
    clearInterval(timerInterval);
    timerInterval = null;
  }

  function actualizarCronometro() {
    const transcurrido = performance.now() - inicioPreguntaTs;
    const restante = Math.max(0, TIEMPO_POR_PREGUNTA_MS - transcurrido);
    const pct = (restante / TIEMPO_POR_PREGUNTA_MS) * 100;
    cronometroBarraEl.style.width = `${pct}%`;
    cronometroBarraEl.classList.toggle('urgente', restante < TIEMPO_POR_PREGUNTA_MS * 0.25);
    cronometroTextoEl.textContent = `${Math.ceil(restante / 1000)}s`;
    if (restante <= 0) {
      detenerCronometro();
      manejarTimeout();
    }
  }

  function mostrarPregunta() {
    respondida = false;
    resultadoEl.hidden = true;
    actualizarProgreso();
    const item = rondaActiva[indiceActual];
    renderPreguntaVisual(item);
    renderOpciones(item);
    iniciarCronometro();
  }

  function responder(opcionElegida) {
    if (respondida) return;
    respondida = true;
    detenerCronometro();
    const tiempo = Math.min(performance.now() - inicioPreguntaTs, TIEMPO_POR_PREGUNTA_MS);
    tiemposRespuesta.push(tiempo);
    evaluarYMostrar(opcionElegida, false);
  }

  function manejarTimeout() {
    if (respondida) return;
    respondida = true;
    tiemposRespuesta.push(TIEMPO_POR_PREGUNTA_MS);
    evaluarYMostrar(null, true);
  }

  function evaluarYMostrar(opcionElegida, fueTimeout) {
    const item = rondaActiva[indiceActual];
    const correcta = item.datos.patron_correcto;
    const esCorrecto = !fueTimeout && opcionElegida === correcta;
    if (esCorrecto) aciertosRonda += 1;

    const etiquetas = etiquetasDe(item);
    Array.from(opcionesEl.children).forEach((btn) => {
      btn.disabled = true;
      if (btn.dataset.opcion === correcta) {
        btn.classList.add('correcta');
      } else if (btn.dataset.opcion === opcionElegida) {
        btn.classList.add('incorrecta');
      }
    });

    resultadoTextoEl.textContent = fueTimeout
      ? `Se acabó el tiempo. Era: ${etiquetas[correcta] || correcta}`
      : esCorrecto
      ? '¡Correcto!'
      : `Incorrecto. Era: ${etiquetas[correcta] || correcta}`;
    resultadoTextoEl.className = `resultado-texto ${esCorrecto ? 'correcta' : 'incorrecta'}`;
    explicacionEl.textContent = item.datos.explicacion;
    resultadoEl.hidden = false;
    actualizarProgreso();

    avanceTimeoutId = setTimeout(avanzar, PAUSA_TRAS_RESPONDER_MS);
  }

  function avanzar() {
    indiceActual += 1;
    if (indiceActual >= rondaActiva.length) {
      terminarRonda();
    } else {
      mostrarPregunta();
    }
  }

  function categoriaMasDebil() {
    const fuentes = [
      { prefijo: 'Velas', key: 'practica-patrones-progreso', etiquetas: window.Fase1.ETIQUETAS },
      { prefijo: 'Canales', key: 'practica-patrones-fase2-progreso', etiquetas: window.Fase2.ETIQUETAS },
      { prefijo: 'Estrategias', key: 'practica-patrones-fase3-progreso', etiquetas: window.Fase3.ETIQUETAS },
    ];

    const candidatos = [];
    fuentes.forEach((fuente) => {
      const progreso = S.cargarProgreso(fuente.key);
      Object.entries(progreso.porPatron || {}).forEach(([patron, datos]) => {
        if (datos.intentos > 0) {
          candidatos.push({
            etiqueta: `${fuente.prefijo}: ${fuente.etiquetas[patron] || patron}`,
            ratio: datos.aciertos / datos.intentos,
            intentos: datos.intentos,
          });
        }
      });
    });

    if (candidatos.length === 0) return null;

    const conSuficientes = candidatos.filter((c) => c.intentos >= MIN_INTENTOS_PARA_DEBIL);
    const pool = conSuficientes.length > 0 ? conSuficientes : candidatos;
    pool.sort((a, b) => a.ratio - b.ratio || b.intentos - a.intentos);
    return pool[0];
  }

  function terminarRonda() {
    detenerCronometro();
    juegoEl.hidden = true;
    resumenEl.hidden = false;

    const promedioMs = tiemposRespuesta.reduce((a, b) => a + b, 0) / tiemposRespuesta.length;

    let historial;
    try {
      historial = JSON.parse(localStorage.getItem(HISTORIAL_KEY)) || { rondas: [] };
    } catch (e) {
      historial = { rondas: [] };
    }
    historial.rondas.push({
      fecha: new Date().toISOString(),
      aciertos: aciertosRonda,
      total: rondaActiva.length,
      promedioMs: Math.round(promedioMs),
    });
    localStorage.setItem(HISTORIAL_KEY, JSON.stringify(historial));

    const debil = categoriaMasDebil();
    resumenAciertosEl.textContent = `Aciertos: ${aciertosRonda} / ${rondaActiva.length}`;
    resumenPromedioEl.textContent = `Tiempo promedio de respuesta: ${(promedioMs / 1000).toFixed(1)}s`;
    resumenDebilEl.textContent = debil
      ? `Categoría más débil: ${debil.etiqueta} (${Math.round(debil.ratio * 100)}% de aciertos en ${debil.intentos} intentos)`
      : 'Categoría más débil: todavía no hay suficientes datos de las otras fases.';
  }

  function iniciarRonda() {
    clearTimeout(avanceTimeoutId);
    rondaActiva = S.barajar(pool).slice(0, PREGUNTAS_POR_RONDA);
    indiceActual = 0;
    aciertosRonda = 0;
    tiemposRespuesta = [];

    inicioEl.hidden = true;
    resumenEl.hidden = true;
    juegoEl.hidden = false;

    grafico.ajustarTamano();
    mostrarPregunta();
  }

  btnEmpezar.addEventListener('click', iniciarRonda);
  btnOtraRonda.addEventListener('click', iniciarRonda);

  function activar() {
    if (!inicializado) {
      inicializado = true;
      grafico = S.crearGraficoVelas(chartContainer);

      Promise.all([
        fetch('data/patterns_fase1.json').then((r) => r.json()),
        fetch('data/patterns_fase2.json').then((r) => r.json()),
        fetch('data/patterns_fase3.json').then((r) => r.json()),
      ])
        .then(([d1, d2, d3]) => {
          pool = [
            ...d1.map((datos) => ({ fase: 1, datos })),
            ...d2.map((datos) => ({ fase: 2, datos })),
            ...d3.map((datos) => ({ fase: 3, datos })),
          ];
          btnEmpezar.disabled = false;
          btnEmpezar.textContent = 'Empezar ronda';
        })
        .catch((err) => {
          btnEmpezar.textContent = 'Error al cargar datos';
          console.error('Error cargando datos de Velocidad:', err);
        });
      return;
    }

    grafico.ajustarTamano();
    if (!juegoEl.hidden) {
      grafico.chart.timeScale().fitContent();
    }
  }

  window.Fase4 = { activar };
})();
