"""Corte de Luz - juego principal.

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

Controles:
  1 / 2    empezar 1 jugador / versus
  ESPACIO  volver a jugar el mismo modo
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
import resultados
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

def nueva_partida(modo, nombres, record):
    """Devuelve el estado inicial de una partida. modo 1 = un jugador, 2 = versus.
    `nombres` son los nombres del versus y `record` el récord a superar."""
    if modo == 1:
        jugadores = [Jugador("Vos", COLOR_RASTRO, 0, ANCHO, FRUTAS_JUGADOR_1 + FRUTAS_JUGADOR_2)]
    else:
        # cada uno con sus frutas y con su bomba mortal
        jugadores = [Jugador(nombres[0], COLOR_JUGADOR_1, 0, MITAD, FRUTAS_JUGADOR_1, True),
                     Jugador(nombres[1], COLOR_JUGADOR_2, MITAD, ANCHO, FRUTAS_JUGADOR_2, True)]
    return {
        "modo": modo,
        "jugadores": jugadores,
        "cartel": DURACION_CARTEL,  # cuenta regresiva antes de empezar
        "tiempo": 0.0,              # segundos jugados (sin contar las pausas)
        "record": record,           # el récord que había al empezar
        "supero_record": False,     # ya pasó el récord durante la partida
        "nuevo_record": False,      # al terminar: ¿quedó como récord nuevo?
        "resultado": "",            # versus: texto del resultado
        "ganador": "",              # versus: nombre del ganador ("" si empataron)
    }


def reglas_de_nivel(nivel):
    """Devuelve las reglas de un nivel (0, 1, 2...). Los primeros vienen de la
    lista NIVELES; después, cada nivel es un poco más difícil, hasta los topes."""
    if nivel < len(NIVELES):
        return NIVELES[nivel]
    base = NIVELES[-1]
    extra = nivel - len(NIVELES) + 1     # cuántos niveles pasamos del último de la lista
    return {
        "max_frutas": min(TOPE_MAX_FRUTAS, base["max_frutas"] + extra // 2),
        "radio": (max(RADIO_MINIMO, base["radio"][0] - extra),
                  max(RADIO_MINIMO + 10, base["radio"][1] - extra)),
        "espera": (max(TOPE_ESPERA[0], base["espera"][0] * ACHIQUE_ESPERA ** extra),
                   max(TOPE_ESPERA[1], base["espera"][1] * ACHIQUE_ESPERA ** extra)),
        "gravedad": min(TOPE_GRAVEDAD, base["gravedad"] * AUMENTO_GRAVEDAD ** extra),
        "bombas": min(TOPE_BOMBAS, base["bombas"] + AUMENTO_BOMBAS * extra),
    }


def nivel_actual(juego):
    """Devuelve el nivel de dificultad. Sube solo, sin avisar: jugando solo,
    cada FRUTAS_POR_NIVEL frutas cortadas; en el versus, cada SEGUNDOS_POR_NIVEL."""
    if juego["modo"] == 1:
        return juego["jugadores"][0].cortadas // FRUTAS_POR_NIVEL
    return NIVEL_INICIAL_VERSUS + int(juego["tiempo"] // SEGUNDOS_POR_NIVEL)


def esta_pausado(juego):
    """Devuelve True si la cámara perdió la linterna de algún jugador."""
    return any(jugador.perdio_la_luz() for jugador in juego["jugadores"])


def resultado_versus(jugadores):
    """Gana el que aguanta más. Devuelve (texto, nombre del ganador) si alguno
    se quedó sin vidas, o None si la partida sigue."""
    uno, dos = jugadores
    if uno.vidas <= 0 and dos.vidas <= 0:
        return "¡EMPATE!", ""
    if dos.vidas <= 0:
        return f"¡GANÓ {uno.nombre.upper()}!", uno.nombre
    if uno.vidas <= 0:
        return f"¡GANÓ {dos.nombre.upper()}!", dos.nombre
    return None


def actualizar_partida(juego, luces, dt, sonidos):
    """Avanza la partida un cuadro. `luces` tiene la posición de la luz de cada
    jugador ((x, y) o None). Devuelve el estado siguiente:
    'jugando', 'perdiste' (1 jugador) o 'fin_versus'."""
    reglas = reglas_de_nivel(nivel_actual(juego))
    jugadores = juego["jugadores"]
    segmentos = [jugador.mover_luz(luz, dt) for jugador, luz in zip(jugadores, luces)]

    # Si la cámara no ve una linterna, el juego no se rompe: se pausa hasta que vuelva.
    if esta_pausado(juego):
        return "jugando"
    juego["tiempo"] += dt

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
        juego["resultado"], juego["ganador"] = resultado
        sonidos["ganar"].play()
        return "fin_versus"

    # Un jugador: avisar una sola vez cuando pasa el récord, y terminar si no le quedan vidas.
    jugador = jugadores[0]
    if juego["record"] > 0 and not juego["supero_record"] and jugador.puntos > juego["record"]:
        juego["supero_record"] = True
        jugador.mostrar_mensaje("¡NUEVO RÉCORD!", AMARILLO, DURACION_MENSAJE * 3)
        sonidos["nivel"].play()
    if jugador.vidas <= 0:
        sonidos["perder"].play()
        return "perdiste"
    return "jugando"


def terminar_partida(juego, datos):
    """Guarda el resultado de la partida que acaba de terminar."""
    if juego["modo"] == 1:
        juego["nuevo_record"] = resultados.registrar_puntaje(datos, juego["jugadores"][0].puntos)
    else:
        uno, dos = juego["jugadores"]
        resultados.registrar_versus(datos, uno, dos, juego["ganador"], juego["tiempo"])


def escribir_nombre(nombres, cual, evento):
    """Agrega o borra letras del nombre que se está escribiendo. Devuelve cuál
    se escribe ahora: 0, 1, o 2 cuando ya están los dos (ENTER en el segundo)."""
    if evento.type == pygame.TEXTINPUT:
        if len(nombres[cual]) < LARGO_MAXIMO_NOMBRE:
            nombres[cual] += evento.text
    elif evento.key == pygame.K_BACKSPACE:
        nombres[cual] = nombres[cual][:-1]
    elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        nombres[cual] = nombres[cual].strip() or f"Jugador {cual + 1}"
        return cual + 1
    return cual


def frutas(cantidad):
    """Devuelve '1 fruta' o 'N frutas', según la cantidad."""
    return f"{cantidad} fruta" if cantidad == 1 else f"{cantidad} frutas"


def formato_tiempo(segundos):
    """Devuelve los segundos como texto 'minutos:segundos' (por ejemplo 1:05)."""
    segundos = int(segundos)
    return f"{segundos // 60}:{segundos % 60:02d}"


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
    """Dibuja un corazón por vida, a partir de (x, y)."""
    for i in range(VIDAS):
        imagen = corazones[i < vidas]       # True = corazón lleno, False = vacío
        pantalla.blit(imagen, imagen.get_rect(center=(x + i * 40, y)))


def dibujar_hud(pantalla, juego, fuentes, paneles, corazones, destello):
    """Paneles con puntos, récord, vidas y los mensajes de cada jugador."""
    if juego["modo"] == 1:
        jugador = juego["jugadores"][0]
        pantalla.blit(paneles["puntos"], (12, 10))
        dibujar_texto(pantalla, "PUNTOS", fuentes["chica"], GRIS, (30, 18), False)
        dibujar_texto(pantalla, str(jugador.puntos), fuentes["grande"], BLANCO, (28, 32), False)
        if juego["supero_record"]:
            dibujar_texto(pantalla, "¡Récord superado!", fuentes["chica"], AMARILLO, (30, 82), False)
        elif juego["record"] > 0:
            dibujar_texto(pantalla, f"Récord: {juego['record']}", fuentes["chica"], AMARILLO, (30, 82), False)
        else:
            dibujar_texto(pantalla, "Sin récord todavía", fuentes["chica"], GRIS, (30, 82), False)
        x_panel = ANCHO - 12 - paneles["vidas"].get_width()
        pantalla.blit(paneles["vidas"], (x_panel, 10))
        dibujar_vidas(pantalla, corazones, jugador.vidas, x_panel + 40, 42)
    else:
        for jugador in juego["jugadores"]:
            x = jugador.x_min + 12
            pantalla.blit(paneles["versus"], (x, 10))
            dibujar_texto(pantalla, jugador.nombre, fuentes["media"], jugador.color, (x + 16, 16), False)
            dibujar_vidas(pantalla, corazones, jugador.vidas, x + 205, 32)
            dibujar_texto(pantalla, f"Frutas: {jugador.cortadas}", fuentes["media"], BLANCO,
                          (x + 16, 50), False)
            if jugador.bomba_usada:
                dibujar_texto(pantalla, "Bomba usada", fuentes["chica"], GRIS, (x + 16, 84), False)
            else:
                pygame.draw.circle(pantalla, COLOR_BOMBA_MORTAL, (x + 24, 95), 8)
                dibujar_texto(pantalla, "Girá la linterna: bomba mortal", fuentes["chica"],
                              COLOR_BOMBA_MORTAL, (x + 38, 84), False)
        dibujar_texto(pantalla, formato_tiempo(juego["tiempo"]), fuentes["media"], BLANCO,
                      (MITAD, ALTO - 24))

    for jugador in juego["jugadores"]:
        centro_zona = (jugador.x_min + jugador.x_max) // 2
        if jugador.destello > 0:
            # la pantalla se pone roja solo en la zona del que cortó la bomba, y se va apagando
            destello.set_alpha(int(255 * min(1, jugador.destello / DURACION_DESTELLO)))
            zona = pygame.Rect(0, 0, jugador.x_max - jugador.x_min, ALTO)
            pantalla.blit(destello, (jugador.x_min, 0), zona)
        if jugador.mensaje_tiempo > 0:
            dibujar_texto(pantalla, jugador.mensaje, fuentes["grande"], jugador.mensaje_color,
                          (centro_zona, 170))
        if jugador.luz is None and not esta_pausado(juego):
            dibujar_texto(pantalla, "No veo la linterna", fuentes["media"], ROJO,
                          (centro_zona, ALTO - 60))


def dibujar_nombres(pantalla, fuentes, nombres, cual, tiempo):
    """La pantalla donde cada jugador escribe su nombre antes del versus."""
    centro = ANCHO // 2
    dibujar_texto(pantalla, "VERSUS", fuentes["titulo"], AMARILLO, (centro, 80))
    dibujar_texto(pantalla, "Escriban sus nombres", fuentes["media"], BLANCO, (centro, 150))
    lados = (("Jugador 1 (izquierda)", COLOR_JUGADOR_1, centro - 220),
             ("Jugador 2 (derecha)", COLOR_JUGADOR_2, centro + 220))
    for i, (titulo, color, x) in enumerate(lados):
        activo = i == cual
        dibujar_texto(pantalla, titulo, fuentes["media"], color, (x, 225))
        caja = pygame.Rect(0, 0, 360, 64)
        caja.center = (x, 285)
        pygame.draw.rect(pantalla, (10, 10, 30), caja, border_radius=12)
        pygame.draw.rect(pantalla, color if activo else GRIS, caja, 4 if activo else 2, border_radius=12)
        texto = nombres[i]
        if activo and int(tiempo * 2) % 2 == 0:
            texto += "|"                     # cursor que titila
        dibujar_texto(pantalla, texto, fuentes["grande"], BLANCO if activo else GRIS, caja.center)
    dibujar_texto(pantalla, "ENTER = listo     BORRAR = corregir     ESC = volver al menú",
                  fuentes["media"], VERDE, (centro, 400))


def dibujar_carteles(pantalla, estado, juego, fuentes, luces, umbral, tiempo, datos):
    """Escribe los textos que corresponden a cada estado (menú, cuenta regresiva, final)."""
    centro = ANCHO // 2
    medio = ALTO // 2
    if estado == "jugando":
        if esta_pausado(juego):
            dibujar_texto(pantalla, "PAUSA", fuentes["grande"], AMARILLO, (centro, medio - 50))
            for i, jugador in enumerate(juego["jugadores"]):
                if jugador.perdio_la_luz():
                    quien = "tu linterna" if juego["modo"] == 1 else f"la linterna de {jugador.nombre}"
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
        dibujar_texto(pantalla, "1  =  un jugador", fuentes["grande"], AMARILLO, (centro, medio + 60))
        dibujar_texto(pantalla, "2  =  versus", fuentes["grande"], AMARILLO, (centro, medio + 110))
        if datos["record"] > 0:
            dibujar_texto(pantalla, f"Récord: {datos['record']}", fuentes["media"], BLANCO,
                          (centro, medio + 160))
        dibujar_texto(pantalla, f"Umbral de brillo: {umbral}   (+/- para ajustar, M para ver la luz)"
                      "   |   F = pantalla completa   |   ESC = salir",
                      fuentes["chica"], GRIS, (centro, ALTO - 20))

    elif estado == "cartel":
        segundos = max(1, int(juego["cartel"]) + 1)
        if juego["modo"] == 2:
            uno, dos = juego["jugadores"]
            dibujar_texto(pantalla, uno.nombre, fuentes["grande"], COLOR_JUGADOR_1, (centro - 240, medio - 165))
            dibujar_texto(pantalla, "vs", fuentes["grande"], AMARILLO, (centro, medio - 165))
            dibujar_texto(pantalla, dos.nombre, fuentes["grande"], COLOR_JUGADOR_2, (centro + 240, medio - 165))
            dibujar_texto(pantalla, "Gana el que aguante más:", fuentes["media"], BLANCO, (centro, medio - 90))
            dibujar_texto(pantalla, "pierde el primero que se queda sin vidas",
                          fuentes["media"], BLANCO, (centro, medio - 60))
            dibujar_texto(pantalla, "Girá la linterna en círculos para mandarle una BOMBA MORTAL al rival",
                          fuentes["chica"], COLOR_BOMBA_MORTAL, (centro, medio - 15))
            dibujar_texto(pantalla, "(una sola vez, y te deja con 1 vida)",
                          fuentes["chica"], COLOR_BOMBA_MORTAL, (centro, medio + 8))
        else:
            dibujar_texto(pantalla, "¡A CORTAR!", fuentes["titulo"], AMARILLO, (centro, medio - 150))
            if juego["record"] > 0:
                dibujar_texto(pantalla, f"Récord a superar: {juego['record']}", fuentes["grande"],
                              BLANCO, (centro, medio - 70))
            else:
                dibujar_texto(pantalla, "Todavía no hay récord: hacé el primero", fuentes["media"],
                              BLANCO, (centro, medio - 70))
            dibujar_texto(pantalla, "La partida sigue hasta que te quedes sin vidas",
                          fuentes["media"], BLANCO, (centro, medio - 15))
            dibujar_texto(pantalla, "y cada vez se pone más difícil",
                          fuentes["media"], BLANCO, (centro, medio + 15))
        dibujar_texto(pantalla, str(segundos), fuentes["titulo"], VERDE, (centro, medio + 120))

    elif estado == "perdiste":
        jugador = juego["jugadores"][0]
        dibujar_texto(pantalla, "FIN DE LA PARTIDA", fuentes["titulo"], ROJO, (centro, medio - 150))
        dibujar_texto(pantalla, f"Cortaste {frutas(jugador.puntos)}", fuentes["grande"], BLANCO,
                      (centro, medio - 65))
        if juego["nuevo_record"]:
            tono = graficos.mezclar(AMARILLO, BLANCO, (math.sin(tiempo * 6) + 1) / 2)
            dibujar_texto(pantalla, "¡NUEVO RÉCORD!", fuentes["titulo"], tono, (centro, medio + 15))
        else:
            faltaron = juego["record"] - jugador.puntos + 1
            dibujar_texto(pantalla, f"Récord: {juego['record']}", fuentes["grande"], AMARILLO,
                          (centro, medio))
            verbo = "Te faltó" if faltaron == 1 else "Te faltaron"
            dibujar_texto(pantalla, f"{verbo} {frutas(faltaron)} para superarlo", fuentes["media"],
                          BLANCO, (centro, medio + 45))
        dibujar_texto(pantalla, "ESPACIO = otra vez     2 = versus     ESC = salir",
                      fuentes["media"], VERDE, (centro, medio + 130))

    elif estado == "fin_versus":
        uno, dos = juego["jugadores"]
        dibujar_texto(pantalla, juego["resultado"], fuentes["titulo"], AMARILLO, (centro, 60))
        dibujar_texto(pantalla, f"{uno.nombre}: {frutas(uno.cortadas)}", fuentes["media"],
                      COLOR_JUGADOR_1, (centro - 210, 125))
        dibujar_texto(pantalla, f"{dos.nombre}: {frutas(dos.cortadas)}", fuentes["media"],
                      COLOR_JUGADOR_2, (centro + 210, 125))
        dibujar_texto(pantalla, f"Duración: {formato_tiempo(juego['tiempo'])}", fuentes["chica"],
                      GRIS, (centro, 155))
        ganadas1, ganadas2, empates = resultados.historial_entre(datos["versus"], uno.nombre, dos.nombre)
        historial = f"Historial: {uno.nombre} {ganadas1} - {ganadas2} {dos.nombre}"
        if empates:
            historial += f"   ({empates} empate{'s' if empates > 1 else ''})"
        dibujar_texto(pantalla, historial, fuentes["grande"], BLANCO, (centro, 205))
        dibujar_texto(pantalla, "Últimas partidas", fuentes["media"], AMARILLO, (centro, 260))
        ultimas = datos["versus"][-PARTIDAS_EN_PANTALLA:][::-1]     # la más nueva primero
        for i, partida in enumerate(ultimas):
            ganador = f"ganó {partida['ganador']}" if partida["ganador"] else "empate"
            linea = (f"{partida['fecha']}    {partida['jugador1']} {partida['frutas1']} - "
                     f"{partida['frutas2']} {partida['jugador2']}    {ganador}")
            dibujar_texto(pantalla, linea, fuentes["chica"], BLANCO if i == 0 else GRIS,
                          (centro, 292 + i * 26))
        dibujar_texto(pantalla, "ESPACIO = revancha     2 = otros nombres     1 = un jugador     ESC = salir",
                      fuentes["media"], VERDE, (centro, ALTO - 35))


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
    fuentes = cargar_fuentes()
    datos = resultados.cargar_resultados()
    fondo = graficos.crear_fondo(ANCHO, ALTO, COLOR_FONDO, OSCURIDAD_CENTRO, OSCURIDAD_BORDE)
    capa_cartel = crear_capa(CAPA_CARTEL)
    destello = crear_capa((255, 30, 30, 110))
    # Las espadas de luz se dibujan en dos capas que después se suman a la pantalla:
    # una chica para el resplandor (se agranda y queda borrosa) y una nítida.
    capa_suave = pygame.Surface((ANCHO // 4, ALTO // 4))
    capa_nitida = pygame.Surface((ANCHO, ALTO))
    corazones = {True: graficos.crear_corazon(28, True), False: graficos.crear_corazon(28, False)}
    paneles = {
        "puntos": graficos.crear_panel(200, 104),
        "vidas": graficos.crear_panel(160, 64),
        "versus": graficos.crear_panel(MITAD - 24, 112),
    }

    # Estados: "menu" -> "cartel" (cuenta regresiva) -> "jugando" -> "perdiste"
    #          versus: "menu" -> "nombres" -> "cartel" -> "jugando" -> "fin_versus"
    estado = "menu"
    nombres = ["", ""]           # nombres del versus (se recuerdan para la revancha)
    cual_nombre = 0              # qué nombre se está escribiendo
    juego = nueva_partida(1, nombres, datos["record"])
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
            elif estado == "nombres":
                # Mientras se escriben los nombres, el teclado es para escribir.
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    pygame.key.stop_text_input()
                    estado = "menu"
                elif evento.type in (pygame.KEYDOWN, pygame.TEXTINPUT):
                    cual_nombre = escribir_nombre(nombres, cual_nombre, evento)
                    if cual_nombre == 2:      # ya están los dos nombres: ¡a jugar!
                        pygame.key.stop_text_input()
                        juego = nueva_partida(2, nombres, datos["record"])
                        estado = "cartel"
            elif evento.type == pygame.KEYDOWN:
                puede_empezar = estado in ("menu", "perdiste", "fin_versus")
                if evento.key == pygame.K_ESCAPE:
                    corriendo = False
                elif evento.key in (pygame.K_1, pygame.K_KP1) and puede_empezar:
                    juego = nueva_partida(1, nombres, datos["record"])
                    estado = "cartel"
                elif evento.key in (pygame.K_2, pygame.K_KP2) and puede_empezar:
                    cual_nombre = 0
                    estado = "nombres"
                    pygame.key.start_text_input()   # ahora sí, las teclas escriben
                elif evento.key == pygame.K_SPACE and puede_empezar:
                    # mismo modo que la última vez (en el versus, con los mismos nombres)
                    juego = nueva_partida(juego["modo"], nombres, datos["record"])
                    estado = "cartel"
                elif evento.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()   # en ventana aparece la X para cerrar
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
        if estado == "menu":
            adornos = actualizar_adornos(adornos, dt)
        elif estado == "cartel":
            juego["cartel"] -= dt
            if juego["cartel"] <= 0:
                estado = "jugando"
        elif estado == "jugando":
            estado = actualizar_partida(juego, luces, dt, sonidos)
            if estado in ("perdiste", "fin_versus"):
                terminar_partida(juego, datos)      # se guarda el resultado

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
        # (el resplandor se difumina y se agranda: queda suave, como luz de verdad)
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
        if estado == "nombres":
            dibujar_nombres(pantalla, fuentes, nombres, cual_nombre, tiempo)
        else:
            dibujar_carteles(pantalla, estado, juego, fuentes, luces, umbral, tiempo, datos)

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
