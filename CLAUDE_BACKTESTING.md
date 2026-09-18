# CLAUDE_BACKTESTING.md — Backtesting real de las 5 estrategias

Lee esto completo. Tiene dos partes: (A) correr el pipeline de datos
reales, (B) construir la pestaña interactiva. Haz commit separado para
cada una. Esta es una sesión distinta a las anteriores — aquí SÍ hay que
ejecutar código Python con acceso a internet real (Yahoo Finance), algo
que no se hizo en las sesiones previas.

## Contexto (para que entiendas el objetivo, no solo los pasos)

Las Fases 1-4 practican con datos SINTÉTICOS (inventados por un generador,
con etiquetas garantizadas). Esto es distinto: aquí se aplican las 5
estrategias formalizadas sobre precios REALES de SPY y QQQ, para medir
qué tan bien funcionan de verdad, y se construye una pestaña donde
Camilo puede poner a prueba su criterio contra esos casos reales.

## PARTE A — Correr el pipeline

### 1. Instalar dependencias (una sola vez)

```bash
pip3 install yfinance pandas numpy --break-system-packages
```

### 2. Correr el script

```bash
python3 data/backtest_pipeline.py
```

Esto descarga datos reales de Yahoo Finance (necesita internet), detecta
los casos históricos de las 5 estrategias, y genera dos archivos en el
directorio donde lo corras:
- `backtest_stats.json` — probabilidades agregadas por estrategia
- `backtest_cases.json` — casos individuales con las velas y el resultado real

Muévelos a `data/backtesting/` (créala si no existe) antes de seguir.

### 3. Revisar la salida ANTES de construir nada

El script imprime, por estrategia, cuántos casos encontró (`n`) y los
porcentajes de gana/pierde/neutral. Revisa:

- **Si alguna estrategia da `n: 0`** ("Sin casos detectados"): no es
  necesariamente un bug — puede ser que en 60 días esa configuración
  específica simplemente no ocurrió. Antes de tocar el código, corre de
  nuevo agregando un tercer ticker conocido y líquido (ej. AAPL) a la
  lista `TICKERS` del script, para ver si aparece con más datos. Si
  sigue en 0 después de eso, es válido dejarlo así y decirlo en el
  resumen — no fuerces detecciones bajando artificialmente los umbrales
  solo para tener n>0.
- **Si el número total de casos es absurdamente alto** (cientos por
  estrategia): probablemente `buscar_linea()` está siendo demasiado
  permisiva (encuentra "líneas" en casi cualquier ruido). Puedes
  ajustar `TOLERANCIA_LINEA` o `LOOKBACK_CANAL` (están como constantes
  al inicio del script, documentadas) — pero antes de tocarlas, mira 2-3
  casos concretos del `backtest_cases.json` generado y confirma con tus
  propios ojos si la línea que se dibujaría ahí tiene sentido o no.
- Cuenta cuántos casos totales quedaron en `backtest_cases.json` — el
  script limita a 60 por estrategia como máximo, así que no debería ser
  gigante.

Documenta en el resumen final los números que viste (n por estrategia,
% gana/pierde) — Camilo los necesita para decidir si vale la pena seguir
afinando esto.

### Definition of done (Parte A)

- [ ] `backtest_stats.json` y `backtest_cases.json` existen en
      `data/backtesting/` con datos reales (no vacíos, salvo que
      legítimamente una estrategia no tuvo casos).
- [ ] Revisaste manualmente al menos 2-3 casos de `backtest_cases.json`
      (las velas se ven coherentes con la estrategia que dice detectar).
- [ ] Commit: `Backtesting: pipeline corrido con datos reales (SPY, QQQ)`.

---

## PARTE B — Pestaña "Backtesting" en la app

### Formato de los datos generados

`backtest_stats.json`:
```json
{
  "generado": "2026-...",
  "periodo_datos": "60d",
  "tickers": ["SPY", "QQQ"],
  "estrategias": {
    "VV11": {"n": 23, "direccion": "CALL", "pct_gana": 60.9, "pct_pierde": 30.4,
              "pct_neutral": 8.7, "movimiento_promedio_pct": 0.8,
              "confiabilidad": "baja (n<20, tratar como orientativo, no concluyente)"},
    ...
  }
}
```

`backtest_cases.json` — array de casos:
```json
{
  "id": "SPY-VV11-142", "ticker": "SPY", "estrategia": "VV11", "direccion": "CALL",
  "fecha": "2026-...", "velas": [ {"o":...,"h":...,"l":...,"c":...}, ... ],
  "vela_gatillo_idx": 9, "volumen_pct_avg": 83.4,
  "move_pct": 1.2, "resultado": "gana"
}
```

### Flujo de la pantalla

1. **Vista de probabilidades** (arriba de todo, siempre visible): una
   tarjeta por estrategia mostrando `pct_gana`/`pct_pierde`/`pct_neutral`
   como barras simples, el `movimiento_promedio_pct`, y el texto de
   `confiabilidad` bien visible (no lo escondas en letra chica — es
   importante que Camilo no sobre-confíe en muestras chicas).
2. **Modo de revisión interactiva** (el "juego"): igual mecánica que
   Fase 3 pero con datos reales:
   - Muestra las velas de contexto de un caso (`velas`, resaltando
     `vela_gatillo_idx`), SIN mostrar el resultado.
   - Pregunta: "¿Qué estrategia aplica aquí, y crees que ganó o
     perdió?" — dos decisiones en una: identificar la estrategia Y
     predecir el resultado.
   - Al responder, revela `estrategia` real, `resultado` real,
     `move_pct`, y compara contra las probabilidades agregadas de esa
     estrategia (ej. "Esta vez perdió, pero la estrategia gana el 61%
     de las veces históricamente — una pérdida individual no invalida
     el patrón").
3. Guarda su propio progreso en `localStorage`, en clave separada de
   las demás fases.

### Definition of done (Parte B)

- [ ] La vista de probabilidades se ve clara, con el aviso de
      confiabilidad visible para cada estrategia.
- [ ] El modo de revisión funciona con los casos reales, sin repetir
      hasta agotar el mazo (mismo patrón ya usado en las otras fases —
      reutiliza `PatronesShared` si aplica).
- [ ] Verificación con Chrome headless, sin errores de consola.
- [ ] Commit: `Backtesting: pestaña interactiva con probabilidades reales`.

## Nota final para el resumen

Incluye en el resumen, además de lo técnico: con cuántos días de datos
reales se construyó esto (recuerda: máximo 60 días por límite gratuito
de Yahoo), y una frase clara de que estos resultados son un punto de
partida, no una prueba estadística sólida — eso ayuda a que Camilo lo
lea con las expectativas correctas.
