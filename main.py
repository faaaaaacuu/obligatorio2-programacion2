"""Corte de Luz - juego principal.

Prendé la linterna del celular, apuntala a la cámara y movela como una
espada: cada fruta que cruza el rastro de la luz se corta. Las bombas y
las frutas que se caen sin cortar quitan una vida.

Modos:
  1 jugador: 5 niveles, cada uno más difícil.
  Versus:    pantalla dividida, cada jugador con su linterna y sus frutas en su
             mitad. Gana el primero en llegar a la meta o el que sobrevive.
             Girando la linterna en círculos se carga una bomba mortal que
             aparece en la mitad del rival (una vez por partida, te deja con 1 vida).

Controles:
  1 / 2    empezar 1 jugador / versus
  ESPACIO  empezar / volver a jugar el mismo modo
  + / -    subir / bajar el umbral de brillo de la detección
  M        mostrar / ocultar lo que la cámara toma como "luz"
  F        pantalla completa / ventana
  ESC      salir (también se puede cerrar con la X de la ventana)
"""

import math
import os
import random

# Al agrandar el juego a pantalla completa, que lo suavice en vez de pixelarlo.
os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "linear")

import pygame

import graficos
import vision
from ajustes import *
from objetos import Fruta, Jugador

CARPETA = os.path.dirname(os.path.abspath(__file__))
NOMBRES_SONIDOS = ("corte", "bomba", "caida", "nivel", "ganar", "perder", "lanzar", "mortal")
MITAD = ANCHO // 2
# En el menú todavía no hay modo elegido: se busca una luz en cada mitad.
ZONAS_MENU = [(0, MITAD), (MITAD, ANCHO)]


# ---------------------------------------------------------------------------
# Carga de recursos (se llama una sola vez, antes del bucle)
# ---------------------------------------------------------------------------

def cargar_sonidos():
    """Carga los sonidos una sola vez. Devuelve un diccionario nombre -> Sound."""
    sonidos = {}
    for nombre in NOMBRES_SONIDOS:
        ruta = os.path.join(CARPETA, "sonidos", nombre + ".wav")
        sonidos[nombre] = pygame.mixer.Sound(ruta)
    return sonidos


def cargar_fuentes():
    """Devuelve un diccionario con las fuentes de distintos tamaños."""
    return {
        "titulo": pygame.font.SysFont(FUENTE_TITULO, 64),
        "grande": pygame.font.SysFont(FUENTE_TITULO, 38),
        "media": pygame.font.SysFont(FUENTE, 22, bold=True),
        "chica": pygame.font.SysFont(FUENTE, 14, bold=True),
    }


def crear_capa(color):
    """Devuelve una superficie del tamaño de la ventana, de un color semitransparente."""
    capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    capa.fill(color)
    return capa


# ---------------------------------------------------------------------------
# Lógica de la partida
# ---------------------------------------------------------------------------

def nueva_partida(modo):
    """Devuelve el estado inicial de una partida. modo 1 = un jugador, 2 = versus."""
    if modo == 1:
        jugadores = [Jugador("Jugador", COLOR_RASTRO, 0, ANCHO,
                             FRUTAS_JUGADOR_1 + FRUTAS_JUGADOR_2)]
    else:
        # cada uno con sus frutas y con su bomba mortal
        jugadores = [Jugador("Jugador 1", COLOR_JUGADOR_1, 0, MITAD, FRUTAS_JUGADOR_1, True),
                     Jugador("Jugador 2", COLOR_JUGADOR_2, MITAD, ANCHO, FRUTAS_JUGADOR_2, True)]
    juego = {"modo": modo, "jugadores": jugadores, "resultado": ""}
    empezar_nivel(juego, 0)
    return juego


def empezar_nivel(juego, numero):
    """Deja todo listo para arrancar el nivel `numero` (0 = nivel 1)."""
    juego["nivel"] = numero
    juego["cartel"] = DURACION_CARTEL   # cuenta regresiva del cartel "NIVEL X"
    for jugador in juego["jugadores"]:
        jugador.reiniciar()


def reglas_actuales(juego):
    """Devuelve las reglas que se usan ahora: las del nivel o las del versus."""
    if juego["modo"] == 2:
        return REGLAS_VERSUS
    return NIVELES[juego["nivel"]]


def esta_pausado(juego):
    """Devuelve True si la cámara perdió la linterna de algún jugador."""
    return any(jugador.perdio_la_luz() for jugador in juego["jugadores"])


def resultado_versus(jugadores):
    """Devuelve el texto del resultado si el versus terminó, o None si sigue."""
    uno, dos = jugadores
    llego_uno = uno.cortadas >= REGLAS_VERSUS["meta"] or dos.vidas <= 0
    llego_dos = dos.cortadas >= REGLAS_VERSUS["meta"] or uno.vidas <= 0
    if llego_uno and llego_dos:
        return "¡EMPATE!"
    if llego_uno:
        return f"¡GANÓ EL {uno.nombre.upper()}!"
    if llego_dos:
        return f"¡GANÓ EL {dos.nombre.upper()}!"
    return None


def actualizar_partida(juego, luces, dt, sonidos):
    """Avanza la partida un cuadro. `luces` tiene la posición de la luz de cada
    jugador ((x, y) o None). Devuelve el estado siguiente:
    'jugando', 'cartel' (pasó de nivel), 'ganaste', 'perdiste' o 'fin_versus'."""
    reglas = reglas_actuales(juego)
    jugadores = juego["jugadores"]
    segmentos = [jugador.mover_luz(luz, dt) for jugador, luz in zip(jugadores, luces)]

    # Si la cámara no ve una linterna, el juego no se rompe: se pausa hasta que vuelva.
    if esta_pausado(juego):
        return "jugando"

    for jugador, segmento in zip(jugadores, segmentos):
        jugador.actualizar(segmento, reglas, dt, sonidos)

    if juego["modo"] == 2:
        # Bomba mortal: si uno completó la bola girando la linterna, le aparece al otro.
        for jugador, rival in ((jugadores[0], jugadores[1]), (jugadores[1], jugadores[0])):
            if jugador.cargar_bomba():
                rival.recibir_bomba()
                sonidos["lanzar"].play()

        resultado = resultado_versus(jugadores)
        if resultado is None:
            return "jugando"
        juego["resultado"] = resultado
        sonidos["ganar"].play()
        return "fin_versus"

    # Un jugador: ¿perdió, pasó de nivel o ganó?
    jugador = jugadores[0]
    if jugador.vidas <= 0:
        sonidos["perder"].play()
        return "perdiste"
    if jugador.cortadas >= reglas["meta"]:
        if juego["nivel"] + 1 < len(NIVELES):
            empezar_nivel(juego, juego["nivel"] + 1)
            sonidos["nivel"].play()
            return "cartel"
        sonidos["ganar"].play()
        return "ganaste"
    return "jugando"


# ---------------------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------------------

def a_superficie(imagen_rgb):
    """Convierte una imagen RGB (la que devuelve vision) en una superficie de pygame."""
    alto, ancho = imagen_rgb.shape[:2]
    return pygame.image.frombuffer(imagen_rgb.tobytes(), (ancho, alto), "RGB")


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


def dibujar_titulo(pantalla, fuente, tiempo):
    """El título del menú: cada letra sube y baja como una ola y cambia de color."""
    texto = "CORTE DE LUZ"
    x = ANCHO // 2 - fuente.size(texto)[0] // 2
    for i, letra in enumerate(texto):
        ola = math.sin(tiempo * 3 + i * 0.5) * 6
        tono = graficos.mezclar(AMARILLO, (255, 120, 0), (math.sin(tiempo * 2 + i * 0.4) + 1) / 2)
        dibujar_texto(pantalla, letra, fuente, tono, (x, int(60 + ola)), False)
        x += fuente.size(letra)[0]


def actualizar_adornos(adornos, dt):
    """Frutas que vuelan de fondo en el menú, solo de adorno. Devuelve la lista nueva."""
    if random.random() < dt * 1.2 and len(adornos) < 5:
        # solo por los costados, así no tapan el texto del medio
        x_min, x_max = random.choice(((0, ANCHO_ZONA_ADORNOS), (ANCHO - ANCHO_ZONA_ADORNOS, ANCHO)))
        adornos.append(Fruta(REGLAS_ADORNOS, x_min, x_max, FRUTAS_JUGADOR_1 + FRUTAS_JUGADOR_2))
    for fruta in adornos:
        fruta.actualizar(dt)
    return [fruta for fruta in adornos if not fruta.se_cayo()]


def dibujar_vidas(pantalla, corazones, vidas, x, y):
    """Dibuja un corazón por vida, centrados a partir de (x, y)."""
    for i in range(VIDAS):
        imagen = corazones[i < vidas]       # True = corazón lleno, False = vacío
        pantalla.blit(imagen, imagen.get_rect(center=(x + i * 40, y)))


def dibujar_hud(pantalla, juego, fuentes, paneles, corazones, destello):
    """Paneles con nivel, progreso, puntos, vidas y mensajes de cada jugador."""
    reglas = reglas_actuales(juego)
    if juego["modo"] == 1:
        jugador = juego["jugadores"][0]
        pantalla.blit(paneles["nivel"], (12, 10))
        dibujar_texto(pantalla, f"Nivel {juego['nivel'] + 1}/{len(NIVELES)}",
                      fuentes["media"], AMARILLO, (28, 18), False)
        dibujar_texto(pantalla, f"{jugador.cortadas}/{reglas['meta']}",
                      fuentes["chica"], BLANCO, (200, 24), False)
        graficos.dibujar_barra(pantalla, pygame.Rect(28, 58, 238, 18),
                               jugador.cortadas / reglas["meta"], VERDE)
        x_panel = ANCHO - 12 - paneles["puntos"].get_width()
        pantalla.blit(paneles["puntos"], (x_panel, 10))
        dibujar_texto(pantalla, f"Puntos: {jugador.puntos}", fuentes["media"], BLANCO,
                      (x_panel + 16, 18), False)
        dibujar_vidas(pantalla, corazones, jugador.vidas, x_panel + 36, 60)
    else:
        for jugador in juego["jugadores"]:
            x = jugador.x_min + 12
            pantalla.blit(paneles["versus"], (x, 10))
            dibujar_texto(pantalla, jugador.nombre, fuentes["media"], jugador.color, (x + 16, 16), False)
            dibujar_vidas(pantalla, corazones, jugador.vidas, x + 205, 32)
            barra = pygame.Rect(x + 16, 54, paneles["versus"].get_width() - 32, 18)
            graficos.dibujar_barra(pantalla, barra, jugador.cortadas / reglas["meta"], jugador.color)
            dibujar_texto(pantalla, f"{jugador.cortadas}/{reglas['meta']}", fuentes["chica"],
                          BLANCO, barra.center)
            if jugador.bomba_usada:
                dibujar_texto(pantalla, "Bomba usada", fuentes["chica"], GRIS, (x + 16, 80), False)
            else:
                pygame.draw.circle(pantalla, COLOR_BOMBA_MORTAL, (x + 24, 91), 8)
                dibujar_texto(pantalla, "Girá la linterna: bomba mortal", fuentes["chica"],
                              COLOR_BOMBA_MORTAL, (x + 38, 80), False)

    for jugador in juego["jugadores"]:
        centro_zona = (jugador.x_min + jugador.x_max) // 2
        if jugador.destello > 0:
            # la pantalla se pone roja solo en la zona del que cortó la bomba, y se va apagando
            destello.set_alpha(int(255 * min(1, jugador.destello / DURACION_DESTELLO)))
            zona = pygame.Rect(0, 0, jugador.x_max - jugador.x_min, ALTO)
            pantalla.blit(destello, (jugador.x_min, 0), zona)
        if jugador.mensaje_tiempo > 0:
            dibujar_texto(pantalla, jugador.mensaje, fuentes["grande"], ROJO, (centro_zona, 170))
        if jugador.luz is None and not esta_pausado(juego):
            dibujar_texto(pantalla, "No veo la linterna", fuentes["media"], ROJO,
                          (centro_zona, ALTO - 40))


def dibujar_carteles(pantalla, estado, juego, fuentes, luces, umbral, tiempo):
    """Escribe los textos que corresponden a cada estado (menú, nivel, fin...)."""
    centro = ANCHO // 2
    medio = ALTO // 2
    if estado == "jugando":
        if esta_pausado(juego):
            dibujar_texto(pantalla, "PAUSA", fuentes["grande"], AMARILLO, (centro, medio - 50))
            for i, jugador in enumerate(juego["jugadores"]):
                if jugador.perdio_la_luz():
                    quien = "tu linterna" if juego["modo"] == 1 else f"la linterna del {jugador.nombre}"
                    dibujar_texto(pantalla, f"No veo {quien}", fuentes["media"], ROJO,
                                  (centro, medio + 10 + i * 40))
            dibujar_texto(pantalla, "Apuntala a la cámara para seguir", fuentes["chica"], BLANCO,
                          (centro, medio + 100))
        return

    if estado == "menu":
        dibujar_titulo(pantalla, fuentes["titulo"], tiempo)
        dibujar_texto(pantalla, "Prendé la linterna del celular y cortá las frutas con la luz",
                      fuentes["media"], BLANCO, (centro, medio - 75))
        dibujar_texto(pantalla, "Esquivá las bombas y no dejes caer frutas",
                      fuentes["chica"], BLANCO, (centro, medio - 42))
        if any(luz is not None for luz in luces):
            dibujar_texto(pantalla, "Linterna detectada", fuentes["media"], VERDE, (centro, medio + 5))
        else:
            dibujar_texto(pantalla, "No veo la linterna", fuentes["media"], ROJO, (centro, medio + 5))
        dibujar_texto(pantalla, f"1  =  un jugador ({len(NIVELES)} niveles)", fuentes["grande"],
                      AMARILLO, (centro, medio + 65))
        dibujar_texto(pantalla, "2  =  versus", fuentes["grande"], AMARILLO, (centro, medio + 120))
        dibujar_texto(pantalla, f"Umbral de brillo: {umbral}   (+/- para ajustar, M para ver la luz)"
                      "   |   F = pantalla completa   |   ESC = salir",
                      fuentes["chica"], GRIS, (centro, ALTO - 25))
    elif estado == "cartel":
        segundos = max(1, int(juego["cartel"]) + 1)
        if juego["modo"] == 2:
            dibujar_texto(pantalla, "VERSUS", fuentes["titulo"], AMARILLO, (centro, medio - 170))
            dibujar_texto(pantalla, f"Gana el primero en cortar {REGLAS_VERSUS['meta']} frutas",
                          fuentes["media"], BLANCO, (centro, medio - 95))
            dibujar_texto(pantalla, "o el que sobreviva si el otro se queda sin vidas",
                          fuentes["chica"], BLANCO, (centro, medio - 62))
            dibujar_texto(pantalla, "Girá la linterna en círculos para mandarle una BOMBA MORTAL al rival",
                          fuentes["chica"], COLOR_BOMBA_MORTAL, (centro, medio - 20))
            dibujar_texto(pantalla, "(una sola vez, y te deja con 1 vida)",
                          fuentes["chica"], COLOR_BOMBA_MORTAL, (centro, medio + 4))
            dibujar_texto(pantalla, "Jugador 1: izquierda", fuentes["media"], COLOR_JUGADOR_1,
                          (centro - 210, medio + 60))
            dibujar_texto(pantalla, "Jugador 2: derecha", fuentes["media"], COLOR_JUGADOR_2,
                          (centro + 210, medio + 60))
        else:
            reglas = reglas_actuales(juego)
            if juego["nivel"] > 0:
                dibujar_texto(pantalla, "¡NIVEL SUPERADO!", fuentes["grande"], VERDE, (centro, medio - 140))
            dibujar_texto(pantalla, f"NIVEL {juego['nivel'] + 1}", fuentes["titulo"], AMARILLO,
                          (centro, medio - 55))
            dibujar_texto(pantalla, f"Cortá {reglas['meta']} frutas para pasar",
                          fuentes["media"], BLANCO, (centro, medio + 25))
            if reglas["bombas"] > 0:
                dibujar_texto(pantalla, "Cuidado con las bombas", fuentes["media"], ROJO,
                              (centro, medio + 65))
        dibujar_texto(pantalla, str(segundos), fuentes["titulo"], VERDE, (centro, medio + 150))
    else:
        jugador = juego["jugadores"][0]
        if estado == "ganaste":
            dibujar_texto(pantalla, "¡GANASTE!", fuentes["titulo"], VERDE, (centro, medio - 90))
            dibujar_texto(pantalla, f"Pasaste los {len(NIVELES)} niveles  -  Puntos: {jugador.puntos}",
                          fuentes["media"], BLANCO, (centro, medio))
        elif estado == "perdiste":
            dibujar_texto(pantalla, "FIN DE LA PARTIDA", fuentes["titulo"], ROJO, (centro, medio - 90))
            dibujar_texto(pantalla, f"Llegaste al nivel {juego['nivel'] + 1}  -  Puntos: {jugador.puntos}",
                          fuentes["media"], BLANCO, (centro, medio))
        else:  # "fin_versus"
            uno, dos = juego["jugadores"]
            dibujar_texto(pantalla, juego["resultado"], fuentes["titulo"], AMARILLO, (centro, medio - 90))
            dibujar_texto(pantalla, f"{uno.nombre}: {uno.cortadas} frutas", fuentes["media"],
                          COLOR_JUGADOR_1, (centro - 210, medio))
            dibujar_texto(pantalla, f"{dos.nombre}: {dos.cortadas} frutas", fuentes["media"],
                          COLOR_JUGADOR_2, (centro + 210, medio))
        dibujar_texto(pantalla, "ESPACIO = revancha     1 / 2 = cambiar de modo     ESC = salir",
                      fuentes["media"], VERDE, (centro, medio + 90))


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    pygame.init()
    # SCALED: el juego sigue midiendo ANCHO x ALTO y pygame lo agranda a la pantalla.
    opciones = pygame.SCALED
    if PANTALLA_COMPLETA:
        opciones |= pygame.FULLSCREEN
    pantalla = pygame.display.set_mode((ANCHO, ALTO), opciones)
    pygame.display.set_caption(TITULO)
    reloj = pygame.time.Clock()

    # La cámara, los sonidos, las fuentes y las capas se abren / arman una sola vez.
    cap = vision.abrir_camara()
    if cap is None:
        print("No se pudo abrir la cámara. Revisá que esté conectada y los permisos.")
        pygame.quit()
        return
    sonidos = cargar_sonidos()
    fuentes = cargar_fuentes()
    fondo = graficos.crear_fondo(ANCHO, ALTO, COLOR_FONDO, OSCURIDAD_CENTRO, OSCURIDAD_BORDE)
    capa_cartel = crear_capa(CAPA_CARTEL)
    destello = crear_capa((255, 30, 30, 110))
    # Las espadas de luz se dibujan en dos capas que después se suman a la pantalla:
    # una chica para el resplandor (se agranda y queda borrosa) y una nítida.
    capa_suave = pygame.Surface((ANCHO // 4, ALTO // 4))
    capa_nitida = pygame.Surface((ANCHO, ALTO))
    corazones = {True: graficos.crear_corazon(28, True), False: graficos.crear_corazon(28, False)}
    paneles = {
        "nivel": graficos.crear_panel(270, 84),
        "puntos": graficos.crear_panel(200, 84),
        "versus": graficos.crear_panel(MITAD - 24, 104),
    }

    # Estados: "menu" -> "cartel" (NIVEL X) -> "jugando" -> "cartel" ... -> "ganaste"
    #          y si se acaban las vidas -> "perdiste". En el versus: -> "fin_versus".
    estado = "menu"
    juego = nueva_partida(1)
    adornos = []                 # frutas que vuelan de fondo en el menú
    umbral = UMBRAL_BRILLO
    ver_mascara = False
    tiempo = 0.0                 # segundos desde que arrancó (para las animaciones)
    dt = 1 / FPS
    corriendo = True

    while corriendo:
        # 1) EVENTOS
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False
            elif evento.type == pygame.KEYDOWN:
                puede_empezar = estado in ("menu", "ganaste", "perdiste", "fin_versus")
                if evento.key == pygame.K_ESCAPE:
                    corriendo = False
                elif evento.key in (pygame.K_1, pygame.K_KP1) and puede_empezar:
                    juego = nueva_partida(1)
                    estado = "cartel"
                elif evento.key in (pygame.K_2, pygame.K_KP2) and puede_empezar:
                    juego = nueva_partida(2)
                    estado = "cartel"
                elif evento.key == pygame.K_SPACE and puede_empezar:
                    juego = nueva_partida(juego["modo"])   # mismo modo que la última vez
                    estado = "cartel"
                elif evento.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()   # en ventana aparece la X para cerrar
                elif evento.key == pygame.K_m:
                    ver_mascara = not ver_mascara
                elif evento.unicode in ("+", "="):
                    umbral = min(UMBRAL_MAXIMO, umbral + PASO_UMBRAL)
                elif evento.unicode in ("-", "_"):
                    umbral = max(UMBRAL_MINIMO, umbral - PASO_UMBRAL)

        # 2) CÁMARA: vision.py devuelve la posición de cada luz (x, y) o None.
        #    Cada jugador busca su luz solo en su zona de la pantalla.
        cuadro = vision.leer_cuadro(cap)
        if estado == "menu":
            zonas = ZONAS_MENU
        else:
            zonas = [(jugador.x_min, jugador.x_max) for jugador in juego["jugadores"]]
        luces = [vision.detectar_luz(cuadro, umbral, x_min, x_max) for x_min, x_max in zonas]

        # 3) ACTUALIZAR
        tiempo += dt
        if estado == "menu":
            adornos = actualizar_adornos(adornos, dt)
        elif estado == "cartel":
            juego["cartel"] -= dt
            if juego["cartel"] <= 0:
                estado = "jugando"
        elif estado == "jugando":
            estado = actualizar_partida(juego, luces, dt, sonidos)

        # 4) DIBUJAR
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
                pygame.draw.line(capa_suave, (60, 60, 80), (MITAD // 4, 0), (MITAD // 4, ALTO // 4), 3)
        elif estado == "menu":
            for luz in luces:   # en el menú se ve dónde está cada luz
                graficos.dibujar_espada(capa_suave, capa_nitida, [], COLOR_RASTRO, luz)
        # las capas de brillo se SUMAN: el negro no cambia nada y los colores iluminan
        # el resplandor se difumina y se agranda: queda suave, como luz de verdad
        resplandor = graficos.difuminar(capa_suave, DESENFOQUE_BRILLO)
        resplandor = pygame.transform.smoothscale(resplandor, (ANCHO, ALTO))
        pantalla.blit(resplandor, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        pantalla.blit(capa_nitida, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        if estado == "jugando":
            dibujar_hud(pantalla, juego, fuentes, paneles, corazones, destello)
        if estado != "jugando" or esta_pausado(juego):
            pantalla.blit(capa_cartel, (0, 0))
        if estado == "menu":
            for fruta in adornos:
                fruta.dibujar(pantalla)
        dibujar_carteles(pantalla, estado, juego, fuentes, luces, umbral, tiempo)

        if ver_mascara and cuadro is not None:
            chica = vision.mascara_chica_rgb(cuadro, umbral, ANCHO // 4, ALTO // 4)
            pantalla.blit(a_superficie(chica), (ANCHO - ANCHO // 4 - 10, ALTO - ALTO // 4 - 10))

        pygame.display.flip()
        dt = min(reloj.tick(FPS) / 1000, 0.1)  # tope por si un cuadro tarda mucho

    # Al cerrar la ventana se libera la cámara.
    cap.release()
    pygame.quit()


if __name__ == "__main__":
    main()
