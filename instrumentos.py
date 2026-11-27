"""Los instrumentos y herramientas de sonido que usa generar_sonidos.py: ondas, reverb,
katana, koto, shakuhachi, taiko, gong, cuerdas, coro, campana, furin y la voz del kiai.
Todo se sintetiza con matemática: no hay grabaciones.
"""

import math
import numpy as np
import random


MUESTRAS_POR_SEGUNDO = 22050


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


def brillo_metalico(duracion, intensidad=1.0, tono=1.0):
    """El "eeesh" de la hoja de metal: varias frecuencias agudas que no son
    múltiplos entre sí (por eso suena a metal y no a nota musical), cada una
    apagándose a su ritmo. Dos de ellas están muy cerca y "laten" (vibran).
    `tono` sube o baja todas las frecuencias juntas (otra hoja, otro brillo)."""
    parciales = [  # (frecuencia, volumen, cuánto tarda en apagarse)
        (2350 * tono, 1.0, 0.30), (2366 * tono, 0.8, 0.30), (3540 * tono, 0.6, 0.20),
        (4980 * tono, 0.45, 0.14), (6620 * tono, 0.3, 0.10),
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
           segundos_cola=1.5, tono_hoja=1.0):
    """Un corte de katana: el silbido del aire y, un poquito después, el brillo de
    la hoja, todo con la reverb de la sala para que quede sonando hasta apagarse."""
    aire = normalizar(silbido(duracion_silbido, *frecuencias, pico=pico, semilla=semilla), 1.0)
    hoja = normalizar(brillo_metalico(1.4, tono=tono_hoja), brillo)   # dura hasta apagarse solo
    tajo = juntar(aire, hoja, duracion_silbido * pico * 0.8)
    return normalizar(desvanecer_final(sacar_silencio_final(reverb(tajo, segundos_cola))), maximo)


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


def grito(duracion=0.75):
    """Un kiai, el grito de las artes marciales: "¡iyaaah!". Es una voz sintetizada:
    una nota grave con muchos armónicos (como las cuerdas vocales), de la que solo
    suenan fuerte los que caen en las "formantes" de la vocal. Arranca en "i" y
    pasa enseguida a "a"; la nota sube de golpe y después cae, con algo de
    aspereza (ronquera) y aire, como un grito de verdad."""
    azar = np.random.default_rng(7)
    t = np.arange(int(MUESTRAS_POR_SEGUNDO * duracion)) / MUESTRAS_POR_SEGUNDO
    avance = t / duracion
    # la nota: sube de 170 a 250 Hz al principio y cae hasta 140 al final
    tono = np.where(t < 0.09, 170 + 80 * t / 0.09, 250 - 110 * (np.maximum(0, t - 0.09) / (duracion - 0.09)) ** 1.5)
    tono = tono * (1 + 0.02 * azar.standard_normal(len(t)).cumsum() / 300)   # temblor de la voz
    fase = 2 * np.pi * np.cumsum(tono) / MUESTRAS_POR_SEGUNDO
    # formantes: de la "i" (300, 2250, 2900) a la "a" (780, 1200, 2700) en 0,1 segundos
    paso = np.minimum(1, t / 0.1)
    formantes = [(300 + 480 * paso, 1.0, 90), (2250 - 1050 * paso, 0.5 + 0.2 * paso, 140),
                 (2900 - 200 * paso, 0.2, 200)]
    sonido = np.zeros_like(t)
    for k in range(1, 30):
        armonico = k * tono
        ganancia = sum(a * np.exp(-((armonico - centro) / ancho) ** 2) for centro, a, ancho in formantes)
        sonido += (ganancia + 0.02 / k) * np.sin(k * fase)
    aspereza = 1 + 0.35 * np.sin(2 * np.pi * 38 * t) * azar.uniform(0.5, 1, len(t))
    sonido = sonido / (np.abs(sonido).max() + 1e-9) * aspereza
    aire = azar.uniform(-1, 1, len(t)) * 0.12 * (1 + 2 * avance ** 3)      # sopla más al final ("aaah...h")
    volumen = np.minimum(1, t / 0.03) * np.minimum(1, (duracion - t) / 0.25)
    return list((sonido + aire) * volumen)


def campana(frecuencia, duracion=2.5, azar=random):
    """La campana "rin" de los templos japoneses (un cuenco de metal que se toca
    con un palito): unas pocas frecuencias que no son múltiplos entre sí, cada
    una doble y apenas desafinada, así "late" (el "uaua-uaua" del cuenco)."""
    parciales = [(1.0, 1.0, 2.2), (2.76, 0.45, 1.2), (5.40, 0.2, 0.6), (8.93, 0.08, 0.3)]
    t = np.arange(int(MUESTRAS_POR_SEGUNDO * duracion)) / MUESTRAS_POR_SEGUNDO
    sonido = np.zeros_like(t)
    for proporcion, volumen, apagado in parciales:
        f = frecuencia * proporcion
        for desvio in (0.0, 1.6):                       # dos casi iguales: el latido
            sonido += volumen * np.sin(2 * np.pi * (f + desvio) * t + azar.uniform(0, 6.3)) * np.exp(-t / apagado)
    golpe = np.exp(-t / 0.004) * np.sin(2 * np.pi * 3100 * t) * 0.3   # el palito contra el metal
    sonido = (sonido + golpe) * np.minimum(1, t / 0.002)
    return list(sonido / (np.abs(sonido).max() + 1e-9))


def furin(azar):
    """Un furin, la campanita de vidrio que cuelga en las ventanas: agudo y
    cristalino, con un segundo toquecito porque el badajo rebota."""
    sonido = campana(2350, 1.2, azar)
    return juntar([m * 0.6 for m in sonido], [m * 0.3 for m in campana(2350 * 1.5, 0.8, azar)], 0.09)
