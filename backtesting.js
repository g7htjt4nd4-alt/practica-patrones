// Backtesting — probabilidades reales por estrategia + modo de revisión
// interactiva sobre casos históricos reales de SPY/QQQ.
(function () {
  'use strict';

  const S = window.PatronesShared;
  const STORAGE_KEY = 'practica-patrones-backtesting-progreso';
  const URL_STATS = 'data/backtesting/backtest_stats.json';
  const URL_CASOS = 'data/backtesting/backtest_cases.json';

  const ORDEN_ESTRATEGIAS = ['VV11', 'SMA_hora', 'SMA_dia', 'V10_roja', 'Falso_Gap'];
  const MIN_N_PARA_PROBABILIDAD = 5;

  const ETIQUETAS_RESULTADO = {
    gana: 'Ganó',
    pierde: 'Perdió',
    neutral: 'Neutral',
  };

  const statsEl = document.getElementById('bt-stats');
  const btnReset = document.getElementById('bt-btn-reset');
  const probabilidadesEl = document.getElementById('bt-probabilidades');
  const chartContainer = document.getElementById('bt-chart');
  const casoMetaEl = document.getElementById('bt-caso-meta');
  const opcionesEstrategiaEl = document.getElementById('bt-opciones-estrategia');
  const opcionesPrediccionEl = document.getElementById('bt-opciones-prediccion');
  const btnRevelar = document.getElementById('bt-btn-revelar');
  const resultadoEl = document.getElementById('bt-resultado');
  const resultadoTextoEl = document.getElementById('bt-resultado-texto');
  const resultadoDetalleEl = document.getElementById('bt-resultado-detalle');
  const btnSiguiente = document.getElementById('bt-btn-siguiente');

  const mazo = S.crearMazo();
  let stats = null;
  let casos = [];
  let actual = null;
  let grafico = null;
  let inicializado = false;
  let estrategiaElegida = null;
  let prediccionElegida = null;

  let progreso = cargarProgreso();

  function cargarProgreso() {
    try {
      const guardado = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (guardado && typeof guardado.intentos === 'number') return guardado;
    } catch (e) {
      /* localStorage vacío o corrupto: se parte de cero */
    }
    return { intentos: 0, aciertosEstrategia: 0, aciertosPrediccion: 0 };
  }

  function guardarProgreso() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progreso));
  }

  function renderStats() {
    statsEl.textContent = `Estrategia: ${progreso.aciertosEstrategia} / ${progreso.intentos} · Predicción: ${progreso.aciertosPrediccion} / ${progreso.intentos}`;
  }

  function etiquetaEstrategia(clave) {
    return (window.Fase3 && window.Fase3.ETIQUETAS && window.Fase3.ETIQUETAS[clave]) || clave;
  }

  function renderProbabilidades() {
    probabilidadesEl.innerHTML = '';
    ORDEN_ESTRATEGIAS.forEach((clave) => {
      const datos = stats.estrategias[clave];
      const fuente = stats.fuentes && stats.fuentes[clave];
      const fuenteHTML = fuente ? `<p class="bt-prob-fuente">Fuente: ${fuente}</p>` : '';
      const card = document.createElement('div');
      card.className = 'bt-prob-card';

      if (!datos || datos.n === 0) {
        card.innerHTML = `
          <h3>${etiquetaEstrategia(clave)}</h3>
          <p class="bt-prob-aviso">${(datos && datos.aviso) || 'Sin casos detectados en el período.'}</p>
          ${fuenteHTML}
        `;
        probabilidadesEl.appendChild(card);
        return;
      }

      if (datos.n < MIN_N_PARA_PROBABILIDAD) {
        card.innerHTML = `
          <h3>${etiquetaEstrategia(clave)}</h3>
          <p class="bt-prob-n">n = ${datos.n} casos detectados</p>
          <p class="bt-prob-insuficiente">
            Muestra insuficiente para estimar una probabilidad (menos de 5
            casos). Necesita más corridas del backtest acumulándose con el
            tiempo.
          </p>
          ${fuenteHTML}
        `;
        probabilidadesEl.appendChild(card);
        return;
      }

      card.innerHTML = `
        <h3>${etiquetaEstrategia(clave)}</h3>
        <div class="bt-prob-barra">
          <span class="bt-prob-segmento bt-prob-gana" style="width:${datos.pct_gana}%" title="Gana ${datos.pct_gana}%"></span>
          <span class="bt-prob-segmento bt-prob-pierde" style="width:${datos.pct_pierde}%" title="Pierde ${datos.pct_pierde}%"></span>
          <span class="bt-prob-segmento bt-prob-neutral" style="width:${datos.pct_neutral}%" title="Neutral ${datos.pct_neutral}%"></span>
        </div>
        <p class="bt-prob-leyenda">
          <span class="bt-leyenda-gana">Gana ${datos.pct_gana}%</span> ·
          <span class="bt-leyenda-pierde">Pierde ${datos.pct_pierde}%</span> ·
          <span class="bt-leyenda-neutral">Neutral ${datos.pct_neutral}%</span>
        </p>
        <p class="bt-prob-movimiento">Movimiento promedio: ${datos.movimiento_promedio_pct}%</p>
        <p class="bt-prob-confiabilidad">n = ${datos.n} · ${datos.confiabilidad}</p>
        ${fuenteHTML}
      `;
      probabilidadesEl.appendChild(card);
    });
  }

  function siguienteCaso() {
    const idx = mazo.siguienteIndice(casos.length);
    actual = casos[idx];
    estrategiaElegida = null;
    prediccionElegida = null;
    btnRevelar.hidden = false;
    btnRevelar.disabled = true;
    resultadoEl.hidden = true;

    try {
      dibujarCaso(actual);
    } catch (e) {
      console.error('Error dibujando el caso (se continúa igual):', e);
    }

    casoMetaEl.textContent = `${actual.ticker} — ${new Date(actual.fecha).toLocaleString('es', { dateStyle: 'medium', timeStyle: 'short' })}`;

    renderOpcionesEstrategia();
    renderOpcionesPrediccion();
  }

  function dibujarCaso(caso) {
    window.Fase1.dibujarEnGrafico(grafico, {
      velas: caso.velas,
      vela_objetivo_idx: caso.vela_gatillo_idx,
    });
  }

  function renderOpcionesEstrategia() {
    opcionesEstrategiaEl.innerHTML = '';
    ORDEN_ESTRATEGIAS.forEach((clave) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn btn-opcion';
      btn.textContent = etiquetaEstrategia(clave);
      btn.dataset.opcion = clave;
      btn.addEventListener('click', () => {
        estrategiaElegida = clave;
        Array.from(opcionesEstrategiaEl.children).forEach((b) => b.classList.toggle('seleccionada', b === btn));
        actualizarBotonRevelar();
      });
      opcionesEstrategiaEl.appendChild(btn);
    });
  }

  function renderOpcionesPrediccion() {
    opcionesPrediccionEl.innerHTML = '';
    ['gana', 'pierde', 'neutral'].forEach((clave) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn btn-opcion';
      btn.textContent = ETIQUETAS_RESULTADO[clave];
      btn.dataset.opcion = clave;
      btn.addEventListener('click', () => {
        prediccionElegida = clave;
        Array.from(opcionesPrediccionEl.children).forEach((b) => b.classList.toggle('seleccionada', b === btn));
        actualizarBotonRevelar();
      });
      opcionesPrediccionEl.appendChild(btn);
    });
  }

  function actualizarBotonRevelar() {
    btnRevelar.disabled = !(estrategiaElegida && prediccionElegida);
  }

  function revelarResultado() {
    btnRevelar.hidden = true;
    btnRevelar.disabled = true;

    const estrategiaOk = estrategiaElegida === actual.estrategia;
    const prediccionOk = prediccionElegida === actual.resultado;

    Array.from(opcionesEstrategiaEl.children).forEach((btn) => {
      btn.disabled = true;
      btn.classList.remove('seleccionada');
      if (btn.dataset.opcion === actual.estrategia) btn.classList.add('correcta');
      else if (btn.dataset.opcion === estrategiaElegida) btn.classList.add('incorrecta');
    });
    Array.from(opcionesPrediccionEl.children).forEach((btn) => {
      btn.disabled = true;
      btn.classList.remove('seleccionada');
      if (btn.dataset.opcion === actual.resultado) btn.classList.add('correcta');
      else if (btn.dataset.opcion === prediccionElegida) btn.classList.add('incorrecta');
    });

    progreso.intentos += 1;
    if (estrategiaOk) progreso.aciertosEstrategia += 1;
    if (prediccionOk) progreso.aciertosPrediccion += 1;
    guardarProgreso();
    renderStats();

    const datosEstrategia = stats.estrategias[actual.estrategia];
    resultadoTextoEl.textContent = `Era ${etiquetaEstrategia(actual.estrategia)} — ${ETIQUETAS_RESULTADO[actual.resultado]} (${actual.move_pct}% de movimiento).`;
    resultadoTextoEl.className = `resultado-texto ${estrategiaOk && prediccionOk ? 'correcta' : 'incorrecta'}`;

    let comparacion = '';
    if (datosEstrategia && datosEstrategia.n > 0) {
      comparacion = `Históricamente, ${etiquetaEstrategia(actual.estrategia)} gana el ${datosEstrategia.pct_gana}% de las veces (n=${datosEstrategia.n}, confiabilidad ${datosEstrategia.confiabilidad}) — un caso individual no invalida ni confirma el patrón.`;
    }
    resultadoDetalleEl.textContent = comparacion;

    resultadoEl.hidden = false;
  }

  btnRevelar.addEventListener('click', revelarResultado);
  btnSiguiente.addEventListener('click', siguienteCaso);

  btnReset.addEventListener('click', () => {
    const confirmado = window.confirm('¿Reiniciar el progreso guardado de Backtesting? Esta acción no se puede deshacer.');
    if (!confirmado) return;
    localStorage.removeItem(STORAGE_KEY);
    progreso = { intentos: 0, aciertosEstrategia: 0, aciertosPrediccion: 0 };
    renderStats();
  });

  function activar() {
    if (!inicializado) {
      inicializado = true;
      grafico = S.crearGraficoVelas(chartContainer);
      renderStats();

      Promise.all([
        fetch(URL_STATS).then((r) => r.json()),
        fetch(URL_CASOS).then((r) => r.json()),
      ])
        .then(([statsData, casosData]) => {
          stats = statsData;
          casos = casosData;
          renderProbabilidades();
          if (casos.length > 0) {
            siguienteCaso();
          } else {
            casoMetaEl.textContent = 'No hay casos guardados todavía.';
          }
        })
        .catch((err) => {
          probabilidadesEl.textContent = 'No se pudieron cargar los datos de backtesting.';
          console.error('Error cargando datos de backtesting:', err);
        });
      return;
    }
    grafico.ajustarTamano();
    grafico.chart.timeScale().fitContent();
  }

  window.Backtesting = { activar };
})();
