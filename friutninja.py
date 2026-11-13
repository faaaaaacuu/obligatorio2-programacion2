"""Fruit Ninja controlado con el flash (linterna) del celular usando OpenCV.

Controles:
  ESPACIO  empezar / volver a jugar
  + / -    subir / bajar el umbral de brillo (si detecta cosas de mas o de menos)
  M        mostrar / ocultar lo que la camara ve como "luz"
  Q / ESC  salir

Prende la linterna del celular, apuntala a la camara y movela como una
espada. Cada fruta que cruza el rastro de la luz suma puntos; las bombas
quitan una vida.

El juego tiene 5 niveles. En cada nivel hay que cortar una cantidad de
frutas para pasar al siguiente. Cada nivel es un poco mas dificil:
mas frutas a la vez, mas chicas, mas rapidas y con mas bombas.
"""

import math
import random
import time

import cv2
import numpy as np


VENTANA = "FRUIT NINJA - FLASH"
INDICE_CAMARA = 0
UMBRAL_BRILLO = 235        # 0-255: que tan brillante tiene que ser un pixel para contar como flash
AREA_MINIMA_FLASH = 30     # area minima (pixeles) de la mancha de luz, para ignorar reflejos chicos
VIDAS_INICIALES = 3        # las vidas se recargan al empezar cada nivel
DURACION_CARTEL = 2.5      # segundos que se muestra el cartel "NIVEL X" antes de empezar
ALTURA_MIN = 0.65          # hasta donde suben las frutas, como fraccion del alto de la pantalla
ALTURA_MAX = 0.85          # (0.85 = llegan casi arriba de todo)

# Cada nivel es un diccionario con sus reglas. Para hacerlo mas facil o mas
# dificil, o para agregar niveles, solo hay que tocar esta lista.
#   meta:       frutas que hay que cortar para pasar de nivel
#   max_frutas: cuantas frutas puede haber en pantalla a la vez
#   radio:      tamano de las frutas (min, max) en pixeles
#   espera:     segundos entre una fruta y la siguiente (min, max)
#   gravedad:   mas alto = suben y caen mas rapido
#   bombas:     probabilidad de que salga una bomba (0.2 = 20%)
NIVELES = [
    {"meta": 8,  "max_frutas": 3, "radio": (60, 85), "espera": (1.5, 2.2), "gravedad": 450, "bombas": 0.00},
    {"meta": 10, "max_frutas": 3, "radio": (55, 80), "espera": (1.2, 1.9), "gravedad": 500, "bombas": 0.10},
    {"meta": 12, "max_frutas": 4, "radio": (50, 72), "espera": (1.0, 1.6), "gravedad": 560, "bombas": 0.15},
    {"meta": 14, "max_frutas": 5, "radio": (45, 65), "espera": (0.8, 1.3), "gravedad": 640, "bombas": 0.18},
    {"meta": 16, "max_frutas": 6, "radio": (40, 58), "espera": (0.6, 1.1), "gravedad": 720, "bombas": 0.22},
]

COLORES_FRUTAS = [
    (40, 180, 255),   # naranja
    (60, 220, 60),    # manzana verde
    (220, 80, 220),   # ciruela
    (40, 80, 240),    # manzana roja
    (255, 180, 40),   # banana
]
BLANCO = (255, 255, 255)
ROJO = (40, 40, 230)
VERDE = (50, 220, 70)
AMARILLO = (0, 220, 255)


def texto(img, mensaje, posicion, escala=0.8, color=BLANCO, grosor=2, centrado=False):
    fuente = cv2.FONT_HERSHEY_DUPLEX
    (ancho, alto), _ = cv2.getTextSize(mensaje, fuente, escala, grosor)
    x, y = posicion
    if centrado:
        x -= ancho // 2
        y += alto // 2
    cv2.putText(img, mensaje, (x, y), fuente, escala, (0, 0, 0),
                grosor + 5, cv2.LINE_AA)
    cv2.putText(img, mensaje, (x, y), fuente, escala, color, grosor, cv2.LINE_AA)


def oscurecer(frame, w, h):
    """Pone una capa oscura sobre la imagen para que se lean los carteles."""
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (10, 10, 35), -1)
    return cv2.addWeighted(overlay, 0.72, frame, 0.28, 0)


def distancia_punto_segmento(punto, inicio, fin):
    segmento = np.array(fin, dtype=np.float32) - inicio
    largo = float(np.dot(segmento, segmento))
    if largo == 0:
        return float(np.linalg.norm(np.array(punto) - inicio))
    t = np.clip(np.dot(np.array(punto) - inicio, segmento) / largo, 0, 1)
    proyeccion = inicio + t * segmento
    return float(np.linalg.norm(np.array(punto) - proyeccion))


class Fruta:
    def __init__(self, x, y, radio, color, w, h, gravedad, bomba=False):
        self.x, self.y = float(x), float(y)
        self.radio = radio
        self.color = color
        self.bomba = bomba
        self.gravedad = gravedad
        # Elijo hasta que altura sube y calculo la velocidad justa para llegar ahi
        # (v = raiz(2 * g * altura)). Despues la gravedad la hace caer.
        punto_mas_alto = h * (1 - random.uniform(ALTURA_MIN, ALTURA_MAX))
        subida = self.y - punto_mas_alto
        self.vy = -math.sqrt(2 * gravedad * subida)
        # Se mueve un poco de costado, siempre hacia el centro para no salirse.
        self.vx = random.uniform(20, 90) * (1 if self.x < w / 2 else -1)
        self.giro = random.uniform(0, math.tau)
        self.cortada = False

    def actualizar(self, dt):
        self.vy += self.gravedad * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.giro += dt * 5

    def dibujar(self, imagen):
        centro = (int(self.x), int(self.y))
        if self.bomba:
            cv2.circle(imagen, centro, self.radio, (25, 25, 25), -1)
            cv2.circle(imagen, centro, self.radio, BLANCO, 2)
            cruz = self.radio // 3
            cv2.line(imagen, (centro[0] - cruz, centro[1] - cruz),
                     (centro[0] + cruz, centro[1] + cruz), ROJO, 6)
            cv2.line(imagen, (centro[0] + cruz, centro[1] - cruz),
                     (centro[0] - cruz, centro[1] + cruz), ROJO, 6)
            cv2.line(imagen, (centro[0] + 10, centro[1] - self.radio + 4),
                     (centro[0] + 25, centro[1] - self.radio - 18), AMARILLO, 5)
            return

        cv2.circle(imagen, centro, self.radio, self.color, -1)
        cv2.circle(imagen, centro, self.radio, BLANCO, 2)
        cv2.ellipse(imagen, (centro[0] - self.radio // 3, centro[1] - self.radio // 3),
                    (self.radio // 5, self.radio // 8), -30, 0, 360, BLANCO, -1)
        cv2.ellipse(imagen, (centro[0], centro[1] - self.radio - 5),
                    (self.radio // 3, self.radio // 7), 25, 0, 360, (30, 130, 30), -1)


def crear_fruta(w, h, reglas):
    """Crea una fruta (o bomba) con las reglas del nivel actual."""
    radio = random.randint(*reglas["radio"])
    return Fruta(
        random.randint(int(w * 0.15), int(w * 0.85)),
        h + radio,
        radio,
        random.choice(COLORES_FRUTAS),
        w, h,
        reglas["gravedad"],
        bomba=random.random() < reglas["bombas"],
    )


def detectar_flash(imagen, umbral):
    """Busca la mancha de luz mas grande (el flash del celular).
    Devuelve (punto, mascara): punto es (x, y) o None si no hay luz."""
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    gris = cv2.GaussianBlur(gris, (11, 11), 0)
    _, mascara = cv2.threshold(gris, umbral, 255, cv2.THRESH_BINARY)
    # erosionar y dilatar borra puntitos sueltos (reflejos chicos)
    mascara = cv2.erode(mascara, None, iterations=1)
    mascara = cv2.dilate(mascara, None, iterations=2)

    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contornos:
        return None, mascara
    mayor = max(contornos, key=cv2.contourArea)
    if cv2.contourArea(mayor) < AREA_MINIMA_FLASH:
        return None, mascara
    momentos = cv2.moments(mayor)
    if momentos["m00"] == 0:
        return None, mascara
    centro = (int(momentos["m10"] / momentos["m00"]), int(momentos["m01"] / momentos["m00"]))
    return centro, mascara


def main():
    cap = cv2.VideoCapture(INDICE_CAMARA)
    if not cap.isOpened():
        raise SystemExit("No se pudo abrir la camara. Revisa sus permisos.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cv2.namedWindow(VENTANA, cv2.WINDOW_NORMAL)

    umbral = UMBRAL_BRILLO
    ver_mascara = False
    # Estados: "menu" -> "cartel" (NIVEL X) -> "jugando" -> "cartel" ... -> "ganaste"
    #          y si se acaban las vidas -> "fin"
    estado = "menu"
    nivel = 0                  # indice en la lista NIVELES (0 = nivel 1)
    frutas = []
    rastro = []
    dedos_previos = []
    puntuacion = 0             # puntos totales de la partida
    cortadas = 0               # frutas cortadas en el nivel actual
    vidas = VIDAS_INICIALES
    cartel_hasta = 0.0
    ultimo_spawn = 0.0
    espera = 0.5
    mensaje = ""
    mensaje_hasta = 0.0

    def empezar_nivel(numero, ahora):
        """Deja todo listo para arrancar el nivel `numero` (empieza con el cartel)."""
        nonlocal estado, nivel, frutas, rastro, dedos_previos, cortadas, vidas
        nonlocal cartel_hasta, espera
        estado = "cartel"
        nivel = numero
        frutas = []
        rastro = []
        dedos_previos = []
        cortadas = 0
        vidas = VIDAS_INICIALES
        cartel_hasta = ahora + DURACION_CARTEL
        espera = 0.5           # la primera fruta del nivel sale enseguida

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            ahora = time.time()
            flash, mascara = detectar_flash(frame, umbral)
            # Lista de puntos para la logica del corte (vacia si no se ve la luz,
            # asi el rastro no salta de un lado a otro de la pantalla).
            dedos = [flash] if flash is not None else []
            reglas = NIVELES[nivel]

            if estado == "cartel" and ahora >= cartel_hasta:
                estado = "jugando"
                ultimo_spawn = ahora

            if estado == "jugando":
                if ahora - ultimo_spawn > espera and len(frutas) < reglas["max_frutas"]:
                    frutas.append(crear_fruta(w, h, reglas))
                    ultimo_spawn = ahora
                    espera = random.uniform(*reglas["espera"])
                for fruta in frutas:
                    fruta.actualizar(1 / 60)

                nuevos_segmentos = []
                for anterior, dedo in zip(dedos_previos, dedos):
                    nuevos_segmentos.append((anterior, dedo))
                for dedo in dedos:
                    rastro.append(dedo)
                rastro = rastro[-18:]
                dedos_previos = dedos

                for fruta in frutas:
                    if fruta.cortada:
                        continue
                    if any(distancia_punto_segmento((fruta.x, fruta.y), a, b)
                           < fruta.radio + 12 for a, b in nuevos_segmentos):
                        fruta.cortada = True
                        if fruta.bomba:
                            vidas -= 1
                            mensaje = "BOMBA!"
                            mensaje_hasta = ahora + 0.7
                        else:
                            puntuacion += 1
                            cortadas += 1
                            mensaje = "+1"
                            mensaje_hasta = ahora + 0.35

                frutas_activas = []
                frutas_perdidas = 0
                for fruta in frutas:
                    if fruta.cortada:
                        continue
                    if fruta.y > h + 100:
                        if not fruta.bomba:
                            frutas_perdidas += 1
                    else:
                        frutas_activas.append(fruta)
                frutas = frutas_activas
                vidas -= frutas_perdidas

                if vidas <= 0:
                    estado = "fin"
                elif cortadas >= reglas["meta"]:
                    if nivel + 1 < len(NIVELES):
                        empezar_nivel(nivel + 1, ahora)
                        reglas = NIVELES[nivel]
                    else:
                        estado = "ganaste"
                        frutas = []

            else:
                rastro = []
                dedos_previos = []

            for fruta in frutas:
                fruta.dibujar(frame)
            for a, b in zip(rastro, rastro[1:]):
                cv2.line(frame, a, b, (255, 255, 255), 5, cv2.LINE_AA)
            for dedo in dedos:
                cv2.circle(frame, dedo, 14, AMARILLO, 3)

            if estado == "menu":
                frame = oscurecer(frame, w, h)
                texto(frame, "FRUIT NINJA", (w // 2, h // 2 - 110), 2.4, AMARILLO, 5, True)
                texto(frame, "Prende la linterna del celular y corta con la luz", (w // 2, h // 2 - 25), 0.95, BLANCO, 2, True)
                texto(frame, f"{len(NIVELES)} niveles - evita las bombas y no dejes caer frutas",
                      (w // 2, h // 2 + 25), 0.8, BLANCO, 2, True)
                texto(frame, "Flash detectado" if flash else "No veo el flash",
                      (w // 2, h // 2 + 65), 0.8, VERDE if flash else ROJO, 2, True)
                texto(frame, "ESPACIO para empezar  |  Q para salir", (w // 2, h // 2 + 105), 0.9, VERDE, 2, True)
                texto(frame, f"Umbral de brillo: {umbral}  (+/- para ajustar, M para ver la luz)",
                      (w // 2, h // 2 + 150), 0.65, BLANCO, 1, True)
            elif estado == "cartel":
                frame = oscurecer(frame, w, h)
                if nivel > 0:
                    texto(frame, "NIVEL SUPERADO!", (w // 2, h // 2 - 130), 1.2, VERDE, 3, True)
                texto(frame, f"NIVEL {nivel + 1}", (w // 2, h // 2 - 50), 2.6, AMARILLO, 6, True)
                texto(frame, f"Corta {reglas['meta']} frutas para pasar", (w // 2, h // 2 + 40), 1.0, BLANCO, 2, True)
                if reglas["bombas"] > 0:
                    texto(frame, "Cuidado con las bombas", (w // 2, h // 2 + 85), 0.8, ROJO, 2, True)
                texto(frame, f"Empieza en {max(1, math.ceil(cartel_hasta - ahora))}...",
                      (w // 2, h // 2 + 140), 0.9, VERDE, 2, True)
            elif estado == "jugando":
                texto(frame, f"Nivel {nivel + 1}/{len(NIVELES)}", (25, 45), 1.0, AMARILLO, 2)
                texto(frame, f"Frutas: {cortadas}/{reglas['meta']}", (25, 90), 1.0, BLANCO, 2)
                texto(frame, f"Vidas: {max(vidas, 0)}", (25, 130), 0.8, ROJO, 2)
                texto(frame, f"Puntos: {puntuacion}", (w - 230, 45), 1.0, BLANCO, 2)
                if ahora < mensaje_hasta:
                    texto(frame, mensaje, (w // 2, 130), 1.5,
                          ROJO if mensaje == "BOMBA!" else VERDE, 4, True)
            elif estado == "ganaste":
                frame = oscurecer(frame, w, h)
                texto(frame, "GANASTE!", (w // 2, h // 2 - 90), 2.4, VERDE, 5, True)
                texto(frame, f"Pasaste los {len(NIVELES)} niveles  -  Puntuacion: {puntuacion}",
                      (w // 2, h // 2 - 5), 1.0, BLANCO, 2, True)
                texto(frame, "ESPACIO para jugar de nuevo  |  Q para salir",
                      (w // 2, h // 2 + 85), 0.9, VERDE, 2, True)
            else:  # "fin"
                frame = oscurecer(frame, w, h)
                texto(frame, "FIN DE LA PARTIDA", (w // 2, h // 2 - 90), 1.8, AMARILLO, 4, True)
                texto(frame, f"Llegaste al nivel {nivel + 1}  -  Puntuacion: {puntuacion}",
                      (w // 2, h // 2 - 15), 1.1, BLANCO, 2, True)
                texto(frame, "ESPACIO para revancha  |  Q para salir",
                      (w // 2, h // 2 + 85), 0.9, VERDE, 2, True)

            if ver_mascara:
                # Recuadro arriba a la derecha con lo que la camara toma como "luz"
                chica = cv2.resize(mascara, (w // 4, h // 4))
                frame[10:10 + h // 4, w - 10 - w // 4:w - 10] = cv2.cvtColor(chica, cv2.COLOR_GRAY2BGR)

            cv2.imshow(VENTANA, frame)
            tecla = cv2.waitKey(1) & 0xFF
            if tecla in (ord("q"), 27):
                break
            if tecla in (ord("+"), ord("=")):
                umbral = min(254, umbral + 5)
            if tecla in (ord("-"), ord("_")):
                umbral = max(150, umbral - 5)
            if tecla == ord("m"):
                ver_mascara = not ver_mascara
            if tecla == ord(" ") and estado in ("menu", "fin", "ganaste"):
                puntuacion = 0
                empezar_nivel(0, time.time())
            if cv2.getWindowProperty(VENTANA, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
