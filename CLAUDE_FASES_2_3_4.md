# CLAUDE_FASES_2_3_4.md — Continuación del proyecto (Fase 1 ya está lista)

Lee este archivo completo antes de tocar código. La Fase 1 (flashcards de
velas) ya está construida y commiteada — no la reconstruyas ni la
regeneres, solo intégrala con lo nuevo (ver "Integración" al final).

Esta sesión construye, en orden, las Fases 2, 3 y 4. Termina cada fase
por completo (con su commit) antes de empezar la siguiente — no las
mezcles en un solo commit gigante.

## Restricciones (las mismas de CLAUDE.md)

Sin backend, sin llamadas de red salvo el CDN de `lightweight-charts` ya
usado en Fase 1, progreso en `localStorage`, interfaz en español con la
terminología exacta del curso.

## Datos ya generados (no los regeneres)

```
data/patterns_fase2.json   <- 48 ejemplos, canales y rupturas
data/patterns_fase3.json   <- 48 ejemplos, checklist de las 5 estrategias
data/generate_channels.py  <- generador de fase2, por si se necesitan más
data/generate_scenarios.py <- generador de fase3, por si se necesitan más
```

---

## FASE 2 — Canales y rupturas

### Formato de `data/patterns_fase2.json`

```json
{
  "id": "canal_bajis-000",
  "patron_correcto": "canal_bajista_valido_con_ruptura",
  "opciones": ["canal_bajista_valido_con_ruptura", "canal_bajista_valido_sin_ruptura",
               "canal_alcista_valido_con_ruptura", "canal_alcista_valido_sin_ruptura",
               "canal_invalido", "ninguno"],
  "velas": [ {"o":...,"h":...,"l":...,"c":...}, ... ],
  "indices_toque": [2, 7],
  "linea": {"tipo": "bajista", "punto_inicio": {"idx": 2, "valor": 206.1},
            "punto_fin": {"idx": 7, "valor": 195.8}},
  "explicacion": "..."
}
```

- `linea` es `null` para `canal_invalido` y `ninguno` (no hay recta que
  trazar — ese es justamente el punto).
- Cuando `linea` no es null, dibújala sobre el gráfico de velas
  (extendida a lo largo de todo el rango visible) usando
  `punto_inicio`/`punto_fin` para calcular la pendiente. Marca visualmente
  los `indices_toque` (ej. un punto o círculo sobre esas velas).

### Flujo de pantalla

Igual estructura que Fase 1 (mazo aleatorio sin repetir, 6 opciones en vez
de 7, explicación al responder, contador de aciertos por categoría en
`localStorage`), pero:

- Dibuja la línea de tendencia además de las velas.
- El texto de las opciones debe ser legible en español, no el slug crudo
  del JSON. Usa estas etiquetas:
  - `canal_bajista_valido_con_ruptura` → "Canal bajista válido, con ruptura"
  - `canal_bajista_valido_sin_ruptura` → "Canal bajista válido, sin ruptura"
  - `canal_alcista_valido_con_ruptura` → "Canal alcista válido, con ruptura"
  - `canal_alcista_valido_sin_ruptura` → "Canal alcista válido, sin ruptura"
  - `canal_invalido` → "Canal inválido (solo 1 toque)"
  - `ninguno` → "Ninguno / rango lateral"

### Definition of done (Fase 2)

- [ ] Los 6 tipos se distinguen visualmente (línea + velas coherentes).
- [ ] Selección de opción → feedback + explicación + botón "Siguiente".
- [ ] Progreso de Fase 2 persiste en `localStorage`, en una clave separada
      de la de Fase 1 (no mezclar los contadores).
- [ ] Commit propio: algo como `Fase 2: canales y rupturas`.

---

## FASE 3 — Checklist de las 5 estrategias

### Formato de `data/patterns_fase3.json`

```json
{
  "id": "VV11-005",
  "patron_correcto": "VV11",
  "opciones": ["VV11", "SMA_hora", "SMA_dia", "V10_roja", "Falso_Gap", "ninguna"],
  "contexto": "AAPL: la vela V10 (9:30-10:00) abrió con gap bajista y cerró verde alcista. Ahora estás en la vela V11 (10:00-11:00): es verde alcista y acaba de romper el canal bajista que traía el precio.",
  "vela_gatillo": {"o":100.0,"h":101.4,"l":99.63,"c":101.07},
  "volumen": {"actual_pct_avg": 83, "umbral_pct_avg": 50},
  "explicacion": "..."
}
```

Esta fase es distinta a las anteriores: no es reconocimiento visual puro,
es aplicar el checklist completo tal como está en
`notas-curso-bolsa-newlife.md` sección 9. Por eso cada ejemplo trae:

1. **Un texto de contexto** (léelo tal cual, es la "historia" del setup).
2. **Una vela gatillo** para dibujar (color/dirección es lo que importa
   aquí, no un patrón de mecha complejo).
3. **Un dato de volumen** (cuando aplica — `V10_roja` y `Falso_Gap` no
   dependen del umbral de volumen del playbook, por eso ese campo es
   `null` en esos casos; no lo muestres si es `null`).

### Flujo de pantalla

1. Muestra el `contexto` como texto destacado (es lo primero que se lee).
2. Dibuja la `vela_gatillo` (una vela sola basta, no hace falta más
   contexto visual — el contexto ya está en el texto).
3. Si `volumen` no es `null`, muéstralo de forma simple: por ejemplo dos
   barras (actual vs. umbral) o el texto "Volumen: 83% del promedio
   (umbral: 50%)".
4. 6 opciones con estas etiquetas en español:
   - `VV11` → "VV11 (gap + ruptura de canal)"
   - `SMA_hora` → "S.M.A. — Temporalidad de 1 hora"
   - `SMA_dia` → "S.M.A. — Temporalidad de Día"
   - `V10_roja` → "V10 Roja (reversión en canal bajista)"
   - `Falso_Gap` → "Falso Gap"
   - `ninguna` → "Ninguna estrategia aplica todavía"
5. Al responder: feedback + `explicacion` + "Siguiente".

### Definition of done (Fase 3)

- [ ] El contexto se lee completo antes de responder (no se corta).
- [ ] El campo `volumen` se oculta limpiamente cuando es `null`, sin dejar
      un hueco vacío raro en el layout.
- [ ] Progreso en su propia clave de `localStorage`.
- [ ] Commit propio: `Fase 3: checklist de las 5 estrategias`.

---

## FASE 4 — Modo velocidad

No hay datos nuevos que generar. Esta fase reutiliza los datasets de las
Fases 1, 2 y 3 ya cargados.

### Qué construir

1. Un modo "velocidad" seleccionable desde la navegación (ver
   "Integración" abajo): mezcla ejemplos de las 3 fases en una sola
   secuencia, con un cronómetro visible (ej. 10-15 segundos por
   pregunta, configurable con una constante fácil de cambiar en el
   código).
2. Si se acaba el tiempo sin responder, cuenta como fallo y pasa al
   siguiente automáticamente (mostrando igual la explicación un momento).
3. Al final de una ronda (ej. 15 preguntas), muestra un resumen: aciertos,
   tiempo promedio de respuesta, y el patrón/categoría donde más falló
   (usando los contadores por categoría que ya vienes guardando desde las
   fases 1-3).
4. Guarda el historial de rondas de velocidad en su propia clave de
   `localStorage` (fecha, aciertos, promedio) — no hace falta gráfico de
   evolución todavía, con guardar los datos basta.

### Definition of done (Fase 4)

- [ ] El cronómetro se ve y funciona (cuenta regresiva visible).
- [ ] Al vencer el tiempo, avanza solo sin trabarse.
- [ ] El resumen final muestra al menos: aciertos totales y la categoría
      más débil.
- [ ] Commit propio: `Fase 4: modo velocidad`.

---

## Integración (al final, después de las 3 fases)

Con las 4 fases ya construidas, agrega una navegación simple en la
cabecera (pestañas o botones): "Velas" (Fase 1) · "Canales" (Fase 2) ·
"Estrategias" (Fase 3) · "Velocidad" (Fase 4). No hace falta un router
complejo — con mostrar/ocultar secciones alcanza. Verifica que cambiar de
pestaña no borre el progreso de las otras.

Termina con un último commit de integración: `Integración: navegación
entre las 4 fases`.

## Verificación final antes de terminar

- [ ] Repite la verificación con Chrome headless que ya usaste en Fase 1
      (o el método que hayas usado) para las 4 fases, no solo la última.
- [ ] Sin errores en consola en ninguna pestaña.
- [ ] `git log --oneline` muestra los commits de cada fase por separado,
      más el de integración.

Cuando termines todo, deja un resumen breve de qué quedó y qué NO
alcanzaste a hacer (si algo quedó pendiente), para que Camilo sepa qué
revisar primero.
