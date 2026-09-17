# CLAUDE_GLOSARIO.md — Agregar glosario visual de referencia

Lee este archivo completo. Esto se agrega DESPUÉS de que las Fases 1-4 ya
estén construidas (si alguna todavía no existe, avísame en vez de
inventarla). No regeneres nada de lo que ya está commiteado — esto es
una adición, no una reconstrucción.

## Por qué

Al practicar en frío (Fase 1), es fácil no saber todavía qué es, por
ejemplo, un Marubozu — hace falta poder ver una referencia clara antes
de o después de fallar, no solo velas con ruido aleatorio.

## Datos ya generados (no los regeneres)

```
data/glosario/martillo.png
data/glosario/gancho.png
data/glosario/marubozu.png
data/glosario/doji.png
data/glosario/envolvente_alcista.png
data/glosario/envolvente_bajista.png
data/glosario/ninguno.png
data/glosario/glosario_fase1.json   <- manifiesto: {patron, archivo, titulo, definicion}
```

Son diagramas idealizados y anotados (no las velas ruidosas de
`patterns_fase1.json`) — pensados para enseñar el patrón, no para
practicar reconocimiento.

## Qué construir

### 1. Pestaña "Glosario" en la navegación principal

Una quinta pestaña, junto a Velas / Canales / Estrategias / Velocidad.
Lista las 7 entradas de `glosario_fase1.json` (imagen + título +
definición), navegable en cualquier momento, sin quiz — es solo
referencia. Layout simple: grid o lista vertical, una tarjeta por
patrón.

### 2. Botón "Ver referencia" en la Fase 1 (flashcards de velas)

Justo después de responder una pregunta (ya sea que acertó o falló),
junto al botón "Siguiente", agrega un botón secundario "Ver imagen de
referencia" que muestra (inline, o en un modal simple) la imagen y
definición de `glosario_fase1.json` correspondiente al
`patron_correcto` de esa pregunta — así, si falló porque no sabía qué
era un Marubozu, puede verlo ahí mismo antes de seguir.

No hace falta un botón separado para "ver la opción que elegiste" — con
mostrar la referencia del patrón correcto alcanza.

### 3. (Opcional, solo si el tiempo alcanza) Extender a Fase 2 y 3

Si te sobra alcance en esta sesión, considera el mismo patrón de "ver
referencia" para Fase 2 (qué es un canal válido vs. inválido) y Fase 3
(qué implica cada estrategia). No generes imágenes nuevas para esto sin
avisar primero — si decides hacerlo, usa las explicaciones textuales que
ya existen en esos datasets en vez de crear PNGs nuevos (por ejemplo, un
texto expandido con las reglas del checklist). Si no alcanzas, déjalo
para una próxima sesión y dilo en el resumen final.

## Definition of done

- [ ] La pestaña "Glosario" muestra las 7 imágenes con su título y
      definición, sin necesidad de estar respondiendo nada.
- [ ] En Fase 1, tras responder, el botón "Ver imagen de referencia"
      muestra la imagen correcta para esa pregunta específica.
- [ ] Las imágenes cargan bien (rutas relativas correctas a
      `data/glosario/`).
- [ ] Sin errores de consola.
- [ ] Commit: `Glosario visual de referencia`.

Al terminar, resume qué quedó y si alcanzaste a extender a Fase 2/3 o no.
