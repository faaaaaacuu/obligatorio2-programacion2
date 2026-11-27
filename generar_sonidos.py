"""Genera los efectos de sonido (.wav) de la carpeta sonidos/.

No hace falta correrlo para jugar: los .wav ya están incluidos.
Cada sonido se arma con ondas seno y ruido filtrado, imitando
instrumentos japoneses (koto, shakuhachi, taiko, campana rin, gong), con
reverb y un desvanecido al final. Los cortes suenan a katana: un silbido de aire
("shhh") más el brillo metálico de la hoja ("eeesh").
"""

import math
import os
import random
import struct
import wave

import numpy as np    # para los instrumentos con muchas ondas sumadas (cuerdas, coro): es mucho más rápido

from instrumentos import (MUESTRAS_POR_SEGUNDO, barrido, brillo_metalico, campana, coro,
                          cuerda_corta, cuerdas, desvanecer_final, furin, gong, grito, juntar,
                          katana, koto, normalizar, palillos, reverb, sacar_silencio_final,
                          shakuhachi, silbido, sumar_en, taiko)

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sonidos")


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
        """Redondea la frecuencia para que dé un número entero de vueltas en todo el loop: así, al repetirse, no se nota el corte."""
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


def espadazo():
    """El espadazo de la intro: un corte de katana largo y con mucha hoja."""
    return katana(0.42, 0.55, 0.85, (600, 6500, 1800), 0.45, 2, 2.2)


def victoria():
    """El sonido de ganar el versus: los dos espadazos de la intro (la firma del
    juego), el koto sube rapidísimo por la escala "yo" (la japonesa alegre: Re,
    Mi, Sol, La, Si), cae un o-daiko con el gong y queda sonando un acorde de
    koto con la shakuhachi encima, hasta apagarse."""
    azar = random.Random(21)
    re4, mi4, sol4, la4, si4 = 293.66, 329.63, 392.00, 440.00, 493.88
    pista = [0.0] * int(MUESTRAS_POR_SEGUNDO * 4.0)
    # ¡shheeesh! ¡shheeesh!
    sumar_en(pista, espadazo(), 0.0, 0.7)
    sumar_en(pista, espadazo(), 0.28, 0.7)
    # subida del koto: dos octavas de la escala yo, cada vez más rápida
    subida = [re4, mi4, sol4, la4, si4, re4 * 2, mi4 * 2, sol4 * 2, la4 * 2]
    segundo = 0.62
    for k, frecuencia in enumerate(subida):
        sumar_en(pista, koto(frecuencia, 0.8, azar), segundo, 0.45 + 0.04 * k)
        segundo += 0.075 - 0.004 * k
    # llegada: o-daiko grande + gong + acorde de koto rasgueado (Re, La, Re, Mi agudo)
    llegada = segundo + 0.03
    sumar_en(pista, taiko(1.0, azar, tono=0.7, caida=0.7, duracion=1.6), llegada, 1.0)
    sumar_en(pista, gong(3.0), llegada, 0.35)
    for k, frecuencia in enumerate((re4 / 2, la4 / 2, re4, la4, re4 * 2)):
        sumar_en(pista, koto(frecuencia, 2.2, azar), llegada + 0.025 * k, 0.4)
    # la flauta: entra en La y sube al Re agudo, que queda sonando
    sumar_en(pista, shakuhachi(la4 * 2, 0.35, azar), llegada + 0.05, 0.35)
    sumar_en(pista, shakuhachi(re4 * 2, 1.6, azar), llegada + 0.35, 0.4)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(pista, 1.8, 0.3))), 0.85)


def bomba_mortal():
    """La bomba mortal: un kiai (grito de guerra) con un espadazo, y al caer el
    golpe un o-daiko enorme, la explosión y un gong grave que queda retumbando."""
    azar = random.Random(31)
    golpe = normalizar(grito(), 0.9)
    golpe = juntar(golpe, [m * 0.7 for m in espadazo()], 0.0)
    caida = 0.2                                      # el tambor cae junto con el tajo
    explosion = normalizar(barrido(220, 30, 1.2, 0.9, ruido=1.0), 0.45)
    golpe = juntar(golpe, explosion, caida)
    golpe = juntar(golpe, taiko(1.0, azar, tono=0.6, caida=1.0, duracion=2.0), caida)
    golpe = juntar(golpe, [m * 0.5 for m in gong(3.0)], caida + 0.02)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(golpe, 1.8, 0.3))), 0.9)


def envainar():
    """Guardar la katana en la vaina: la hoja se desliza raspando (un siseo
    metálico agudo y parejo, más largo que un corte) y termina con el "¡chin!"
    de la guarda que choca contra la boca de la vaina."""
    raspado = normalizar(silbido(0.55, 3800, 5200, 4600, pico=0.75, semilla=51, ancho_banda=6.0), 0.5)
    roce = normalizar(brillo_metalico(0.55, tono=1.6), 0.08)       # la hoja vibrando mientras entra
    chin = normalizar(brillo_metalico(0.9, tono=1.35), 0.9)
    golpecito = [m * 0.6 for m in palillos(0.7)]                    # la madera de la vaina
    sonido = juntar(juntar(raspado, roce, 0), chin, 0.52)
    return juntar(sonido, golpecito, 0.52)


def derrota():
    """El sonido de perder, como el final de un duelo: el samurái guarda la
    katana (envainar), y la shakuhachi baja por la escala miyako-bushi (la
    melancólica, la de la música del juego) con el koto, sobre un taiko y un
    gong graves y suaves."""
    azar = random.Random(41)
    pista = [0.0] * int(MUESTRAS_POR_SEGUNDO * 4.2)
    sumar_en(pista, envainar(), 0.0, 0.9)
    inicio = 0.85
    frase = [("A4", 0.0, 0.45), ("G4", 0.4, 0.45), ("Eb4", 0.8, 0.5), ("D4", 1.25, 1.6)]
    for nombre, segundo, duracion in frase:
        sumar_en(pista, shakuhachi(NOTAS[nombre], duracion, azar), inicio + segundo, 0.5)
    for nombre, segundo in (("D4", 0.0), ("Bb3", 0.8), ("D3", 1.25), ("A3", 1.3)):
        sumar_en(pista, koto(NOTAS[nombre], 1.6, azar), inicio + segundo, 0.35)
    sumar_en(pista, taiko(0.6, azar, tono=0.75, caida=0.6, duracion=1.4), inicio + 1.25, 0.6)
    sumar_en(pista, gong(2.2), inicio + 1.25, 0.3)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(pista, 1.8, 0.35))), 0.75)


def bomba_comun():
    """Cortar una bomba: la katana pega contra el hierro ("¡clang!", un metal
    grave y desafinado), revienta la pólvora y retumba un taiko."""
    azar = random.Random(61)
    tajo = katana(0.14, 0.2, 1.0, (1100, 5600, 2600), 0.4, 62)
    clang = normalizar(brillo_metalico(0.9, tono=0.55), 0.8)
    estallido = normalizar(barrido(160, 40, 0.5, 0.8, ruido=1.0), 0.6)
    tambor = taiko(1.0, azar, tono=0.85, caida=0.35, duracion=0.9)
    golpe = juntar(juntar(juntar([m * 0.5 for m in tajo], clang, 0.04), estallido, 0.05), tambor, 0.05)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(golpe, 1.2, 0.3))), 0.8)


def fruta_caida():
    """Se cayó una fruta: un golpe apagado contra el tatami (taiko chiquito y
    seco) y el koto que baja medio tono, como un "uy"."""
    azar = random.Random(71)
    golpe = [m * 0.7 for m in taiko(1.0, azar, tono=1.6, caida=0.07, duracion=0.35)]
    golpe = juntar(golpe, [m * 0.4 for m in koto(NOTAS["Eb4"], 0.4, azar)], 0.06)
    golpe = juntar(golpe, [m * 0.45 for m in koto(NOTAS["D4"], 0.9, azar)], 0.2)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(golpe, 0.9, 0.25))), 0.5)


def record():
    """Nuevo récord (y la aparición del título en la intro): un golpe de la
    campana rin y el koto que sube Re, La, Re, como un "¡ahí está!"."""
    azar = random.Random(81)
    golpe = [m * 0.55 for m in campana(NOTAS["D5"], 2.5, azar)]
    for k, nombre in enumerate(("D4", "A4", "D5")):
        golpe = juntar(golpe, [m * 0.45 for m in koto(NOTAS[nombre], 1.0, azar)], 0.02 + 0.09 * k)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(golpe, 1.5, 0.3))), 0.6)


def vida_extra():
    """+1 vida por el combo: el koto sube rapidito por la escala "yo" y lo cierra
    el furin, la campanita de vidrio."""
    azar = random.Random(91)
    golpe = [0.0]
    for k, frecuencia in enumerate((587.33, 659.25, 783.99, 880.00)):    # Re, Mi, Sol, La agudos
        golpe = juntar(golpe, [m * 0.45 for m in koto(frecuencia, 0.6, azar)], 0.06 * k)
    golpe = juntar(golpe, furin(azar), 0.24)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(golpe, 1.3, 0.3))), 0.6)


def golpe_de_sello():
    """El sello (hanko) que se estampa en la intro: un golpe de madera seco y
    grave, el "plaf" del papel y un taiko que lo acompaña."""
    azar = random.Random(101)
    madera = taiko(1.0, azar, tono=2.2, caida=0.05, duracion=0.3)
    papel = [azar.uniform(-1, 1) * math.exp(-i / (MUESTRAS_POR_SEGUNDO * 0.012)) * 0.5
             for i in range(int(MUESTRAS_POR_SEGUNDO * 0.1))]
    tambor = [m * 0.7 for m in taiko(1.0, azar, tono=0.8, caida=0.4, duracion=1.0)]
    golpe = juntar(juntar(madera, papel, 0), tambor, 0)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(golpe, 1.2, 0.3))), 0.8)


def lanzamiento():
    """Se lanza la bomba mortal al rival: un shime-daiko (tambor chico) que redobla
    cada vez más rápido mientras sube el silbido, y un palillazo al soltarla."""
    azar = random.Random(111)
    pista = [0.0] * int(MUESTRAS_POR_SEGUNDO * 1.0)
    segundo, espera = 0.0, 0.11
    while segundo < 0.6:
        sumar_en(pista, taiko(0.5 + segundo, azar, tono=2.4, caida=0.05, duracion=0.15), segundo, 0.6)
        segundo += espera
        espera *= 0.85
    sumar_en(pista, normalizar(silbido(0.6, 300, 4000, 3000, pico=0.85, semilla=3), 0.7), 0.0, 1.0)
    sumar_en(pista, palillos(1.0), 0.62, 0.8)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(pista, 1.0, 0.3))), 0.65)


# Variantes del corte, para que no suene siempre igual: cada una con otro largo,
# otro barrido del silbido (frecuencia de inicio, pico y final), otro momento del
# pico, otro "azar" para el ruido y otra hoja (más grave o más aguda).
# (duración, brillo, frecuencias, pico, semilla, tono de la hoja)
VARIANTES_CORTE = [
    (0.20, 0.35, (900, 5200, 2500), 0.40, 1, 1.00),    # el tajo de siempre
    (0.16, 0.30, (1200, 6400, 3200), 0.30, 11, 1.18),  # más corto y agudo, como un latigazo
    (0.26, 0.40, (700, 4300, 1900), 0.50, 12, 0.86),   # más largo y grave, una hoja pesada
    (0.22, 0.25, (1000, 5800, 2200), 0.35, 13, 1.07),  # más aire que metal
    (0.18, 0.45, (800, 4800, 3000), 0.45, 14, 0.94),   # más brillo de la hoja
]


def guardar(nombre, muestras):
    """Guarda las muestras (números entre -1 y 1) como un .wav mono de 16 bits en la carpeta sonidos/."""
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
    for numero, (duracion, brillo, frecuencias, pico, semilla, tono) in enumerate(VARIANTES_CORTE):
        guardar(f"corte_{numero}", katana(duracion, brillo, 0.7, frecuencias, pico, semilla, tono_hoja=tono))
    guardar("espadazo", espadazo())                                             # el de la intro
    guardar("bomba", bomba_comun())
    guardar("caida", fruta_caida())
    guardar("nivel", record())
    guardar("ganar", victoria())
    guardar("lanzar", lanzamiento())
    guardar("mortal", bomba_mortal())
    guardar("vida", vida_extra())
    guardar("sello", golpe_de_sello())
    guardar("perder", derrota())
    guardar("musica_menu", componer_musica(0))              # la tranquila: menú, intro y finales
    for intensidad in range(len(TEMPOS_EPICOS)):             # las épicas: durante la partida
        guardar(f"musica_{intensidad}", componer_musica_epica(intensidad))
    for numero in (3, 2, 1):
        guardar(f"cuenta_{numero}", cuenta_regresiva(numero))
    guardar("comienzo", comienzo())
    print("Sonidos generados en", CARPETA)
