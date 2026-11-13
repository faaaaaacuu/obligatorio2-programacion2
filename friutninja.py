"""Fruit Ninja controlado con las manos usando OpenCV y MediaPipe.

Controles:
  ESPACIO  empezar / volver a jugar
  Q / ESC  salir

Mueve la punta del dedo indice como una espada. Cada fruta que cruza el
rastro del dedo suma puntos; las bombas quitan una vida.
"""

import math
import random
import time

import cv2
import mediapipe as mp
import numpy as np


VENTANA = "FRUIT NINJA - MANOS"
INDICE_CAMARA = 0
VIDAS_INICIALES = 3
DURACION_PARTIDA = 60
MAX_FRUTAS = 12
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

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


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


def distancia_punto_segmento(punto, inicio, fin):
    segmento = np.array(fin, dtype=np.float32) - inicio
    largo = float(np.dot(segmento, segmento))
    if largo == 0:
        return float(np.linalg.norm(np.array(punto) - inicio))
    t = np.clip(np.dot(np.array(punto) - inicio, segmento) / largo, 0, 1)
    proyeccion = inicio + t * segmento
    return float(np.linalg.norm(np.array(punto) - proyeccion))


class Fruta:
    def __init__(self, x, y, radio, color, bomba=False):
        self.x, self.y = float(x), float(y)
        self.radio = radio
        self.color = color
        self.bomba = bomba
        self.vx = random.uniform(-180, 180)
        self.vy = random.uniform(-760, -560)
        self.giro = random.uniform(0, math.tau)
        self.cortada = False

    def actualizar(self, dt):
        self.vy += 980 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.giro += dt * 5

    def dibujar(self, imagen):
        centro = (int(self.x), int(self.y))
        if self.bomba:
            cv2.circle(imagen, centro, self.radio, (25, 25, 25), -1)
            cv2.circle(imagen, centro, self.radio, BLANCO, 2)
            cv2.line(imagen, (centro[0] - 12, centro[1] - 12),
                     (centro[0] + 12, centro[1] + 12), ROJO, 4)
            cv2.line(imagen, (centro[0] + 12, centro[1] - 12),
                     (centro[0] - 12, centro[1] + 12), ROJO, 4)
            cv2.line(imagen, (centro[0] + 10, centro[1] - self.radio + 4),
                     (centro[0] + 20, centro[1] - self.radio - 12), AMARILLO, 4)
            return

        cv2.circle(imagen, centro, self.radio, self.color, -1)
        cv2.circle(imagen, centro, self.radio, BLANCO, 2)
        cv2.ellipse(imagen, (centro[0] - self.radio // 3, centro[1] - self.radio // 3),
                    (self.radio // 5, self.radio // 8), -30, 0, 360, BLANCO, -1)
        cv2.ellipse(imagen, (centro[0], centro[1] - self.radio - 5),
                    (self.radio // 3, self.radio // 7), 25, 0, 360, (30, 130, 30), -1)


def crear_fruta(w, h):
    radio = random.randint(25, 42)
    return Fruta(
        random.randint(radio + 10, w - radio - 10),
        h + radio,
        radio,
        random.choice(COLORES_FRUTAS),
        bomba=random.random() < 0.14,
    )


def detectar_dedos(resultado, imagen, w, h):
    puntos = []
    if resultado.multi_hand_landmarks:
        for landmarks in resultado.multi_hand_landmarks:
            mp_draw.draw_landmarks(imagen, landmarks, mp_hands.HAND_CONNECTIONS)
            dedo = landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            puntos.append((int(dedo.x * w), int(dedo.y * h)))
    return puntos


def main():
    cap = cv2.VideoCapture(INDICE_CAMARA)
    if not cap.isOpened():
        raise SystemExit("No se pudo abrir la camara. Revisa sus permisos.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cv2.namedWindow(VENTANA, cv2.WINDOW_NORMAL)

    manos = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.65,
        min_tracking_confidence=0.55,
    )
    estado = "menu"
    frutas = []
    rastro = []
    dedos_previos = []
    puntuacion = 0
    vidas = VIDAS_INICIALES
    inicio = 0.0
    ultimo_spawn = 0.0
    mensaje = ""
    mensaje_hasta = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            ahora = time.time()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resultado = manos.process(rgb)
            dedos = detectar_dedos(resultado, frame, w, h)

            if estado == "jugando":
                if ahora - ultimo_spawn > random.uniform(0.35, 0.75) and len(frutas) < MAX_FRUTAS:
                    frutas.append(crear_fruta(w, h))
                    ultimo_spawn = ahora
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
                if vidas <= 0 or ahora - inicio >= DURACION_PARTIDA:
                    estado = "fin"

            else:
                rastro = []
                dedos_previos = []

            for fruta in frutas:
                fruta.dibujar(frame)
            for a, b in zip(rastro, rastro[1:]):
                cv2.line(frame, a, b, (255, 255, 255), 5, cv2.LINE_AA)
            for dedo in dedos:
                cv2.circle(frame, dedo, 12, AMARILLO, -1)

            if estado == "menu":
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, h), (10, 10, 35), -1)
                frame = cv2.addWeighted(overlay, 0.72, frame, 0.28, 0)
                texto(frame, "FRUIT NINJA", (w // 2, h // 2 - 110), 2.4, AMARILLO, 5, True)
                texto(frame, "Corta las frutas moviendo el dedo indice", (w // 2, h // 2 - 25), 0.95, BLANCO, 2, True)
                texto(frame, "Evita las bombas y no dejes caer frutas", (w // 2, h // 2 + 25), 0.8, BLANCO, 2, True)
                texto(frame, "ESPACIO para empezar  |  Q para salir", (w // 2, h // 2 + 105), 0.9, VERDE, 2, True)
            elif estado == "jugando":
                texto(frame, f"Puntos: {puntuacion}", (25, 45), 1.0, BLANCO, 2)
                texto(frame, f"Vidas: {'♥ ' * max(vidas, 0)}", (25, 85), 0.8, ROJO, 2)
                texto(frame, f"Tiempo: {max(0, DURACION_PARTIDA - int(ahora - inicio))}",
                      (w - 220, 45), 0.8, AMARILLO, 2)
                if ahora < mensaje_hasta:
                    texto(frame, mensaje, (w // 2, 130), 1.5,
                          ROJO if mensaje == "BOMBA!" else VERDE, 4, True)
            else:
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, h), (10, 10, 35), -1)
                frame = cv2.addWeighted(overlay, 0.72, frame, 0.28, 0)
                texto(frame, "FIN DE LA PARTIDA", (w // 2, h // 2 - 90), 1.8, AMARILLO, 4, True)
                texto(frame, f"Puntuacion: {puntuacion}", (w // 2, h // 2 - 15), 1.3, BLANCO, 3, True)
                texto(frame, "ESPACIO para revancha  |  Q para salir",
                      (w // 2, h // 2 + 85), 0.9, VERDE, 2, True)

            cv2.imshow(VENTANA, frame)
            tecla = cv2.waitKey(1) & 0xFF
            if tecla in (ord("q"), 27):
                break
            if tecla == ord(" ") and estado in ("menu", "fin"):
                estado = "jugando"
                frutas = []
                rastro = []
                dedos_previos = []
                puntuacion = 0
                vidas = VIDAS_INICIALES
                inicio = ultimo_spawn = time.time()
            if cv2.getWindowProperty(VENTANA, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        manos.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
