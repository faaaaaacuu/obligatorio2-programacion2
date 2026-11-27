"""La intro (dos espadazos de luz y el título), la pantalla de inicio (el título,
los dos modos y si se ve la linterna), la pantalla donde se escriben los nombres
del versus y el abanico para elegir el color de la luz.

Las tarjetas con las reglas y el tutorial están en tarjetas.py.
"""

import math
import os

import pygame

import graficos
import interfaz
from ajustes import (ABERTURA_ABANICO, ALTO, ALTO_TECLA_CHICA, ALTO_TECLA_MEDIA, AMARILLO, ANCHO,
                     APARECE_TITULO, APERTURA_PALETA, ARCHIVO_FUENTE_TEXTO, BLANCO, CAJA_NOMBRE,
                     COLORES_ESPADA, COLOR_BOMBA_MORTAL, COLOR_DESTELLO_INTRO,
                     COLOR_DESTELLO_TARJETA, COLOR_JUGADOR_1, COLOR_JUGADOR_2, CONTORNO,
                     DESENFOQUE_BRILLO, ESPADAZOS, FRUTAS_JUGADOR_1, FRUTAS_JUGADOR_2, GRIS, KANJI,
                     KANJI_COLORES, LACA, LARGO_MAXIMO_NOMBRE, LUZ_FAROL, MADERA, MADERA_CLARA,
                     NEGRO, PANEL_MODO, RADIO_ABANICO, RADIO_CENTRO_ABANICO, RADIO_FRUTA_DEMO,
                     ROJO, SALIENTE_ELEGIDO, SELLO_INTRO, TAMANIO_VIDA_TARJETA, TARJETA_ALTO,
                     TARJETA_ANCHO, TARJETA_ANIMACION_ALTO, TITULO, VELO_PALETA, VERDE, Y_LINTERNA,
                     Y_MODOS)
from graficos import mezclar
from interfaz import (dibujar_atajos, dibujar_texto)
from tarjetas import luz_en


CARPETA = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Imágenes (se arman una sola vez, antes del bucle)
# ---------------------------------------------------------------------------

def crear_imagenes(fuentes):
    """Arma todas las imágenes de la intro y la pantalla de inicio. Devuelve un diccionario."""
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
    imagenes["vidas"] = {True: interfaz.crear_vida(TAMANIO_VIDA_TARJETA, True),
                        False: interfaz.crear_vida(TAMANIO_VIDA_TARJETA, False)}
    rojo = pygame.Surface((TARJETA_ANCHO, TARJETA_ANIMACION_ALTO), pygame.SRCALPHA)
    rojo.fill(COLOR_DESTELLO_TARJETA)
    imagenes["rojo"] = rojo
    imagenes["tarjeta"] = interfaz.crear_panel(TARJETA_ANCHO, TARJETA_ALTO)
    imagenes["modo"] = interfaz.crear_panel(*PANEL_MODO)
    blanco = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    blanco.fill(COLOR_DESTELLO_INTRO)
    imagenes["blanco"] = blanco               # para el destello de la intro
    # estética de dojo: sello rojo con el kanji 光 ("luz") y faroles de papel.
    # (crear_sello devuelve None si la compu no tiene una fuente con ese kanji)
    # el kanji sale de la fuente Potta One; si no estuviera, no se dibuja el sello
    hay_kanji = os.path.exists(os.path.join(CARPETA, ARCHIVO_FUENTE_TEXTO))
    imagenes["sello"] = interfaz.crear_sello(KANJI, fuentes["kanji"], 64) if hay_kanji else None
    imagenes["sello_chico"] = interfaz.crear_sello(KANJI, fuentes["kanji_chico"], 42) if hay_kanji else None
    imagenes["farol"] = interfaz.crear_farol(70)
    imagenes["velo"] = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)   # oscurece lo de atrás de la paleta
    imagenes["velo"].fill((0, 0, 0, VELO_PALETA))
    # lienzo donde se arma cada tarjeta del tutorial antes de agrandarla y girarla
    imagenes["lienzo_tarjeta"] = pygame.Surface((TARJETA_ANCHO, TARJETA_ALTO), pygame.SRCALPHA)
    imagenes["halo_farol"] = graficos.crear_halo(70, LUZ_FAROL, alfa_maximo=90)
    return imagenes


def dibujar_titulo(pantalla, fuente, tiempo, sello):
    """El título con el sello rojo al lado. Las letras se mecen apenas y les
    pasa un brillo dorado, despacio (minimalista)."""
    texto = TITULO.upper()
    ancho = fuente.size(texto)[0]
    if sello is not None:
        ancho += 16 + sello.get_width()
    x = ANCHO // 2 - ancho // 2
    for i, letra in enumerate(texto):
        ola = math.sin(tiempo * 2 + i * 0.5) * 3
        tono = mezclar(AMARILLO, BLANCO, (math.sin(tiempo * 1.5 - i * 0.35) + 1) / 4)
        dibujar_texto(pantalla, letra, fuente, tono, (x, int(10 + ola)), False)
        x += fuente.size(letra)[0]
    if sello is not None:
        pantalla.blit(sello, sello.get_rect(midleft=(x + 16, 10 + fuente.get_height() // 2)))


def dibujar_tecla(pantalla, fuente, letra, x, y, tiempo):
    """Una tecla amarilla que "late", para mostrar qué apretar."""
    latido = (math.sin(tiempo * 4) + 1) / 2
    tecla = pygame.Rect(x, y + int(2 * latido), 48, 48)
    pygame.draw.rect(pantalla, mezclar(AMARILLO, NEGRO, 0.5), tecla.move(0, 3), border_radius=10)   # costado
    pygame.draw.rect(pantalla, mezclar(AMARILLO, BLANCO, latido * 0.4), tecla, border_radius=10)
    imagen = fuente.render(letra, True, CONTORNO)
    pantalla.blit(imagen, imagen.get_rect(center=tecla.center))


def dibujar_inicio(pantalla, fuentes, imagenes, tiempo, hay_luz, color, record, umbral):
    """Dibuja toda la pantalla de inicio."""
    centro = ANCHO // 2
    # dos faroles de papel colgando en las esquinas, que se balancean despacio
    interfaz.dibujar_farol(pantalla, imagenes["farol"], imagenes["halo_farol"], 50, 10, tiempo)
    interfaz.dibujar_farol(pantalla, imagenes["farol"], imagenes["halo_farol"], ANCHO - 50, 10, tiempo, 1.7)
    dibujar_titulo(pantalla, fuentes["titulo"], tiempo, imagenes["sello_chico"])
    # Las reglas no se repiten acá: ya las mostró el tutorial (con R se vuelven a ver).
    # Esta pantalla tiene solo lo necesario para empezar: el modo y si se ve la linterna.

    # Los dos modos, con la tecla para empezar cada uno
    if record > 0:
        detalle_solo = f"Superá el récord: {record} frutas"
    else:
        detalle_solo = "¡Hacé el primer récord!"
    modos = (("1", "UN JUGADOR", detalle_solo),
             ("2", "VERSUS", "Dos linternas, pantalla dividida"))
    y = Y_MODOS
    for i, (tecla, titulo, detalle) in enumerate(modos):
        x = centro - 350 + i * 360
        pantalla.blit(imagenes["modo"], (x, y))
        # todo el panel es un botón: con un clic empieza ese modo
        panel = pygame.Rect((x, y), PANEL_MODO)
        interfaz.registrar_zona(panel, tecla)
        if panel.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(pantalla, BLANCO, panel, 1, border_radius=8)
        dibujar_tecla(pantalla, fuentes["grande"], tecla, x + 14, y + 11, tiempo + i)
        dibujar_texto(pantalla, titulo, fuentes["media"], AMARILLO, (x + 76, y + 12), False)
        dibujar_texto(pantalla, detalle, fuentes["texto"], BLANCO, (x + 76, y + 44), False)

    # Estado de la linterna: es lo único que hay que mirar antes de empezar
    if hay_luz:
        dibujar_texto(pantalla, "Linterna detectada", fuentes["media"], VERDE, (centro, Y_LINTERNA))
    else:
        dibujar_texto(pantalla, "Prendé la linterna y apuntala a la cámara", fuentes["media"], ROJO,
                      (centro, Y_LINTERNA))

    # Las demás teclas, chiquitas abajo (el color de la luz se ve en el nombre del color)
    nombre_color, tono = color
    dibujar_atajos(pantalla, [(("C",), f"color de la luz: {nombre_color}")], fuentes["chica"],
                   fuentes["texto"], ALTO_TECLA_CHICA, tono, tono, (centro, ALTO - 50))
    atajos = [(("R",), "ver las reglas"), (("+", "-"), f"brillo ({umbral})"), (("M",), "ver la luz"),
              (("F",), "pantalla completa"), (("ESC",), "salir")]
    dibujar_atajos(pantalla, atajos, fuentes["chica"], fuentes["texto"], ALTO_TECLA_CHICA, GRIS, GRIS,
                   (centro, ALTO - 20))


# ---------------------------------------------------------------------------
# Intro: lo primero que se ve al abrir el juego
# ---------------------------------------------------------------------------

# Los espadazos, el título y el sello de la intro tienen sus tiempos en ajustes.py.
# Sonidos de la intro: (segundo en que suena, nombre del sonido)
SONIDOS_INTRO = [(ESPADAZOS[0][2], "espadazo"), (ESPADAZOS[1][2], "espadazo"),
                 (APARECE_TITULO, "nivel"), (SELLO_INTRO, "sello")]


def sonidos_a_tocar(antes, ahora):
    """Devuelve los sonidos de la intro que tocan entre el segundo `antes` y `ahora`."""
    return [nombre for momento, nombre in SONIDOS_INTRO if antes < momento <= ahora]


def dibujar_espadazo(capa_suave, capa_nitida, t, desde, hasta, t0, t1, color):
    """Un espadazo: la hoja de luz cruza la pantalla de punta a punta y deja
    una marca que se va apagando."""
    if t < t0:
        return
    apagado = 1.0 if t <= t1 else max(0.0, 1 - (t - t1) / 0.6)
    if apagado <= 0:
        return
    tono = mezclar(NEGRO, color, apagado)
    punta = luz_en(t, desde, hasta, t0, t1)
    # la marca fina de todo lo que ya cortó
    pygame.draw.line(capa_nitida, mezclar(NEGRO, color, 0.5 * apagado), desde, punta, 2)
    # la hoja: las posiciones de los últimos instantes
    puntos = [luz_en(t - k * 0.02, desde, hasta, t0, t1) for k in range(10, -1, -1)]
    graficos.dibujar_espada(capa_suave, capa_nitida, puntos, tono, punta if t <= t1 else None)


def dibujar_intro(pantalla, capa_suave, capa_nitida, fuentes, imagenes, t):
    """La intro: pantalla negra, dos espadazos de luz, un destello, se pinta un
    ensō (el círculo zen) y aparece el título; al final se estampa el sello."""
    pantalla.fill(NEGRO)

    # Los espadazos se dibujan con brillo, igual que la luz en el juego (capas que se suman)
    capa_suave.fill(NEGRO)
    capa_nitida.fill(NEGRO)
    for desde, hasta, t0, t1, color in ESPADAZOS:
        dibujar_espadazo(capa_suave, capa_nitida, t, desde, hasta, t0, t1, color)
    resplandor = graficos.difuminar(capa_suave, DESENFOQUE_BRILLO)
    pantalla.blit(pygame.transform.smoothscale(resplandor, (ANCHO, ALTO)), (0, 0),
                  special_flags=pygame.BLEND_RGB_ADD)
    pantalla.blit(capa_nitida, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    centro = (ANCHO // 2, ALTO // 2 - 30)
    if t >= APARECE_TITULO - 0.05:
        # el ensō se pinta detrás del título, de una sola pincelada
        avance = (t - APARECE_TITULO + 0.05) / 0.55
        interfaz.dibujar_enso(pantalla, centro, 165, mezclar(NEGRO, ROJO, 0.8), 30, avance)

    if t >= APARECE_TITULO:
        dt = t - APARECE_TITULO
        interfaz.dibujar_farol(pantalla, imagenes["farol"], imagenes["halo_farol"], 70, 30, t)
        interfaz.dibujar_farol(pantalla, imagenes["farol"], imagenes["halo_farol"], ANCHO - 70, 30, t, 1.7)
        # el título entra grande y "golpea" hasta su tamaño normal
        avance = min(1.0, dt / 0.35)
        escala = 1 + 0.7 * (1 - avance) ** 3
        ancho, alto = fuentes["titulo"].size(TITULO.upper())
        titulo = pygame.Surface((ancho + 12, alto + 12), pygame.SRCALPHA)
        dibujar_texto(titulo, TITULO.upper(), fuentes["titulo"], AMARILLO, (ancho // 2 + 6, alto // 2 + 6))
        titulo = pygame.transform.rotozoom(titulo, 0, 1.15 * escala)
        # resplandor del título: el mismo texto (más oscuro y sobre fondo negro, porque al
        # SUMARLO a la pantalla el negro no aporta nada), achicado, borroneado y agrandado
        # al tamaño del título que se ve
        texto = fuentes["titulo"].render(TITULO.upper(), True, mezclar(NEGRO, AMARILLO, 0.6), NEGRO)
        margen = alto                     # lugar para que el brillo se desvanezca antes del borde
        lienzo = pygame.Surface((ancho + 2 * margen, alto + 2 * margen))
        lienzo.fill(NEGRO)
        lienzo.blit(texto, (margen, margen))
        ancho_lienzo, alto_lienzo = lienzo.get_size()
        brillo = pygame.transform.smoothscale(lienzo, (ancho_lienzo // 8, alto_lienzo // 8))
        brillo = graficos.difuminar(brillo, 2)
        tamanio = 1.15 * escala           # el mismo tamaño que el título
        brillo = pygame.transform.smoothscale(brillo, (int(ancho_lienzo * tamanio), int(alto_lienzo * tamanio)))
        pantalla.blit(brillo, brillo.get_rect(center=centro), special_flags=pygame.BLEND_RGB_ADD)
        pantalla.blit(titulo, titulo.get_rect(center=centro))

        # el sello rojo se estampa a la derecha del título: cae grande y "golpea"
        if imagenes["sello"] is not None and t >= SELLO_INTRO:
            golpe = min(1.0, (t - SELLO_INTRO) / 0.15)
            sello = pygame.transform.rotozoom(imagenes["sello"], 0, 1 + 0.9 * (1 - golpe) ** 2)
            x_sello = centro[0] + titulo.get_width() // 2 + 6
            pantalla.blit(sello, sello.get_rect(center=(x_sello, centro[1] + 34)))

        if dt > 0.6:
            dibujar_texto(pantalla, "Un juego de linterna y cámara", fuentes["media"], BLANCO,
                          (ANCHO // 2, ALTO // 2 + 160))
        if dt > 1.2 and int(t * 2) % 2 == 0:
            dibujar_texto(pantalla, "Apretá cualquier tecla", fuentes["chica"], GRIS,
                          (ANCHO // 2, ALTO - 50))

    # destello blanco justo cuando aparece el título
    destello = t - (APARECE_TITULO - 0.08)
    if 0 <= destello < 0.45:
        imagenes["blanco"].set_alpha(int(230 * (1 - destello / 0.45)))
        pantalla.blit(imagenes["blanco"], (0, 0))


def confirmar_nombre(nombres, cual):
    """Deja fijo el nombre `cual` (sin espacios de más). Si quedó vacío, le pone
    "Jugador 1" o "Jugador 2"."""
    nombres[cual] = nombres[cual].strip() or f"Jugador {cual + 1}"


def escribir_nombre(nombres, cual, evento):
    """Agrega o borra letras del nombre que se está escribiendo. Devuelve cuál
    se escribe ahora: 0, 1, o 2 cuando ya están los dos (ENTER en el segundo).
    El nombre del jugador 1 queda fijo al pasar al 2, pero se puede volver a
    corregir: con la flecha izquierda, o borrando cuando el nombre 2 está vacío."""
    if evento.type == pygame.TEXTINPUT:
        if len(nombres[cual]) < LARGO_MAXIMO_NOMBRE:
            nombres[cual] += evento.text
    elif evento.key == pygame.K_BACKSPACE:
        if cual == 1 and nombres[1] == "":
            return 0                         # nada que borrar: se vuelve al nombre 1
        nombres[cual] = nombres[cual][:-1]
    elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        confirmar_nombre(nombres, cual)
        return cual + 1
    elif evento.key == pygame.K_LEFT and cual == 1:
        return 0                             # volver a corregir el nombre 1
    elif evento.key == pygame.K_RIGHT and cual == 0:
        confirmar_nombre(nombres, 0)         # igual que ENTER, pero sin empezar
        return 1
    return cual


def caja_nombre(i):
    """Devuelve el rectángulo de la caja donde se escribe el nombre del jugador `i`."""
    caja = pygame.Rect((0, 0), CAJA_NOMBRE)
    caja.center = (ANCHO // 2 + (-220 if i == 0 else 220), 285)
    return caja


def dibujar_listo(pantalla, caja, color):
    """Dibuja un "tilde" de listo en la esquina de la caja de un nombre que ya está fijo."""
    x, y = caja.right - 26, caja.centery
    pygame.draw.lines(pantalla, color, False, [(x - 8, y), (x - 2, y + 7), (x + 10, y - 8)], 4)


def dibujar_nombres(pantalla, fuentes, nombres, cual, tiempo):
    """La pantalla donde cada jugador escribe su nombre antes del versus."""
    centro = ANCHO // 2
    dibujar_texto(pantalla, "VERSUS", fuentes["titulo"], AMARILLO, (centro, 80))
    dibujar_texto(pantalla, "Escriban sus nombres", fuentes["media"], BLANCO, (centro, 150))
    lados = (("Jugador 1 (izquierda)", COLOR_JUGADOR_1, centro - 220),
             ("Jugador 2 (derecha)", COLOR_JUGADOR_2, centro + 220))
    for i, (titulo, color, x) in enumerate(lados):
        activo = i == cual
        fijo = i < cual                      # el nombre 1, ya confirmado
        dibujar_texto(pantalla, titulo, fuentes["media"], color, (x, 225))
        caja = caja_nombre(i)
        pygame.draw.rect(pantalla, LACA, caja, border_radius=4)
        pygame.draw.rect(pantalla, color if activo or fijo else GRIS, caja, 3 if activo else 1,
                         border_radius=4)
        texto = nombres[i]
        if activo and int(tiempo * 2) % 2 == 0:
            texto += "|"                     # cursor que titila
        if fijo:
            # queda fijo, en su color y con un tilde, pero se puede volver a corregir
            dibujar_texto(pantalla, texto, fuentes["grande"], color, caja.center)
            dibujar_listo(pantalla, caja, color)
            dibujar_atajos(pantalla, [(("←",), "corregir")], fuentes["chica"], fuentes["texto"],
                           ALTO_TECLA_CHICA, GRIS, GRIS, (x, caja.bottom + 24))
        else:
            dibujar_texto(pantalla, texto, fuentes["grande"], BLANCO if activo else GRIS, caja.center)
    atajos = [(("ENTER",), "listo"), (("BORRAR",), "corregir"), (("ESC",), "volver al inicio")]
    dibujar_atajos(pantalla, atajos, fuentes["media"], fuentes["chica"], ALTO_TECLA_MEDIA, BLANCO,
                   AMARILLO, (centro, 400))


# ---------------------------------------------------------------------------
# Paleta de colores: con C, en la pantalla de inicio se abre un abanico japonés
# (sensu). Cada gajo de papel es un color, con su kanji siguiendo la varilla.
# ---------------------------------------------------------------------------

def clavo_abanico():
    """Devuelve el punto donde se juntan las varillas (el clavo del abanico):
    abajo al medio, justo arriba de la línea del color."""
    return (ANCHO // 2, ALTO - 76)


def punto_abanico(angulo, radio):
    """Devuelve el punto a `radio` píxeles del clavo, en la dirección `angulo`
    (en grados: 0 es para arriba, negativo a la izquierda, positivo a la derecha)."""
    cx, cy = clavo_abanico()
    a = math.radians(angulo)
    return (cx + math.sin(a) * radio, cy - math.cos(a) * radio)


def angulos_gajo(i, apertura):
    """Devuelve (desde, hasta) en grados del gajo `i`. Con `apertura` 0 el abanico
    está cerrado (todos los gajos juntos) y con 1 está abierto del todo."""
    total = ABERTURA_ABANICO * apertura
    ancho = total / len(COLORES_ESPADA)
    desde = -total / 2 + i * ancho
    return desde, desde + ancho


def rect_paleta():
    """Devuelve el rectángulo que ocupa el abanico abierto (para saber si un clic cayó adentro)."""
    cx, cy = clavo_abanico()
    radio = RADIO_ABANICO + SALIENTE_ELEGIDO
    return pygame.Rect(cx - radio, cy - radio - 40, radio * 2, radio + 50)


def piedra_en(posicion):
    """Devuelve el número del gajo (color) que está en `posicion`, o None."""
    cx, cy = clavo_abanico()
    dx, dy = posicion[0] - cx, posicion[1] - cy
    distancia = math.hypot(dx, dy)
    if not RADIO_CENTRO_ABANICO <= distancia <= RADIO_ABANICO + SALIENTE_ELEGIDO:
        return None
    angulo = math.degrees(math.atan2(dx, -dy))
    for i in range(len(COLORES_ESPADA)):
        desde, hasta = angulos_gajo(i, 1)
        if desde <= angulo < hasta:
            return i
    return None


def borde_de_gajo(desde, hasta, radio, pasos=6):
    """Devuelve los puntos del borde de afuera de un gajo (un arco)."""
    return [punto_abanico(desde + (hasta - desde) * k / pasos, radio) for k in range(pasos + 1)]


def dibujar_gajo(pantalla, desde, hasta, radio, color):
    """Un gajo de papel plegado: dos pliegues, uno más claro y otro más oscuro,
    que es lo que hace que un abanico se vea como un abanico."""
    medio = (desde + hasta) / 2
    for a, b, tono in ((desde, medio, mezclar(color, BLANCO, 0.15)), (medio, hasta, mezclar(color, NEGRO, 0.18))):
        puntos = borde_de_gajo(a, b, radio, 3) + borde_de_gajo(b, a, RADIO_CENTRO_ABANICO + 8, 3)
        pygame.draw.polygon(pantalla, tono, puntos)


def dibujar_paleta(pantalla, fuentes, imagenes, elegido, t):
    """Dibuja el abanico abierto (o abriéndose). `elegido` es el color marcado y
    `t` los segundos desde que se abrió."""
    apertura = min(1.0, t / APERTURA_PALETA)
    apertura = 1 - (1 - apertura) ** 3          # se abre rápido y frena al final
    pantalla.blit(imagenes["velo"], (0, 0))      # lo de atrás queda oscuro y no distrae
    clavo = clavo_abanico()
    # primero los gajos que no están elegidos, y al final el elegido (queda arriba)
    orden = [i for i in range(len(COLORES_ESPADA)) if i != elegido] + [elegido]
    for i in orden:
        nombre, color = COLORES_ESPADA[i]
        desde, hasta = angulos_gajo(i, apertura)
        radio = RADIO_ABANICO + (SALIENTE_ELEGIDO if i == elegido else 0)
        dibujar_gajo(pantalla, desde, hasta, radio, color if i == elegido else mezclar(color, NEGRO, 0.25))
        # las varillas de madera, desde el clavo hasta el borde del papel
        for angulo in (desde, hasta):
            pygame.draw.line(pantalla, MADERA, clavo, punto_abanico(angulo, radio), 2)
        if i == elegido:
            # un hilo dorado en el borde del gajo elegido
            pygame.draw.lines(pantalla, AMARILLO, False, borde_de_gajo(desde, hasta, radio), 2)
        if apertura > 0.6:
            # el kanji, inclinado como su varilla
            medio = (desde + hasta) / 2
            tinta = mezclar(color, CONTORNO, 0.75) if i == elegido else mezclar(color, CONTORNO, 0.55)
            kanji = pygame.transform.rotozoom(fuentes["kanji_chico"].render(KANJI_COLORES[i], True, tinta),
                                              -medio, 1)
            pantalla.blit(kanji, kanji.get_rect(center=punto_abanico(medio, radio - 30)))
    # las dos varillas de afuera, más gruesas, y el clavo
    for angulo in angulos_gajo(0, apertura)[:1] + angulos_gajo(len(COLORES_ESPADA) - 1, apertura)[1:]:
        pygame.draw.line(pantalla, MADERA_CLARA, clavo, punto_abanico(angulo, RADIO_ABANICO + 6), 5)
    pygame.draw.circle(pantalla, MADERA, clavo, 9)
    pygame.draw.circle(pantalla, AMARILLO, clavo, 4)
    if apertura >= 1:
        dibujar_atajos(pantalla, [(("←", "→"), "elegir"), (("ENTER",), "listo")], fuentes["texto"],
                       fuentes["texto"], 20, GRIS, AMARILLO,
                       (clavo[0], clavo[1] - RADIO_ABANICO - SALIENTE_ELEGIDO - 22))
