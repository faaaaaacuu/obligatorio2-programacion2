"""Genera los efectos de sonido (.wav) de la carpeta sonidos/.

No hace falta correrlo para jugar: los .wav ya están incluidos.
Cada sonido se arma con ondas seno (notas) y algo de ruido, con un
desvanecido al final.
"""

import math
import os
import random
import struct
import wave

MUESTRAS_POR_SEGUNDO = 22050
CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sonidos")


def barrido(frecuencia_inicio, frecuencia_fin, duracion, volumen=0.5, ruido=0.0):
    """Devuelve las muestras de un sonido cuya frecuencia va de una a otra
    y que se va apagando. Si las dos frecuencias son iguales, es una nota."""
    total = int(MUESTRAS_POR_SEGUNDO * duracion)
    muestras = []
    fase = 0.0
    for i in range(total):
        avance = i / total
        frecuencia = frecuencia_inicio + (frecuencia_fin - frecuencia_inicio) * avance
        fase += 2 * math.pi * frecuencia / MUESTRAS_POR_SEGUNDO
        valor = math.sin(fase) + random.uniform(-1, 1) * ruido
        muestras.append(valor * volumen * (1 - avance))
    return muestras


def nota(frecuencia, duracion, volumen=0.5):
    """Devuelve las muestras de una nota que se va apagando."""
    return barrido(frecuencia, frecuencia, duracion, volumen)


def guardar(nombre, muestras):
    ruta = os.path.join(CARPETA, nombre + ".wav")
    with wave.open(ruta, "w") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(MUESTRAS_POR_SEGUNDO)
        datos = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, m)) * 32767))
                         for m in muestras)
        archivo.writeframes(datos)


if __name__ == "__main__":
    os.makedirs(CARPETA, exist_ok=True)
    guardar("corte", barrido(500, 1800, 0.14, 0.35, ruido=0.5))
    guardar("bomba", barrido(140, 40, 0.6, 0.8, ruido=0.9))
    guardar("caida", barrido(420, 160, 0.3, 0.4))
    guardar("nivel", nota(660, 0.12) + nota(880, 0.12) + nota(1100, 0.3))
    guardar("ganar", nota(523, 0.15) + nota(659, 0.15) + nota(784, 0.15) + nota(1047, 0.5))
    guardar("lanzar", barrido(200, 1200, 0.5, 0.45, ruido=0.2))
    guardar("mortal", barrido(300, 30, 1.2, 0.9, ruido=1.0))
    guardar("perder", nota(392, 0.25) + nota(330, 0.25) + nota(262, 0.6))
    print("Sonidos generados en", CARPETA)
