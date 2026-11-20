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
FUENTE_TITULO = "arialblack,impact,arial"
FUENTE = "verdana,arial"

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

# --- Colores (R, G, B) ---
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
AMARILLO = (255, 220, 0)
VERDE = (70, 220, 50)
ROJO = (230, 40, 40)
GRIS_OSCURO = (25, 25, 25)
GRIS = (150, 150, 160)
VERDE_HOJA = (60, 170, 50)
MARRON = (110, 70, 30)
CONTORNO = (20, 15, 30)              # borde oscuro de frutas y bombas (estilo dibujo animado)
# Filtro de color del punto de luz y su estela (1 jugador; se cambia con la tecla C)
COLORES_ESPADA = [
    ("Cian", (0, 220, 255)),
    ("Verde", (60, 255, 90)),
    ("Rosa", (255, 60, 200)),
    ("Rojo", (255, 50, 50)),
    ("Violeta", (170, 90, 255)),
    ("Amarillo", (255, 220, 0)),
]
COLOR_JUGADOR_1 = (80, 200, 255)     # celeste (versus, mitad izquierda)
COLOR_JUGADOR_2 = (255, 140, 40)     # naranja (versus, mitad derecha)
COLOR_FONDO = (10, 10, 35)           # tinte azulado que oscurece la cámara
OSCURIDAD_CENTRO = 130               # 0-255: cuánto se oscurece la cámara en el centro...
OSCURIDAD_BORDE = 225                # ...y en los bordes (viñeta)
CAPA_CARTEL = (10, 10, 35, 200)      # más oscura, para los carteles
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

# --- Intro (lo primero que se ve al abrir el juego) ---
DURACION_INTRO = 5.0       # segundos hasta que pasa sola a la pantalla de inicio
COLORES_INTRO = [(0, 220, 255), (255, 60, 200)]   # color de cada uno de los dos espadazos

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
RADIO_BOMBA_MORTAL = 48
GRAVEDAD_BOMBA_MORTAL = 160  # cae despacio, así molesta un buen rato
VIDAS_AL_TIRAR_BOMBA = 1
