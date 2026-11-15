"""Constantes del juego: colores, tamaños, velocidades y rangos de detección.

Para cambiar la dificultad o la detección alcanza con tocar este archivo.
"""

# --- Ventana ---
ANCHO = 960
ALTO = 540
FPS = 30
TITULO = "Corte de Luz"
PANTALLA_COMPLETA = True   # el juego se agranda a toda la pantalla (tecla F para cambiar)

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
TOLERANCIA_SIN_LUZ = 0.6   # segundos sin ver la luz antes de pausar el juego

# --- Colores (R, G, B) ---
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
AMARILLO = (255, 220, 0)
VERDE = (70, 220, 50)
ROJO = (230, 40, 40)
GRIS_OSCURO = (25, 25, 25)
GRIS = (150, 150, 160)
VERDE_HOJA = (30, 130, 30)
COLOR_RASTRO = (190, 240, 255)       # rastro de la luz en el modo de 1 jugador
COLOR_JUGADOR_1 = (80, 200, 255)     # celeste (versus, mitad izquierda)
COLOR_JUGADOR_2 = (255, 140, 40)     # naranja (versus, mitad derecha)
CAPA_OSCURA = (10, 10, 35, 150)      # capa semitransparente sobre la cámara
CAPA_CARTEL = (10, 10, 35, 210)      # más oscura, para los carteles
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
VIDAS = 3                  # las vidas se recargan al empezar cada nivel
DURACION_CARTEL = 2.5      # segundos que se muestra "NIVEL X" antes de empezar
DURACION_MENSAJE = 0.6     # segundos que se ve un mensaje como "+1" o "BOMBA!"
DURACION_DESTELLO = 0.25   # segundos que la pantalla queda roja al cortar una bomba

# --- Frutas ---
ALTURA_MINIMA = 0.65       # hasta dónde suben las frutas, como fracción del alto de la pantalla
ALTURA_MAXIMA = 0.85
VELOCIDAD_LATERAL = (15, 70)   # píxeles por segundo hacia el centro (mín, máx)
GIRO_PEDAZOS = 130         # velocidad con la que se separan las dos mitades al cortar

# --- La espada de luz ---
LARGO_RASTRO = 12          # cuántas posiciones de la luz se dibujan en el rastro
GROSOR_RASTRO = 10
RADIO_LUZ = 12
MARGEN_CORTE = 10          # píxeles extra alrededor de la fruta que también cuentan como corte
MOVIMIENTO_MINIMO = 6      # la luz tiene que moverse al menos esto en un cuadro para cortar

# Cada nivel es un diccionario con sus reglas. Para hacerlo más fácil o más
# difícil, o para agregar niveles, solo hay que tocar esta lista.
#   meta:       frutas que hay que cortar para pasar de nivel
#   max_frutas: cuántas frutas puede haber en pantalla a la vez
#   radio:      tamaño de las frutas (mín, máx) en píxeles
#   espera:     segundos entre una fruta y la siguiente (mín, máx)
#   gravedad:   más alto = suben y caen más rápido (píxeles por segundo al cuadrado)
#   bombas:     probabilidad de que salga una bomba (0.2 = 20 %)
NIVELES = [
    {"meta": 8,  "max_frutas": 3, "radio": (45, 64), "espera": (1.5, 2.2), "gravedad": 110, "bombas": 0.00},
    {"meta": 10, "max_frutas": 3, "radio": (41, 60), "espera": (1.2, 1.9), "gravedad": 150, "bombas": 0.10},
    {"meta": 12, "max_frutas": 4, "radio": (38, 54), "espera": (1.0, 1.6), "gravedad": 200, "bombas": 0.15},
    {"meta": 14, "max_frutas": 5, "radio": (34, 49), "espera": (0.8, 1.3), "gravedad": 270, "bombas": 0.18},
    {"meta": 16, "max_frutas": 6, "radio": (30, 44), "espera": (0.6, 1.1), "gravedad": 360, "bombas": 0.22},
]

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

# Versus (2 jugadores, pantalla dividida): cada uno corta en su mitad.
# Gana el primero que llega a la meta, o el que sobrevive si el otro se queda sin vidas.
REGLAS_VERSUS = {"meta": 15, "max_frutas": 3, "radio": (34, 50), "espera": (1.0, 1.6),
                 "gravedad": 200, "bombas": 0.15}
