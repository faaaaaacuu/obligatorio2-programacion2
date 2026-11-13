"""Corte de Luz - juego principal.

Prendé la linterna del celular, apuntala a la cámara y movela como una
espada: cada fruta que cruza el rastro de la luz se corta. Las bombas y
las frutas que se caen sin cortar quitan una vida.

Modos:
  1 jugador: 5 niveles, cada uno más difícil.
  Versus:    pantalla dividida, cada jugador con su linterna en su mitad.
             Gana el primero en llegar a la meta o el que sobrevive.

Controles:
  1 / 2    empezar 1 jugador / versus
  ESPACIO  empezar / volver a jugar el mismo modo
  + / -    subir / bajar el umbral de brillo de la detección
  M        mostrar / ocultar lo que la cámara toma como "luz"
  ESC      salir (también se puede cerrar con la X de la ventana)
"""

import os

import pygame

import vision
from ajustes import *
from objetos import Jugador

CARPETA = os.path.dirname(os.path.abspath(__file__))
NOMBRES_SONIDOS = ("corte", "bomba", "caida", "nivel", "ganar", "perder")
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
        "titulo": pygame.font.Font(None, 110),
        "grande": pygame.font.Font(None, 64),
        "media": pygame.font.Font(None, 40),
        "chica": pygame.font.Font(None, 28),
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
        jugadores = [Jugador("Jugador", COLOR_RASTRO, 0, ANCHO)]
    else:
        jugadores = [Jugador("Jugador 1", COLOR_JUGADOR_1, 0, MITAD),
                     Jugador("Jugador 2", COLOR_JUGADOR_2, MITAD, ANCHO)]
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
    """Escribe un texto con sombra negra para que se lea sobre la cámara."""
    sombra = fuente.render(mensaje, True, NEGRO)
    imagen = fuente.render(mensaje, True, color)
    rect = imagen.get_rect()
    if centrado:
        rect.center = posicion
    else:
        rect.topleft = posicion
    pantalla.blit(sombra, rect.move(3, 3))
    pantalla.blit(imagen, rect)


def dibujar_vidas(pantalla, vidas, x, y):
    """Dibuja un círculo por vida: rojo si la tiene, gris si la perdió."""
    for i in range(VIDAS):
        color = ROJO if i < vidas else GRIS_OSCURO
        pygame.draw.circle(pantalla, color, (x + i * 36, y), 13)
        pygame.draw.circle(pantalla, BLANCO, (x + i * 36, y), 13, 2)


def dibujar_hud(pantalla, juego, fuentes, destello):
    """Nivel, frutas cortadas, puntos, vidas y mensajes de cada jugador."""
    reglas = reglas_actuales(juego)
    if juego["modo"] == 1:
        jugador = juego["jugadores"][0]
        dibujar_texto(pantalla, f"Nivel {juego['nivel'] + 1}/{len(NIVELES)}",
                      fuentes["media"], AMARILLO, (20, 15), False)
        dibujar_texto(pantalla, f"Frutas: {jugador.cortadas}/{reglas['meta']}",
                      fuentes["media"], BLANCO, (20, 55), False)
        dibujar_texto(pantalla, f"Puntos: {jugador.puntos}",
                      fuentes["media"], BLANCO, (ANCHO - 200, 15), False)
        dibujar_vidas(pantalla, jugador.vidas, ANCHO - 180, 75)
    else:
        pygame.draw.line(pantalla, BLANCO, (MITAD, 0), (MITAD, ALTO), 3)
        for jugador in juego["jugadores"]:
            x = jugador.x_min + 20
            dibujar_texto(pantalla, jugador.nombre, fuentes["media"], jugador.color, (x, 15), False)
            dibujar_texto(pantalla, f"Frutas: {jugador.cortadas}/{reglas['meta']}",
                          fuentes["chica"], BLANCO, (x, 52), False)
            dibujar_vidas(pantalla, jugador.vidas, jugador.x_max - 110, 30)

    for jugador in juego["jugadores"]:
        centro_zona = (jugador.x_min + jugador.x_max) // 2
        if jugador.mensaje_tiempo > 0:
            color = VERDE if jugador.mensaje == "+1" else ROJO
            dibujar_texto(pantalla, jugador.mensaje, fuentes["grande"], color, (centro_zona, 120))
        if jugador.destello > 0:
            # la pantalla se pone roja solo en la zona del que cortó la bomba
            zona = pygame.Rect(0, 0, jugador.x_max - jugador.x_min, ALTO)
            pantalla.blit(destello, (jugador.x_min, 0), zona)
        if jugador.luz is None and not esta_pausado(juego):
            dibujar_texto(pantalla, "No veo la linterna", fuentes["media"], ROJO,
                          (centro_zona, ALTO - 40))


def dibujar_carteles(pantalla, estado, juego, fuentes, luces, umbral, capa_cartel):
    """Dibuja el cartel que corresponde a cada estado (menú, nivel, fin...)."""
    centro = ANCHO // 2
    medio = ALTO // 2
    if estado == "jugando":
        if esta_pausado(juego):
            pantalla.blit(capa_cartel, (0, 0))
            dibujar_texto(pantalla, "PAUSA", fuentes["grande"], AMARILLO, (centro, medio - 50))
            for i, jugador in enumerate(juego["jugadores"]):
                if jugador.perdio_la_luz():
                    quien = "tu linterna" if juego["modo"] == 1 else f"la linterna del {jugador.nombre}"
                    dibujar_texto(pantalla, f"No veo {quien}", fuentes["media"], ROJO,
                                  (centro, medio + 10 + i * 40))
            dibujar_texto(pantalla, "Apuntala a la cámara para seguir", fuentes["chica"], BLANCO,
                          (centro, medio + 100))
        return

    pantalla.blit(capa_cartel, (0, 0))
    if estado == "menu":
        dibujar_texto(pantalla, "CORTE DE LUZ", fuentes["titulo"], AMARILLO, (centro, medio - 160))
        dibujar_texto(pantalla, "Prendé la linterna del celular y cortá las frutas con la luz",
                      fuentes["media"], BLANCO, (centro, medio - 80))
        dibujar_texto(pantalla, "Esquivá las bombas y no dejes caer frutas",
                      fuentes["chica"], BLANCO, (centro, medio - 40))
        if any(luz is not None for luz in luces):
            dibujar_texto(pantalla, "Linterna detectada", fuentes["media"], VERDE, (centro, medio + 5))
        else:
            dibujar_texto(pantalla, "No veo la linterna", fuentes["media"], ROJO, (centro, medio + 5))
        dibujar_texto(pantalla, f"1 = un jugador ({len(NIVELES)} niveles)", fuentes["media"], VERDE,
                      (centro, medio + 60))
        dibujar_texto(pantalla, "2 = versus (cada uno en su mitad, con su linterna)",
                      fuentes["media"], VERDE, (centro, medio + 100))
        dibujar_texto(pantalla, f"Umbral de brillo: {umbral}   (+/- para ajustar, M para ver la luz)"
                      "   |   ESC para salir", fuentes["chica"], BLANCO, (centro, medio + 160))
    elif estado == "cartel":
        segundos = max(1, int(juego["cartel"]) + 1)
        if juego["modo"] == 2:
            dibujar_texto(pantalla, "VERSUS", fuentes["titulo"], AMARILLO, (centro, medio - 110))
            dibujar_texto(pantalla, f"Gana el primero en cortar {REGLAS_VERSUS['meta']} frutas",
                          fuentes["media"], BLANCO, (centro, medio - 25))
            dibujar_texto(pantalla, "o el que sobreviva si el otro se queda sin vidas",
                          fuentes["chica"], BLANCO, (centro, medio + 15))
            dibujar_texto(pantalla, "Jugador 1: izquierda", fuentes["media"], COLOR_JUGADOR_1,
                          (centro - 200, medio + 70))
            dibujar_texto(pantalla, "Jugador 2: derecha", fuentes["media"], COLOR_JUGADOR_2,
                          (centro + 200, medio + 70))
        else:
            reglas = reglas_actuales(juego)
            if juego["nivel"] > 0:
                dibujar_texto(pantalla, "¡NIVEL SUPERADO!", fuentes["grande"], VERDE, (centro, medio - 140))
            dibujar_texto(pantalla, f"NIVEL {juego['nivel'] + 1}", fuentes["titulo"], AMARILLO,
                          (centro, medio - 50))
            dibujar_texto(pantalla, f"Cortá {reglas['meta']} frutas para pasar",
                          fuentes["media"], BLANCO, (centro, medio + 30))
            if reglas["bombas"] > 0:
                dibujar_texto(pantalla, "Cuidado con las bombas", fuentes["media"], ROJO,
                              (centro, medio + 75))
        dibujar_texto(pantalla, f"Empieza en {segundos}...", fuentes["media"], VERDE,
                      (centro, medio + 130))
    else:
        jugador = juego["jugadores"][0]
        if estado == "ganaste":
            dibujar_texto(pantalla, "¡GANASTE!", fuentes["titulo"], VERDE, (centro, medio - 90))
            dibujar_texto(pantalla, f"Pasaste los {len(NIVELES)} niveles  -  Puntos: {jugador.puntos}",
                          fuentes["media"], BLANCO, (centro, medio))
        elif estado == "perdiste":
            dibujar_texto(pantalla, "FIN DE LA PARTIDA", fuentes["grande"], ROJO, (centro, medio - 90))
            dibujar_texto(pantalla, f"Llegaste al nivel {juego['nivel'] + 1}  -  Puntos: {jugador.puntos}",
                          fuentes["media"], BLANCO, (centro, medio))
        else:  # "fin_versus"
            uno, dos = juego["jugadores"]
            dibujar_texto(pantalla, juego["resultado"], fuentes["grande"], AMARILLO, (centro, medio - 90))
            dibujar_texto(pantalla, f"{uno.nombre}: {uno.cortadas} frutas", fuentes["media"],
                          COLOR_JUGADOR_1, (centro - 200, medio))
            dibujar_texto(pantalla, f"{dos.nombre}: {dos.cortadas} frutas", fuentes["media"],
                          COLOR_JUGADOR_2, (centro + 200, medio))
        dibujar_texto(pantalla, "ESPACIO revancha  |  1 o 2 para cambiar de modo  |  ESC salir",
                      fuentes["media"], VERDE, (centro, medio + 85))


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption(TITULO)
    reloj = pygame.time.Clock()

    # La cámara, los sonidos y las fuentes se abren / cargan una sola vez.
    cap = vision.abrir_camara()
    if cap is None:
        print("No se pudo abrir la cámara. Revisá que esté conectada y los permisos.")
        pygame.quit()
        return
    sonidos = cargar_sonidos()
    fuentes = cargar_fuentes()
    capa_oscura = crear_capa(CAPA_OSCURA)
    capa_cartel = crear_capa(CAPA_CARTEL)
    destello = crear_capa((255, 0, 0, 90))

    # Estados: "menu" -> "cartel" (NIVEL X) -> "jugando" -> "cartel" ... -> "ganaste"
    #          y si se acaban las vidas -> "perdiste". En el versus: -> "fin_versus".
    estado = "menu"
    juego = nueva_partida(1)
    umbral = UMBRAL_BRILLO
    ver_mascara = False
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
        if estado == "cartel":
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
        pantalla.blit(capa_oscura, (0, 0))

        if estado == "jugando":
            for jugador in juego["jugadores"]:
                jugador.dibujar(pantalla)
            dibujar_hud(pantalla, juego, fuentes, destello)
        dibujar_carteles(pantalla, estado, juego, fuentes, luces, umbral, capa_cartel)
        if estado == "menu":
            for luz in luces:   # en el menú se ve dónde está cada luz
                if luz is not None:
                    pygame.draw.circle(pantalla, AMARILLO, luz, RADIO_LUZ, 3)

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
