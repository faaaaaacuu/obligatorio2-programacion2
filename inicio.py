"""Pantalla de inicio: el título, las reglas y cómo empezar.

Cada regla es una "tarjeta" con un título, una explicación corta y una
animación que se repite mostrando qué pasa en el juego. Las animaciones no
usan la cámara: son dibujos calculados a partir del tiempo. Por ejemplo, en
"Cortá frutas" la fruta sube durante el primer segundo, en t = 1.0 pasa la luz
y la corta, y después las mitades caen. Con `t % duracion` se repiten.
"""

import math

import pygame

import graficos
from graficos import dibujar_texto, mezclar
from ajustes import (ANCHO, ALTO, TARJETA_ANCHO, TARJETA_ALTO, TARJETA_ANIMACION_ALTO,
                     SEPARACION_TARJETAS, Y_TARJETAS, RADIO_FRUTA_DEMO, DESFASE_TARJETAS,
                     FRUTAS_JUGADOR_1, FRUTAS_JUGADOR_2, COLORES_ESPADA, COLOR_JUGADOR_1,
                     COLOR_JUGADOR_2, COLOR_BOMBA_MORTAL, BLANCO, NEGRO, AMARILLO, VERDE,
                     ROJO, GRIS, CONTORNO)

LUZ = COLORES_ESPADA[0][1]      # color de la luz en las animaciones
COLORES_EXPLOSION = [(255, 140, 30), (255, 220, 60), (255, 255, 255), (90, 90, 90)]


# ---------------------------------------------------------------------------
# Imágenes (se arman una sola vez, antes del bucle)
# ---------------------------------------------------------------------------

def crear_imagenes():
    """Arma todas las imágenes que usan las animaciones. Devuelve un diccionario."""
    tipos = {fruta["tipo"]: fruta for fruta in FRUTAS_JUGADOR_1 + FRUTAS_JUGADOR_2}
    r = RADIO_FRUTA_DEMO
    imagenes = {}
    for nombre in ("naranja", "manzana", "sandia"):
        imagenes[nombre] = graficos.crear_imagen_fruta(tipos[nombre], r)
        imagenes[nombre + "_mitades"] = [graficos.crear_imagen_mitad(tipos[nombre], r, -1),
                                         graficos.crear_imagen_mitad(tipos[nombre], r, 1)]
        imagenes[nombre + "_jugo"] = [tipos[nombre]["pulpa"], tipos[nombre]["color"]]
    imagenes["bomba"] = graficos.crear_imagen_bomba(r)
    imagenes["mortal"] = graficos.crear_imagen_bomba(r, mortal=True)
    imagenes["halo"] = graficos.crear_halo(r * 2, COLOR_BOMBA_MORTAL)
    imagenes["corazones"] = {True: graficos.crear_corazon(16, True),
                             False: graficos.crear_corazon(16, False)}
    rojo = pygame.Surface((TARJETA_ANCHO, TARJETA_ANIMACION_ALTO), pygame.SRCALPHA)
    rojo.fill((255, 40, 40, 255))
    imagenes["rojo"] = rojo
    imagenes["tarjeta"] = graficos.crear_panel(TARJETA_ANCHO, TARJETA_ALTO)
    imagenes["modo"] = graficos.crear_panel(340, 74)
    return imagenes


# ---------------------------------------------------------------------------
# Herramientas para las animaciones
# ---------------------------------------------------------------------------

def partir_texto(texto, fuente, ancho):
    """Divide un texto en renglones que entren en `ancho` píxeles. Devuelve la lista de renglones."""
    renglones = []
    actual = ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if fuente.size(prueba)[0] <= ancho or not actual:
            actual = prueba
        else:
            renglones.append(actual)
            actual = palabra
    if actual:
        renglones.append(actual)
    return renglones


def pegar(sup, imagen, x, y, angulo=0, escala=1):
    """Pega una imagen centrada en (x, y), girada y agrandada si hace falta."""
    if angulo or escala != 1:
        imagen = pygame.transform.rotozoom(imagen, angulo, escala)
    sup.blit(imagen, imagen.get_rect(center=(int(x), int(y))))


def luz_en(t, desde, hasta, t0, t1):
    """Devuelve dónde está la luz en el momento t, si va de `desde` a `hasta`
    entre los segundos t0 y t1 (antes se queda en `desde`, después en `hasta`)."""
    avance = max(0.0, min(1.0, (t - t0) / (t1 - t0)))
    return (desde[0] + (hasta[0] - desde[0]) * avance,
            desde[1] + (hasta[1] - desde[1]) * avance)


def dibujar_estela(sup, puntos, color, con_punta=True):
    """La luz y su estela, como en el juego (brillo de color y centro blanco)."""
    if len(puntos) > 1:
        for ancho, tono in ((9, mezclar(NEGRO, color, 0.5)), (5, color), (2, BLANCO)):
            pygame.draw.lines(sup, tono, False, puntos, ancho)
    if con_punta and puntos:
        x, y = int(puntos[-1][0]), int(puntos[-1][1])
        pygame.draw.circle(sup, mezclar(NEGRO, color, 0.5), (x, y), 10)
        pygame.draw.circle(sup, color, (x, y), 6)
        pygame.draw.circle(sup, BLANCO, (x, y), 3)


def dibujar_corte(sup, t, desde, hasta, t0, t1, color=LUZ):
    """Dibuja la luz haciendo un corte recto de `desde` a `hasta` entre t0 y t1."""
    if t < t0 or t > t1 + 0.25:
        return
    # la estela son las posiciones de los últimos instantes
    puntos = [luz_en(t - k * 0.03, desde, hasta, t0, t1) for k in range(8, -1, -1)
              if t - k * 0.03 >= t0]
    dibujar_estela(sup, puntos, color, con_punta=t <= t1)


def dibujar_mitades(sup, mitades, x, y, dt):
    """Las dos mitades de una fruta cortada hace `dt` segundos: se separan, giran y caen."""
    for lado, imagen in zip((-1, 1), mitades):
        pegar(sup, imagen, x + lado * 40 * dt, y + 20 * dt + 160 * dt * dt, lado * 150 * dt)


def dibujar_salpicon(sup, x, y, dt, colores, cantidad=10, rapidez=90):
    """Gotitas (o chispas) que salen para todos lados desde (x, y) y se achican."""
    duracion = 0.6
    if dt < 0 or dt > duracion:
        return
    for i in range(cantidad):
        angulo = i * 2 * math.pi / cantidad + 0.4
        px = x + math.cos(angulo) * rapidez * dt
        py = y + math.sin(angulo) * rapidez * dt + 200 * dt * dt
        radio = 4.5 * (1 - dt / duracion)
        if radio >= 1:
            pygame.draw.circle(sup, colores[i % len(colores)], (int(px), int(py)), radio)


def texto_flotante(sup, fuente, texto, color, x, y, dt, duracion=0.9):
    """Un texto que sube desde (x, y) y se desvanece."""
    if dt < 0 or dt > duracion:
        return
    transparencia = int(255 * (1 - dt / duracion))
    for tono, corrida in ((CONTORNO, 2), (color, 0)):
        imagen = fuente.render(texto, True, tono)
        imagen.set_alpha(transparencia)
        sup.blit(imagen, imagen.get_rect(center=(int(x) + corrida, int(y - 25 * dt) + corrida)))


def dibujar_vidas(sup, imagenes, llenas, nueva=None, dt=0):
    """Tres corazoncitos arriba a la derecha. Si `nueva` es el número de un
    corazón que se acaba de llenar, aparece agrandado y se achica."""
    ancho = sup.get_width()
    for i in range(3):
        escala = 1
        if i == nueva and dt < 0.3:
            escala = 1.8 - dt / 0.3 * 0.8
        pegar(sup, imagenes["corazones"][i < llenas], ancho - 46 + i * 18, 12, escala=escala)


def fruta_subiendo(t, apice):
    """Altura de una fruta que sube y llega a su punto más alto (y = 48) en el segundo `apice`."""
    return 48 + 80 * ((t - apice) / apice) ** 2


# ---------------------------------------------------------------------------
# Las animaciones: cada una recibe la zona donde dibujar y el tiempo
# ---------------------------------------------------------------------------

def animar_cortar(sup, t, imagenes, fuentes):
    """Una naranja sube, la luz pasa por encima y la corta: +1 punto."""
    t %= 2.6
    centro = sup.get_width() // 2
    corte = 1.0
    if t < corte:
        pegar(sup, imagenes["naranja"], centro, fruta_subiendo(t, 0.95), t * 90)
    else:
        dt = t - corte
        dibujar_mitades(sup, imagenes["naranja_mitades"], centro, 48, dt)
        dibujar_salpicon(sup, centro, 48, dt, imagenes["naranja_jugo"])
        texto_flotante(sup, fuentes["tarjeta"], "+1", VERDE, centro + 36, 36, dt)
    dibujar_corte(sup, t, (12, 94), (sup.get_width() - 12, 20), 0.85, 1.15)


def animar_bomba(sup, t, imagenes, fuentes):
    """Sube una bomba, la luz la corta y explota: -1 vida."""
    t %= 2.6
    centro = sup.get_width() // 2
    corte = 1.0
    if t < corte:
        y = fruta_subiendo(t, 0.95)
        pegar(sup, imagenes["bomba"], centro, y)
        mx, my = graficos.punta_de_mecha(RADIO_FRUTA_DEMO)
        graficos.dibujar_chispa(sup, centro + mx, y + my)
        dibujar_vidas(sup, imagenes, 3)
    else:
        dt = t - corte
        if dt < 0.35:     # destello rojo que se apaga
            imagenes["rojo"].set_alpha(int(110 * (1 - dt / 0.35)))
            sup.blit(imagenes["rojo"], (0, 0))
        dibujar_salpicon(sup, centro, 48, dt, COLORES_EXPLOSION, cantidad=16, rapidez=140)
        dibujar_vidas(sup, imagenes, 2)
        texto_flotante(sup, fuentes["texto"], "-1 vida", ROJO, sup.get_width() - 30, 46, dt, 1.2)
    dibujar_corte(sup, t, (12, 94), (sup.get_width() - 12, 20), 0.85, 1.15)


def animar_caida(sup, t, imagenes, fuentes):
    """Una manzana sube y vuelve a caer sin que nadie la corte: -1 vida."""
    t %= 2.8
    sale = 2.0          # en este momento la manzana sale por abajo
    if t < sale:
        x = 22 + 55 * t
        y = 128 - 160 * t + 80 * t * t          # sube hasta y = 48 (en t = 1) y vuelve a bajar
        pegar(sup, imagenes["manzana"], x, y, t * 120)
        dibujar_vidas(sup, imagenes, 3)
    else:
        dibujar_vidas(sup, imagenes, 2)
        texto_flotante(sup, fuentes["texto"], "-1 vida", ROJO, sup.get_width() - 30, 46, t - sale, 0.8)
    # la luz está quieta en otro lado: no la corta
    dibujar_estela(sup, [(26, 34 + 4 * math.sin(t * 3))], LUZ)


def animar_triple(sup, t, imagenes, fuentes):
    """La luz corta 3 frutas de un solo trazo: +1 vida (si te falta alguna)."""
    t %= 3.2
    ancho = sup.get_width()
    desde, hasta = (6, 88), (ancho - 6, 26)
    t0, t1 = 1.0, 1.5
    frutas = (("sandia", 30), ("manzana", 80), ("naranja", 130))
    ultimo_corte = t0
    for i, (nombre, x) in enumerate(frutas):
        # en qué momento pasa la luz por esta fruta, y a qué altura
        corte = t0 + (t1 - t0) * (x - desde[0]) / (hasta[0] - desde[0])
        y = luz_en(corte, desde, hasta, t0, t1)[1]
        ultimo_corte = corte
        if t < corte:
            pegar(sup, imagenes[nombre], x, y + 3 * math.sin(t * 3 + i), t * 60)
        else:
            dt = t - corte
            dibujar_mitades(sup, imagenes[nombre + "_mitades"], x, y, dt)
            dibujar_salpicon(sup, x, y, dt, imagenes[nombre + "_jugo"], cantidad=6)
            texto_flotante(sup, fuentes["tarjeta"], str(i + 1), AMARILLO, x, y - 26, dt, 0.7)
    premio = ultimo_corte + 0.15
    if t < premio:
        dibujar_vidas(sup, imagenes, 2)
    else:
        dibujar_vidas(sup, imagenes, 3, nueva=2, dt=t - premio)
        texto_flotante(sup, fuentes["texto"], "+1 vida", VERDE, ancho - 30, 46, t - premio, 1.2)
    dibujar_corte(sup, t, desde, hasta, t0, t1)


def animar_mortal(sup, t, imagenes, fuentes):
    """Versus: la luz gira en círculos, se carga una bola y se va a la mitad del rival."""
    t %= 4.2
    ancho, alto = sup.get_size()
    mitad = ancho // 2
    pygame.draw.line(sup, GRIS, (mitad, 4), (mitad, alto - 4), 2)
    dibujar_texto(sup, "VOS", fuentes["texto"], COLOR_JUGADOR_1, (mitad // 2, 12))
    dibujar_texto(sup, "RIVAL", fuentes["texto"], COLOR_JUGADOR_2, (mitad + mitad // 2, 12))
    centro = (mitad // 2, 62)
    carga = 2.0          # segundos girando hasta completar la bola
    vuelo = 0.6          # segundos que tarda en llegar al rival
    if t < carga:
        # la luz da vueltas (1 vuelta y media) y la bola crece en el medio
        avance = t / carga
        radio_bola = int(4 + 14 * avance)
        graficos.ovalo_con_volumen(sup, centro, radio_bola * 2, radio_bola * 2, COLOR_BOMBA_MORTAL, 6)
        anillo = pygame.Rect(0, 0, radio_bola * 2 + 10, radio_bola * 2 + 10)
        anillo.center = centro
        pygame.draw.arc(sup, BLANCO, anillo, math.pi / 2, math.pi / 2 + 2 * math.pi * avance, 2)
        puntos = []
        for k in range(10, -1, -1):
            angulo = -math.pi / 2 + 3 * math.pi * max(0.0, t - k * 0.04) / carga
            puntos.append((centro[0] + 26 * math.cos(angulo), centro[1] + 26 * math.sin(angulo)))
        dibujar_estela(sup, puntos, COLOR_JUGADOR_1)
    elif t < carga + vuelo:
        # la bola vuela hacia la mitad del rival
        avance = (t - carga) / vuelo
        x = centro[0] + (mitad + mitad // 2 - centro[0]) * avance
        y = centro[1] - 30 * math.sin(math.pi * avance)
        graficos.ovalo_con_volumen(sup, (x, y), 36, 36, COLOR_BOMBA_MORTAL, 6)
    else:
        # en la mitad del rival aparece la bomba mortal
        dt = t - carga - vuelo
        x, y = mitad + mitad // 2, 62 + 3 * math.sin(t * 4)
        imagenes["halo"].set_alpha(int(150 + 100 * math.sin(t * 7)))
        pegar(sup, imagenes["halo"], x, y)
        pegar(sup, imagenes["mortal"], x, y)
        texto_flotante(sup, fuentes["texto"], "¡CUIDADO!", COLOR_BOMBA_MORTAL, x, alto - 4, dt * 0.2, 1.0)


# ---------------------------------------------------------------------------
# Tarjetas y pantalla de inicio
# ---------------------------------------------------------------------------

class Tarjeta:
    """Una regla del juego: un título, una explicación corta y una animación
    que se repite mostrando qué pasa."""

    def __init__(self, titulo, texto, color, animacion):
        self.titulo = titulo
        self.texto = texto
        self.color = color
        self.animacion = animacion      # una de las funciones animar_...

    def dibujar(self, pantalla, x, y, fuentes, imagenes, tiempo):
        pantalla.blit(imagenes["tarjeta"], (x, y))
        # una rayita de color arriba, para distinguir cada regla
        pygame.draw.rect(pantalla, self.color, (x + 14, y + 7, TARJETA_ANCHO - 28, 4), border_radius=2)
        # la animación se dibuja en una "subsuperficie": un pedazo de la pantalla con
        # coordenadas propias (0, 0 es su esquina) que no deja dibujar afuera de él
        zona = pantalla.subsurface(pygame.Rect(x + 6, y + 14, TARJETA_ANCHO - 12, TARJETA_ANIMACION_ALTO))
        self.animacion(zona, tiempo, imagenes, fuentes)
        centro = x + TARJETA_ANCHO // 2
        y_texto = y + 14 + TARJETA_ANIMACION_ALTO + 16
        dibujar_texto(pantalla, self.titulo, fuentes["tarjeta"], self.color, (centro, y_texto))
        for i, renglon in enumerate(partir_texto(self.texto, fuentes["texto"], TARJETA_ANCHO - 18)):
            dibujar_texto(pantalla, renglon, fuentes["texto"], BLANCO, (centro, y_texto + 26 + i * 17))


TARJETAS = [
    Tarjeta("CORTÁ FRUTAS", "Usá la linterna como una espada: cada fruta es 1 punto.",
            VERDE, animar_cortar),
    Tarjeta("¡BOMBAS NO!", "Si cortás una bomba, perdés una vida.", ROJO, animar_bomba),
    Tarjeta("QUE NO CAIGAN", "Cada fruta que se cae sin cortar te saca una vida.",
            AMARILLO, animar_caida),
    Tarjeta("TRIPLE", "3 frutas en un solo trazo te devuelven una vida.", LUZ, animar_triple),
    Tarjeta("BOMBA MORTAL", "Versus: girá la luz en círculos y se la mandás al rival.",
            COLOR_BOMBA_MORTAL, animar_mortal),
]


def dibujar_titulo(pantalla, fuente, tiempo):
    """El título: cada letra sube y baja como una ola y cambia de color."""
    texto = "CORTE DE LUZ"
    x = ANCHO // 2 - fuente.size(texto)[0] // 2
    for i, letra in enumerate(texto):
        ola = math.sin(tiempo * 3 + i * 0.5) * 6
        tono = mezclar(AMARILLO, (255, 120, 0), (math.sin(tiempo * 2 + i * 0.4) + 1) / 2)
        dibujar_texto(pantalla, letra, fuente, tono, (x, int(8 + ola)), False)
        x += fuente.size(letra)[0]


def dibujar_tecla(pantalla, fuente, letra, x, y, tiempo):
    """Una tecla amarilla que "late", para mostrar qué apretar."""
    latido = (math.sin(tiempo * 4) + 1) / 2
    tecla = pygame.Rect(x, y + int(2 * latido), 48, 48)
    pygame.draw.rect(pantalla, CONTORNO, tecla.move(0, 4), border_radius=10)    # sombra
    pygame.draw.rect(pantalla, mezclar(AMARILLO, BLANCO, latido * 0.4), tecla, border_radius=10)
    pygame.draw.rect(pantalla, CONTORNO, tecla, 2, border_radius=10)
    imagen = fuente.render(letra, True, CONTORNO)
    pantalla.blit(imagen, imagen.get_rect(center=tecla.center))


def dibujar_inicio(pantalla, fuentes, imagenes, tiempo, hay_luz, color, record, umbral):
    """Dibuja toda la pantalla de inicio."""
    centro = ANCHO // 2
    dibujar_titulo(pantalla, fuentes["titulo"], tiempo)

    # Las tarjetas con las reglas (cada animación arranca un poco después que la anterior)
    total = len(TARJETAS) * TARJETA_ANCHO + (len(TARJETAS) - 1) * SEPARACION_TARJETAS
    x = (ANCHO - total) // 2
    for i, tarjeta in enumerate(TARJETAS):
        tarjeta.dibujar(pantalla, x + i * (TARJETA_ANCHO + SEPARACION_TARJETAS), Y_TARJETAS,
                        fuentes, imagenes, tiempo + i * DESFASE_TARJETAS)

    y = Y_TARJETAS + TARJETA_ALTO + 16
    dibujar_texto(pantalla, "Tenés 3 vidas  ·  el juego no termina: se pone cada vez más difícil "
                  " ·  jugá hasta perder", fuentes["chica"], BLANCO, (centro, y))

    # Los dos modos, con la tecla para empezar cada uno
    if record > 0:
        detalle_solo = f"Superá el récord: {record} frutas"
    else:
        detalle_solo = "¡Hacé el primer récord!"
    modos = (("1", "UN JUGADOR", detalle_solo),
             ("2", "VERSUS", "Dos linternas, pantalla dividida"))
    y += 20
    for i, (tecla, titulo, detalle) in enumerate(modos):
        x = centro - 350 + i * 360
        pantalla.blit(imagenes["modo"], (x, y))
        dibujar_tecla(pantalla, fuentes["grande"], tecla, x + 14, y + 11, tiempo + i)
        dibujar_texto(pantalla, titulo, fuentes["media"], AMARILLO, (x + 76, y + 12), False)
        dibujar_texto(pantalla, detalle, fuentes["texto"], BLANCO, (x + 76, y + 44), False)

    # Estado de la linterna y color elegido
    y += 98
    if hay_luz:
        dibujar_texto(pantalla, "Linterna detectada", fuentes["media"], VERDE, (centro - 190, y))
    else:
        dibujar_texto(pantalla, "No veo la linterna", fuentes["media"], ROJO, (centro - 190, y))
    nombre_color, tono = color
    dibujar_texto(pantalla, f"C = color de la luz: {nombre_color}", fuentes["media"], tono,
                  (centro + 190, y))
    dibujar_texto(pantalla, f"+/- umbral de brillo ({umbral})   ·   M = ver la luz   ·   "
                  "F = pantalla completa   ·   ESC = salir", fuentes["chica"], GRIS, (centro, ALTO - 16))
