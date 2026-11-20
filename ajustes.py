"""Constantes del juego: colores, tamaños, velocidades y rangos de detección.

Para cambiar la dificultad o la detección alcanza con tocar este archivo.
"""

# --- Ventana ---
ANCHO = 960
ALTO = 540
FPS = 30
TITULO = "Corte de Luz"
PANTALLA_COMPLETA = True   # el juego se agranda a toda la pantalla (tecla F para cambiar)
# Fuentes que se prueban en orden (si no está ninguna, pygame usa la suya)
# Estética: dojo japonés de noche, minimalista. Las fuentes vienen con el juego
# (carpeta fuentes/, licencia libre OFL), así se ven igual en cualquier compu:
#   Shojumaru: títulos, con trazo de pincel japonés
#   Potta One: textos y el kanji del sello
ARCHIVO_FUENTE_TITULO = "fuentes/Shojumaru-Regular.ttf"
ARCHIVO_FUENTE_TEXTO = "fuentes/PottaOne-Regular.ttf"
FUENTE_RESPALDO = "verdana,arial"   # por si falta el archivo de alguna fuente
KANJI = "光"                         # "luz", para el sello rojo

# --- Cámara y detección de la linterna ---
INDICE_CAMARA = 0
ANCHO_CAMARA = 1280        # resolución que se le pide a la cámara
ALTO_CAMARA = 720
UMBRAL_BRILLO = 235        # 0-255: qué tan brillante tiene que ser un píxel para contar como luz
UMBRAL_MINIMO = 150        # rango en el que se puede mover el umbral con + y -
UMBRAL_MAXIMO = 254
PASO_UMBRAL = 5
DESENFOQUE = 11            # tamaño del desenfoque (impar) para sacar ruido antes de detectar
AREA_MINIMA_LUZ = 25       # área mínima (píxeles) de la mancha de luz, para ignorar reflejos chicos
TOLERANCIA_SIN_LUZ = 2.0   # segundos sin ver la luz antes de darla por perdida (aviso y pausa)
HUECO_MAXIMO_CORTE = 0.12  # si la luz desaparece menos que esto (unos 3 cuadros), el corte sigue de donde estaba
# Velocidad máxima (píxeles por segundo) a la que una mano puede mover la luz. Si la luz
# "salta" más rápido que esto, es un reflejo (por ejemplo en una pared blanca) y no cuenta.
# Ej.: del centro a la esquina de arriba a la izquierda son ~550 px; en 0.2 s serían
# ~2750 px/s: imposible. Cruzar media pantalla en 0.25 s (~1900 px/s) sí vale.
VELOCIDAD_MAXIMA_LUZ = 2500

# --- Colores (R, G, B): laca negra, papel, bermellón y dorado ---
BLANCO = (242, 234, 216)             # "blanco papel" (washi), un poco cálido
NEGRO = (0, 0, 0)
AMARILLO = (222, 184, 96)            # dorado
VERDE = (130, 205, 140)              # verde jade suave
ROJO = (205, 55, 45)                 # bermellón
GRIS_OSCURO = (30, 26, 28)
GRIS = (150, 140, 128)               # gris cálido
LACA = (16, 13, 16)                  # negro laca de los paneles
MADERA = (52, 34, 24)                # madera oscura (marco del shoji)
MADERA_CLARA = (150, 110, 70)        # madera de la reja del shoji
ROJO_FAROL = (200, 50, 40)           # papel rojo de los faroles
LUZ_FAROL = (255, 170, 90)           # resplandor cálido de los faroles
VERDE_HOJA = (60, 170, 50)
MARRON = (110, 70, 30)
CONTORNO = (14, 10, 12)              # borde oscuro de frutas, bombas y textos (como tinta)
# Filtro de color del punto de luz y su estela (1 jugador; se cambia con la tecla C)
COLORES_ESPADA = [
    ("Oro", (240, 195, 90)),
    ("Bermellón", (240, 70, 50)),
    ("Jade", (80, 220, 170)),
    ("Sakura", (245, 150, 195)),
    ("Índigo", (110, 130, 240)),
    ("Luna", (225, 230, 245)),
]
COLOR_JUGADOR_1 = (80, 215, 180)     # jade (versus, mitad izquierda)
COLOR_JUGADOR_2 = (240, 120, 60)     # bermellón anaranjado (versus, mitad derecha)
COLOR_FONDO = (12, 11, 24)           # índigo de noche que oscurece la cámara
OSCURIDAD_CENTRO = 140               # 0-255: cuánto se oscurece la cámara en el centro...
OSCURIDAD_BORDE = 230                # ...y en los bordes (viñeta)
CAPA_CARTEL = (10, 9, 16, 215)       # más oscura, para los carteles
# Reja del shoji (panel de papel japonés) que se ve sobre la cámara
SHOJI_COLUMNAS = 8
SHOJI_FILAS = 5
OPACIDAD_SHOJI = 45                  # 0-255: qué tan marcada se ve la reja (poco, para no molestar)
COLOR_BOMBA_MORTAL = (180, 70, 255)  # violeta

# Cada jugador tiene sus propias frutas, así en el versus se distinguen de un vistazo.
#   tipo:  cómo se dibuja
#   color: color de la cáscara
#   pulpa: color de adentro (se ve al cortarla)
FRUTAS_JUGADOR_1 = [
    {"tipo": "manzana", "color": (220, 30, 40),  "pulpa": (255, 245, 200)},
    {"tipo": "naranja", "color": (255, 140, 0),  "pulpa": (255, 195, 90)},
    {"tipo": "sandia",  "color": (40, 150, 50),  "pulpa": (240, 60, 80)},
]
FRUTAS_JUGADOR_2 = [
    {"tipo": "uva",     "color": (130, 50, 170), "pulpa": (200, 230, 150)},
    {"tipo": "kiwi",    "color": (140, 100, 50), "pulpa": (120, 200, 60)},
    {"tipo": "limon",   "color": (250, 230, 40), "pulpa": (255, 250, 180)},
]

# --- Partida ---
VIDAS = 3                  # para toda la partida
DURACION_CARTEL = 3        # segundos de cuenta regresiva antes de empezar
DURACION_MENSAJE = 0.6     # segundos que se ve un mensaje como "+1" o "BOMBA!"
DURACION_DESTELLO = 0.25   # segundos que la pantalla queda roja al cortar una bomba
FRUTAS_PARA_VIDA = 3       # frutas cortadas en un solo trazo para ganar una vida (si tenés menos de 3)
GIRO_MAXIMO_TRAZO = 90     # grados: si la luz dobla más que esto de golpe, empieza otro trazo

# --- Frutas ---
ALTURA_MINIMA = 0.65       # hasta dónde suben las frutas, como fracción del alto de la pantalla
ALTURA_MAXIMA = 0.85
VELOCIDAD_LATERAL = (15, 70)   # píxeles por segundo hacia el centro (mín, máx)
VELOCIDAD_GIRO = (40, 160) # grados por segundo que giran las frutas mientras vuelan
SEPARACION_PEDAZOS = 130   # velocidad con la que se separan las dos mitades al cortar

# --- Partículas (jugo y explosiones) ---
GOTAS_POR_CORTE = 14
CHISPAS_POR_BOMBA = 30
GRAVEDAD_PARTICULAS = 700
DURACION_TEXTO_FLOTANTE = 0.7   # segundos que se ve el "+1" que sube desde la fruta
DESENFOQUE_BRILLO = 3      # cuánto se difumina el resplandor de la espada de luz

# --- Sonido ---
CANALES_DE_AUDIO = 32      # cuántos sonidos pueden sonar a la vez
# Música de fondo (la compone generar_sonidos.py). La primera es la tranquila del
# menú; las otras 4 son las épicas de la partida, cada una más rápida y cargada.
ARCHIVOS_MUSICA = ["sonidos/musica_menu.wav"] + [f"sonidos/musica_{i}.wav" for i in range(4)]
NIVEL_MINIMO_MUSICA = [0, 2, 4, 7]   # desde qué nivel de dificultad suena cada versión épica
VOLUMEN_MUSICA = 0.35      # de 0 a 1: más baja que los efectos, para que no tape los cortes
FUNDIDO_MUSICA_MS = 1500   # milisegundos que tarda en pasar de una versión a otra

# --- Botón para volver a la pantalla de inicio (también con ESC) ---
BOTON_INICIO = (90, 14, 150, 40)     # x, y, ancho, alto (arriba a la izquierda, al lado del farol)

# --- Intro (lo primero que se ve al abrir el juego) ---
DURACION_INTRO = 5.0       # segundos hasta que pasa sola a la pantalla de inicio
COLORES_INTRO = [(240, 195, 90), (240, 70, 50)]   # color de cada espadazo: oro y bermellón

# --- Pantalla de inicio: tarjetas con las reglas y su animación ---
TARJETA_ANCHO = 172
TARJETA_ALTO = 218
TARJETA_ANIMACION_ALTO = 108   # alto de la parte de la tarjeta donde va la animación
SEPARACION_TARJETAS = 12
Y_TARJETAS = 106
RADIO_FRUTA_DEMO = 20          # tamaño de las frutas en las animaciones
DESFASE_TARJETAS = 0.7         # segundos de diferencia entre la animación de una tarjeta y la siguiente

# --- La espada de luz ---
LARGO_RASTRO = 12          # cuántas posiciones de la luz se dibujan en el rastro
GROSOR_RASTRO = 10
RADIO_LUZ = 12
MARGEN_CORTE = 10          # píxeles extra alrededor de la fruta que también cuentan como corte
MOVIMIENTO_MINIMO = 6      # la luz tiene que moverse al menos esto en un cuadro para cortar

# --- Dificultad ---
# El juego no termina hasta que perdés. La dificultad sube sola, sin avisar:
#   1 jugador: cada FRUTAS_POR_NIVEL frutas cortadas se pasa al nivel siguiente.
#   Versus:    cada SEGUNDOS_POR_NIVEL segundos (igual para los dos jugadores).
FRUTAS_POR_NIVEL = 10
SEGUNDOS_POR_NIVEL = 20
NIVEL_INICIAL_VERSUS = 1

# Los primeros niveles están armados a mano. Para hacerlo más fácil o más difícil
# alcanza con tocar esta lista.
#   max_frutas: cuántas frutas puede haber en pantalla a la vez
#   radio:      tamaño de las frutas (mín, máx) en píxeles
#   espera:     segundos entre una fruta y la siguiente (mín, máx)
#   gravedad:   más alto = suben y caen más rápido (píxeles por segundo al cuadrado)
#   bombas:     probabilidad de que salga una bomba (0.2 = 20 %)
NIVELES = [
    {"max_frutas": 3, "radio": (45, 64), "espera": (1.5, 2.2), "gravedad": 110, "bombas": 0.00},
    {"max_frutas": 3, "radio": (41, 60), "espera": (1.2, 1.9), "gravedad": 150, "bombas": 0.10},
    {"max_frutas": 4, "radio": (38, 54), "espera": (1.0, 1.6), "gravedad": 200, "bombas": 0.15},
    {"max_frutas": 5, "radio": (34, 49), "espera": (0.8, 1.3), "gravedad": 270, "bombas": 0.18},
    {"max_frutas": 6, "radio": (30, 44), "espera": (0.6, 1.1), "gravedad": 360, "bombas": 0.22},
]
# Después del último nivel de la lista, cada nivel nuevo es un poco más difícil
# que el anterior, pero sin pasar estos topes (si no, sería imposible).
AUMENTO_GRAVEDAD = 1.06    # cada nivel extra, la gravedad se multiplica por esto
ACHIQUE_ESPERA = 0.93      # y la espera entre frutas por esto
AUMENTO_BOMBAS = 0.02
TOPE_GRAVEDAD = 650
TOPE_ESPERA = (0.3, 0.5)
TOPE_BOMBAS = 0.35
TOPE_MAX_FRUTAS = 8
RADIO_MINIMO = 26
# En el versus cada jugador tiene media pantalla: las frutas son más chicas
# (este número multiplica su tamaño) para que se pueda controlar la situación.
ESCALA_FRUTAS_VERSUS = 0.7
# Las frutas y sus restos no pasan al campo del otro jugador: rebotan contra el
# borde de su zona y conservan esta parte de la velocidad (0.5 = la mitad).
REBOTE_EN_EL_BORDE = 0.5

# --- Resultados guardados ---
ARCHIVO_RESULTADOS = "resultados.json"   # récord y partidas del versus
PARTIDAS_EN_PANTALLA = 5   # cuántas partidas del versus se muestran al terminar
LARGO_MAXIMO_NOMBRE = 12

# --- Bomba mortal (solo en el versus) ---
# Girando la linterna en círculos se carga una bola; al completarla se convierte
# en una bomba que aparece en la mitad del rival. Si el rival la corta, pierde.
# Se puede usar una sola vez por partida y el que la tira queda con 1 vida.
VENTANA_CIRCULO = 60       # cuántas posiciones recientes de la luz se miran (unos 2 segundos)
VUELTAS_PARA_BOMBA = 1.5   # vueltas seguidas que hay que dar para completar la bola
MOVIMIENTO_MINIMO_GIRO = 5 # píxeles: movimientos más chicos no cuentan (temblor de la mano)
GIRO_MAXIMO_POR_PASO = 60  # grados: si la luz dobla más de golpe es un corte, no un círculo
RADIO_BOLA = 40            # tamaño de la bola cuando está completa
RADIO_BOMBA_MORTAL = 38
GRAVEDAD_BOMBA_MORTAL = 160  # cae despacio, así molesta un buen rato
VIDAS_AL_TIRAR_BOMBA = 1
