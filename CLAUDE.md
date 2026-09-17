# CLAUDE.md — App de práctica de patrones de velas japonesas

Lee este archivo completo antes de escribir código. Es la única fuente de
contexto que necesitas — no busques en internet ni asumas requisitos que
no estén aquí.

## Qué es esto

Simulador de entrenamiento personal (un solo usuario, sin login) para
reconocer patrones de velas japonesas y setups de trading más rápido,
antes de operar cuenta real. NO es una plataforma de trading ni usa datos
de mercado en vivo.

## Restricciones duras (no negociables)

- **Sin backend.** Todo corre en el navegador: HTML + CSS + JS plano (o
  React si lo prefieres, pero sin build step complejo — vale Vite si
  hace la vida más fácil, pero prioriza simplicidad sobre arquitectura).
- **Sin llamadas de red en tiempo de ejecución** salvo cargar la librería
  de gráficos desde un CDN (`lightweight-charts` de TradingView, pin de
  versión). Los datos de velas ya vienen en un JSON local, no se
  descargan.
- **Progreso guardado en `localStorage`** del navegador. No hay cuenta
  ni sincronización entre dispositivos — es intencional.
- **Interfaz en español**, con la terminología exacta que uso en mis
  notas del curso (ver abajo) — no traduzcas los términos a su nombre en
  inglés salvo que ya los use así (ej. "Doji", "Marubozu" quedan igual).

## Estructura de carpetas esperada

```
/index.html
/style.css
/app.js
/data/
  patterns_fase1.json      <- ya generado, no lo edites a mano
  generate_candles.py      <- generador, para producir más datos si hace falta
```

## Datos: `data/patterns_fase1.json`

Array de objetos con esta forma (ya generado y verificado visualmente,
úsalo tal cual):

```json
{
  "id": "mar-000",
  "patron_correcto": "martillo",
  "opciones": ["martillo","gancho","marubozu","doji","envolvente_alcista","envolvente_bajista","ninguno"],
  "velas": [ {"o":444.47,"h":444.94,"l":442.94,"c":444.07}, ... ],
  "vela_objetivo_idx": 4,
  "explicacion": "Mechón largo abajo, cuerpo pequeño arriba..."
}
```

- `velas` es la secuencia completa a dibujar (contexto + vela objetivo).
- `vela_objetivo_idx` es el índice (0-based) de la vela que hay que
  identificar — resáltala visualmente (ej. con un halo o fondo distinto)
  para que quede claro cuál se está preguntando.
- `opciones` son las 7 posibles respuestas (siempre las mismas 7 —
  puedes tomarlas de cualquier ejemplo, no varían).
- `patron_correcto` es la respuesta correcta contra la que validar.

## Alcance de ESTA sesión (Fase 1 — flashcards de velas)

Construir el flujo completo, de principio a fin, para practicar los 7
patrones de la Fase 1. Nada de Fase 2/3/4 todavía (canales, estrategias,
modo velocidad) — eso son sesiones futuras, no las adelantes.

### Flujo de la pantalla

1. Al cargar, tomar un ejemplo aleatorio de `patterns_fase1.json` (sin
   repetir hasta agotar el mazo; al agotarlo, volver a barajar).
2. Dibujar la secuencia de velas con `lightweight-charts`, resaltando la
   vela objetivo.
3. Mostrar las 7 opciones como botones (multiple choice).
4. Al elegir una opción:
   - Marcar visualmente correcto/incorrecto.
   - Mostrar el texto de `explicacion`.
   - Botón "Siguiente" para pasar al próximo ejemplo.
5. Header persistente con: aciertos / intentos totales, y un botón
   "Reiniciar progreso" (limpia `localStorage`).
6. Guardar en `localStorage`: aciertos totales, intentos totales, y por
   patrón (para que más adelante se pueda mostrar "tu punto débil es
   Gancho", aunque esa vista no hay que construirla todavía — solo
   guarda el dato).

### Criterio de "terminado" (definition of done)

- [ ] Puedo abrir `index.html` directo en el navegador (sin servidor) y
      funciona. Si `lightweight-charts` por CDN no carga con `file://`,
      dejar instrucciones claras de cómo levantar un server local
      trivial (`python3 -m http.server`) — un solo comando, en el
      README.
- [ ] Los 7 patrones se ven visualmente distintos y coherentes con su
      definición (mechas largas donde corresponde, cuerpos grandes en
      marubozu, etc. — los datos ya están bien construidos, solo hay
      que dibujarlos fiel a los valores o/h/l/c).
- [ ] El conteo de aciertos persiste si cierro y vuelvo a abrir el
      navegador (localStorage funcionando).
- [ ] No hay errores en la consola del navegador.
- [ ] Commit hecho con mensaje claro al terminar, para que la siguiente
      sesión (Fase 2) arranque de un estado limpio.

## Lo que NO debes hacer en esta sesión

- No construir login, backend, ni base de datos.
- No conectar APIs de mercado real.
- No adelantar Fase 2 (canales), Fase 3 (checklist de estrategias) ni
  Fase 4 (modo velocidad) — cada una es su propia sesión con su propio
  dataset.
- No sobre-diseñar la UI — funcional y clara basta; se puede pulir
  visualmente en la última sesión (Fase 4).

## Referencia rápida de los patrones (por si necesitas describirlos en la UI)

- **Martillo:** mechón largo abajo, cuerpo pequeño arriba → rechazo
  alcista, más relevante tras una caída.
- **Gancho:** mechón largo arriba, cuerpo pequeño abajo → rechazo
  bajista, más relevante tras una subida.
- **Marubozu:** cuerpo grande, casi sin mechas → dominio absoluto de
  una dirección.
- **Doji:** apertura ≈ cierre → equilibrio total, máxima incertidumbre.
- **Envolvente alcista/bajista:** el cuerpo de la segunda vela envuelve
  por completo el cuerpo de la anterior → reversión fuerte.
- **Ninguno:** vela normal, sin patrón especial.
