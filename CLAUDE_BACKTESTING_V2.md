# CLAUDE_BACKTESTING_V2.md — Pipeline con fuentes de datos mixtas

Esta sesión REEMPLAZA el pipeline anterior (`backtest_pipeline.py`) por
uno nuevo (`backtest_pipeline_v2.py`) que corrige un bug de raíz y
resuelve el problema de `SMA_dia` en 0. Si ya corriste la Parte A de
`CLAUDE_BACKTESTING.md` y tienes `data/backtesting/backtest_stats.json`
y `backtest_cases.json` de la versión anterior, este script los
sobrescribe — es el comportamiento esperado.

## Qué cambió y por qué (para que puedas explicárselo a Camilo)

1. **Bug de raíz corregido:** la v1 leía cada bloque de 1 hora (V11,
   V12...) como 2 velas de 30 min sueltas en vez de 1 vela horaria — un
   mismo quiebre se contaba varias veces (por eso Falso_Gap dio n=108).
   La v2 agrega las 2 sub-velas de 30 min de cada bloque en 1 sola vela
   antes de detectar nada.
2. **3 fuentes de datos en vez de 1**, cada estrategia usa la que le
   corresponde:

   | Estrategia | Fuente | Por qué |
   |---|---|---|
   | VV11, V10_roja, Falso_Gap | 30 min (60 días) | Necesitan la V10 exacta (9:30-10:00) |
   | SMA_hora | 1 hora (730 días) | No depende de la V10 exacta, se beneficia de más historia |
   | SMA_dia | Diaria (5 años) + 1h para confirmar | Necesita 100-200 cierres DIARIOS reales, imposible con solo 60 días |

## Pasos

### 1. Dependencias (si ya las instalaste para la v1, sáltate esto)

```bash
pip3 install yfinance pandas numpy --break-system-packages
```

### 2. Correr el pipeline nuevo

```bash
python3 data/backtest_pipeline_v2.py
```

Mueve `backtest_stats.json` y `backtest_cases.json` a `data/backtesting/`,
reemplazando los de la v1.

### 3. Revisar antes de tocar la UI

- Confirma en la consola que `SMA_dia` ya NO da `n: 0` (ese era el punto
  central de este cambio). Si sigue en 0, revisa si el ticker tiene
  suficiente historia diaria (SPY y QQQ la tienen de sobra, no debería
  pasar).
- Confirma que `Falso_Gap` bajó su `n` frente a los 108 originales de la
  v1 — un número mucho más bajo (probablemente de un dígito a unas
  pocas decenas) es lo esperado y correcto, no un problema.
- Revisa 2-3 casos de cada estrategia en `backtest_cases.json` a mano,
  igual que en la sesión anterior.
- Si algún número te sigue pareciendo raro, dilo en el resumen en vez de
  ajustar umbrales a ciegas.

### 4. Actualizar la pestaña Backtesting (si ya la construiste)

Si ya existe la pestaña Backtesting de la sesión anterior, solo necesita
apuntar a los nuevos archivos (ya deberían llamarse igual:
`backtest_stats.json` / `backtest_cases.json`, mismo formato de campos)
— no debería requerir cambios de UI. Verifica que la vista de
probabilidades y el modo de revisión sigan funcionando con los datos
nuevos. Si el formato de algún campo cambió de forma incompatible,
ajusta el código de la pestaña para que coincida (revisa el ejemplo de
formato más abajo).

Si por algún motivo la pestaña Backtesting todavía no existe, constrúyela
según la Parte B de `CLAUDE_BACKTESTING.md` (el spec original), usando
estos datos nuevos.

### Formato de datos (sin cambios de fondo respecto al original)

```json
// backtest_stats.json
{
  "generado": "...", "tickers": ["SPY", "QQQ"],
  "fuentes": {"VV11": "30min (60d)", "SMA_dia": "diario (5y) + 1h para confirmación", ...},
  "estrategias": {
    "VV11": {"n": 8, "direccion": "CALL", "pct_gana": 62.5, "pct_pierde": 25.0,
              "pct_neutral": 12.5, "movimiento_promedio_pct": 0.9,
              "confiabilidad": "baja (n<20, orientativo, no concluyente)"},
    ...
  }
}
// backtest_cases.json (igual formato que antes, un array de casos)
```

## Definition of done

- [ ] `SMA_dia` ya no está en 0 (o, si legítimamente sigue en 0 con SPY
      y QQQ teniendo de sobra historia diaria, investigar por qué antes
      de continuar).
- [ ] `Falso_Gap` bajó su n de forma sustancial frente a los 108 de la v1.
- [ ] Revisaste manualmente 2-3 casos de cada estrategia.
- [ ] La pestaña Backtesting funciona con los datos nuevos, sin errores
      de consola.
- [ ] Commit: `Backtesting v2: fuentes de datos mixtas, fix de doble conteo`.

## Resumen final

Incluye la tabla de resultados por estrategia (n, % gana/pierde/neutral,
confiabilidad) como hiciste la vez anterior, y confirma explícitamente
si `SMA_dia` y el conteo de `Falso_Gap` quedaron resueltos.
