# CLAUDE_BACKTESTING_V3.md — Acumulación histórica + fix de UI

Dos partes independientes, commit separado para cada una.

## PARTE A — Acumulación histórica entre corridas

`backtest_pipeline_v3.py` reemplaza a `backtest_pipeline_v2.py`. La
lógica de detección de las 5 estrategias es IDÉNTICA a la v2 (ya
validada con datos reales) — lo único que cambia es que ahora los casos
se guardan en un archivo permanente (`backtest_history_store.json`) y
cada corrida nueva se SUMA a ese archivo en vez de reemplazarlo. Los
`id` de cada caso ahora se arman con la fecha del caso (no con su
posición), así que un mismo caso detectado en dos corridas distintas se
reconoce como el mismo y no se duplica.

### Pasos

1. Copia `backtest_pipeline_v3.py` a `data/`. Puedes borrar
   `backtest_pipeline_v2.py` o dejarlo, no se usa más.
2. Corre:
   ```bash
   python3 data/backtest_pipeline_v3.py
   ```
3. Va a imprimir algo como:
   ```
   Casos detectados en ESTA corrida: 41
   Casos realmente nuevos (no vistos en corridas anteriores): 41
   Total acumulado en backtest_history_store.json: 41
   ```
   La primera vez que corres la v3, "realmente nuevos" y "total
   acumulado" van a ser iguales (no hay historia previa todavía) — eso
   es normal, no un error. El valor de esto se nota recién quien lo
   corra de nuevo en unas semanas: ahí "realmente nuevos" va a ser un
   número más chico que el total acumulado.
4. Mueve `backtest_stats.json`, `backtest_cases.json` Y
   `backtest_history_store.json` (los 3 archivos) a `data/backtesting/`.
   **El tercero es el más importante para el futuro** — es el que
   acumula entre corridas, no lo borres nunca. Los otros dos se
   regeneran cada vez a partir de él.
5. Confirma que los números de `backtest_stats.json` coincidan
   razonablemente con los que ya tenías de la v2 (deberían ser iguales o
   muy parecidos, ya que es la primera corrida de la v3 y no hay nada
   más que sumar todavía).

### Definition of done (Parte A)

- [ ] Los 3 archivos existen en `data/backtesting/`.
- [ ] `backtest_history_store.json` no está vacío ni corrupto (es un
      array JSON válido).
- [ ] Commit: `Backtesting v3: acumulación histórica entre corridas`.

---

## PARTE B — La UI no debe mostrar porcentajes engañosos con n bajo

En la vista de probabilidades de la pestaña Backtesting: cuando el `n`
de una estrategia sea **menor a 5**, NO muestres el porcentaje de
gana/pierde/neutral como si fuera un dato confiable (ahMismo ahora, con
n=2, se ve "100% gana" en letras grandes, lo cual es engañoso).

En su lugar, para esos casos:
- Muestra el `n` igual (es información real: "2 casos detectados").
- En vez de las barras de porcentaje, muestra un texto claro tipo:
  **"Muestra insuficiente para estimar una probabilidad (menos de 5
  casos). Necesita más corridas del backtest acumulándose con el
  tiempo."**
- No ocultes la estrategia de la lista — solo cambia cómo se presenta
  cuando el n es tan bajo que el porcentaje no dice nada real.

Para n entre 5 y 19, deja el comportamiento actual (mostrar el
porcentaje con la nota de "confiabilidad baja") — el cambio es
específicamente para el caso extremo de n<5.

### Definition of done (Parte B)

- [ ] Con n<5, la tarjeta de esa estrategia muestra el aviso de muestra
      insuficiente en vez de un porcentaje grande.
- [ ] Con n>=5, no cambió nada del comportamiento anterior.
- [ ] Verificado en Chrome headless, sin errores de consola.
- [ ] Commit: `Backtesting: aviso de muestra insuficiente para n<5`.

## Resumen final

Incluye: los números de la primera corrida de la v3 (deberían coincidir
con los de la v2), y confirma que ambas partes quedaron aplicadas.
Recuérdale a Camilo (para que lo lea en el resumen, no hace falta que
hagas nada de código para esto) que para que la acumulación realmente
sirva, tiene que volver a correr `data/backtest_pipeline_v3.py`
periódicamente — por ejemplo, una vez al mes — y cada vez le va a sumar
la ventana de 60 días más reciente al histórico ya guardado.
