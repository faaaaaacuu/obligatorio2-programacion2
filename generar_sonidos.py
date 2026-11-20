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

import numpy as np    # para los instrumentos con muchas ondas sumadas (cuerdas, coro): es mucho más rápido

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


def eco_que_se_apaga(muestras, retardo, segundos_en_apagarse):
    """Un eco que se repite: a cada sonido le suma lo que sonó `retardo` segundos
    antes, un poco más bajo. Con `segundos_en_apagarse` se elige cuánto tarda en
    bajar a casi nada (en audio se llama "filtro peine")."""
    paso = int(MUESTRAS_POR_SEGUNDO * retardo)
    ganancia = 10 ** (-3 * retardo / segundos_en_apagarse)
    salida = list(muestras)
    for i in range(paso, len(salida)):
        salida[i] += salida[i - paso] * ganancia
    return salida


def difusor(muestras, retardo, ganancia=0.7):
    """Desparrama un sonido en el tiempo sin cambiar su color, para que los ecos
    no se escuchen de a uno sino como una nube (en audio: filtro "pasa todo")."""
    paso = int(MUESTRAS_POR_SEGUNDO * retardo)
    entrada = list(muestras)
    salida = [0.0] * len(entrada)
    for i in range(len(entrada)):
        anterior_entrada = entrada[i - paso] if i >= paso else 0.0
        anterior_salida = salida[i - paso] if i >= paso else 0.0
        salida[i] = -ganancia * entrada[i] + anterior_entrada + ganancia * anterior_salida
    return salida


def reverb(muestras, segundos_cola=1.5, mezcla=0.35):
    """Le agrega reverberación (el eco de una sala, como un dojo de madera), y le
    deja `segundos_cola` de silencio al final para que el eco se apague solo.
    Es la reverb clásica de Schroeder: 4 ecos de distinto largo sumados, y
    después 2 difusores. `mezcla` es cuánto se oye la sala (0 = nada, 1 = solo sala)."""
    con_cola = muestras + [0.0] * int(MUESTRAS_POR_SEGUNDO * segundos_cola)
    ecos = [0.0] * len(con_cola)
    for retardo in (0.0297, 0.0371, 0.0411, 0.0437):     # largos distintos: no "chocan" entre sí
        for i, valor in enumerate(eco_que_se_apaga(con_cola, retardo, segundos_cola * 0.8)):
            ecos[i] += valor / 4
    sala = difusor(difusor(ecos, 0.005), 0.0017)
    return [seco * (1 - mezcla) + mojado * mezcla for seco, mojado in zip(con_cola, sala)]


def sacar_silencio_final(muestras, umbral=0.0005):
    """Saca del final las muestras que ya casi no se oyen (más bajas que `umbral`
    respecto del punto más fuerte), así el archivo no tiene una cola muda."""
    limite = max(abs(m) for m in muestras) * umbral
    final = len(muestras)
    while final > 0 and abs(muestras[final - 1]) < limite:
        final -= 1
    return muestras[:final]


def desvanecer_final(muestras, segundos=0.25):
    """Baja el volumen hasta cero en los últimos `segundos`, para que nunca termine de golpe."""
    total = int(MUESTRAS_POR_SEGUNDO * segundos)
    salida = list(muestras)
    for k in range(min(total, len(salida))):
        salida[-1 - k] *= k / total
    return salida


def katana(duracion_silbido, brillo, maximo, frecuencias=(900, 5200, 2500), pico=0.4, semilla=1,
           segundos_cola=1.5):
    """Un corte de katana: el silbido del aire y, un poquito después, el brillo de
    la hoja, todo con la reverb de la sala para que quede sonando hasta apagarse."""
    aire = normalizar(silbido(duracion_silbido, *frecuencias, pico=pico, semilla=semilla), 1.0)
    hoja = normalizar(brillo_metalico(1.4), brillo)            # dura hasta apagarse solo
    tajo = juntar(aire, hoja, duracion_silbido * pico * 0.8)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(tajo, segundos_cola))), maximo)


# ---------------------------------------------------------------------------
# Música de fondo: una pieza original y tranquila, con aire de dojo japonés
# ---------------------------------------------------------------------------

# Escala japonesa "miyako-bushi" (Re, Mi bemol, Sol, La, Si bemol), en varias octavas.
NOTAS = {
    "D2": 73.42, "G2": 98.00, "A2": 110.00, "Bb2": 116.54, "D3": 146.83, "Eb3": 155.56, "G3": 196.00, "A3": 220.00,
    "Bb3": 233.08, "D4": 293.66, "Eb4": 311.13, "G4": 392.00, "A4": 440.00, "Bb4": 466.16,
    "D5": 587.33, "Eb5": 622.25, "G5": 783.99, "A5": 880.00,
}
# Las notas de la escala en orden, de grave a agudo (5 notas por octava)
ESCALA = ["D3", "Eb3", "G3", "A3", "Bb3", "D4", "Eb4", "G4", "A4", "Bb4", "D5", "Eb5", "G5", "A5"]
# Una versión de la música por intensidad: cuanto más difícil el juego, más rápida
# (pulsos por minuto) y con más notas. 0 = tranquila ... 3 = frenética.
TEMPOS = [72, 88, 104, 120]

# Melodía del koto: 16 compases de 8 corcheas cada uno ("_" = silencio)
MELODIA_KOTO = [
    "D5 _ A4 _ Bb4 A4 G4 _",   "D4 _ _ _ G4 _ A4 _",      "Bb4 _ A4 G4 Eb4 _ D4 _",  "_ _ A3 D4 _ _ _ _",
    "G4 _ A4 Bb4 D5 _ Eb5 D5", "Bb4 _ A4 _ G4 _ _ _",     "Eb4 D4 _ G4 A4 _ Bb4 A4", "D4 _ _ _ _ _ _ _",
    "D5 _ A4 _ Bb4 A4 G4 _",   "D4 _ G4 A4 Bb4 _ A4 _",   "Bb4 _ A4 G4 Eb4 _ D4 _",  "_ _ D4 _ A3 _ D3 _",
    "D5 _ Eb5 _ G5 _ Eb5 D5",  "Bb4 A4 _ G4 _ _ A4 _",    "Bb4 _ A4 G4 Eb4 D4 _ _",  "D4 _ _ _ _ _ _ _",
]
# Bajo del koto: una nota grave en el pulso 1 y otra en el pulso 3 de cada compás
BAJO_KOTO = ["D3 A3", "D3 A3", "G3 D4", "A3 D3", "G3 D4", "G3 D4", "Bb3 D4", "D3 A3"] * 2
# Shakuhachi (flauta): notas largas en la segunda mitad de cada parte, (nota, pulsos)
FLAUTA = {4: [("A4", 4), ("G4", 2), ("Bb4", 2), ("A4", 3), ("G4", 1), ("D4", 4)],
          12: [("D5", 4), ("Eb5", 2), ("D5", 2), ("Bb4", 3), ("A4", 1), ("D5", 4)]}


def koto(frecuencia, duracion, azar):
    """Una cuerda pulsada (síntesis Karplus-Strong): un golpe de ruido corto
    recorre una "línea de retardo" una y otra vez; cada vuelta se suaviza un
    poco (promedio de dos muestras), así suena como una cuerda que se apaga."""
    retardo = MUESTRAS_POR_SEGUNDO / frecuencia - 0.5   # el promedio agrega media muestra
    largo = int(retardo) + 2
    linea = [0.0] * largo
    golpe = int(retardo)
    ruido = [azar.uniform(-1, 1) for _ in range(golpe)]
    for k in range(1, golpe):                           # golpe más suave: menos "chirrido"
        ruido[k] = 0.5 * (ruido[k] + ruido[k - 1])
    muestras = []
    anterior = 0.0
    for i in range(int(MUESTRAS_POR_SEGUNDO * duracion)):
        posicion = i - retardo
        if posicion < 0:
            retardada = 0.0
        else:
            k = int(posicion)
            fraccion = posicion - k                     # retardo con decimales: afinación exacta
            retardada = linea[k % largo] * (1 - fraccion) + linea[(k + 1) % largo] * fraccion
        valor = (ruido[i] if i < golpe else 0.0) + 0.5 * (retardada + anterior) * 0.997
        anterior = retardada
        linea[i % largo] = valor
        muestras.append(valor)
    return desvanecer_final(muestras, 0.05)


def shakuhachi(frecuencia, duracion, azar):
    """La flauta de bambú: un tono suave con un poco de "soplido", que entra
    despacio, con vibrato que aparece de a poco, y se apaga al final."""
    muestras = []
    fase = 0.0
    x1 = x2 = y1 = y2 = 0.0
    total = int(MUESTRAS_POR_SEGUNDO * duracion)
    for i in range(total):
        t = i / MUESTRAS_POR_SEGUNDO
        vibrato = 1 + 0.006 * math.sin(2 * math.pi * 5 * t) * min(1.0, t / 0.8)
        subida = 0.97 + 0.03 * min(1.0, t / 0.15)       # la nota "entra" un poquito desde abajo
        fase += 2 * math.pi * frecuencia * vibrato * subida / MUESTRAS_POR_SEGUNDO
        tono = math.sin(fase) + 0.25 * math.sin(2 * fase) + 0.08 * math.sin(3 * fase)
        # soplido: ruido filtrado cerca del tono (más fuerte al principio de la nota)
        w = 2 * math.pi * min(frecuencia * 2, 4000) / MUESTRAS_POR_SEGUNDO
        alfa = math.sin(w) / 2
        x = azar.uniform(-1, 1)
        y = (alfa * x - alfa * x2 + 2 * math.cos(w) * y1 - (1 - alfa) * y2) / (1 + alfa)
        x2, x1, y2, y1 = x1, x, y1, y
        soplido = y * (0.5 + 1.5 * max(0.0, 1 - t / 0.3))
        volumen = min(1.0, t / 0.25) * min(1.0, (duracion - t) / 0.35)
        muestras.append((tono * 0.8 + soplido * 0.35) * volumen)
    return muestras


def taiko(fuerza, azar=random, tono=1.0, caida=0.35, duracion=0.9):
    """Un golpe de tambor: un tono que baja rápido de agudo a grave, más un "toc".
    `tono` < 1 lo hace más grave (como el o-daiko, el tambor gigante) y > 1 más
    agudo (como el shime-daiko, el chiquito); `caida` es cuánto tarda en apagarse."""
    muestras = []
    fase = 0.0
    for i in range(int(MUESTRAS_POR_SEGUNDO * duracion)):
        t = i / MUESTRAS_POR_SEGUNDO
        frecuencia = (55 + 65 * math.exp(-t / 0.05)) * tono
        fase += 2 * math.pi * frecuencia / MUESTRAS_POR_SEGUNDO
        cuerpo = math.sin(fase) * math.exp(-t / caida)
        toc = azar.uniform(-1, 1) * math.exp(-t / 0.008) * 0.3
        muestras.append((cuerpo + toc) * fuerza)
    return muestras


def sumar_en(pista, sonido, segundo, volumen):
    """Suma `sonido` a la `pista` a partir de `segundo`, con ese `volumen`.
    Si se pasa del final, "da la vuelta" y sigue sonando al principio: así,
    cuando la música se repite, las notas del final no se cortan."""
    inicio = int(MUESTRAS_POR_SEGUNDO * segundo)
    for i, valor in enumerate(sonido):
        pista[(inicio + i) % len(pista)] += valor * volumen


def palillos(fuerza=1.0):
    """Hyoshigi: dos palillos de madera que chocan ("¡tac!"). Unas pocas
    frecuencias agudas que se apagan enseguida, y un segundo choquecito más
    suave porque los palillos rebotan."""
    resonancias = [(1250, 1.0, 0.035), (2480, 0.6, 0.025), (3900, 0.35, 0.015)]
    muestras = []
    for i in range(int(MUESTRAS_POR_SEGUNDO * 0.25)):
        t = i / MUESTRAS_POR_SEGUNDO
        valor = 0.0
        for retraso, volumen_golpe in ((0.0, 1.0), (0.022, 0.35)):      # el golpe y el rebote
            tg = t - retraso
            if tg >= 0:
                valor += volumen_golpe * sum(v * math.sin(2 * math.pi * f * tg) * math.exp(-tg / d)
                                             for f, v, d in resonancias)
        muestras.append(valor * fuerza)
    return muestras


def gong(duracion=3.0):
    """Un gong: frecuencias graves que no son múltiplos entre sí y tardan en
    apagarse, con un leve "uaaa" (la afinación baja un poquito al principio)."""
    parciales = [(98, 1.0, 1.6), (147.5, 0.7, 1.2), (205, 0.5, 1.0), (261, 0.35, 0.8),
                 (333, 0.25, 0.6), (420, 0.15, 0.5)]
    fases = [0.0] * len(parciales)
    muestras = []
    for i in range(int(MUESTRAS_POR_SEGUNDO * duracion)):
        t = i / MUESTRAS_POR_SEGUNDO
        curva = 1 + 0.012 * math.exp(-t / 0.3)
        valor = 0.0
        for k, (f, v, d) in enumerate(parciales):
            fases[k] += 2 * math.pi * f * curva / MUESTRAS_POR_SEGUNDO
            valor += v * math.sin(fases[k]) * math.exp(-t / d)
        muestras.append(valor * min(1.0, t / 0.02))
    return muestras


def vecina(nota, pasos):
    """Devuelve la nota que está `pasos` lugares más arriba (o abajo, si es
    negativo) en la escala."""
    i = ESCALA.index(nota) + pasos
    return ESCALA[max(0, min(len(ESCALA) - 1, i))]


def melodia_del_compas(renglon, intensidad, azar):
    """Pasa un compás de la melodía (8 corcheas) a 16 semicorcheas y, según la
    intensidad, le agrega notas. Devuelve 16 lugares (una nota o None).
      1 o más: rellena algunos silencios con una nota vecina de la anterior
      3:       pone notas de paso entre corcheas (carreritas en semicorcheas)"""
    corcheas = [None if n == "_" else n for n in renglon.split()]
    semis = [None] * 16
    for k, nota in enumerate(corcheas):
        semis[2 * k] = nota
    if intensidad >= 1:
        ultima = None
        for k, nota in enumerate(corcheas):
            if nota:
                ultima = nota
            elif ultima and azar.random() < 0.55:
                semis[2 * k] = vecina(ultima, azar.choice((-1, 1)))
    if intensidad >= 3:
        for k in range(0, 14, 2):
            a, b = semis[k], semis[k + 2]
            if a and b and azar.random() < 0.6:
                semis[k + 1] = vecina(a, 1 if ESCALA.index(b) > ESCALA.index(a) else -1)
    return semis


def bajo_del_compas(raiz, quinta, intensidad):
    """Las notas graves de un compás, en corcheas (8 lugares), según la intensidad:
    más intensidad = el bajo toca más seguido y salta de octava."""
    arriba = vecina(raiz, 5)            # la misma nota, una octava más aguda
    patrones = [
        [raiz, None, None, None, quinta, None, None, None],          # pulsos 1 y 3
        [raiz, None, raiz, None, quinta, None, raiz, None],          # los 4 pulsos
        [raiz, raiz, quinta, raiz, raiz, quinta, raiz, quinta],      # corcheas
        [raiz, arriba, quinta, arriba, raiz, arriba, quinta, arriba],  # corcheas saltando
    ]
    return patrones[intensidad]


def componer_musica(intensidad=0):
    """Arma la pieza con la intensidad pedida (0 = tranquila ... 3 = frenética):
    koto, bajo, flauta, taiko, palillos y un zumbido grave, con reverb. Al final
    pega la cola de la reverb sobre el principio, así cuando se repite en loop
    no se nota dónde termina y dónde empieza."""
    azar = random.Random(42 + intensidad)
    pulso = 60 / TEMPOS[intensidad]
    compas = 4 * pulso
    total = len(MELODIA_KOTO) * compas
    largo = int(MUESTRAS_POR_SEGUNDO * total)
    melodia = [0.0] * largo          # lo que va con reverb
    percusion = [0.0] * largo        # el taiko, los palillos y el zumbido van más "secos"
    duracion_nota = 2.5 * 72 / TEMPOS[intensidad]       # más rápido = notas más cortas

    for numero, renglon in enumerate(MELODIA_KOTO):
        original = renglon.split()
        for lugar, nota in enumerate(melodia_del_compas(renglon, intensidad, azar)):
            if nota is None:
                continue
            momento = numero * compas + lugar * pulso / 4
            es_original = lugar % 2 == 0 and original[lugar // 2] == nota
            sumar_en(melodia, koto(NOTAS[nota], duracion_nota, azar), momento, 0.5 if es_original else 0.38)
            if intensidad >= 2 and es_original:        # la melodía doblada una octava arriba
                sumar_en(melodia, koto(NOTAS[vecina(nota, 5)], duracion_nota, azar), momento, 0.2)
    for numero, renglon in enumerate(BAJO_KOTO):
        raiz, quinta = renglon.split()
        for corchea, nota in enumerate(bajo_del_compas(raiz, quinta, intensidad)):
            if nota:
                sumar_en(melodia, koto(NOTAS[nota], duracion_nota * 1.2, azar),
                         numero * compas + corchea * pulso / 2, 0.3)
    for compas_inicial, notas in FLAUTA.items():
        momento = compas_inicial * compas
        for nota, pulsos in notas:
            sumar_en(melodia, shakuhachi(NOTAS[nota], pulsos * pulso, azar), momento, 0.22)
            momento += pulsos * pulso

    for numero in range(len(MELODIA_KOTO)):
        inicio = numero * compas
        if intensidad == 0:
            golpes = [(0, 0.45)] if numero % 2 == 0 else []
        elif intensidad == 1:
            golpes = [(0, 0.5), (2, 0.35)]
        else:
            golpes = [(0, 0.6), (1, 0.35), (2, 0.5), (3, 0.35)]
        for p, fuerza in golpes:
            sumar_en(percusion, taiko(fuerza, azar), inicio + p * pulso, 1)
        if numero % 4 == 3:          # "don-don" al final de cada frase
            sumar_en(percusion, taiko(0.6, azar), inicio + 3 * pulso, 1)
            sumar_en(percusion, taiko(0.5, azar), inicio + 3.5 * pulso, 1)
        if intensidad == 3 and numero % 2 == 1:          # redoble: 4 golpecitos rápidos
            for k in range(4):
                sumar_en(percusion, taiko(0.3 + 0.08 * k, azar), inicio + (3 + k / 4) * pulso, 1)
        if intensidad >= 2:          # palillos de madera a contratiempo
            for p in ((1.5, 3.5) if intensidad == 2 else (0.5, 1.5, 2.5, 3.5)):
                sumar_en(percusion, palillos(0.12), inicio + p * pulso, 1)

    # Zumbido grave (Re y La) que "respira" despacio. Cada onda tiene que dar un
    # número entero de vueltas en toda la pieza; si no, al repetirse haría "click".
    def vueltas_enteras(frecuencia):
        return round(frecuencia * total) / total
    re, la, respiro_f = vueltas_enteras(NOTAS["D2"]), vueltas_enteras(NOTAS["A2"]), 7 / total
    for i in range(largo):
        t = i / MUESTRAS_POR_SEGUNDO
        respiro = 0.7 + 0.3 * math.sin(2 * math.pi * respiro_f * t)
        percusion[i] += 0.06 * respiro * (math.sin(2 * math.pi * re * t) + 0.6 * math.sin(2 * math.pi * la * t))

    con_reverb = reverb(melodia, segundos_cola=3.0, mezcla=0.35 - 0.04 * intensidad)
    pieza = [m + (percusion[i] if i < largo else 0.0) for i, m in enumerate(con_reverb)]
    # lo que sobra después del final (la cola) se suma al principio: loop sin cortes
    loop = pieza[:largo]
    for i, valor in enumerate(pieza[largo:]):
        loop[i] += valor
    return normalizar(loop, 0.8)


# ---------------------------------------------------------------------------
# Música épica para la partida
# ---------------------------------------------------------------------------

TEMPOS_EPICOS = [100, 112, 124, 138]     # una versión por intensidad, de 0 a 3
# Acorde de cuerdas y notas del coro según la nota grave de cada compás
ACORDES = {"D3": ["D2", "A2", "D3", "A3"], "G3": ["G2", "D3", "G3", "Bb3"],
           "A3": ["A2", "D3", "A3", "D4"], "Bb3": ["Bb2", "D3", "Bb3", "D4"]}
CORO = {"D3": ["D4", "A4"], "G3": ["G4", "D5"], "A3": ["A4", "D5"], "Bb3": ["Bb4", "D5"]}
# Ritmos por compás en semicorcheas (16 lugares), uno por intensidad.
# O-daiko: "D" golpe fuerte, "d" suave. Bajo de cuerdas: R = nota grave, O = una
# octava arriba, Q = la quinta. Shime-daiko: "x" golpe.
ODAIKO = ["D.......d.......", "D.......D...d...", "D...d...D.d.D...", "D..dD...D.dDD.d."]
BAJO_CUERDAS = ["R...R...R...R...", "R.R.R.O.R.R.R.O.", "R.RRO.R.R.RRO.Q.", "RROROQROROROROQO"]
SHIME = ["x...x...x...x...", "x.x.x.x.x.x.x.x.", "x.xxx.x.x.xxx.xx", "xxxxxxxxxxxxxxxx"]


def cuerdas(frecuencias, duracion, azar, armonicos=10):
    """Un acorde de cuerdas sostenido, como una orquesta de fondo: cada nota es
    una onda con muchos armónicos, tocada por 3 "músicos" apenas desafinados
    entre sí para que suene ancho. Entra y sale despacio.
    (Con numpy: cada cuenta se hace sobre toda la lista de muestras de una vez.)"""
    t = np.arange(int(MUESTRAS_POR_SEGUNDO * duracion)) / MUESTRAS_POR_SEGUNDO
    sonido = np.zeros_like(t)
    for f in frecuencias:
        for desafinacion in (-0.005, 0.0, 0.005):
            fase = azar.uniform(0, 2 * math.pi)
            for k in range(1, armonicos + 1):
                if f * k > 6000:
                    break
                sonido += np.sin(2 * np.pi * f * (1 + desafinacion) * k * t + fase * k) / k ** 1.3
    entrada = np.minimum(1, t / (duracion * 0.3))
    salida = np.minimum(1, (duracion - t) / (duracion * 0.3))
    sonido *= entrada * salida
    return list(sonido / (np.abs(sonido).max() + 1e-9))


def coro(frecuencias, duracion, azar):
    """Un coro cantando "aaah": cada voz tiene muchos armónicos, pero solo suenan
    fuerte los que caen cerca de las "formantes" de la vocal A (las frecuencias
    que la boca resalta al decir "a"). Con vibrato, como voces de verdad."""
    formantes = [(800, 1.0, 110), (1150, 0.6, 120), (2900, 0.15, 180)]
    t = np.arange(int(MUESTRAS_POR_SEGUNDO * duracion)) / MUESTRAS_POR_SEGUNDO
    sonido = np.zeros_like(t)
    for f in frecuencias:
        for desafinacion in (-0.007, 0.0, 0.007):
            vibrato = 1 + 0.004 * np.sin(2 * np.pi * azar.uniform(4.5, 5.5) * t)
            fase = 2 * np.pi * f * (1 + desafinacion) * np.cumsum(vibrato) / MUESTRAS_POR_SEGUNDO
            for k in range(1, int(4000 / f) + 1):
                armonico = k * f
                ganancia = sum(a * math.exp(-((armonico - centro) / ancho) ** 2)
                               for centro, a, ancho in formantes) + 0.03 / k
                sonido += ganancia * np.sin(k * fase)
    entrada = np.minimum(1, t / (duracion * 0.35))
    salida = np.minimum(1, (duracion - t) / (duracion * 0.3))
    sonido *= entrada * salida
    return list(sonido / (np.abs(sonido).max() + 1e-9))


def cuerda_corta(frecuencia):
    """Una nota corta y grave de cuerdas (como los violonchelos marcando el ritmo)."""
    t = np.arange(int(MUESTRAS_POR_SEGUNDO * 0.3)) / MUESTRAS_POR_SEGUNDO
    onda = sum(np.sin(2 * np.pi * frecuencia * k * t) / k for k in range(1, 11))
    return list(onda * np.minimum(1, t / 0.008) * np.exp(-t / 0.09))


def componer_musica_epica(intensidad):
    """La música de la partida: la misma melodía de koto y flauta, pero con un
    fondo épico de cuerdas, coro, o-daiko (tambor gigante), shime-daiko (tambor
    chico que empuja el ritmo) y un bajo de cuerdas. Más intensidad = más rápida
    y con más instrumentos y notas."""
    azar = random.Random(100 + intensidad)
    pulso = 60 / TEMPOS_EPICOS[intensidad]
    compas = 4 * pulso
    semi = pulso / 4
    total = len(MELODIA_KOTO) * compas
    largo = int(MUESTRAS_POR_SEGUNDO * total)
    con_sala = [0.0] * largo         # lo que lleva reverb (melodía, cuerdas, coro, o-daiko)
    seco = [0.0] * largo             # lo que va más directo (bajo de cuerdas, shime-daiko)
    duracion_nota = 2.5 * 72 / TEMPOS_EPICOS[intensidad]

    for numero, renglon in enumerate(MELODIA_KOTO):
        inicio = numero * compas
        raiz = BAJO_KOTO[numero].split()[0]
        acorde = ACORDES[raiz]
        # melodía del koto (con más notas cuanto más intensidad) y doblada una octava arriba
        original = renglon.split()
        for lugar, nota in enumerate(melodia_del_compas(renglon, intensidad, azar)):
            if nota is None:
                continue
            es_original = lugar % 2 == 0 and original[lugar // 2] == nota
            sumar_en(con_sala, koto(NOTAS[nota], duracion_nota, azar), inicio + lugar * semi,
                     0.55 if es_original else 0.4)
            if es_original and intensidad >= 1:
                sumar_en(con_sala, koto(NOTAS[vecina(nota, 5)], duracion_nota, azar), inicio + lugar * semi, 0.22)
        # el acorde de cuerdas, sostenido todo el compás (y un poco más, para que se enlacen)
        sumar_en(con_sala, cuerdas([NOTAS[n] for n in acorde], compas * 1.3, azar), inicio, 0.3)
        # el coro: en la segunda mitad desde la intensidad 2, y siempre en la 3
        if intensidad == 3 or (intensidad == 2 and numero >= 8):
            sumar_en(con_sala, coro([NOTAS[n] for n in CORO[raiz]], compas * 1.3, azar), inicio, 0.2)
        # bajo de cuerdas, o-daiko y shime-daiko, según los ritmos de esta intensidad
        notas_bajo = {"R": acorde[0], "Q": acorde[1], "O": acorde[2]}
        for lugar in range(16):
            momento = inicio + lugar * semi
            letra = BAJO_CUERDAS[intensidad][lugar]
            if letra in notas_bajo:
                sumar_en(seco, cuerda_corta(NOTAS[notas_bajo[letra]]), momento, 0.32)
            golpe = ODAIKO[intensidad][lugar]
            if golpe != ".":
                fuerza = 1.0 if golpe == "D" else 0.55
                sumar_en(con_sala, taiko(fuerza, azar, tono=0.72, caida=0.7, duracion=1.4), momento, 0.9)
            if SHIME[intensidad][lugar] == "x":
                acento = 0.35 if lugar % 4 == 0 else 0.2
                sumar_en(seco, taiko(acento, azar, tono=3.8, caida=0.05, duracion=0.2), momento, 1)
        if numero % 4 == 3:          # al final de cada frase: redoble de o-daiko que crece
            for k in range(4 if intensidad < 2 else 8):
                paso = 4 // (1 if intensidad < 2 else 2)
                sumar_en(con_sala, taiko(0.5 + 0.06 * k, azar, tono=0.8, caida=0.4, duracion=1.0),
                         inicio + (12 + k * paso // 2) * semi, 0.8)
    for compas_inicial, notas in FLAUTA.items():
        momento = compas_inicial * compas
        for nota, pulsos in notas:
            sumar_en(con_sala, shakuhachi(NOTAS[nota], pulsos * pulso, azar), momento, 0.25)
            momento += pulsos * pulso
    if intensidad >= 2:              # palillos de madera a contratiempo
        for numero in range(len(MELODIA_KOTO)):
            for p in ((1.5, 3.5) if intensidad == 2 else (0.5, 1.5, 2.5, 3.5)):
                sumar_en(seco, palillos(0.1), numero * compas + p * pulso, 1)

    sala = reverb(con_sala, segundos_cola=3.5, mezcla=0.32)
    pieza = [m + (seco[i] if i < largo else 0.0) for i, m in enumerate(sala)]
    loop = pieza[:largo]
    for i, valor in enumerate(pieza[largo:]):        # la cola de la reverb vuelve al principio
        loop[i] += valor
    return normalizar(loop, 0.85)


def cuenta_regresiva(numero):
    """El sonido de cada número de la cuenta regresiva. El 3 y el 2: palillos con
    un taiko chico (el 2 un poco más agudo, para que suba la tensión). El 1, el
    más épico: un o-daiko grande y un silbido que crece hasta el arranque."""
    azar = random.Random(10 + numero)
    if numero >= 2:
        tambor = taiko(1.0, azar, tono=1.0 if numero == 3 else 1.3, caida=0.25, duracion=0.7)
        golpe = juntar(palillos(0.8), [m * 0.7 for m in tambor], 0)
        return normalizar(desvanecer_final(sacar_silencio_final(reverb(golpe, 1.0, 0.3))), 0.65)
    tambor = taiko(1.0, azar, tono=0.7, caida=0.8, duracion=1.6)
    subida = normalizar(silbido(1.0, 300, 3500, 3200, pico=0.95, semilla=11), 0.45)
    golpe = juntar(juntar(tambor, palillos(1.0), 0), subida, 0.05)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(golpe, 1.5, 0.35))), 0.9)


def comienzo():
    """El arranque de la partida: o-daiko, gong y un acorde de cuerdas que crece."""
    azar = random.Random(5)
    golpe = juntar(taiko(1.0, azar, tono=0.72, caida=0.9, duracion=1.8), [m * 0.6 for m in gong(3.0)], 0)
    golpe = juntar(golpe, [m * 0.35 for m in cuerdas([NOTAS[n] for n in ACORDES["D3"]] + [NOTAS["D4"]], 2.6, azar)], 0)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(golpe, 2.0, 0.3))), 0.9)


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
    guardar("espadazo", katana(0.42, 0.55, 0.85, (600, 6500, 1800), 0.45, 2, 2.2))  # el de la intro
    guardar("bomba", barrido(140, 40, 0.6, 0.8, ruido=0.9))
    guardar("caida", barrido(420, 160, 0.3, 0.4))
    guardar("nivel", nota(660, 0.12) + nota(880, 0.12) + nota(1100, 0.3))
    guardar("ganar", nota(523, 0.15) + nota(659, 0.15) + nota(784, 0.15) + nota(1047, 0.5))
    guardar("lanzar", normalizar(desvanecer_final(reverb(silbido(0.6, 300, 4000, 3000, pico=0.85, semilla=3),
                                                         1.0)), 0.6))
    guardar("mortal", barrido(300, 30, 1.2, 0.9, ruido=1.0))
    guardar("vida", nota(784, 0.08) + nota(1047, 0.08) + nota(1319, 0.08) + nota(1568, 0.25))
    guardar("sello", barrido(170, 60, 0.14, 0.8, ruido=0.5))
    guardar("perder", nota(392, 0.25) + nota(330, 0.25) + nota(262, 0.6))
    guardar("musica_menu", componer_musica(0))              # la tranquila: menú, intro y finales
    for intensidad in range(len(TEMPOS_EPICOS)):             # las épicas: durante la partida
        guardar(f"musica_{intensidad}", componer_musica_epica(intensidad))
    for numero in (3, 2, 1):
        guardar(f"cuenta_{numero}", cuenta_regresiva(numero))
    guardar("comienzo", comienzo())
    print("Sonidos generados en", CARPETA)
