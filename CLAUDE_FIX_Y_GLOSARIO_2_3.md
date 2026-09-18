# CLAUDE_FIX_Y_GLOSARIO_2_3.md — Bug de mazo + Glosario de Canales y Estrategias

Lee este archivo completo. Tiene dos partes: primero un fix, después una
extensión. Haz un commit separado para cada una.

## PARTE A — Investigar y arreglar: Fase 2 y Fase 3 solo muestran 1 pregunta

Camilo reporta que en las pestañas Canales (Fase 2) y Estrategias (Fase
3), solo ve una pregunta — no avanza a ejemplos distintos como sí lo
hace Fase 1.

**Dato confirmado:** el problema NO está en los datos. `data/patterns_fase2.json`
y `data/patterns_fase3.json` tienen 48 ejemplos cada uno (verificado
directamente). El bug está en la lógica de la aplicación.

### Qué revisar

1. Compara cómo Fase 1 arma y avanza su mazo (baraja el array completo,
   usa un índice que avanza, repite barajando solo al agotrarse) contra
   cómo lo hacen Fase 2 y 3. Es muy probable que el mazo de Fase 2/3 se
   esté reinicializando en cada render en vez de mantenerse en estado, o
   que el índice no se esté incrementando, o que el "Siguiente" esté
   volviendo a tomar el ejemplo en la posición 0 en vez de avanzar.
2. Revisa también si el `fetch` de cada dataset se está haciendo una sola
   vez al cargar la pestaña (correcto) o en cada clic (podría explicar
   que siempre "reinicie" al mismo primer ejemplo si además no se
   baraja distinto cada vez con una semilla fija).
3. Prueba manualmente: entra a Canales, responde, click "Siguiente" 5
   veces seguidas, confirma que las velas/línea de cada pregunta son
   visiblemente distintas entre sí (no la misma repetida). Haz lo mismo
   en Estrategias (el contexto de texto debe cambiar).

### Definition of done (Parte A)

- [ ] En Canales, 10 clics en "Siguiente" muestran 10 ejemplos distintos
      (no la misma pregunta, no un ciclo de solo 1 ni 2).
- [ ] Lo mismo en Estrategias.
- [ ] El comportamiento de "no repetir hasta agotar el mazo, luego
      rebarajar" queda igual que en Fase 1 (usa el mismo patrón de
      código si tiene sentido reutilizarlo).
- [ ] Commit: `Fix: mazo de Fase 2 y 3 no avanzaba correctamente`.

Si al investigar descubres que el bug es otra cosa distinta a lo que se
describe arriba, arréglalo igual y explica en el resumen final qué era
realmente.

---

## PARTE B — Extender el Glosario a Canales y Estrategias

Ahora mismo la pestaña Glosario solo cubre los 7 patrones de velas
(Fase 1). Se agregan dos secciones más.

### Datos ya generados (no los regeneres)

```
data/glosario_fase2/canal_bajista_con_ruptura.png
data/glosario_fase2/canal_bajista_sin_ruptura.png
data/glosario_fase2/canal_alcista_con_ruptura.png
data/glosario_fase2/canal_alcista_sin_ruptura.png
data/glosario_fase2/canal_invalido.png
data/glosario_fase2/ninguno_canal.png
data/glosario_fase2/glosario_fase2.json   <- manifiesto: {patron, archivo, titulo, definicion}

data/glosario_fase3.json   <- fichas de texto (sin imagen): {patron, titulo, direccion,
                               temporalidad, checklist[], senal_ruptura, definicion}
```

### Qué construir

1. **Dentro de la pestaña Glosario**, agrega sub-navegación simple (3
   secciones): "Velas" (lo que ya existe) · "Canales" · "Estrategias".
   No hace falta un router — con mostrar/ocultar bloques alcanza, igual
   que hiciste con las 5 pestañas principales.
2. **Sección Canales:** igual formato que Velas (imagen + título +
   definición), usando `data/glosario_fase2/glosario_fase2.json`.
3. **Sección Estrategias:** aquí NO hay imagen — son fichas de texto.
   Por cada entrada de `data/glosario_fase3.json` (campo `fichas`),
   muestra una tarjeta con: título, dirección (CALL/PUT — dale un color
   distinto a cada una, ej. verde para CALL y rojo para PUT),
   temporalidad, la lista `checklist` como viñetas, la señal de ruptura,
   y la definición. Es información densa — prioriza que se lea bien
   sobre que se vea minimalista.
4. **Botón "Ver referencia" en Fase 2:** igual mecánica que ya existe en
   Fase 1 — tras responder, muestra la imagen+definición de
   `glosario_fase2.json` para el `patron_correcto` de esa pregunta.
5. **Botón "Ver referencia" en Fase 3:** tras responder, muestra la
   ficha de texto (no imagen) de `glosario_fase3.json` para el
   `patron_correcto` de esa pregunta — reutiliza el mismo componente de
   tarjeta que construiste para la sección Estrategias del Glosario.

### Definition of done (Parte B)

- [ ] Las 3 secciones del Glosario son navegables sin perder el
      progreso de las fases.
- [ ] Sección Canales: 6 imágenes con definición, igual de legibles que
      las de Velas.
- [ ] Sección Estrategias: 6 fichas de texto completas y legibles.
- [ ] "Ver referencia" funciona en Fase 2 (imagen) y Fase 3 (ficha de
      texto), mostrando el patrón correcto de la pregunta específica
      que se acaba de responder.
- [ ] Sin errores de consola en ninguna sección.
- [ ] Commit: `Glosario: secciones de Canales y Estrategias`.

## Verificación final

Repite la verificación con Chrome headless (o el método que uses) en
las 5 pestañas principales + las 3 secciones del Glosario. Confirma en
particular que el fix de la Parte A sigue funcionando después de los
cambios de la Parte B (a veces un refactor de navegación rompe el
estado del mazo).

Termina con un resumen: qué causaba el bug de la Parte A, y qué quedó
listo de la Parte B.
