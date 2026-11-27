"""La interfaz: textos, teclas dibujadas (que también son botones), paneles y los adornos
del dojo (faroles, sello, ensō).
"""

import math
import pygame

from ajustes import (AMARILLO, BLANCO, COLOR_FONDO_BARRA, COLOR_VIDA_VACIA, CONTORNO,
                     CORRIDA_SOMBRA, ESPACIO_TECLA, GRIS, LACA, LUZ_VELA, MADERA, MADERA_CLARA,
                     NEGRO, OPACIDAD_SHOJI, ROJO, ROJO_FAROL, SEPARACION_ATAJOS, SHOJI_COLUMNAS,
                     SHOJI_FILAS, SOMBRA_TEXTO)
from graficos import (S, achicar, mezclar, ovalo_con_volumen)


# ---------------------------------------------------------------------------
# Pantalla e interfaz
# ---------------------------------------------------------------------------

# Zonas de la pantalla que se pueden clickear: cada tecla dibujada es también un botón,
# como en cualquier programa. Es una lista de (rectángulo, tecla). Se vacía al empezar
# a dibujar cada cuadro y se va llenando mientras se dibuja; main.py la usa al hacer clic.
zonas_clic = []


def registrar_zona(rect, etiqueta):
    """Anota que hacer clic en `rect` es lo mismo que apretar la tecla `etiqueta`."""
    zonas_clic.append((pygame.Rect(rect), etiqueta))


def tecla_en(posicion):
    """Devuelve la tecla del botón que está en `posicion`, o None si no hay ninguno.
    Se recorre de atrás para adelante: gana lo que se dibujó último (lo de arriba)."""
    for rect, etiqueta in reversed(zonas_clic):
        if rect.collidepoint(posicion):
            return etiqueta
    return None


def ancho_tecla(fuente, letra, alto):
    """Devuelve el ancho de una tecla dibujada: cuadrada si es una letra, más
    larga si dice una palabra (ESC, ESPACIO, ENTER)."""
    return max(alto, fuente.size(letra)[0] + alto // 2)


def dibujar_tecla_chica(pantalla, fuente, letra, x, y, alto, color):
    """Dibuja una tecla como la de un teclado, con `letra` adentro y la esquina de
    arriba a la izquierda en (x, y). Devuelve su ancho, para dibujar lo que sigue al lado."""
    ancho = ancho_tecla(fuente, letra, alto)
    tecla = pygame.Rect(int(x), int(y), ancho, alto)
    radio = max(3, alto // 5)
    # el costado de la tecla, del mismo color pero más oscuro (sin contorno negro)
    pygame.draw.rect(pantalla, mezclar(color, NEGRO, 0.5), tecla.move(0, 2), border_radius=radio)
    pygame.draw.rect(pantalla, color, tecla, border_radius=radio)
    imagen = fuente.render(letra, True, CONTORNO)
    pantalla.blit(imagen, imagen.get_rect(center=tecla.center))
    return ancho


def medir_atajos(atajos, fuente_texto, fuente_tecla, alto):
    """Devuelve el ancho total de una fila de atajos (las teclas y sus textos)."""
    total = 0
    for i, (teclas, texto) in enumerate(atajos):
        for letra in teclas:
            total += ancho_tecla(fuente_tecla, letra, alto) + ESPACIO_TECLA
        total += fuente_texto.size(texto)[0]
        if i < len(atajos) - 1:
            total += SEPARACION_ATAJOS
    return total


def dibujar_atajos(pantalla, atajos, fuente_texto, fuente_tecla, alto, color_texto, color_tecla,
                   posicion, centrado=True):
    """Dibuja una fila de atajos: cada uno es (teclas, texto), por ejemplo
    (("ESC",), "salir") o (("+", "-"), "brillo"). Cada tecla se dibuja como la de un
    teclado y el texto va al lado. `posicion` es el centro de la fila (o, si `centrado`
    es False, su punta izquierda), a la altura del medio de las teclas."""
    x, y = posicion
    if centrado:
        x -= medir_atajos(atajos, fuente_texto, fuente_tecla, alto) // 2
    raton = pygame.mouse.get_pos()
    for teclas, texto in atajos:
        # todo el atajo (teclas y texto) es un botón: se ilumina con el mouse encima
        ancho = medir_atajos([(teclas, texto)], fuente_texto, fuente_tecla, alto)
        zona = pygame.Rect(int(x) - 4, y - alto // 2 - 4, ancho + 8, alto + 8)
        encima = zona.collidepoint(raton)
        registrar_zona(zona, teclas[0])
        tono_tecla = mezclar(color_tecla, BLANCO, 0.45) if encima else color_tecla
        for letra in teclas:
            ancho_letra = dibujar_tecla_chica(pantalla, fuente_tecla, letra, x, y - alto // 2 - 1, alto,
                                              tono_tecla)
            if len(teclas) > 1:
                # si hay varias teclas (+ y -), cada una es su propio botón
                registrar_zona((int(x), y - alto // 2 - 1, ancho_letra, alto), letra)
            x += ancho_letra + ESPACIO_TECLA
        dibujar_texto(pantalla, texto, fuente_texto, BLANCO if encima else color_texto,
                      (x, y - fuente_texto.get_height() // 2), False)
        x += fuente_texto.size(texto)[0] + SEPARACION_ATAJOS


def dibujar_texto(pantalla, mensaje, fuente, color, posicion, centrado=True):
    """Escribe un texto con una sombra suave debajo, para que se lea sobre la cámara
    sin necesidad de un contorno grueso."""
    imagen = fuente.render(mensaje, True, color)
    sombra = fuente.render(mensaje, True, NEGRO)
    sombra.set_alpha(SOMBRA_TEXTO)
    rect = imagen.get_rect()
    if centrado:
        rect.center = posicion
    else:
        rect.topleft = posicion
    pantalla.blit(sombra, rect.move(0, CORRIDA_SOMBRA))
    pantalla.blit(imagen, rect)


def crear_fondo(ancho, alto, color, alfa_centro, alfa_borde, pasos=24):
    """Devuelve la capa que va encima de la cámara: la oscurece (más en los
    bordes, efecto "viñeta") y le pone la reja de madera de un shoji, el panel
    de papel de los dojos japoneses. Así la cámara se ve como detrás de un shoji
    de noche."""
    sup = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    sup.fill((*color, alfa_borde))
    for i in range(pasos):
        t = i / (pasos - 1)                     # 0 = afuera, 1 = el centro
        alfa = int(alfa_borde + (alfa_centro - alfa_borde) * t)
        rect = pygame.Rect(0, 0, int(ancho * (1.5 - 0.9 * t)), int(alto * (1.5 - 0.9 * t)))
        rect.center = (ancho // 2, alto // 2)
        pygame.draw.ellipse(sup, (*color, alfa), rect)

    # La reja va en otra superficie que después se pega encima (así se mezcla
    # con la viñeta en vez de reemplazarla).
    reja = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    madera = (*MADERA_CLARA, OPACIDAD_SHOJI)
    for i in range(1, SHOJI_COLUMNAS):
        x = ancho * i // SHOJI_COLUMNAS
        pygame.draw.line(reja, madera, (x, 0), (x, alto), 2)
    for j in range(1, SHOJI_FILAS):
        y = alto * j // SHOJI_FILAS
        pygame.draw.line(reja, madera, (0, y), (ancho, y), 2)
    # el marco: una viga arriba y abajo y dos postes a los costados, más oscuros
    marco = (*MADERA, 235)
    pygame.draw.rect(reja, marco, (0, 0, ancho, 7))
    pygame.draw.rect(reja, marco, (0, alto - 7, ancho, 7))
    pygame.draw.rect(reja, marco, (0, 0, 7, alto))
    pygame.draw.rect(reja, marco, (ancho - 7, 0, 7, alto))
    sup.blit(reja, (0, 0))
    return sup


def crear_panel(ancho, alto):
    """Devuelve un panel de laca negra con un filete dorado, para poner textos encima."""
    sup = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    rect = sup.get_rect()
    # un solo filete, fino y tenue: el panel acompaña sin recargar
    pygame.draw.rect(sup, (*LACA, 200), rect, border_radius=8)
    pygame.draw.rect(sup, (*AMARILLO, 70), rect, 1, border_radius=8)
    return sup


def crear_vida(tam, llena):
    """Devuelve el ícono de una vida: un sello redondo bermellón, o un círculo
    vacío si se perdió. Se dibuja al doble y se achica para que quede suave."""
    lado = tam * S
    sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
    centro = (lado / 2, lado / 2)
    r = lado * 0.42
    if llena:
        pygame.draw.circle(sup, CONTORNO, centro, r + S)
        pygame.draw.circle(sup, ROJO, centro, r)
        # anillo de adentro, como el borde de un sello
        pygame.draw.circle(sup, mezclar(ROJO, BLANCO, 0.35), centro, r * 0.62, max(1, int(1.3 * S)))
        pygame.draw.circle(sup, mezclar(ROJO, BLANCO, 0.6), (centro[0] - r * 0.4, centro[1] - r * 0.4), r * 0.16)
    else:
        pygame.draw.circle(sup, COLOR_VIDA_VACIA, centro, r)
        pygame.draw.circle(sup, GRIS, centro, r, S)
    return achicar(sup)


def dibujar_enso(sup, centro, radio, color, grosor, avance=1.0):
    """Dibuja un ensō: el círculo zen pintado de una sola pincelada. Empieza
    finito, engorda en el medio, termina "seco" y queda abierto.
    `avance` (de 0 a 1) dice cuánto del trazo ya se pintó (para animarlo)."""
    pasos = 180
    largo = 0.9                         # el círculo no se cierra del todo
    cx, cy = centro
    for i in range(int(pasos * min(1.0, avance))):
        f = i / pasos
        if f > 0.8 and i % 3 == 0:
            continue                    # al final al pincel le falta tinta: queda cortado
        angulo = math.radians(-100) + f * largo * 2 * math.pi
        ancho = grosor * (0.3 + 0.7 * math.sin(math.pi * min(1.0, f * 1.1)))
        temblor = 1 + 0.025 * math.sin(f * 37)       # la mano no es perfecta
        x = cx + math.cos(angulo) * radio * temblor
        y = cy + math.sin(angulo) * radio * temblor
        pygame.draw.circle(sup, color, (int(x), int(y)), max(1, int(ancho / 2)))


def crear_farol(alto):
    """Devuelve un farol de papel rojo (chōchin), como los que cuelgan en un dojo."""
    ancho = int(alto * 0.62)
    w, h = ancho * S, alto * S
    sup = pygame.Surface((w, h), pygame.SRCALPHA)
    cuerpo = pygame.Rect(0, int(h * 0.12), w, int(h * 0.76))
    pygame.draw.ellipse(sup, CONTORNO, cuerpo.inflate(2 * S, 2 * S))
    ovalo_con_volumen(sup, cuerpo.center, cuerpo.width, cuerpo.height, ROJO_FAROL)
    # adentro hay una vela: el centro brilla más
    ovalo_con_volumen(sup, cuerpo.center, cuerpo.width * 0.55, cuerpo.height * 0.6,
                      mezclar(ROJO_FAROL, LUZ_VELA, 0.6), 8)
    # las costillas de bambú del farol
    for k in range(1, 6):
        y = cuerpo.top + cuerpo.height * k / 6
        dy = (y - cuerpo.centery) / (cuerpo.height / 2)
        mitad = cuerpo.width / 2 * math.sqrt(max(0.0, 1 - dy * dy))
        pygame.draw.line(sup, mezclar(ROJO_FAROL, NEGRO, 0.45),
                         (cuerpo.centerx - mitad + S, y), (cuerpo.centerx + mitad - S, y), S)
    # las tapas de arriba y de abajo
    tapa = pygame.Rect(0, 0, int(w * 0.55), int(h * 0.13))
    for y in (h * 0.07, h * 0.93):
        tapa.center = (w // 2, int(y))
        pygame.draw.rect(sup, CONTORNO, tapa, border_radius=2 * S)
    return achicar(sup)


def crear_sello(texto, fuente, tam):
    """Devuelve un sello rojo (hanko) con un kanji, un poco torcido como si lo
    hubieran estampado a mano. Devuelve None si la fuente no tiene ese kanji."""
    metricas = fuente.metrics(texto)
    if not metricas or metricas[0] is None or metricas[0][1] == 0:
        return None
    sup = pygame.Surface((tam, tam), pygame.SRCALPHA)
    pygame.draw.rect(sup, ROJO, sup.get_rect(), border_radius=tam // 10)
    pygame.draw.rect(sup, mezclar(ROJO, BLANCO, 0.3), sup.get_rect().inflate(-tam // 7, -tam // 7),
                     max(1, tam // 30), border_radius=tam // 14)
    letra = fuente.render(texto, True, BLANCO)
    sup.blit(letra, letra.get_rect(center=(tam // 2, tam // 2 + 2)))
    return pygame.transform.rotozoom(sup, -6, 1)


def dibujar_farol(pantalla, farol, halo, x, largo_cuerda, tiempo, fase=0.0):
    """Dibuja un farol colgado del techo en x, que se balancea despacio."""
    angulo = math.radians(4 * math.sin(tiempo * 1.3 + fase))
    largo = largo_cuerda + farol.get_height() / 2
    cx = x + math.sin(angulo) * largo
    cy = math.cos(angulo) * largo
    arriba = (x + math.sin(angulo) * largo_cuerda, math.cos(angulo) * largo_cuerda)
    pygame.draw.line(pantalla, CONTORNO, (x, 0), arriba, 2)
    halo.set_alpha(int(150 + 30 * math.sin(tiempo * 2.1 + fase)))     # la vela titila
    pantalla.blit(halo, halo.get_rect(center=(int(cx), int(cy))))
    imagen = pygame.transform.rotozoom(farol, math.degrees(-angulo), 1)
    pantalla.blit(imagen, imagen.get_rect(center=(int(cx), int(cy))))


def dibujar_barra(pantalla, rect, fraccion, color):
    """Barra de progreso: se llena según `fraccion` (de 0 a 1)."""
    pygame.draw.rect(pantalla, COLOR_FONDO_BARRA, rect, border_radius=rect.height // 2)
    if fraccion > 0:
        lleno = rect.copy()
        lleno.width = max(rect.height, int(rect.width * min(1, fraccion)))
        pygame.draw.rect(pantalla, color, lleno, border_radius=rect.height // 2)
        reflejo = lleno.inflate(-6, -rect.height // 2)
        reflejo.top = lleno.top + 3
        pygame.draw.rect(pantalla, mezclar(color, BLANCO, 0.45), reflejo, border_radius=4)
    pygame.draw.rect(pantalla, BLANCO, rect, 2, border_radius=rect.height // 2)
