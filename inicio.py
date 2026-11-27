"""La intro (dos espadazos de luz y el título) y la pantalla de inicio
(el título, las reglas y cómo empezar).

Cada regla es una "tarjeta" con un título, una explicación corta y una
animación que se repite mostrando qué pasa en el juego. Las animaciones no
usan la cámara: son dibujos calculados a partir del tiempo. Por ejemplo, en
"Cortá frutas" la fruta sube durante el primer segundo, en t = 1.0 pasa la luz
y la corta, y después las mitades caen. Con `t % duracion` se repiten.
"""

import math
import os

import pygame

import graficos
from graficos import dibujar_texto, mezclar, dibujar_atajos
from ajustes import (ANCHO, ALTO, TARJETA_ANCHO, TARJETA_ALTO, TARJETA_ANIMACION_ALTO,
                     Y_MODOS, Y_LINTERNA, RADIO_FRUTA_DEMO,
                     FRUTAS_JUGADOR_1, FRUTAS_JUGADOR_2, COLORES_ESPADA, COLOR_JUGADOR_1,
                     COLOR_JUGADOR_2, COLOR_BOMBA_MORTAL, BLANCO, NEGRO, AMARILLO, VERDE,
                     ROJO, GRIS, CONTORNO, DESENFOQUE_BRILLO, COLORES_INTRO, KANJI, ARCHIVO_FUENTE_TEXTO, LUZ_FAROL, TITULO)
from ajustes import (COLORES_EXPLOSION, COLOR_DESTELLO_TARJETA, COLOR_DESTELLO_INTRO,
                     TAMANIO_VIDA_TARJETA, PANEL_MODO, ESPADAZOS, APARECE_TITULO, SELLO_INTRO)
from ajustes import (TUTORIAL_ENTRADA, TUTORIAL_SALIDA, TUTORIAL_PAUSA, TUTORIAL_ESCALA, TUTORIAL_GIRO,
                     TUTORIAL_FLOTE, TAMANIO_NUMERO_TUTORIAL, BOTON_SALTEAR, LACA)
from ajustes import ALTO_TECLA_CHICA

LUZ = COLORES_ESPADA[0][1]      # color de la luz en las animaciones
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
    imagenes["vidas"] = {True: graficos.crear_vida(TAMANIO_VIDA_TARJETA, True),
                        False: graficos.crear_vida(TAMANIO_VIDA_TARJETA, False)}
    rojo = pygame.Surface((TARJETA_ANCHO, TARJETA_ANIMACION_ALTO), pygame.SRCALPHA)
    rojo.fill(COLOR_DESTELLO_TARJETA)
    imagenes["rojo"] = rojo
    imagenes["tarjeta"] = graficos.crear_panel(TARJETA_ANCHO, TARJETA_ALTO)
    imagenes["modo"] = graficos.crear_panel(*PANEL_MODO)
    blanco = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    blanco.fill(COLOR_DESTELLO_INTRO)
    imagenes["blanco"] = blanco               # para el destello de la intro
    # estética de dojo: sello rojo con el kanji 光 ("luz") y faroles de papel.
    # (crear_sello devuelve None si la compu no tiene una fuente con ese kanji)
    # el kanji sale de la fuente Potta One; si no estuviera, no se dibuja el sello
    hay_kanji = os.path.exists(os.path.join(CARPETA, ARCHIVO_FUENTE_TEXTO))
    imagenes["sello"] = graficos.crear_sello(KANJI, fuentes["kanji"], 64) if hay_kanji else None
    imagenes["sello_chico"] = graficos.crear_sello(KANJI, fuentes["kanji_chico"], 42) if hay_kanji else None
    imagenes["farol"] = graficos.crear_farol(70)
    # lienzo donde se arma cada tarjeta del tutorial antes de agrandarla y girarla
    imagenes["lienzo_tarjeta"] = pygame.Surface((TARJETA_ANCHO, TARJETA_ALTO), pygame.SRCALPHA)
    imagenes["halo_farol"] = graficos.crear_halo(70, LUZ_FAROL, alfa_maximo=90)
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
    """Tres sellitos de vida arriba a la derecha. Si `nueva` es el número de una
    vida que se acaba de recuperar, aparece agrandada y se achica."""
    ancho = sup.get_width()
    for i in range(3):
        escala = 1
        if i == nueva and dt < 0.3:
            escala = 1.8 - dt / 0.3 * 0.8
        pegar(sup, imagenes["vidas"][i < llenas], ancho - 46 + i * 18, 12, escala=escala)


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

    def __init__(self, titulo, texto, color, animacion, vuelta, sonidos):
        """Guarda el título, el texto, el color de la rayita y la función que anima la tarjeta.
        `vuelta` es cuántos segundos dura la animación antes de repetirse y `sonidos` es
        la lista de (segundo, nombre) que suenan en el tutorial cuando pasa cada cosa."""
        self.titulo = titulo
        self.texto = texto
        self.color = color
        self.animacion = animacion      # una de las funciones animar_...
        self.vuelta = vuelta
        self.sonidos = sonidos
        self.duracion = vuelta + TUTORIAL_PAUSA   # cuánto se queda en el tutorial

    def dibujar(self, pantalla, x, y, fuentes, imagenes, tiempo):
        """Dibuja la tarjeta en (x, y): el panel, la animación arriba y el título y el texto abajo."""
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


# Los segundos de los sonidos coinciden con lo que pasa en cada animación
# (por ejemplo, en animar_cortar la luz corta la naranja en t = 1.0).
TARJETAS = [
    Tarjeta("CORTÁ FRUTAS", "Usá la linterna como una espada: cada fruta es 1 punto.",
            VERDE, animar_cortar, 2.6, [(0.95, "corte")]),
    Tarjeta("¡BOMBAS NO!", "Si cortás una bomba, perdés una vida.", ROJO, animar_bomba,
            2.6, [(0.95, "corte"), (1.0, "bomba")]),
    Tarjeta("QUE NO CAIGAN", "Cada fruta que se cae sin cortar te saca una vida.",
            AMARILLO, animar_caida, 2.8, [(2.0, "caida")]),
    Tarjeta("TRIPLE", "3 frutas en un solo trazo te devuelven una vida.",
            COLORES_ESPADA[3][1], animar_triple, 3.2,
            [(1.08, "corte"), (1.25, "corte"), (1.42, "corte"), (1.57, "vida")]),
    Tarjeta("BOMBA MORTAL", "Versus: girá la luz en círculos y se la mandás al rival.",
            COLOR_BOMBA_MORTAL, animar_mortal, 4.2, [(0.2, "lanzar"), (2.6, "mortal")]),
]


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
    pygame.draw.rect(pantalla, CONTORNO, tecla.move(0, 4), border_radius=10)    # sombra
    pygame.draw.rect(pantalla, mezclar(AMARILLO, BLANCO, latido * 0.4), tecla, border_radius=10)
    pygame.draw.rect(pantalla, CONTORNO, tecla, 2, border_radius=10)
    imagen = fuente.render(letra, True, CONTORNO)
    pantalla.blit(imagen, imagen.get_rect(center=tecla.center))


def dibujar_inicio(pantalla, fuentes, imagenes, tiempo, hay_luz, color, record, umbral):
    """Dibuja toda la pantalla de inicio."""
    centro = ANCHO // 2
    # dos faroles de papel colgando en las esquinas, que se balancean despacio
    graficos.dibujar_farol(pantalla, imagenes["farol"], imagenes["halo_farol"], 50, 10, tiempo)
    graficos.dibujar_farol(pantalla, imagenes["farol"], imagenes["halo_farol"], ANCHO - 50, 10, tiempo, 1.7)
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
        graficos.dibujar_enso(pantalla, centro, 165, mezclar(NEGRO, ROJO, 0.8), 30, avance)

    if t >= APARECE_TITULO:
        dt = t - APARECE_TITULO
        graficos.dibujar_farol(pantalla, imagenes["farol"], imagenes["halo_farol"], 70, 30, t)
        graficos.dibujar_farol(pantalla, imagenes["farol"], imagenes["halo_farol"], ANCHO - 70, 30, t, 1.7)
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

# ---------------------------------------------------------------------------
# Tutorial: la primera vez que se abre el juego, después de la intro, las
# tarjetas pasan de a una, grandes, al estilo motion graphics. Cada tarjeta
# entra desde la derecha, muestra su animación (con sus sonidos) y sale por
# la izquierda. Se puede pasar a la siguiente o saltear todo.
# ---------------------------------------------------------------------------

def suavizar_entrada(avance):
    """Curva "ease out back" de los motion graphics: arranca rápido, se pasa un
    poquito del final y vuelve. Recibe el avance (0 a 1) y devuelve el suavizado."""
    p = max(0.0, min(1.0, avance)) - 1
    rebote = 1.7         # cuánto se pasa del final antes de volver
    return 1 + (rebote + 1) * p ** 3 + rebote * p ** 2


def duracion_tarjeta(indice):
    """Devuelve cuántos segundos está en pantalla la tarjeta `indice` del tutorial
    (entrada + su animación + salida)."""
    return TUTORIAL_ENTRADA + TARJETAS[indice].duracion + TUTORIAL_SALIDA


def sonidos_tutorial(indice, antes, ahora):
    """Devuelve los sonidos de la tarjeta `indice` que tocan entre el segundo `antes`
    (incluido) y `ahora`, contados desde que la tarjeta empezó a entrar."""
    momentos = [(0.0, "espadazo")]       # el "zas" de la tarjeta entrando
    momentos += [(TUTORIAL_ENTRADA + t, nombre) for t, nombre in TARJETAS[indice].sonidos]
    return [nombre for momento, nombre in momentos if antes <= momento < ahora]


def pasar_tarjeta(indice, t):
    """Con la flecha se pasa a la siguiente tarjeta: si todavía no empezó a salir,
    se salta al momento en que sale. Devuelve el nuevo tiempo de la tarjeta."""
    return max(t, TUTORIAL_ENTRADA + TARJETAS[indice].duracion)


def lugar_de_tarjeta(indice, t):
    """Devuelve (x, inclinación, escala) de la tarjeta en el segundo `t`: entra
    desde la derecha, se queda en el centro y sale por la izquierda."""
    centro = ANCHO // 2
    medio_ancho = TARJETA_ANCHO * TUTORIAL_ESCALA / 2
    afuera_derecha = ANCHO + medio_ancho + 20
    afuera_izquierda = -medio_ancho - 20
    fin_animacion = TUTORIAL_ENTRADA + TARJETAS[indice].duracion
    if t < TUTORIAL_ENTRADA:
        avance = suavizar_entrada(t / TUTORIAL_ENTRADA)
        x = afuera_derecha + (centro - afuera_derecha) * avance
        return x, TUTORIAL_GIRO * (1 - avance), TUTORIAL_ESCALA * (0.75 + 0.25 * avance)
    if t < fin_animacion:
        return centro, 0, TUTORIAL_ESCALA
    # al salir acelera (avance al cuadrado), como si la empujaran
    avance = min(1.0, (t - fin_animacion) / TUTORIAL_SALIDA) ** 2
    x = centro + (afuera_izquierda - centro) * avance
    return x, -TUTORIAL_GIRO * avance, TUTORIAL_ESCALA * (1 - 0.25 * avance)


def dibujar_boton_saltear(pantalla, fuentes):
    """El botón para saltear el tutorial (también con ESPACIO o ESC). Se ilumina
    si el mouse está encima."""
    boton = pygame.Rect(BOTON_SALTEAR)
    encima = boton.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(pantalla, LACA, boton, border_radius=4)
    pygame.draw.rect(pantalla, BLANCO if encima else AMARILLO, boton, 2 if encima else 1, border_radius=4)
    dibujar_texto(pantalla, "SALTEAR", fuentes["media"], BLANCO if encima else AMARILLO,
                  (boton.centerx - 12, boton.centery))
    # dos flechitas hacia la derecha (como el botón de "adelantar")
    x, y = boton.right - 26, boton.centery
    for corrida in (0, 9):
        pygame.draw.polygon(pantalla, AMARILLO, [(x + corrida + 6, y), (x + corrida - 3, y - 7),
                                                  (x + corrida - 3, y + 7)])


def dibujar_tutorial(pantalla, fuentes, imagenes, indice, t, tiempo):
    """Dibuja el tutorial con la tarjeta `indice`. `t` son los segundos desde que la
    tarjeta empezó a entrar y `tiempo` los segundos desde que arrancó el juego."""
    pantalla.fill(NEGRO)
    tarjeta = TARJETAS[indice]
    centro_y = ALTO // 2 + 12
    graficos.dibujar_farol(pantalla, imagenes["farol"], imagenes["halo_farol"], 70, 30, tiempo)
    graficos.dibujar_farol(pantalla, imagenes["farol"], imagenes["halo_farol"], ANCHO - 70, 30, tiempo, 1.7)
    dibujar_texto(pantalla, "CÓMO SE JUEGA", fuentes["grande"], AMARILLO, (ANCHO // 2, 34))

    x, angulo, escala = lugar_de_tarjeta(indice, t)
    if TUTORIAL_ENTRADA <= t < TUTORIAL_ENTRADA + tarjeta.duracion:
        centro_y += int(TUTORIAL_FLOTE * math.sin((t - TUTORIAL_ENTRADA) * 2.5))   # flota apenas

    # número grande de fondo ("01", "02"...), que se mueve más lento que la tarjeta
    # (efecto de profundidad, como en los motion graphics)
    numero = fuentes["numero_grande"].render(f"{indice + 1:02d}", True, mezclar(NEGRO, tarjeta.color, 0.3))
    numero = pygame.transform.rotozoom(numero, 0, TAMANIO_NUMERO_TUTORIAL)
    x_numero = ANCHO // 2 - 300 + (x - ANCHO // 2) * 0.5
    pantalla.blit(numero, numero.get_rect(center=(int(x_numero), centro_y)))

    # líneas de velocidad detrás de la tarjeta mientras entra
    if t < TUTORIAL_ENTRADA + 0.2:
        apagado = 1 - t / (TUTORIAL_ENTRADA + 0.2)
        borde = x + TARJETA_ANCHO * escala / 2
        for corrida, grosor in ((-120, 3), (-40, 2), (60, 3), (140, 2)):
            pygame.draw.line(pantalla, mezclar(NEGRO, tarjeta.color, apagado),
                             (borde, centro_y + corrida), (borde + 260 * apagado, centro_y + corrida), grosor)

    # la tarjeta se arma en su lienzo (la animación empieza cuando terminó de entrar
    # y se frena al final, así no vuelve a arrancar mientras sale) y después se
    # agranda y se gira
    lienzo = imagenes["lienzo_tarjeta"]
    lienzo.fill((0, 0, 0, 0))
    t_animacion = min(max(0.0, t - TUTORIAL_ENTRADA), tarjeta.vuelta - 0.01)
    tarjeta.dibujar(lienzo, 0, 0, fuentes, imagenes, t_animacion)
    imagen = pygame.transform.rotozoom(lienzo, angulo, escala)
    pantalla.blit(imagen, imagen.get_rect(center=(int(x), centro_y)))

    # puntitos que muestran en qué tarjeta vamos
    for i in range(len(TARJETAS)):
        px = ANCHO // 2 + int((i - (len(TARJETAS) - 1) / 2) * 22)
        if i == indice:
            pygame.draw.circle(pantalla, tarjeta.color, (px, ALTO - 24), 6)
        else:
            pygame.draw.circle(pantalla, GRIS, (px, ALTO - 24), 3)
    dibujar_atajos(pantalla, [(("→",), "siguiente"), (("ESPACIO",), "saltear")], fuentes["chica"],
                   fuentes["texto"], ALTO_TECLA_CHICA, GRIS, AMARILLO, (18, ALTO - 36), False)
    dibujar_boton_saltear(pantalla, fuentes)
