"""Light Fruit Ninja - juego principal.

Prendé la linterna del celular, apuntala a la cámara y movela como una
espada: cada fruta que cruza el rastro de la luz se corta. Las bombas y
las frutas que se caen sin cortar quitan una vida.

Modos:
  1 jugador: la partida no termina hasta que perdés las 3 vidas, y se pone
             cada vez más difícil (sin avisar). Hay que superar el récord.
  Versus:    cada jugador escribe su nombre y juega en su mitad de la
             pantalla, con su linterna y sus frutas. Gana el que aguante más.
             Girando la linterna en círculos se carga una bomba mortal que
             aparece en la mitad del rival (una vez por partida, te deja con 1 vida).
             Las partidas quedan guardadas.

Controles (todo lo que aparece como tecla en pantalla también se puede clickear):
  1 / 2            empezar 1 jugador / versus
  ESPACIO / ENTER  volver a jugar el mismo modo
  P                pausar / seguir
  R                ver las reglas (el tutorial)
  + / -            subir / bajar el umbral de brillo de la detección
  M                mostrar / ocultar lo que la cámara toma como "luz"
  C                abrir el abanico para elegir el color de la luz
  F                pantalla completa / ventana
  ESC              volver a la pantalla de inicio (en la partida, primero pregunta;
                   en la pantalla de inicio, sale). Cmd+Q / Ctrl+Q o la X cierran el juego.

Este archivo tiene el bucle principal. Lo demás está repartido por tema:
  partida.py (la partida y sus pantallas), jugador.py y objetos.py (lo que se mueve),
  inicio.py y tarjetas.py (intro, pantalla de inicio, tutorial), graficos.py e
  interfaz.py (dibujos y textos), vision.py (la cámara), musica.py, resultados.py.
"""

import math
import os
import random

# Al agrandar el juego a pantalla completa, que lo suavice en vez de pixelarlo.
os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "linear")

import pygame

import graficos
import inicio
import interfaz
import resultados
import tarjetas
import vision
from interfaz import dibujar_atajos
from musica import Musica
from partida import (a_superficie, actualizar_partida, apretar, caja_nombre, confirmar_nombre,
                     dibujar_boton_inicio, dibujar_carteles, dibujar_hud, dibujar_nombres,
                     es_salir_del_sistema, escribir_nombre, esta_pausado, intensidad_de_musica,
                     nueva_partida, terminar_partida)

from ajustes import *

CARPETA = os.path.dirname(os.path.abspath(__file__))
NOMBRES_SONIDOS = ("bomba", "caida", "nivel", "ganar", "perder", "lanzar", "mortal", "vida", "sello",
                   "espadazo", "cuenta_3", "cuenta_2", "cuenta_1", "comienzo")
# En el menú todavía no hay modo elegido: se busca una luz en cada mitad.
ZONAS_MENU = [(0, MITAD), (MITAD, ANCHO)]


# ---------------------------------------------------------------------------
# Carga de recursos (se llama una sola vez, antes del bucle)
# ---------------------------------------------------------------------------

class SonidoVariado:
    """Varias versiones de un mismo sonido. Cada vez que se toca suena una al azar,
    pero nunca la misma dos veces seguidas: así los cortes no se vuelven repetitivos.
    Se usa igual que un Sound: sonidos["corte"].play()."""

    def __init__(self, versiones):
        """Recibe la lista de versiones (objetos Sound) del mismo sonido."""
        self.versiones = versiones
        self.anterior = None        # índice de la última que sonó

    def elegir(self):
        """Devuelve el índice de una versión al azar distinta de la anterior."""
        opciones = [i for i in range(len(self.versiones)) if i != self.anterior]
        if not opciones:            # si hay una sola versión, se repite
            opciones = [0]
        return random.choice(opciones)

    def play(self):
        """Toca una versión al azar, distinta de la que sonó la vez anterior."""
        self.anterior = self.elegir()
        self.versiones[self.anterior].play()


def cargar_sonidos():
    """Carga los sonidos una sola vez. Devuelve un diccionario nombre -> Sound."""
    # Los cortes tienen reverb y quedan sonando un rato: con más canales se pueden
    # superponer muchos sin que se pierda ninguno (pygame trae 8).
    pygame.mixer.set_num_channels(CANALES_DE_AUDIO)
    sonidos = {}
    for nombre in NOMBRES_SONIDOS:
        ruta = os.path.join(CARPETA, "sonidos", nombre + ".wav")
        sonidos[nombre] = pygame.mixer.Sound(ruta)
    cortes = [pygame.mixer.Sound(os.path.join(CARPETA, "sonidos", f"corte_{i}.wav"))
              for i in range(CANTIDAD_CORTES)]
    sonidos["corte"] = SonidoVariado(cortes)
    return sonidos


def cargar_fuente(archivo, tamanio):
    """Carga una fuente de la carpeta del juego. Si el archivo no está, devuelve
    una fuente del sistema para que el juego no se rompa."""
    ruta = os.path.join(CARPETA, archivo)
    if os.path.exists(ruta):
        return pygame.font.Font(ruta, tamanio)
    return pygame.font.SysFont(FUENTE_RESPALDO, tamanio, bold=True)


def cargar_fuentes():
    """Devuelve un diccionario con las fuentes de distintos tamaños."""
    return {
        "titulo": cargar_fuente(ARCHIVO_FUENTE_TITULO, 56),      # el pincel japonés, solo para lo grande
        "grande": cargar_fuente(ARCHIVO_FUENTE_UI_FUERTE, 32),
        "tarjeta": cargar_fuente(ARCHIVO_FUENTE_UI_FUERTE, 15),
        "media": cargar_fuente(ARCHIVO_FUENTE_UI, 20),
        "chica": cargar_fuente(ARCHIVO_FUENTE_UI, 14),
        "texto": cargar_fuente(ARCHIVO_FUENTE_UI, 12),
        "numero": cargar_fuente(ARCHIVO_FUENTE_UI_FUERTE, 36),
        "numero_grande": cargar_fuente(ARCHIVO_FUENTE_UI_FUERTE, 60),
        "kanji": cargar_fuente(ARCHIVO_FUENTE_TEXTO, 40),
        "kanji_chico": cargar_fuente(ARCHIVO_FUENTE_TEXTO, 26),
    }


def crear_capa(color):
    """Devuelve una superficie del tamaño de la ventana, de un color semitransparente."""
    capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    capa.fill(color)
    return capa


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def hay_algo_clickeable(posicion, estado, paleta_abierta):
    """Devuelve True si en `posicion` hay algo que se puede clickear (un botón, una
    piedra de la paleta o la caja de un nombre)."""
    if interfaz.tecla_en(posicion):
        return True
    if estado == "menu" and paleta_abierta and inicio.piedra_en(posicion) is not None:
        return True
    return estado == "nombres" and any(caja_nombre(i).collidepoint(posicion) for i in (0, 1))


def main():
    """Abre la ventana y la cámara, carga todo una sola vez y corre el bucle principal
    (eventos, actualizar, dibujar, reloj.tick). Al cerrar la ventana libera la cámara."""
    pygame.init()
    # SCALED: el juego sigue midiendo ANCHO x ALTO y pygame lo agranda a la pantalla.
    opciones = pygame.SCALED
    if PANTALLA_COMPLETA:
        opciones |= pygame.FULLSCREEN
    pantalla = pygame.display.set_mode((ANCHO, ALTO), opciones)
    pygame.display.set_caption(TITULO)
    reloj = pygame.time.Clock()
    # Sin "modo escritura": las teclas no generan texto (se activa solo para los nombres).
    pygame.key.stop_text_input()

    # La cámara, los sonidos, las fuentes, los resultados guardados y las capas
    # se abren / cargan / arman una sola vez, antes del bucle.
    cap = vision.abrir_camara()
    if cap is None:
        print("No se pudo abrir la cámara. Revisá que esté conectada y los permisos.")
        pygame.quit()
        return
    sonidos = cargar_sonidos()
    musica = Musica(CARPETA)         # las 4 versiones de la música de fondo
    fuentes = cargar_fuentes()
    datos = resultados.cargar_resultados()
    fondo = interfaz.crear_fondo(ANCHO, ALTO, COLOR_FONDO, OSCURIDAD_CENTRO, OSCURIDAD_BORDE)
    capa_cartel = crear_capa(CAPA_CARTEL)
    destello = crear_capa(COLOR_DESTELLO_BOMBA)
    # Las espadas de luz se dibujan en dos capas que después se suman a la pantalla:
    # una chica para el resplandor (se agranda y queda borrosa) y una nítida.
    capa_suave = pygame.Surface((ANCHO // 4, ALTO // 4))
    capa_nitida = pygame.Surface((ANCHO, ALTO))
    iconos_vida = {True: interfaz.crear_vida(TAMANIO_VIDA, True),
                   False: interfaz.crear_vida(TAMANIO_VIDA, False)}
    imagenes_inicio = inicio.crear_imagenes(fuentes)     # para las animaciones de la pantalla de inicio
    paneles = {
        "puntos": interfaz.crear_panel(*PANEL_PUNTOS),
        "vidas": interfaz.crear_panel(*PANEL_VIDAS),
        "versus": interfaz.crear_panel(MITAD - MARGEN_PANEL_VERSUS, ALTO_PANEL_VERSUS),
    }

    # Estados: "intro" -> "tutorial" -> "menu" -> "cartel" (cuenta regresiva) -> "jugando" -> "perdiste"
    #          versus: "menu" -> "nombres" -> "cartel" -> "jugando" -> "fin_versus"
    estado = "intro"
    tiempo_intro = 0.0           # segundos desde que empezó la intro
    tarjeta_tutorial = 0         # qué tarjeta del tutorial se está mostrando
    tiempo_tutorial = 0.0        # segundos desde que esa tarjeta empezó a entrar
    nombres = ["", ""]           # nombres del versus (se recuerdan para la revancha)
    cual_nombre = 0              # qué nombre se está escribiendo
    indice_color = 0             # filtro de color elegido (posición en COLORES_ESPADA)
    paleta_abierta = False       # la paleta de colores de la pantalla de inicio (tecla C)
    cursor_mano = False          # si el puntero del mouse es la manito (sobre un botón)
    tiempo_paleta = 0.0          # segundos desde que se abrió (para que se despliegue)
    sin_luz_menu = 0.0           # en el menú: segundos seguidos sin ver ninguna linterna
    juego = nueva_partida(1, nombres, datos["record"], COLORES_ESPADA[indice_color][1])
    umbral = UMBRAL_BRILLO
    ver_mascara = False
    tiempo = 0.0                 # segundos desde que arrancó (para las animaciones)
    dt = 1 / FPS
    corriendo = True

    while corriendo:
        # 1) EVENTOS
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT or es_salir_del_sistema(evento):
                corriendo = False               # la X de la ventana, o Cmd+Q / Ctrl+Q
            elif evento.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED):
                # si se cambia a otro programa o se minimiza, la partida se pausa sola
                if estado == "jugando" and juego["pausa"] is None:
                    juego["pausa"] = "manual"
            elif (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
                  and estado == "menu" and paleta_abierta):
                # con la paleta abierta: clic en una piedra la elige; clic en sus teclas
                # funciona como siempre; clic afuera la cierra sin cambiar nada
                elegido = inicio.piedra_en(evento.pos)
                if elegido is not None:
                    indice_color = elegido
                    paleta_abierta = False
                elif inicio.rect_paleta().collidepoint(evento.pos):
                    if interfaz.tecla_en(evento.pos):
                        apretar(interfaz.tecla_en(evento.pos))
                else:
                    paleta_abierta = False
            elif (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
                  and interfaz.tecla_en(evento.pos)):
                # clic en cualquier tecla dibujada (o botón): hace lo mismo que esa tecla
                apretar(interfaz.tecla_en(evento.pos))
            elif (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
                  and estado in ("intro", "tutorial")):
                apretar("→")                    # clic en cualquier lado: seguir adelante
            elif estado == "menu" and paleta_abierta and evento.type == pygame.KEYDOWN:
                # con la paleta abierta, las flechas eligen (el color cambia al instante)
                if evento.key == pygame.K_LEFT:
                    indice_color = (indice_color - 1) % len(COLORES_ESPADA)
                elif evento.key == pygame.K_RIGHT:
                    indice_color = (indice_color + 1) % len(COLORES_ESPADA)
                elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_c,
                                    pygame.K_ESCAPE, pygame.K_SPACE):
                    paleta_abierta = False
            elif estado == "intro" and evento.type == pygame.KEYDOWN:
                # ESPACIO saltea todo (intro y tutorial); cualquier otra tecla pasa al tutorial.
                # ESC cierra el juego, como siempre.
                if evento.key == pygame.K_ESCAPE:
                    corriendo = False
                elif evento.key == pygame.K_SPACE:
                    estado = "menu"
                else:
                    estado = "tutorial"
                    tarjeta_tutorial, tiempo_tutorial = 0, 0.0
            elif estado == "tutorial" and evento.type == pygame.KEYDOWN:
                # flecha (o ENTER) = siguiente tarjeta; ESPACIO o ESC = saltear el tutorial
                if evento.key in (pygame.K_SPACE, pygame.K_ESCAPE):
                    estado = "menu"
                elif evento.key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_KP_ENTER):
                    tiempo_tutorial = tarjetas.pasar_tarjeta(tarjeta_tutorial, tiempo_tutorial)
                elif evento.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()
            elif estado == "nombres":
                # Mientras se escriben los nombres, el teclado es para escribir.
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    # clic en una caja: se pasa a escribir ese nombre
                    if caja_nombre(0).collidepoint(evento.pos):
                        cual_nombre = 0
                    elif caja_nombre(1).collidepoint(evento.pos):
                        confirmar_nombre(nombres, 0)
                        cual_nombre = 1
                elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    pygame.key.stop_text_input()
                    estado = "menu"
                elif evento.type in (pygame.KEYDOWN, pygame.TEXTINPUT):
                    cual_nombre = escribir_nombre(nombres, cual_nombre, evento)
                    if cual_nombre == 2:      # ya están los dos nombres: ¡a jugar!
                        pygame.key.stop_text_input()
                        juego = nueva_partida(2, nombres, datos["record"], COLORES_ESPADA[indice_color][1])
                        estado = "cartel"
            elif estado == "jugando" and juego["pausa"] == "salir" and evento.type == pygame.KEYDOWN:
                # ¿abandonar la partida? S o ENTER = sí; N, ESC o P = no
                if evento.key in (pygame.K_s, pygame.K_RETURN, pygame.K_KP_ENTER):
                    estado = "menu"
                elif evento.key in (pygame.K_n, pygame.K_ESCAPE, pygame.K_p):
                    juego["pausa"] = None
            elif evento.type == pygame.KEYDOWN:
                puede_empezar = estado in ("menu", "perdiste", "fin_versus")
                if evento.key == pygame.K_ESCAPE:
                    if estado == "menu":
                        corriendo = False       # en la pantalla de inicio, ESC cierra el juego
                    elif estado == "jugando":
                        juego["pausa"] = "salir"   # en medio de la partida, primero pregunta
                    else:
                        estado = "menu"         # en las demás, vuelve a la pantalla de inicio
                elif evento.key == pygame.K_p and estado == "jugando":
                    # P pausa y reanuda, como en cualquier juego
                    juego["pausa"] = None if juego["pausa"] == "manual" else "manual"
                elif evento.key in (pygame.K_1, pygame.K_KP1) and puede_empezar:
                    juego = nueva_partida(1, nombres, datos["record"], COLORES_ESPADA[indice_color][1])
                    estado = "cartel"
                elif evento.key in (pygame.K_2, pygame.K_KP2) and puede_empezar:
                    cual_nombre = 0
                    estado = "nombres"
                    pygame.key.start_text_input()   # ahora sí, las teclas escriben
                elif evento.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER) and puede_empezar:
                    # mismo modo que la última vez (en el versus, con los mismos nombres)
                    juego = nueva_partida(juego["modo"], nombres, datos["record"],
                                          COLORES_ESPADA[indice_color][1])
                    estado = "cartel"
                elif evento.key == pygame.K_r and estado == "menu":
                    # volver a ver el tutorial con las reglas
                    estado = "tutorial"
                    tarjeta_tutorial, tiempo_tutorial = 0, 0.0
                elif evento.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()   # en ventana aparece la X para cerrar
                elif evento.key == pygame.K_c and estado == "menu":
                    paleta_abierta = True           # se despliega la paleta de colores
                    tiempo_paleta = 0.0
                elif evento.key == pygame.K_c:
                    # en medio de la partida no se abre la paleta: pasa al siguiente color
                    indice_color = (indice_color + 1) % len(COLORES_ESPADA)
                    if juego["modo"] == 1:
                        juego["jugadores"][0].color = COLORES_ESPADA[indice_color][1]
                elif evento.key == pygame.K_m:
                    ver_mascara = not ver_mascara
                elif evento.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    umbral = min(UMBRAL_MAXIMO, umbral + PASO_UMBRAL)
                elif evento.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    umbral = max(UMBRAL_MINIMO, umbral - PASO_UMBRAL)

        # 2) CÁMARA: vision.py devuelve la posición de cada luz (x, y) o None.
        #    Cada jugador busca su luz solo en su zona de la pantalla.
        cuadro = vision.leer_cuadro(cap)
        if estado in ("menu", "nombres"):
            zonas = ZONAS_MENU
        else:
            zonas = [(jugador.x_min, jugador.x_max) for jugador in juego["jugadores"]]
        luces = [vision.detectar_luz(cuadro, umbral, x_min, x_max) for x_min, x_max in zonas]

        # 3) ACTUALIZAR
        tiempo += dt
        if estado != "menu":
            paleta_abierta = False          # la paleta solo existe en la pantalla de inicio
        tiempo_paleta += dt
        # en el menú, la linterna también se da por perdida recién a los TOLERANCIA_SIN_LUZ segundos
        if any(luz is not None for luz in luces):
            sin_luz_menu = 0.0
        else:
            sin_luz_menu += dt
        if estado == "intro":
            antes = tiempo_intro
            tiempo_intro += dt
            for nombre in inicio.sonidos_a_tocar(antes, tiempo_intro):
                sonidos[nombre].play()
            if tiempo_intro >= DURACION_INTRO:
                estado = "tutorial"
                tarjeta_tutorial, tiempo_tutorial = 0, 0.0
        elif estado == "tutorial":
            antes = tiempo_tutorial
            tiempo_tutorial += dt
            for nombre in tarjetas.sonidos_tutorial(tarjeta_tutorial, antes, tiempo_tutorial):
                sonidos[nombre].play()
            if tiempo_tutorial >= tarjetas.duracion_tarjeta(tarjeta_tutorial):
                # terminó de salir: entra la siguiente (o, si era la última, la pantalla de inicio)
                tarjeta_tutorial += 1
                tiempo_tutorial = 0.0
                if tarjeta_tutorial == len(tarjetas.TARJETAS):
                    estado = "menu"
        elif estado == "cartel":
            # cuenta regresiva: un sonido con cada número; el 3 y el 2 parecidos,
            # el 1 el más épico...
            numero = math.ceil(juego["cartel"])
            if numero != juego["numero_cuenta"]:
                juego["numero_cuenta"] = numero
                sonidos[f"cuenta_{min(numero, 3)}"].play()
            juego["cartel"] -= dt
            if juego["cartel"] <= 0:
                sonidos["comienzo"].play()        # ...y taiko con gong al arrancar
                estado = "jugando"
        elif estado == "jugando":
            estado = actualizar_partida(juego, luces, dt, sonidos)
            if estado in ("perdiste", "fin_versus"):
                terminar_partida(juego, datos)      # se guarda el resultado

        musica.poner(intensidad_de_musica(estado, juego))   # cambia con un fundido si hace falta

        # 4) DIBUJAR
        interfaz.zonas_clic.clear()     # los botones de este cuadro se anotan mientras se dibujan
        if estado == "intro":
            inicio.dibujar_intro(pantalla, capa_suave, capa_nitida, fuentes, imagenes_inicio, tiempo_intro)
            tarjetas.dibujar_boton_saltear(pantalla, fuentes)
        elif estado == "tutorial":
            tarjetas.dibujar_tutorial(pantalla, fuentes, imagenes_inicio, tarjeta_tutorial,
                                    tiempo_tutorial, tiempo)
        else:
            if cuadro is not None:
                pantalla.blit(a_superficie(vision.a_rgb(cuadro)), (0, 0))
            else:
                pantalla.fill(NEGRO)
            pantalla.blit(fondo, (0, 0))

            capa_suave.fill(NEGRO)
            capa_nitida.fill(NEGRO)
            if estado == "jugando":
                for jugador in juego["jugadores"]:
                    jugador.dibujar(pantalla, fuentes["media"])
                    jugador.dibujar_brillo(capa_suave, capa_nitida)
                if juego["modo"] == 2:
                    # línea que divide las dos mitades, con el color de cada jugador
                    for corrida, color in ((-3, COLOR_JUGADOR_1), (3, COLOR_JUGADOR_2), (0, BLANCO)):
                        pygame.draw.line(capa_nitida, graficos.mezclar(NEGRO, color, 0.6),
                                         (MITAD + corrida, 0), (MITAD + corrida, ALTO), 3)
                    pygame.draw.line(capa_suave, COLOR_DIVISION_VERSUS, (MITAD // 4, 0), (MITAD // 4, ALTO // 4), 3)
            elif estado == "menu":
                for luz in luces:   # en el menú se ve dónde está cada luz
                    graficos.dibujar_espada(capa_suave, capa_nitida, [], COLORES_ESPADA[indice_color][1], luz)
            # las capas de brillo se SUMAN: el negro no cambia nada y los colores iluminan
            # (el resplandor se difumina y se agranda: queda suave, como luz de verdad)
            resplandor = graficos.difuminar(capa_suave, DESENFOQUE_BRILLO)
            resplandor = pygame.transform.smoothscale(resplandor, (ANCHO, ALTO))
            pantalla.blit(resplandor, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            pantalla.blit(capa_nitida, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

            if estado == "jugando":
                dibujar_hud(pantalla, juego, fuentes, paneles, iconos_vida, destello)
            if estado != "jugando" or esta_pausado(juego):
                pantalla.blit(capa_cartel, (0, 0))
            if estado == "nombres":
                dibujar_nombres(pantalla, fuentes, nombres, cual_nombre, tiempo)
            else:
                dibujar_carteles(pantalla, estado, juego, fuentes, sin_luz_menu <= TOLERANCIA_SIN_LUZ,
                                 umbral, tiempo, datos, COLORES_ESPADA[indice_color], imagenes_inicio)
            if estado == "menu" and paleta_abierta:
                inicio.dibujar_paleta(pantalla, fuentes, imagenes_inicio, indice_color, tiempo_paleta)
            # cómo volver a la pantalla de inicio: el botón, o mientras se juega solo un aviso chico
            if estado == "jugando" and not esta_pausado(juego):
                dibujar_atajos(pantalla, [(("P",), "pausa"), (("ESC",), "salir")], fuentes["texto"],
                               fuentes["texto"], ALTO_TECLA_CHICA, GRIS, GRIS, (18, ALTO - 24), False)
            elif estado != "menu" and not (estado == "jugando" and juego["pausa"] == "salir"):
                dibujar_boton_inicio(pantalla, fuentes)

            if ver_mascara and cuadro is not None:
                chica = vision.mascara_chica_rgb(cuadro, umbral, ANCHO // 4, ALTO // 4)
                pantalla.blit(a_superficie(chica), (ANCHO - ANCHO // 4 - 10, ALTO - ALTO // 4 - 10))

        # el puntero se vuelve una manito sobre lo que se puede clickear, como en cualquier programa
        mano = hay_algo_clickeable(pygame.mouse.get_pos(), estado, paleta_abierta)
        if mano != cursor_mano:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if mano else pygame.SYSTEM_CURSOR_ARROW)
            cursor_mano = mano

        pygame.display.flip()
        dt = min(reloj.tick(FPS) / 1000, DT_MAXIMO)  # tope por si un cuadro tarda mucho

    # Al cerrar la ventana se libera la cámara.
    cap.release()
    pygame.quit()


if __name__ == "__main__":
    main()
