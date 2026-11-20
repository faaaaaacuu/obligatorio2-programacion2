"""Genera los efectos de sonido (.wav) de la carpeta sonidos/.

No hace falta correrlo para jugar: los .wav ya están incluidos.
Cada sonido se arma con ondas seno (notas) y algo de ruido, con un
desvanecido al final. Los cortes suenan a katana: un silbido de aire
("shhh") más el brillo metálico de la hoja ("eeesh").
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


def silbido(duracion, frecuencia_inicio, frecuencia_pico, frecuencia_fin, pico=0.4, semilla=1,
            ancho_banda=2.5):
    """El "shhh" de una hoja cortando el aire: ruido filtrado para que suene solo
    alrededor de una frecuencia, que sube hasta el `pico` (0 a 1 del sonido) y
    después baja. El volumen también crece hasta el pico y después se apaga.

    El filtro es un "pasa banda" (biquad, la receta clásica de audio): cada
    muestra nueva se calcula con las dos anteriores de la entrada y de la salida.
    `ancho_banda` (Q) más alto = franja más angosta = suena más "silbado"."""
    azar = random.Random(semilla)      # mismo "azar" siempre: el sonido no cambia al regenerarlo
    total = int(MUESTRAS_POR_SEGUNDO * duracion)
    muestras = []
    x1 = x2 = y1 = y2 = 0.0            # las dos entradas y salidas anteriores
    for i in range(total):
        avance = i / total
        if avance < pico:
            frecuencia = frecuencia_inicio + (frecuencia_pico - frecuencia_inicio) * avance / pico
            volumen = (avance / pico) ** 1.5
        else:
            parte = (avance - pico) / (1 - pico)
            frecuencia = frecuencia_pico + (frecuencia_fin - frecuencia_pico) * parte
            volumen = (1 - parte) ** 2
        w = 2 * math.pi * frecuencia / MUESTRAS_POR_SEGUNDO
        alfa = math.sin(w) / (2 * ancho_banda)
        x = azar.uniform(-1, 1)
        y = (alfa * x - alfa * x2 + 2 * math.cos(w) * y1 - (1 - alfa) * y2) / (1 + alfa)
        x2, x1 = x1, x
        y2, y1 = y1, y
        muestras.append(y * volumen)
    return muestras


def brillo_metalico(duracion, intensidad=1.0):
    """El "eeesh" de la hoja de metal: varias frecuencias agudas que no son
    múltiplos entre sí (por eso suena a metal y no a nota musical), cada una
    apagándose a su ritmo. Dos de ellas están muy cerca y "laten" (vibran)."""
    parciales = [  # (frecuencia, volumen, cuánto tarda en apagarse)
        (2350, 1.0, 0.30), (2366, 0.8, 0.30), (3540, 0.6, 0.20),
        (4980, 0.45, 0.14), (6620, 0.3, 0.10),
    ]
    total = int(MUESTRAS_POR_SEGUNDO * duracion)
    muestras = []
    for i in range(total):
        t = i / MUESTRAS_POR_SEGUNDO
        ataque = min(1.0, t / 0.004)            # empieza de golpe, pero sin "click"
        valor = sum(volumen * math.sin(2 * math.pi * frecuencia * t) * math.exp(-t / apagado)
                    for frecuencia, volumen, apagado in parciales)
        muestras.append(valor * ataque * intensidad)
    return muestras


def juntar(base, encima, desde_segundo):
    """Suma el sonido `encima` al sonido `base`, empezando en `desde_segundo`."""
    inicio = int(MUESTRAS_POR_SEGUNDO * desde_segundo)
    largo = max(len(base), inicio + len(encima))
    resultado = base + [0.0] * (largo - len(base))
    for i, valor in enumerate(encima):
        resultado[inicio + i] += valor
    return resultado


def normalizar(muestras, maximo):
    """Sube o baja el volumen para que el punto más fuerte quede en `maximo` (de 0 a 1)."""
    mayor = max(abs(m) for m in muestras) or 1
    return [m * maximo / mayor for m in muestras]


def katana(duracion_silbido, brillo, maximo, frecuencias=(900, 5200, 2500), pico=0.4, semilla=1):
    """Un corte de katana: el silbido del aire y, un poquito después, el brillo de la hoja."""
    aire = normalizar(silbido(duracion_silbido, *frecuencias, pico=pico, semilla=semilla), 1.0)
    hoja = normalizar(brillo_metalico(duracion_silbido * 2.2), brillo)
    return normalizar(juntar(aire, hoja, duracion_silbido * pico * 0.8), maximo)


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
    guardar("corte", katana(0.2, 0.35, 0.7))                                    # tajo corto
    guardar("espadazo", katana(0.42, 0.55, 0.85, (600, 6500, 1800), 0.45, 2))  # el de la intro
    guardar("bomba", barrido(140, 40, 0.6, 0.8, ruido=0.9))
    guardar("caida", barrido(420, 160, 0.3, 0.4))
    guardar("nivel", nota(660, 0.12) + nota(880, 0.12) + nota(1100, 0.3))
    guardar("ganar", nota(523, 0.15) + nota(659, 0.15) + nota(784, 0.15) + nota(1047, 0.5))
    guardar("lanzar", normalizar(silbido(0.6, 300, 4000, 3000, pico=0.85, semilla=3), 0.6))
    guardar("mortal", barrido(300, 30, 1.2, 0.9, ruido=1.0))
    guardar("vida", nota(784, 0.08) + nota(1047, 0.08) + nota(1319, 0.08) + nota(1568, 0.25))
    guardar("sello", barrido(170, 60, 0.14, 0.8, ruido=0.5))
    guardar("perder", nota(392, 0.25) + nota(330, 0.25) + nota(262, 0.6))
    print("Sonidos generados en", CARPETA)
