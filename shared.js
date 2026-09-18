// Utilidades compartidas entre las fases (gráficos, localStorage, barajado).
window.PatronesShared = (function () {
  'use strict';

  const COLOR_ALCISTA = '#2f9e5f';
  const COLOR_BAJISTA = '#e5534b';
  const COLOR_DESTACADO = '#f5c542';

  function crearGraficoVelas(container) {
    const chart = LightweightCharts.createChart(container, {
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
      upColor: COLOR_ALCISTA,
      downColor: COLOR_BAJISTA,
      borderUpColor: COLOR_ALCISTA,
      borderDownColor: COLOR_BAJISTA,
      wickUpColor: COLOR_ALCISTA,
      wickDownColor: COLOR_BAJISTA,
    });

    function ajustarTamano() {
      if (container.clientWidth === 0 || container.clientHeight === 0) return;
      chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    }
    window.addEventListener('resize', ajustarTamano);
    ajustarTamano();

    return { chart, serie, ajustarTamano };
  }

  function velasATiempo(velas, baseTime) {
    baseTime = baseTime || 1700000000;
    return velas.map((vela, i) => ({
      time: baseTime + i * 86400,
      open: vela.o,
      high: vela.h,
      low: vela.l,
      close: vela.c,
    }));
  }

  function barajar(arr) {
    const copia = arr.slice();
    for (let i = copia.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copia[i], copia[j]] = [copia[j], copia[i]];
    }
    return copia;
  }

  // Mazo con la mecánica "no repetir hasta agotar, luego rebarajar" usada
  // por las 4 fases. Antes cada fase reimplementaba esto por su cuenta;
  // se unifica acá para que las 3 copias no puedan divergir entre sí.
  function crearMazo() {
    let indices = [];
    return {
      siguienteIndice(totalEjemplos) {
        if (indices.length === 0) {
          indices = barajar(Array.from({ length: totalEjemplos }, (_, i) => i));
        }
        return indices.pop();
      },
    };
  }

  function cargarProgreso(storageKey) {
    try {
      const guardado = JSON.parse(localStorage.getItem(storageKey));
      if (guardado && typeof guardado.aciertos === 'number') {
        return guardado;
      }
    } catch (e) {
      /* localStorage vacío o corrupto: se ignora y se parte de cero */
    }
    return { aciertos: 0, intentos: 0, porPatron: {} };
  }

  function guardarProgreso(storageKey, progreso) {
    localStorage.setItem(storageKey, JSON.stringify(progreso));
  }

  function registrarIntento(progreso, patron, esCorrecto) {
    progreso.intentos += 1;
    if (esCorrecto) progreso.aciertos += 1;

    if (!progreso.porPatron[patron]) {
      progreso.porPatron[patron] = { aciertos: 0, intentos: 0 };
    }
    progreso.porPatron[patron].intentos += 1;
    if (esCorrecto) progreso.porPatron[patron].aciertos += 1;
  }

  // Dibuja una única vela como SVG (para casos donde no hace falta un
  // gráfico completo de lightweight-charts, ej. la vela gatillo de Fase 3).
  function dibujarVelaSVG(container, vela) {
    const ancho = 160;
    const alto = 220;
    const margen = 20;
    const rango = Math.max(vela.h - vela.l, 0.01);
    const escala = (alto - margen * 2) / rango;
    const y = (valor) => margen + (vela.h - valor) * escala;

    const esAlcista = vela.c >= vela.o;
    const color = esAlcista ? COLOR_ALCISTA : COLOR_BAJISTA;
    const cx = ancho / 2;
    const anchoBody = 48;
    const yOpen = y(vela.o);
    const yClose = y(vela.c);
    const yBodyTop = Math.min(yOpen, yClose);
    const yBodyBottom = Math.max(yOpen, yClose);
    const alturaBody = Math.max(yBodyBottom - yBodyTop, 2);

    container.innerHTML = `
      <svg viewBox="0 0 ${ancho} ${alto}" width="100%" height="100%" role="img" aria-label="Vela gatillo">
        <line x1="${cx}" y1="${y(vela.h)}" x2="${cx}" y2="${y(vela.l)}" stroke="${color}" stroke-width="2" />
        <rect x="${cx - anchoBody / 2}" y="${yBodyTop}" width="${anchoBody}" height="${alturaBody}" fill="${color}" />
      </svg>
    `;
  }

  return {
    COLOR_ALCISTA,
    COLOR_BAJISTA,
    COLOR_DESTACADO,
    crearGraficoVelas,
    velasATiempo,
    barajar,
    crearMazo,
    cargarProgreso,
    guardarProgreso,
    registrarIntento,
    dibujarVelaSVG,
  };
})();
