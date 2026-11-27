# Light Fruit Ninja

Obligatorio 2 de Programación 2.

Juego hecho en Python con **pygame** y **OpenCV** donde **la linterna del celular es la espada**.
La cámara de la computadora busca el punto de luz más brillante de la imagen y lo sigue.
Al mover el celular frente a la cámara, la luz deja un rastro, y las frutas que lo cruzan se cortan.
Sin la cámara no se puede jugar: la luz es el único control para cortar.

Repositorio: https://github.com/faaaaaacuu/obligatorio2-programacion2

## Instalación

Se necesita Python 3.9 o más nuevo, una cámara web y una fuente de luz puntual
```bash
pip install -r requirements.txt
```

Eso instala las tres bibliotecas que usa el juego:

- **pygame** (`pip install pygame`): la ventana, el dibujo, los sonidos y el teclado.
- **opencv-python** (`pip install opencv-python`): la cámara y la detección de la luz (solo en `vision.py`).
- **numpy** (`pip install numpy`): la usa `generar_sonidos.py` para sintetizar la música. Para jugar
  no hace falta, porque los `.wav` ya vienen hechos, pero OpenCV la instala igual.

En macOS, la primera vez el sistema pide permiso para usar la cámara
(a la Terminal o a VS Code, según desde dónde se corra).

## Cómo se juega

```bash
python3 main.py
```

El juego arranca en **pantalla completa**. Con **F** se pasa a ventana (y se puede cerrar con la X)
y con **F** de nuevo se vuelve a pantalla completa. Se puede cambiar en `ajustes.py` (`PANTALLA_COMPLETA`).

Al abrirse, el juego muestra una **intro**: pantalla negra, dos espadazos de luz que forman una X
y aparece el título. Dura unos 5 segundos; cualquier tecla la adelanta.

Después viene el **tutorial**. La primera tarjeta, **"Prepará el lugar"**, muestra cómo tiene que
estar el cuarto: una persona con la linterna y una lámpara prendida atrás; la cámara toma la lámpara
como espada (✗), la lámpara se apaga y la cámara encuentra la linterna (✓). Después, las 5 reglas pasan de a una, en tarjetas grandes, al estilo motion
graphics. Cada tarjeta entra desde la derecha con un "zas" de katana, muestra su animación con los
sonidos de lo que pasa (el corte, la bomba, la fruta que cae, el +1 vida, la bomba mortal) y sale por
la izquierda. Con **→** (o ENTER) se pasa a la siguiente, y con **ESPACIO**, **ESC** o el botón
**SALTEAR** (abajo a la derecha) se va directo a la pantalla de inicio. Los tiempos están en
`ajustes.py` (`TUTORIAL_...`).

Después aparece la **pantalla de inicio**, que tiene solo lo necesario para empezar: los dos modos
y si la cámara ve la linterna. Las reglas no se repiten ahí; con **R** se vuelve a ver el tutorial.

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
  está jugando, primero pregunta **"¿Abandonar la partida?"** (**S** sí / **N** no), porque esa
  partida no se guarda.
- **P** pausa y reanuda. La partida también se pausa sola si se minimiza la ventana o se cambia a
  otro programa.

### Se usa como cualquier programa

- **Todo se puede hacer con el mouse.** Cada tecla que aparece dibujada en pantalla es también un
  botón: se ilumina al pasar el mouse por encima (y el puntero se vuelve una manito) y un clic hace
  lo mismo que apretarla. Los paneles de los modos, las piedras de la paleta y las cajas de los
  nombres también se clickean. En la intro y el tutorial, un clic en cualquier lado sigue adelante.
- **ENTER confirma y ESC vuelve**, en todas las pantallas.
- **Cmd+Q** (Mac) o **Ctrl+Q** (Windows/Linux) cierran el juego, igual que la X de la ventana.

### Modo 1 jugador: superar el récord

La partida **no termina hasta que perdés las 3 vidas**. No hay metas en pantalla: la dificultad
sube sola, sin avisar, cada 10 frutas cortadas. Las frutas salen más seguido, más rápido, más chicas
y con más bombas (ver [Dificultad](#dificultad)).

Al perder se muestra cuántas frutas cortaste y se compara con el **récord**. Si lo superaste,
queda guardado como récord nuevo; si no, te dice cuántas te faltaron. Durante la partida, en el
momento en que pasás el récord aparece **"¡NUEVO RÉCORD!"**. El objetivo es superarlo.

### Modo versus (2 jugadores)

Antes de empezar, cada jugador **escribe su nombre** (ENTER para confirmar, ESC para volver).
Al confirmar el del Jugador 1 queda fijo, con un tilde, pero se puede volver a corregir con **←**,
con un clic en su caja o borrando cuando el nombre del Jugador 2 todavía está vacío.
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

**Filtro de color:** el punto de luz y su estela se tiñen de un color. En la pantalla de inicio, la
tecla **C** abre un **abanico japonés** (*sensu*): cada gajo de papel plegado es un color, con su
kanji inclinado como su varilla: oro (金), bermellón (朱), jade (翠), sakura (桜), índigo (藍) y
luna (月). El gajo elegido sobresale y tiene un hilo dorado; lo de atrás se oscurece. Se elige con las
flechas o con un clic, y ENTER lo cierra. En medio de la partida (jugando solo), **C** pasa directo
al color siguiente. En el versus cada jugador tiene el suyo: jade a la izquierda y bermellón
anaranjado a la derecha.

### En qué condiciones funciona mejor

- **Luz:** un ambiente iluminado, con luz suficiente para que la cámara distinga tu forma, pero
  **sin nada más brillante que la linterna**. Si hay algo más brillante, OpenCV lo toma como la
  espada. Es lo primero que explica el tutorial.
- **Fondo:** sin lámparas, ventanas, pantallas ni paredes blancas brillantes detrás del jugador,
  porque la cámara las puede tomar como la linterna (o como su reflejo).
- **Distancia:** lo bastante lejos para que, con el brazo estirado, la linterna llegue a los bordes
  de la imagen. Si la linterna está muy lejos, la mancha queda más chica que `AREA_MINIMA_LUZ` y no
  se detecta; si está muy cerca, la luz llena media imagen y el punto tiembla.
- La linterna tiene que **apuntar a la cámara**: de costado brilla mucho menos.
- Si algo falla, la tecla **M** muestra lo que la cámara está tomando como luz, y con **+** / **-**
  se ajusta el umbral.

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

Después del nivel 5, la función `reglas_de_nivel` (en `partida.py`) hace cada nivel un poco más
difícil que el anterior: más gravedad, menos espera entre frutas, frutas más chicas y más bombas.
Tiene **topes** (`TOPE_...` en `ajustes.py`) para que nunca se vuelva imposible.

Se sube de nivel cada 10 frutas jugando solo, y cada 20 segundos en el versus
(`FRUTAS_POR_NIVEL` y `SEGUNDOS_POR_NIVEL`). Nunca aparece un cartel de "nivel": se nota en el juego.

## Resultados guardados

El récord y las partidas del versus se guardan en `resultados.json`, en la carpeta del juego
(se crea solo la primera vez). Lo maneja `partida.py` (las funciones `cargar_resultados`, `registrar_puntaje` y `registrar_versus`). Para borrar todo, alcanza con
borrar ese archivo.

## Controles

| Tecla           | Acción                                                     |
|-----------------|------------------------------------------------------------|
| 1               | Empezar en modo 1 jugador                                  |
| 2               | Empezar en modo versus                                     |
| ESPACIO / ENTER | Volver a jugar el mismo modo                               |
| P               | Pausar / seguir la partida                                 |
| S / N           | Al abandonar una partida: sí / no                          |
| + / -           | Subir / bajar el umbral de brillo de la detección          |
| M               | Mostrar / ocultar lo que la cámara está tomando como "luz" |
| C               | Paleta de colores de la luz (en la partida: color siguiente) |
| F               | Pantalla completa / ventana                                |
| → / ENTER       | En el tutorial: pasar a la siguiente tarjeta               |
| R               | En la pantalla de inicio: volver a ver el tutorial         |
| ESPACIO         | En la intro y el tutorial: saltearlos                      |
| ESC             | Volver a la pantalla de inicio (en la pantalla de inicio: salir) |
| Botón INICIO    | Volver a la pantalla de inicio con un clic (arriba a la izquierda) |
| La X / Cmd+Q / Ctrl+Q | Cerrar el juego                                      |
| Mouse           | Clic en cualquier tecla dibujada hace lo mismo que apretarla |

Si el juego detecta otras cosas como si fueran la linterna (lámparas, ventanas, la pantalla),
hay que subir el umbral con **+**. Si no detecta la linterna, hay que bajarlo con **-**.
La tecla **M** muestra un recuadro abajo a la derecha con lo que se está detectando.

## Archivos

| Archivo              | Qué tiene                                                                 |
|----------------------|---------------------------------------------------------------------------|
| `main.py`            | El bucle principal (eventos, actualizar, dibujar, `reloj.tick`), la carga de sonidos y fuentes, y la música de fondo (clase `Musica`, que cambia de versión según la dificultad, con fundido) |
| `partida.py`         | La partida: cómo empieza, cómo avanza cada cuadro, cómo termina, lo que se dibuja encima (puntos, vidas, pausa, finales) y el récord y el historial guardados en `resultados.json` |
| `jugador.py`         | La clase `Jugador`: su luz, su rastro, sus frutas, sus vidas y la bomba mortal |
| `objetos.py`         | Las clases `Fruta`, `BombaMortal`, `Pedazo`, `Particula` y `TextoFlotante` |
| `vision.py`          | Todo lo de OpenCV: abrir la cámara, leer el cuadro y detectar la luz      |
| `inicio.py`          | La intro, la pantalla de inicio, los nombres del versus y el abanico de colores |
| `tarjetas.py`        | Las tarjetas con las reglas (y sus animaciones) y el tutorial            |
| `graficos.py`        | Los dibujos: frutas, bombas y la espada de luz                            |
| `interfaz.py`        | Textos, teclas dibujadas (que también son botones), paneles, faroles y sello |
| `ajustes.py`         | Constantes: colores, frutas de cada jugador, tamaños, velocidades, niveles y rangos de detección |
| `generar_sonidos.py` | Script que compuso la música y los efectos `.wav` (no hace falta correrlo para jugar) |
| `instrumentos.py`    | Los instrumentos sintetizados que usa `generar_sonidos.py` (koto, taiko, katana, coro...) |
| `fuentes/`           | Tipografías Shojumaru, Inter y Potta One, con sus licencias (OFL)        |
| `sonidos/`           | Efectos de sonido y las versiones de la música de fondo                   |

El código está repartido por tema en archivos chicos (entre 250 y 510 líneas, salvo `vision.py`, que la letra pide que esté aparte), para que cada
uno se pueda leer y explicar por separado.

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
licencia al lado), así el juego se ve igual en cualquier compu: **Shojumaru**, con trazo de pincel
japonés, solo para el título y los momentos grandes; **Inter**, una letra limpia pensada para
pantallas, para todos los demás textos; y **Potta One** solo para los kanji (Inter no los tiene).

Los textos no llevan contorno: tienen una sombra suave debajo (`SOMBRA_TEXTO` en `ajustes.py`), que
alcanza para leerlos sobre la cámara oscurecida. Los paneles tienen un solo filete dorado, fino, y
las teclas dibujadas no tienen borde negro: el costado es el mismo color, más oscuro.

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

  Se pasa de una a otra con un fundido (clase `Musica` en `main.py`), sin cortar el juego.
- **Cuenta regresiva:** el **3** y el **2** son palillos de madera (*hyoshigi*) con un taiko chico
  (el 2 un poco más agudo, para que suba la tensión); el **1** es el más épico: un o-daiko grande con
  un silbido que crece hasta el arranque. Al empezar: o-daiko, gong y un acorde de cuerdas.
- **Cortes de katana:** un silbido de aire (ruido filtrado que sube y baja) más el brillo metálico de
  la hoja, con reverb para que quede sonando hasta apagarse. Hay **5 versiones** (`corte_0.wav` …
  `corte_4.wav`): más cortas o largas, más agudas o graves, con más aire o más metal. Cada corte
  suena una al azar, pero nunca la misma dos veces seguidas (clase `SonidoVariado` en `main.py`),
  así no se vuelve repetitivo.
- **Ganar (versus):** los dos espadazos de la intro, el koto que sube rapidísimo por la escala
  *yo* (la japonesa alegre: Re, Mi, Sol, La, Si) y al llegar arriba un o-daiko, un gong y un
  acorde de koto con la shakuhachi encima.
- **Perder:** el samurái **guarda la katana** (el raspado de la hoja entrando en la vaina y el
  "¡chin!" de la guarda al cerrar) y después la shakuhachi baja triste por la *miyako-bushi* con el
  koto, sobre un taiko y un gong suaves.
- **Bomba:** la katana pega contra el hierro ("¡clang!" de metal grave), revienta la pólvora y
  retumba un taiko.
- **Fruta que se cae:** un golpe seco contra el tatami y el koto que baja medio tono, como un "uy".
- **Nuevo récord** (y cuando aparece el título en la intro): la campana **rin** de los templos (un
  cuenco de metal cuyas frecuencias "laten") con el koto subiendo Re, La, Re.
- **+1 vida:** el koto sube rapidito y lo cierra un **furin** (la campanita de vidrio de las
  ventanas japonesas).
- **Sello de la intro:** el golpe de madera del *hanko* (sello japonés) sobre el papel, con un taiko.
- **Lanzar la bomba mortal:** un shime-daiko que redobla cada vez más rápido mientras sube el
  silbido, y un palillazo al soltarla.
- **Bomba mortal:** un **kiai** (el grito de las artes marciales, "¡iyaaah!") con un espadazo, y al
  caer el golpe un o-daiko enorme, la explosión y un gong que queda retumbando. El grito es una voz
  sintetizada: armónicos de una nota grave filtrados por las formantes de las vocales, pasando de
  la "i" a la "a", con la nota que sube de golpe y cae, más ronquera y aire.

## Origen y licencia de los recursos

- **Sonidos y música:** son propios, generados por código con `generar_sonidos.py`. No usan
  grabaciones ni muestras de nadie.
- **Gráficos:** propios, dibujados con pygame en `graficos.py`. El juego no carga imágenes de archivos.
- **Tipografías:** no son propias. Tienen licencia libre SIL Open Font License 1.1, y el texto de cada licencia está al lado de la fuente, en la carpeta `fuentes/`:
  - **Shojumaru**, de Brian J. Bonislawsky (Astigmatic), 2012 (`fuentes/OFL-Shojumaru.txt`).
  - **Potta One**, de The Potta Project Authors, 2020, https://github.com/go108go/Potta (`fuentes/OFL-PottaOne.txt`).
  - **Inter** (Medium y SemiBold), de The Inter Project Authors, 2016-2023, https://github.com/rsms/inter (`fuentes/OFL-Inter.txt`).

## Uso de inteligencia artificial

Usé **Claude** (Anthropic) como asistente durante el desarrollo:

- **Programación:** para escribir y corregir partes del código (la detección de la luz en `vision.py`,
  la física de las frutas, el modo versus, la detección del círculo de la bomba mortal) y para
  buscar errores.
- **Sonido:** para armar `generar_sonidos.py`, el script que sintetiza los efectos y la música.
- **Documentación:** para redactar y ordenar este README, agregar docstrings y pasar las constantes
  a `ajustes.py`.

### Cómo dirigí la herramienta

Trabajé de a un cambio por vez. En cada prompt le daba a Claude el contexto del juego, le planteaba
el problema que veía al probarlo y le decía qué solución quería, con los límites que tenía que
respetar. Después probaba el resultado y seguía con lo siguiente. Estos son tres ejemplos (ordenados
y redactados a partir de lo que le pedí):

> **Contexto:** es un juego en pygame y OpenCV donde se cortan frutas con la luz del celular. La
> pantalla de inicio muestra las 5 reglas en tarjetas animadas, todas juntas.
> **Problema:** es mucha información de golpe y nadie las lee.
> **Solución:** que al abrir el juego, después de la intro, las tarjetas pasen de a una, grandes, al
estilo motion graphics, con los efectos de sonido del juego en el momento en que pasa cada cosa. Se tiene que poder pasar a la siguiente o saltear todo, y la pantalla de inicio tiene que quedar solo con lo necesario para empezar.

> **Contexto:** el juego se maneja solo con teclas que hay que saber de antemano.
> **Problema:** alguien que lo abre por primera vez no sabe qué hacer, y si aprieta ESC sin querer pierde la partida.
> **Solución:** que funcione como cualquier programa. Cada tecla que aparece en pantalla tiene que ser también un botón que se pueda clickear, la partida se tiene que pausar con P o al cambiar de ventana, tiene que preguntar antes de abandonar una partida y Cmd+Q / Ctrl+Q tienen que cerrarlo.

> **Contexto:** `main.py` tiene más de 900 líneas y en la defensa tengo que explicar el código.
> **Problema:** así es difícil de leer y de explicar.
> **Solución:** repartir el código por tema en archivos de entre 300 y 500 líneas, sin cambiar lo que hace el juego, con todo lo de OpenCV en `vision.py` como pide la letra, y comprobar que no quede ningún import roto.

Referencia (APA):

Claude. (2026). *Prompts utilizados para la programación, los sonidos y la documentación del juego
Light Fruit Ninja* [Generación de código y texto]. Recuperado de https://claude.ai
