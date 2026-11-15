# Corte de Luz

Obligatorio 2 de Programación 2.

Juego hecho en Python con **pygame** y **OpenCV** donde **la linterna del celular es la espada**.
La cámara de la computadora busca el punto de luz más brillante de la imagen y lo sigue.
Al mover el celular frente a la cámara, la luz deja un rastro, y las frutas que lo cruzan se cortan.
Sin la cámara no se puede jugar: la luz es el único control para cortar.

Repositorio: https://github.com/faaaaaacuu/obligatorio2-programacion2

## Instalación

Se necesita Python 3.9 o más nuevo, una cámara web y un celular con linterna.

```bash
pip install -r requirements.txt
```

En macOS, la primera vez el sistema pide permiso para usar la cámara
(a la Terminal o a VS Code, según desde dónde se corra).

## Cómo se juega

```bash
python3 main.py
```

El juego arranca en **pantalla completa**. Con **F** se pasa a ventana (y se puede cerrar con la X)
y con **F** de nuevo se vuelve a pantalla completa. Se puede cambiar en `ajustes.py` (`PANTALLA_COMPLETA`).

1. Prender la linterna del celular y apuntarla hacia la cámara.
2. En el menú tiene que aparecer **"Linterna detectada"** en verde (y un círculo amarillo donde está la luz).
3. Apretar **1** para jugar solo o **2** para el versus, y mover el celular como una espada.

- Cada fruta cortada suma un punto.
- Cortar una bomba resta una vida.
- Dejar caer una fruta sin cortarla también resta una vida (las bombas se pueden dejar caer).
- Para cortar hay que mover la luz: si se queda quieta encima de una fruta, no corta.
- Hay **3 vidas** para toda la partida.
- Al terminar, **ESPACIO** arranca otra partida del mismo modo sin cerrar la ventana
  (o **1** / **2** para cambiar de modo).

### Modo 1 jugador: superar el récord

La partida **no termina hasta que perdés las 3 vidas**. No hay metas en pantalla: la dificultad
sube sola, sin avisar, cada 10 frutas cortadas. Las frutas salen más seguido, más rápido, más chicas
y con más bombas (ver [Dificultad](#dificultad)).

Al perder se muestra cuántas frutas cortaste y se compara con el **récord**. Si lo superaste,
queda guardado como récord nuevo; si no, te dice cuántas te faltaron. Durante la partida, en el
momento en que pasás el récord aparece **"¡NUEVO RÉCORD!"**. El objetivo es superarlo.

### Modo versus (2 jugadores)

Antes de empezar, cada jugador **escribe su nombre** (ENTER para confirmar, ESC para volver).
La pantalla se divide al medio: el **Jugador 1** juega en la mitad izquierda y el **Jugador 2**
en la derecha, cada uno con la linterna de su celular. Cada mitad tiene sus propias vidas y
puntos, y la cámara busca una luz distinta en cada mitad.

Cada jugador tiene **sus propias frutas**:

| Jugador 1 (rastro celeste) | Jugador 2 (rastro naranja) |
|----------------------------|----------------------------|
| manzana, naranja, sandía   | uva, kiwi, limón           |

**Bomba mortal:** si un jugador **gira la linterna en círculos** (más o menos una vuelta por
segundo), en el medio del círculo se va formando una bola violeta. Al completar una vuelta y media
la bola se convierte en una bomba mortal que aparece en la mitad del rival. Si el rival la corta,
**se queda sin vidas y pierde en el acto**. Cada jugador la puede usar **una sola vez** por partida,
y tirarla **te deja con 1 vida**. Si el rival la esquiva, la partida sigue.

- **Gana el que aguanta más**: pierde el primero que se queda sin vidas.
- Si los dos se quedan sin vidas a la vez, es empate.
- La dificultad sube sola para los dos cada 20 segundos.
- Cada partida **se guarda** (fecha, nombres, frutas de cada uno y ganador). Al terminar se muestra
  el historial entre esos dos jugadores (por ejemplo "Ana 3 - 1 Facu") y las últimas partidas.
- **ESPACIO** es la revancha con los mismos nombres; **2** permite cambiarlos.

Conviene que cada jugador se pare de su lado y no cruce la linterna a la mitad del otro.

Si la cámara deja de ver una linterna, aparece el aviso "No veo la linterna" y, si pasa más de
medio segundo, el juego se **pausa** hasta que la luz vuelva a aparecer (en el versus se pausa
para los dos, así nadie pierde vidas por eso).

Funciona mejor en un cuarto con poca luz y sin lámparas o ventanas detrás del jugador.

## Dificultad

El juego es infinito, pero cada vez más difícil. Los primeros 5 niveles están armados a mano
en la lista `NIVELES` de `ajustes.py`:

| Nivel | Frutas a la vez | Velocidad  | Bombas |
|-------|-----------------|------------|--------|
| 1     | 3               | muy lenta  | no     |
| 2     | 3               | lenta      | 10 %   |
| 3     | 4               | media      | 15 %   |
| 4     | 5               | rápida     | 18 %   |
| 5     | 6               | muy rápida | 22 %   |

Después del nivel 5, la función `reglas_de_nivel` (en `main.py`) hace cada nivel un poco más
difícil que el anterior: más gravedad, menos espera entre frutas, frutas más chicas y más bombas.
Tiene **topes** (`TOPE_...` en `ajustes.py`) para que nunca se vuelva imposible.

Se sube de nivel cada 10 frutas jugando solo, y cada 20 segundos en el versus
(`FRUTAS_POR_NIVEL` y `SEGUNDOS_POR_NIVEL`). Nunca aparece un cartel de "nivel": se nota en el juego.

## Resultados guardados

El récord y las partidas del versus se guardan en `resultados.json`, en la carpeta del juego
(se crea solo la primera vez). Lo maneja `resultados.py`. Para borrar todo, alcanza con
borrar ese archivo.

## Controles

| Tecla           | Acción                                                     |
|-----------------|------------------------------------------------------------|
| 1               | Empezar en modo 1 jugador                                  |
| 2               | Empezar en modo versus                                     |
| ESPACIO         | Volver a jugar el mismo modo                               |
| + / -           | Subir / bajar el umbral de brillo de la detección          |
| M               | Mostrar / ocultar lo que la cámara está tomando como "luz" |
| F               | Pantalla completa / ventana                                |
| ESC o la X      | Salir                                                      |

Si el juego detecta otras cosas como si fueran la linterna (lámparas, ventanas, la pantalla),
hay que subir el umbral con **+**. Si no detecta la linterna, hay que bajarlo con **-**.
La tecla **M** muestra un recuadro abajo a la derecha con lo que se está detectando.

## Archivos

| Archivo              | Qué tiene                                                                 |
|----------------------|---------------------------------------------------------------------------|
| `main.py`            | El bucle principal (eventos, actualizar, dibujar, `reloj.tick`) y los estados del juego |
| `vision.py`          | Todo lo de OpenCV: abrir la cámara, leer el cuadro y detectar la luz      |
| `objetos.py`         | Las clases `Fruta`, `BombaMortal`, `Pedazo`, `Particula`, `TextoFlotante` y `Jugador` |
| `resultados.py`      | Lee y guarda el récord y el historial del versus (`resultados.json`)     |
| `graficos.py`        | Funciones que dibujan las frutas, bombas, corazones, paneles y el brillo de la espada |
| `ajustes.py`         | Constantes: colores, frutas de cada jugador, tamaños, velocidades, niveles y rangos de detección |
| `sonidos/`           | Efectos de sonido (corte, bomba, caída, nivel, ganar, perder, lanzar y bomba mortal) |
| `generar_sonidos.py` | Script que generó los `.wav` (no hace falta correrlo para jugar)          |

## Cómo funciona la detección

En cada cuadro de la cámara (`vision.py`):

1. La imagen se espeja con `cv2.flip` (para que moverse a la derecha sea ir a la derecha en pantalla).
2. Se pasa a escala de grises y se desenfoca un poco para sacar ruido.
3. Se quedan solo los píxeles más brillantes que el umbral (`cv2.threshold`).
4. Se busca la mancha blanca más grande (`cv2.findContours`) y se devuelve su centro `(x, y)`.
   Si no hay ninguna mancha suficientemente grande, se devuelve `None`.

`detectar_luz` recibe además la zona donde buscar (`x_min`, `x_max`). Jugando solo busca en toda
la pantalla; en el versus se llama una vez por jugador, cada una con su mitad.

El resto del juego solo usa ese resultado. Para saber si una fruta se cortó, se calcula la
distancia entre el centro de la fruta y el segmento que recorrió la luz desde el cuadro anterior.
Si esa distancia es menor que el radio de la fruta, la fruta queda cortada.

### Cómo se detecta el círculo

`contar_vueltas` (en `objetos.py`) mira las últimas posiciones de la luz y la **dirección** en la que
se mueve de un cuadro al siguiente. Al dibujar un círculo, esa dirección dobla un poco cada vez y
siempre para el mismo lado: después de una vuelta dobló 360°. Al cortar, en cambio, la luz va y
vuelve, y eso es un giro brusco (más de 60° de golpe) que vuelve la cuenta a cero. Así un corte
normal no carga la bomba sin querer.

## Gráficos

No se usan imágenes de archivos: todo se dibuja con pygame en `graficos.py`.

- **Frutas con volumen:** cada fruta es una pila de óvalos, cada uno más chico, más claro y corrido
  hacia arriba a la izquierda, lo que da sensación de esfera. La imagen se arma una sola vez cuando
  la fruta aparece y después solo se gira (`rotozoom`).
- **Bordes suaves:** las imágenes se dibujan al doble de tamaño y se achican con `smoothscale`.
- **Corte:** la fruta se parte en la dirección en que se movió la luz, se ve el interior
  (gajos, semillas) y salta jugo (`Particula`).
- **Espada de luz:** se dibuja en dos capas que se **suman** a la pantalla (`BLEND_RGB_ADD`).
  Una capa chica se difumina y se agranda para el resplandor, y otra nítida lleva el centro blanco.
- **Fondo:** la cámara se oscurece más en los bordes (viñeta), así la atención va al centro.
