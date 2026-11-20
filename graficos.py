"""Funciones de dibujo: arman las imágenes de las frutas, las bombas y los
efectos (brillo de la espada, corazones, barras, paneles).

No se cargan imágenes de archivos: todo se dibuja con pygame. Las imágenes de
cada fruta se arman una sola vez, cuando la fruta aparece, y después solo se
giran y se pegan en la pantalla.

Truco para que los bordes queden suaves: las imágenes se dibujan al doble de
tamaño (S = 2) y después se achican con smoothscale, que mezcla los píxeles
del borde (es un "antialiasing" casero).
"""

import math
import random

import pygame

from ajustes import (BLANCO, NEGRO, CONTORNO, MARRON, VERDE_HOJA, GRIS,
                     GROSOR_RASTRO)

S = 2   # las imágenes se dibujan S veces más grandes y después se achican


# ---------------------------------------------------------------------------
# Herramientas básicas
# ---------------------------------------------------------------------------

def mezclar(color1, color2, t):
    """Devuelve un color intermedio: t=0 es color1, t=1 es color2."""
    return tuple(int(a + (b - a) * t) for a, b in zip(color1, color2))


def ovalo_con_volumen(sup, centro, ancho, alto, color, pasos=14):
    """Dibuja un óvalo sombreado para que parezca una esfera (3D): oscuro
    abajo a la derecha y claro arriba a la izquierda, donde "pega la luz".
    Son varios óvalos uno encima del otro, cada uno más chico, más claro y
    más corrido hacia arriba a la izquierda."""
    oscuro = mezclar(color, NEGRO, 0.45)
    claro = mezclar(color, BLANCO, 0.4)
    cx, cy = centro
    for i in range(pasos):
        t = i / (pasos - 1)
        if t < 0.3:
            tono = mezclar(oscuro, color, t / 0.3)
        else:
            tono = mezclar(color, claro, (t - 0.3) / 0.7)
        w = ancho * (1 - 0.65 * t)
        h = alto * (1 - 0.65 * t)
        rect = pygame.Rect(0, 0, int(w), int(h))
        rect.center = (int(cx - ancho * 0.15 * t), int(cy - alto * 0.15 * t))
        pygame.draw.ellipse(sup, tono, rect)


def achicar(sup):
    """Devuelve la imagen achicada S veces, con los bordes suavizados."""
    ancho, alto = sup.get_size()
    return pygame.transform.smoothscale(sup, (ancho // S, alto // S))


def brillito(sup, centro, radio, color):
    """El reflejo blanco que hace que una fruta parezca brillante."""
    rect = pygame.Rect(0, 0, int(radio * 0.5), int(radio * 0.3))
    rect.center = (int(centro[0] - radio * 0.4), int(centro[1] - radio * 0.45))
    pygame.draw.ellipse(sup, mezclar(color, BLANCO, 0.8), rect)


def hoja(sup, base, largo, angulo):
    """Dibuja una hoja con forma de rombo que sale de `base` hacia `angulo` (grados)."""
    a = math.radians(angulo)
    dx, dy = math.cos(a), -math.sin(a)          # hacia dónde apunta la hoja
    px, py = -dy, dx                            # perpendicular (el ancho)
    bx, by = base
    punta = (bx + dx * largo, by + dy * largo)
    medio = (bx + dx * largo * 0.5, by + dy * largo * 0.5)
    ancho = largo * 0.32
    puntos = [base, (medio[0] + px * ancho, medio[1] + py * ancho),
              punta, (medio[0] - px * ancho, medio[1] - py * ancho)]
    pygame.draw.polygon(sup, CONTORNO, puntos, 0)
    adentro = [(x + (medio[0] - x) * 0.18, y + (medio[1] - y) * 0.18) for x, y in puntos]
    pygame.draw.polygon(sup, VERDE_HOJA, adentro)
    pygame.draw.line(sup, mezclar(VERDE_HOJA, NEGRO, 0.4), base, punta, 2 * S)


def superficie_para(radio):
    """Devuelve una superficie transparente con lugar para una fruta de ese
    radio (y un poco más, para el tallo y la hoja), y su centro."""
    lado = int(radio * 2.8)
    return pygame.Surface((lado, lado), pygame.SRCALPHA), (lado // 2, lado // 2)


# ---------------------------------------------------------------------------
# Frutas
# ---------------------------------------------------------------------------

def crear_imagen_fruta(tipo, radio):
    """Devuelve la imagen de una fruta entera, según su tipo."""
    sup, (cx, cy) = superficie_para(radio * S)
    r = radio * S
    nombre = tipo["tipo"]
    color = tipo["color"]
    oscuro = mezclar(color, NEGRO, 0.35)
    azar = random.Random(radio)     # "azar" fijo: la textura no cambia entre cuadros

    if nombre == "uva":
        u = r * 0.4
        detras = [(-0.8, -0.6), (0.8, -0.6), (0, 0.8)]
        delante = [(-1.6, -1.3), (0, -1.4), (1.6, -1.3), (-0.8, 0.1), (0.8, 0.1), (0, 1.5)]
        for fila, tono in ((detras, oscuro), (delante, color)):
            for dx, dy in fila:
                centro = (cx + dx * u, cy + dy * u)
                pygame.draw.circle(sup, CONTORNO, centro, u + 2 * S)
                ovalo_con_volumen(sup, centro, 2 * u, 2 * u, tono, 8)
                pygame.draw.circle(sup, mezclar(tono, BLANCO, 0.75),
                                   (centro[0] - u * 0.35, centro[1] - u * 0.35), u * 0.2)
        pygame.draw.line(sup, MARRON, (cx, cy - 1.9 * u), (cx + 0.15 * r, cy - 1.25 * r), 5 * S)
        hoja(sup, (cx + 0.1 * r, cy - 1.1 * r), r * 0.5, 20)
        return achicar(sup)

    if nombre == "limon":
        ancho, alto = 2 * r, 1.5 * r
        for lado in (-1, 1):            # las dos puntitas
            pygame.draw.circle(sup, CONTORNO, (cx + lado * r, cy), r * 0.22)
            pygame.draw.circle(sup, oscuro, (cx + lado * r, cy), r * 0.22 - 2 * S)
        borde = pygame.Rect(0, 0, int(ancho + 6 * S), int(alto + 6 * S))
        borde.center = (cx, cy)
        pygame.draw.ellipse(sup, CONTORNO, borde)
        ovalo_con_volumen(sup, (cx, cy), ancho, alto, color)
        for _ in range(18):             # poros de la cáscara
            x = cx + azar.uniform(-0.75, 0.75) * r
            y = cy + azar.uniform(-0.5, 0.5) * r
            pygame.draw.circle(sup, mezclar(color, NEGRO, 0.12), (x, y), 1.5 * S)
        brillito(sup, (cx, cy), r, color)
        hoja(sup, (cx, cy - 0.7 * r), r * 0.55, 60)
        return achicar(sup)

    # El resto son redondas.
    pygame.draw.circle(sup, CONTORNO, (cx, cy), r + 3 * S)
    ovalo_con_volumen(sup, (cx, cy), 2 * r, 2 * r, color)

    if nombre == "sandia":
        rayas = mezclar(color, NEGRO, 0.5)
        for ancho in (0.45, 1.05, 1.6):
            rect = pygame.Rect(0, 0, int(r * ancho), int(2 * r - 6 * S))
            rect.center = (cx, cy)
            pygame.draw.ellipse(sup, rayas, rect, 5 * S)
    elif nombre == "naranja":
        for _ in range(35):             # los poros de la naranja
            ang = azar.uniform(0, 2 * math.pi)
            dist = r * math.sqrt(azar.uniform(0, 0.8))
            pygame.draw.circle(sup, mezclar(color, NEGRO, 0.18),
                               (cx + math.cos(ang) * dist, cy + math.sin(ang) * dist), 1.5 * S)
    elif nombre == "kiwi":
        for _ in range(90):             # pelusa: rayitas cortas
            ang = azar.uniform(0, 2 * math.pi)
            dist = r * math.sqrt(azar.uniform(0, 0.85))
            x, y = cx + math.cos(ang) * dist, cy + math.sin(ang) * dist
            tono = mezclar(color, NEGRO if azar.random() < 0.5 else BLANCO, 0.3)
            pygame.draw.line(sup, tono, (x, y), (x + azar.uniform(-3, 3) * S, y + 3 * S), S)

    if nombre != "kiwi":
        brillito(sup, (cx, cy), r, color)
    if nombre == "manzana":
        hundido = pygame.Rect(0, 0, int(r * 0.45), int(r * 0.18))
        hundido.center = (cx, int(cy - r * 0.86))
        pygame.draw.ellipse(sup, mezclar(color, NEGRO, 0.5), hundido)
        pygame.draw.line(sup, MARRON, (cx, cy - 0.85 * r), (cx + 0.15 * r, cy - 1.25 * r), 5 * S)
        hoja(sup, (cx + 0.08 * r, cy - 1.05 * r), r * 0.55, 25)
    elif nombre == "naranja":
        pygame.draw.circle(sup, MARRON, (cx, cy - r * 0.92), 4 * S)
        hoja(sup, (cx, cy - 0.95 * r), r * 0.5, 140)
    return achicar(sup)


def crear_imagen_corte(tipo, radio):
    """Devuelve cómo se ve la fruta por dentro, cortada al medio (cara entera)."""
    sup, (cx, cy) = superficie_para(radio * S)
    r = radio * S
    nombre = tipo["tipo"]
    pulpa = tipo["pulpa"]
    azar = random.Random(radio + 1)
    corteza = (235, 245, 205) if nombre == "sandia" else mezclar(pulpa, BLANCO, 0.5)

    pygame.draw.circle(sup, CONTORNO, (cx, cy), r + 3 * S)
    pygame.draw.circle(sup, tipo["color"], (cx, cy), r)       # cáscara
    pygame.draw.circle(sup, corteza, (cx, cy), r * 0.9)       # parte blanca
    pygame.draw.circle(sup, pulpa, (cx, cy), r * 0.8)         # pulpa
    # un poco más clara en el centro
    pygame.draw.circle(sup, mezclar(pulpa, BLANCO, 0.25), (cx, cy), r * 0.45)

    if nombre in ("naranja", "limon"):
        linea = mezclar(pulpa, BLANCO, 0.6)
        for i in range(8):              # gajos
            ang = i * math.pi / 4
            pygame.draw.line(sup, linea, (cx, cy),
                             (cx + math.cos(ang) * r * 0.78, cy + math.sin(ang) * r * 0.78), 3 * S)
        pygame.draw.circle(sup, linea, (cx, cy), r * 0.12)
    elif nombre == "sandia":
        for _ in range(9):              # semillas negras
            ang = azar.uniform(0, 2 * math.pi)
            dist = r * azar.uniform(0.25, 0.6)
            semilla = pygame.Rect(0, 0, 5 * S, 9 * S)
            semilla.center = (int(cx + math.cos(ang) * dist), int(cy + math.sin(ang) * dist))
            pygame.draw.ellipse(sup, NEGRO, semilla)
    elif nombre == "kiwi":
        pygame.draw.circle(sup, mezclar(pulpa, BLANCO, 0.6), (cx, cy), r * 0.22)
        for i in range(16):             # anillo de semillitas
            ang = i * 2 * math.pi / 16
            pygame.draw.circle(sup, NEGRO, (cx + math.cos(ang) * r * 0.38,
                                            cy + math.sin(ang) * r * 0.38), 2.5 * S)
    elif nombre == "manzana":
        for dx in (-0.12, 0.12):        # dos semillas marrones
            semilla = pygame.Rect(0, 0, 7 * S, 12 * S)
            semilla.center = (int(cx + dx * r), int(cy))
            pygame.draw.ellipse(sup, MARRON, semilla)
    return achicar(sup)


def crear_imagen_mitad(tipo, radio, lado):
    """Devuelve media fruta cortada: la mitad izquierda (lado -1) o derecha (lado 1)."""
    cara = crear_imagen_corte(tipo, radio)
    ancho, alto = cara.get_size()
    mitad = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    if lado < 0:
        recorte = pygame.Rect(0, 0, ancho // 2, alto)
    else:
        recorte = pygame.Rect(ancho // 2, 0, ancho - ancho // 2, alto)
    mitad.blit(cara, recorte.topleft, recorte)
    return mitad


# ---------------------------------------------------------------------------
# Bombas
# ---------------------------------------------------------------------------

def punta_de_mecha(radio):
    """Devuelve dónde termina la mecha, medido desde el centro de la bomba."""
    return (radio * 0.45, -radio * 1.2)


def crear_imagen_bomba(radio, mortal=False):
    """Devuelve la imagen de una bomba. La mortal es violeta y tiene una calavera."""
    sup, (cx, cy) = superficie_para(radio * S)
    r = radio * S
    color = (110, 30, 170) if mortal else (55, 55, 70)

    # mecha (una curvita) y la tapita de metal
    mx, my = punta_de_mecha(r)
    puntos = [(cx, cy - r * 0.95), (cx + r * 0.1, cy - r * 1.15),
              (cx + r * 0.3, cy - r * 1.1), (cx + mx, cy + my)]
    pygame.draw.lines(sup, CONTORNO, False, puntos, 7 * S)
    pygame.draw.lines(sup, (200, 170, 120), False, puntos, 3 * S)
    tapa = pygame.Rect(0, 0, int(r * 0.5), int(r * 0.3))
    tapa.center = (cx, int(cy - r * 0.92))
    pygame.draw.rect(sup, CONTORNO, tapa.inflate(4 * S, 4 * S), border_radius=4 * S)
    pygame.draw.rect(sup, GRIS, tapa, border_radius=3 * S)

    pygame.draw.circle(sup, CONTORNO, (cx, cy), r + 3 * S)
    ovalo_con_volumen(sup, (cx, cy), 2 * r, 2 * r, color)
    brillito(sup, (cx, cy), r, color)

    if mortal:
        # calavera
        cabeza = pygame.Rect(0, 0, int(r * 0.95), int(r * 0.8))
        cabeza.center = (cx, int(cy - r * 0.05))
        pygame.draw.ellipse(sup, BLANCO, cabeza)
        mandibula = pygame.Rect(0, 0, int(r * 0.55), int(r * 0.32))
        mandibula.center = (cx, int(cy + r * 0.38))
        pygame.draw.rect(sup, BLANCO, mandibula, border_radius=4 * S)
        for dx in (-0.2, 0.2):
            pygame.draw.circle(sup, NEGRO, (cx + dx * r, cy - r * 0.08), r * 0.15)
        pygame.draw.polygon(sup, NEGRO, [(cx, cy + r * 0.08), (cx - 4 * S, cy + r * 0.2), (cx + 4 * S, cy + r * 0.2)])
        for dx in (-0.12, 0, 0.12):
            pygame.draw.line(sup, NEGRO, (cx + dx * r, cy + r * 0.3), (cx + dx * r, cy + r * 0.52), 2 * S)
    else:
        # una X roja de advertencia
        x = r * 0.3
        for a, b in (((-x, -x), (x, x)), ((x, -x), (-x, x))):
            pygame.draw.line(sup, (230, 40, 40), (cx + a[0], cy + a[1]), (cx + b[0], cy + b[1]), 6 * S)
    return achicar(sup)


def dibujar_chispa(pantalla, x, y):
    """La chispa de la mecha: cambia de tamaño cada cuadro, así titila."""
    for color, tam in (((255, 120, 0), 9), ((255, 230, 60), 6), (BLANCO, 3)):
        pygame.draw.circle(pantalla, color, (int(x), int(y)), tam + random.randint(-2, 2))


def crear_halo(radio, color, alfa_maximo=150, pasos=14):
    """Devuelve un círculo de luz que se desvanece hacia afuera (para la
    bomba mortal y la bola que se carga). Se dibujan círculos de afuera
    hacia adentro, cada uno más opaco que el anterior."""
    lado = radio * 2
    sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
    for i in range(pasos):
        t = i / pasos
        alfa = int(alfa_maximo * t * t)
        pygame.draw.circle(sup, (*color, alfa), (radio, radio), radio * (1 - t * 0.85))
    return sup


# ---------------------------------------------------------------------------
# Espada de luz (se dibuja en una capa que después se SUMA a la pantalla)
# ---------------------------------------------------------------------------

def difuminar(sup, veces):
    """Devuelve la imagen borroneada: se achica a la mitad y se vuelve a agrandar
    varias veces. Al achicarla, cada píxel se mezcla con sus vecinos."""
    ancho, alto = sup.get_size()
    for _ in range(veces):
        chica = pygame.transform.smoothscale(sup, (ancho // 2, alto // 2))
        sup = pygame.transform.smoothscale(chica, (ancho, alto))
    return sup


def dibujar_espada(capa_suave, capa_nitida, puntos, color, luz):
    """Dibuja el punto de luz y su estela con brillo, teñidos del color elegido
    (el "filtro de color"). Las dos capas se SUMAN a la pantalla (BLEND_ADD):
    el negro no cambia nada y los colores "iluminan".

    - capa_suave es chiquita (un cuarto del tamaño): ahí va el brillo ancho.
      Después se agranda y queda borroso, como un resplandor.
    - capa_nitida es del tamaño de la pantalla: ahí va el centro, más claro
      pero del mismo color."""
    f = capa_suave.get_width() / capa_nitida.get_width()   # 0.25
    centro = mezclar(color, BLANCO, 0.35)                  # el centro: el color, un poco aclarado
    n = len(puntos)
    for capa, escala, pasadas in ((capa_suave, f, ((4.0, 0.8),)),
                                  (capa_nitida, 1, ((1.6, 0.75), (0.6, None)))):
        for factor, intensidad in pasadas:
            tono = centro if intensidad is None else mezclar(NEGRO, color, intensidad)
            for i in range(1, n):
                t = i / (n - 1)                 # 0 = la parte vieja, 1 = la más nueva
                grosor = max(1, int((2 + GROSOR_RASTRO * t) * factor * escala))
                a = (puntos[i - 1][0] * escala, puntos[i - 1][1] * escala)
                b = (puntos[i][0] * escala, puntos[i][1] * escala)
                pygame.draw.line(capa, tono, a, b, grosor)
                pygame.draw.circle(capa, tono, b, grosor / 2)
    if luz is not None:
        pygame.draw.circle(capa_suave, mezclar(NEGRO, color, 0.9), (luz[0] * f, luz[1] * f), 36 * f)
        pygame.draw.circle(capa_nitida, mezclar(NEGRO, color, 0.8), luz, 12)
        pygame.draw.circle(capa_nitida, centro, luz, 7)


# ---------------------------------------------------------------------------
# Pantalla e interfaz
# ---------------------------------------------------------------------------

def dibujar_texto(pantalla, mensaje, fuente, color, posicion, centrado=True):
    """Escribe un texto con borde oscuro para que se lea sobre la cámara."""
    borde = fuente.render(mensaje, True, CONTORNO)
    imagen = fuente.render(mensaje, True, color)
    rect = imagen.get_rect()
    if centrado:
        rect.center = posicion
    else:
        rect.topleft = posicion
    # el mismo texto en oscuro, corrido un poquito para cada lado, hace de borde
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (3, 3)):
        pantalla.blit(borde, rect.move(dx, dy))
    pantalla.blit(imagen, rect)


def crear_fondo(ancho, alto, color, alfa_centro, alfa_borde, pasos=24):
    """Devuelve la capa que oscurece la cámara: más oscura en los bordes
    (efecto "viñeta"), así la atención va al centro."""
    sup = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    sup.fill((*color, alfa_borde))
    for i in range(pasos):
        t = i / (pasos - 1)                     # 0 = afuera, 1 = el centro
        alfa = int(alfa_borde + (alfa_centro - alfa_borde) * t)
        rect = pygame.Rect(0, 0, int(ancho * (1.5 - 0.9 * t)), int(alto * (1.5 - 0.9 * t)))
        rect.center = (ancho // 2, alto // 2)
        pygame.draw.ellipse(sup, (*color, alfa), rect)
    return sup


def crear_panel(ancho, alto):
    """Devuelve un rectángulo redondeado semitransparente para poner el HUD encima."""
    sup = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    pygame.draw.rect(sup, (10, 10, 30, 170), sup.get_rect(), border_radius=14)
    pygame.draw.rect(sup, (255, 255, 255, 60), sup.get_rect(), 2, border_radius=14)
    return sup


def crear_corazon(tam, lleno):
    """Devuelve la imagen de un corazón: rojo si es una vida que queda, gris si
    se perdió. Se dibuja al doble y se achica para que quede suave."""
    lado = tam * 2 * S
    sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
    x, y = lado / 2, lado * 0.42
    r = tam * 0.3 * S
    color = (235, 45, 70) if lleno else (70, 70, 85)
    for tono, extra in ((CONTORNO, 2.5 * S), (color, 0)):
        pygame.draw.circle(sup, tono, (x - r, y - r * 0.3), r + extra)
        pygame.draw.circle(sup, tono, (x + r, y - r * 0.3), r + extra)
        pygame.draw.polygon(sup, tono, [(x - 2 * r - extra, y - r * 0.1),
                                        (x + 2 * r + extra, y - r * 0.1),
                                        (x, y + 1.9 * r + extra * 1.5)])
    if lleno:
        pygame.draw.circle(sup, mezclar(color, BLANCO, 0.6), (x - r * 1.1, y - r * 0.6), r * 0.35)
    return achicar(sup)


def dibujar_barra(pantalla, rect, fraccion, color):
    """Barra de progreso: se llena según `fraccion` (de 0 a 1)."""
    pygame.draw.rect(pantalla, (20, 20, 35), rect, border_radius=rect.height // 2)
    if fraccion > 0:
        lleno = rect.copy()
        lleno.width = max(rect.height, int(rect.width * min(1, fraccion)))
        pygame.draw.rect(pantalla, color, lleno, border_radius=rect.height // 2)
        reflejo = lleno.inflate(-6, -rect.height // 2)
        reflejo.top = lleno.top + 3
        pygame.draw.rect(pantalla, mezclar(color, BLANCO, 0.45), reflejo, border_radius=4)
    pygame.draw.rect(pantalla, BLANCO, rect, 2, border_radius=rect.height // 2)
