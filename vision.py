"""Todo lo de OpenCV: abrir la cámara, leer el cuadro y detectar la linterna.

El resto del juego no usa OpenCV: solo recibe una posición (x, y) o None.
"""

import cv2

from ajustes import (ANCHO, ALTO, INDICE_CAMARA, ANCHO_CAMARA, ALTO_CAMARA,
                     DESENFOQUE, AREA_MINIMA_LUZ)


def abrir_camara():
    """Abre la cámara. Devuelve el objeto de captura o None si no se pudo."""
    cap = cv2.VideoCapture(INDICE_CAMARA)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, ANCHO_CAMARA)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTO_CAMARA)
    return cap


def leer_cuadro(cap):
    """Lee un cuadro, lo espeja y lo lleva al tamaño de la ventana.
    Devuelve el cuadro (BGR) o None si la lectura falló."""
    ok, cuadro = cap.read()
    if not ok:
        return None
    cuadro = cv2.flip(cuadro, 1)  # espejo: si muevo la mano a la derecha, va a la derecha
    cuadro = cv2.resize(cuadro, (ANCHO, ALTO))
    return cuadro


def mascara_de_luz(cuadro, umbral):
    """Devuelve una imagen blanco y negro: blanco donde hay luz más fuerte que el umbral."""
    gris = cv2.cvtColor(cuadro, cv2.COLOR_BGR2GRAY)
    gris = cv2.GaussianBlur(gris, (DESENFOQUE, DESENFOQUE), 0)
    _, mascara = cv2.threshold(gris, umbral, 255, cv2.THRESH_BINARY)
    # erosionar y dilatar borra puntitos sueltos (reflejos chicos)
    mascara = cv2.erode(mascara, None, iterations=1)
    mascara = cv2.dilate(mascara, None, iterations=2)
    return mascara


def detectar_luz(cuadro, umbral, x_min=0, x_max=ANCHO):
    """Busca la mancha de luz más grande (la linterna del celular) entre las
    columnas x_min y x_max (en el versus, cada jugador busca en su mitad).
    Devuelve su centro (x, y) en coordenadas de la pantalla, o None si no hay."""
    if cuadro is None:
        return None
    mascara = mascara_de_luz(cuadro[:, x_min:x_max], umbral)
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
    if not contornos:
        return None
    mayor = max(contornos, key=cv2.contourArea)
    if cv2.contourArea(mayor) < AREA_MINIMA_LUZ:
        return None
    momentos = cv2.moments(mayor)
    if momentos["m00"] == 0:
        return None
    x = int(momentos["m10"] / momentos["m00"]) + x_min   # se corre a su lugar en la pantalla
    y = int(momentos["m01"] / momentos["m00"])
    return (x, y)


def a_rgb(cuadro):
    """OpenCV trabaja en BGR y pygame en RGB: devuelve el cuadro convertido."""
    return cv2.cvtColor(cuadro, cv2.COLOR_BGR2RGB)


def mascara_chica_rgb(cuadro, umbral, ancho, alto):
    """Devuelve la máscara de luz achicada y en RGB, para mostrarla en un
    recuadro y ver qué está tomando la cámara como "luz" (tecla M)."""
    mascara = mascara_de_luz(cuadro, umbral)
    mascara = cv2.resize(mascara, (ancho, alto))
    return cv2.cvtColor(mascara, cv2.COLOR_GRAY2RGB)
