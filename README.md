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

Al abrirse, el juego muestra una **intro**: pantalla negra, dos espadazos de luz que forman una X
y aparece el título. Dura unos 5 segundos y se puede saltear con cualquier tecla.

Después, la **pantalla de inicio** explica las reglas con 5 tarjetas animadas (cortar frutas, las bombas,
las frutas que se caen, el triple y la bomba mortal del versus) y muestra cómo empezar cada modo.

1. Prender la linterna del celular y apuntarla hacia la cámara.
2. En la pantalla de inicio tiene que aparecer **"Linterna detectada"** en verde.
3. Apretar **1** para jugar solo o **2** para el versus, y mover el celular como una espada.

- Cada fruta cortada suma un punto.
- Cortar una bomba resta una vida.
- Dejar caer una fruta sin cortarla también resta una vida (las bombas se pueden dejar caer).
- Para cortar hay que mover la luz: si se queda quieta encima de una fruta, no corta.
- Hay **3 vidas** para toda la partida.
- **Triple:** si en **un solo trazo** cortás 3 frutas y tenés menos de 3 vidas, ganás una vida.
  Un trazo es un movimiento seguido de la luz: si la luz se frena, se pierde o va y vuelve,
  empieza otro trazo. Funciona en los dos modos.
- Al terminar, **ESPACIO** arranca otra partida del mismo modo sin cerrar la ventana
  (o **1** / **2** para cambiar de modo).
- **ESC** (o el botón **INICIO**) vuelve a la pantalla de inicio desde cualquier lado. Si se
  estaba jugando, esa partida se abandona y no se guarda.

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

Como cada uno tiene media pantalla, en el versus las frutas son **más chicas** (70 % del tamaño,
`ESCALA_FRUTAS_VERSUS`), y **nada pasa al campo del rival**: las frutas, sus mitades y el jugo
rebotan contra el borde de la zona de cada jugador, y además cada uno se dibuja recortado a su mitad.

Conviene que cada jugador se pare de su lado y no cruce la linterna a la mitad del otro.

Si la cámara deja de ver una linterna, no se la da por perdida enseguida: durante **2 segundos**
el punto se queda quieto donde estaba y la estela se va borrando (así un corte muy rápido que la
cámara no llegó a ver no corta el juego). Si pasan los 2 segundos, aparece el aviso
**"No veo la linterna"** y el juego se **pausa** hasta que la luz vuelva (en el versus se pausa
para los dos, así nadie pierde vidas por eso). Se cambia con `TOLERANCIA_SIN_LUZ` en `ajustes.py`.

**Reflejos (límite de velocidad):** a veces la cámara confunde la linterna con su reflejo en una
pared o superficie blanca, y la "luz" salta de golpe a otro lado. Para que eso no corte frutas,
el juego calcula a qué velocidad se movió la luz desde la última posición buena. Si es más rápida
que lo que puede una mano (`VELOCIDAD_MAXIMA_LUZ` = 2500 píxeles por segundo; por ejemplo, ir del
centro a la esquina de arriba en 0,2 s), ese punto no cuenta. Si el reflejo se queda quieto, al
rato se acepta, pero como un trazo nuevo, sin unir los dos lugares.

**Filtro de color:** el punto de luz y su estela se tiñen de un color. Jugando solo, la tecla **C**
cambia entre cian, verde, rosa, rojo, violeta y amarillo (también en medio de la partida). En el
versus cada jugador tiene el suyo: celeste a la izquierda y naranja a la derecha.

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
| C               | Cambiar el color de la luz y su estela (1 jugador)         |
| F               | Pantalla completa / ventana                                |
| ESC             | Volver a la pantalla de inicio (en la pantalla de inicio: salir) |
| Botón INICIO    | Volver a la pantalla de inicio con un clic (arriba a la izquierda) |
| La X            | Cerrar el juego                                            |

Si el juego detecta otras cosas como si fueran la linterna (lámparas, ventanas, la pantalla),
hay que subir el umbral con **+**. Si no detecta la linterna, hay que bajarlo con **-**.
La tecla **M** muestra un recuadro abajo a la derecha con lo que se está detectando.

## Archivos

| Archivo              | Qué tiene                                                                 |
|----------------------|---------------------------------------------------------------------------|
| `main.py`            | El bucle principal (eventos, actualizar, dibujar, `reloj.tick`) y los estados del juego |
| `vision.py`          | Todo lo de OpenCV: abrir la cámara, leer el cuadro y detectar la luz      |
| `objetos.py`         | Las clases `Fruta`, `BombaMortal`, `Pedazo`, `Particula`, `TextoFlotante` y `Jugador` |
| `inicio.py`          | La intro (espadazos y título) y la pantalla de inicio con las reglas animadas |
| `musica.py`          | La música de fondo: cambia de versión según la dificultad, con fundido     |
| `resultados.py`      | Lee y guarda el récord y el historial del versus (`resultados.json`)     |
| `graficos.py`        | Funciones que dibujan las frutas, bombas, corazones, paneles y el brillo de la espada |
| `ajustes.py`         | Constantes: colores, frutas de cada jugador, tamaños, velocidades, niveles y rangos de detección |
| `fuentes/`           | Tipografías Shojumaru y Potta One, con sus licencias (OFL)                |
| `sonidos/`           | Efectos de sonido (los cortes suenan a katana) y la música de fondo `musica.wav` |
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

**Estética: dojo japonés de noche, minimalista.** Laca negra e índigo de base, acentos bermellón y
dorado, textos color papel. La cámara se ve oscura, como detrás de un *shoji* (panel de papel) con su
reja de madera. Hay faroles de papel rojo que se balancean, un *ensō* (el círculo zen pintado de una
pincelada) en la intro y en la cuenta regresiva, y un sello rojo (*hanko*) con el kanji 光 ("luz").
Las vidas son sellos redondos bermellón.

Las tipografías vienen incluidas en la carpeta `fuentes/` (licencia libre SIL OFL, con su archivo de
licencia al lado), así el juego se ve igual en cualquier compu: **Shojumaru** para los títulos, con
trazo de pincel japonés, y **Potta One** para los textos y el kanji del sello.

- **Frutas con volumen:** cada fruta es una pila de óvalos, cada uno más chico, más claro y corrido
  hacia arriba a la izquierda, lo que da sensación de esfera. La imagen se arma una sola vez cuando
  la fruta aparece y después solo se gira (`rotozoom`).
- **Bordes suaves:** las imágenes se dibujan al doble de tamaño y se achican con `smoothscale`.
- **Corte:** la fruta se parte en la dirección en que se movió la luz, se ve el interior
  (gajos, semillas) y salta jugo (`Particula`).
- **Espada de luz:** se dibuja en dos capas que se **suman** a la pantalla (`BLEND_RGB_ADD`).
  Una capa chica se difumina y se agranda para el resplandor, y otra nítida lleva el centro blanco.
- **Fondo:** la cámara se oscurece más en los bordes (viñeta), así la atención va al centro.

## Música y sonidos

Todo el audio lo genera `generar_sonidos.py` (no hace falta correrlo para jugar: los `.wav` ya
están incluidos). Es todo original: no usa grabaciones ni canciones de nadie.

- **Música de fondo** (suena en loop todo el tiempo): una pieza de 16 compases en la escala
  japonesa *miyako-bushi* (Re, Mi♭, Sol, La, Si♭). El **koto** se sintetiza con el método de cuerda
  pulsada *Karplus-Strong*; la **shakuhachi** (flauta) es un tono con vibrato y soplido; hay
  **taiko** (tambor), palillos de madera y un zumbido grave. Todo con reverb, y armada para que al
  repetirse no se note el corte.
- **Menú, intro y finales:** la versión tranquila (`musica_menu.wav`).
- **Durante la partida, música épica que acompaña la dificultad:** 4 versiones (`musica_0.wav` a
  `musica_3.wav`) con la misma melodía de koto y flauta, más un fondo cinematográfico de
  **cuerdas** (acordes en 3 voces apenas desafinadas), **coro** ("aaah", sintetizado con las
  formantes de la vocal A), **o-daiko** (el tambor japonés gigante), **shime-daiko** (tambor chico que
  empuja el ritmo) y un **bajo de cuerdas** cortas. Cuanto más difícil, más rápida y cargada:

  | Versión | Tempo | Desde el nivel | Qué suma |
  |---|---|---|---|
  | 1 | 100 | 1 | cuerdas, o-daiko en los pulsos fuertes, bajo en negras |
  | 2 | 112 | 3 | melodía doblada a la octava, más o-daiko, bajo en corcheas |
  | 3 | 124 | 5 | coro en la segunda mitad, palillos, ritmos más cortados |
  | 4 | 138 | 8 | coro siempre, carreritas de koto, shime en semicorcheas, redobles |

  Se pasa de una a otra con un fundido (`musica.py`), sin cortar el juego.
- **Cuenta regresiva:** el **3** y el **2** son palillos de madera (*hyoshigi*) con un taiko chico
  (el 2 un poco más agudo, para que suba la tensión); el **1** es el más épico: un o-daiko grande con
  un silbido que crece hasta el arranque. Al empezar: o-daiko, gong y un acorde de cuerdas.
- **Cortes de katana:** un silbido de aire (ruido filtrado que sube y baja) más el brillo metálico de
  la hoja, con reverb para que quede sonando hasta apagarse.
