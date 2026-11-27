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

Controles:
  1 / 2    empezar 1 jugador / versus
  ESPACIO  volver a jugar el mismo modo
  + / -    subir / bajar el umbral de brillo de la detección
  M        mostrar / ocultar lo que la cámara toma como "luz"
  C        cambiar el color de la luz y su estela (1 jugador)
  F        pantalla completa / ventana
  ESC      volver a la pantalla de inicio (en la pantalla de inicio: salir)
           También hay un botón "INICIO" que se puede clickear, y la X cierra la ventana.
"""

import math
import os
import random

# Al agrandar el juego a pantalla completa, que lo suavice en vez de pixelarlo.
os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "linear")

import pygame

import graficos
import inicio
import resultados
from musica import Musica
import vision
from ajustes import *
from graficos import dibujar_texto
from objetos import Jugador

CARPETA = os.path.dirname(os.path.abspath(__file__))
NOMBRES_SONIDOS = ("bomba", "caida", "nivel", "ganar", "perder", "lanzar", "mortal", "vida", "sello",
                   "espadazo", "cuenta_3", "cuenta_2", "cuenta_1", "comienzo")
MITAD = ANCHO // 2
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
        "titulo": cargar_fuente(ARCHIVO_FUENTE_TITULO, 56),
        "grande": cargar_fuente(ARCHIVO_FUENTE_TITULO, 34),
        "tarjeta": cargar_fuente(ARCHIVO_FUENTE_TITULO, 15),
        "media": cargar_fuente(ARCHIVO_FUENTE_TEXTO, 20),
        "chica": cargar_fuente(ARCHIVO_FUENTE_TEXTO, 14),
        "texto": cargar_fuente(ARCHIVO_FUENTE_TEXTO, 12),
        "numero": cargar_fuente(ARCHIVO_FUENTE_TEXTO, 36),   # números claros (el 0 de Shojumaru confunde)
        "numero_grande": cargar_fuente(ARCHIVO_FUENTE_TEXTO, 60),
        "kanji": cargar_fuente(ARCHIVO_FUENTE_TEXTO, 40),
        "kanji_chico": cargar_fuente(ARCHIVO_FUENTE_TEXTO, 26),
    }


def crear_capa(color):
    """Devuelve una superficie del tamaño de la ventana, de un color semitransparente."""
    capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    capa.fill(color)
    return capa


# ---------------------------------------------------------------------------
# Lógica de la partida
# ---------------------------------------------------------------------------

def nueva_partida(modo, nombres, record, color):
    """Devuelve el estado inicial de una partida. modo 1 = un jugador, 2 = versus.
    `nombres` son los nombres del versus, `record` el récord a superar y
    `color` el filtro de color de la luz jugando solo."""
    if modo == 1:
        jugadores = [Jugador("Vos", color, 0, ANCHO, FRUTAS_JUGADOR_1 + FRUTAS_JUGADOR_2)]
    else:
        # cada uno con sus frutas y con su bomba mortal
        jugadores = [Jugador(nombres[0], COLOR_JUGADOR_1, 0, MITAD, FRUTAS_JUGADOR_1, True),
                     Jugador(nombres[1], COLOR_JUGADOR_2, MITAD, ANCHO, FRUTAS_JUGADOR_2, True)]
    return {
        "modo": modo,
        "jugadores": jugadores,
        "cartel": DURACION_CARTEL,  # cuenta regresiva antes de empezar
        "numero_cuenta": None,      # el último número de la cuenta regresiva que sonó
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


def achicar_frutas(reglas, escala):
    """Devuelve una copia de las reglas con las frutas `escala` veces su tamaño."""
    chico, grande = reglas["radio"]
    return dict(reglas, radio=(int(chico * escala), int(grande * escala)))


def nivel_actual(juego):
    """Devuelve el nivel de dificultad. Sube solo, sin avisar: jugando solo,
    cada FRUTAS_POR_NIVEL frutas cortadas; en el versus, cada SEGUNDOS_POR_NIVEL."""
    if juego["modo"] == 1:
        return juego["jugadores"][0].cortadas // FRUTAS_POR_NIVEL
    return NIVEL_INICIAL_VERSUS + int(juego["tiempo"] // SEGUNDOS_POR_NIVEL)


def intensidad_de_musica(estado, juego):
    """Qué música va: 0 es la tranquila (fuera de la partida); durante la partida
    va una épica, de 1 a 4, más rápida y cargada cuanto más alto es el nivel."""
    if estado != "jugando":
        return 0
    nivel = nivel_actual(juego)
    return sum(1 for minimo in NIVEL_MINIMO_MUSICA if nivel >= minimo)


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
    if juego["modo"] == 2:
        reglas = achicar_frutas(reglas, ESCALA_FRUTAS_VERSUS)    # media pantalla: frutas más chicas
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


def dibujar_vidas(pantalla, iconos_vida, vidas, x, y):
    """Dibuja un sello por vida, a partir de (x, y)."""
    for i in range(VIDAS):
        imagen = iconos_vida[i < vidas]     # True = vida que queda, False = perdida
        pantalla.blit(imagen, imagen.get_rect(center=(x + i * 40, y)))


def dibujar_hud(pantalla, juego, fuentes, paneles, iconos_vida, destello):
    """Paneles con puntos, récord, vidas y los mensajes de cada jugador."""
    if juego["modo"] == 1:
        jugador = juego["jugadores"][0]
        pantalla.blit(paneles["puntos"], (12, 10))
        dibujar_texto(pantalla, "PUNTOS", fuentes["chica"], GRIS, (30, 18), False)
        dibujar_texto(pantalla, str(jugador.puntos), fuentes["numero"], BLANCO, (28, 30), False)
        if juego["supero_record"]:
            dibujar_texto(pantalla, "¡Récord superado!", fuentes["chica"], AMARILLO, (30, 82), False)
        elif juego["record"] > 0:
            dibujar_texto(pantalla, f"Récord: {juego['record']}", fuentes["chica"], AMARILLO, (30, 82), False)
        else:
            dibujar_texto(pantalla, "Sin récord todavía", fuentes["chica"], GRIS, (30, 82), False)
        x_panel = ANCHO - 12 - paneles["vidas"].get_width()
        pantalla.blit(paneles["vidas"], (x_panel, 10))
        dibujar_vidas(pantalla, iconos_vida, jugador.vidas, x_panel + 40, 42)
    else:
        for jugador in juego["jugadores"]:
            x = jugador.x_min + 12
            pantalla.blit(paneles["versus"], (x, 10))
            dibujar_texto(pantalla, jugador.nombre, fuentes["media"], jugador.color, (x + 16, 16), False)
            dibujar_vidas(pantalla, iconos_vida, jugador.vidas, x + 205, 32)
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


def dibujar_boton_inicio(pantalla, fuentes):
    """El botón para volver a la pantalla de inicio. Se aprieta con ESC o
    haciendo clic; si el mouse está encima, se ilumina."""
    boton = pygame.Rect(BOTON_INICIO)
    encima = boton.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(pantalla, LACA, boton, border_radius=4)
    pygame.draw.rect(pantalla, BLANCO if encima else AMARILLO, boton, 2 if encima else 1, border_radius=4)
    # una flechita hacia la izquierda
    x, y = boton.left + 18, boton.centery
    pygame.draw.polygon(pantalla, AMARILLO, [(x - 7, y), (x + 4, y - 7), (x + 4, y + 7)])
    dibujar_texto(pantalla, "INICIO", fuentes["media"], BLANCO if encima else AMARILLO,
                  (boton.left + 32, boton.centery - fuentes["media"].get_height() // 2), False)
    dibujar_texto(pantalla, "ESC", fuentes["texto"], GRIS, (boton.right - 22, boton.centery))


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
        caja = pygame.Rect((0, 0), CAJA_NOMBRE)
        caja.center = (x, 285)
        pygame.draw.rect(pantalla, LACA, caja, border_radius=4)
        pygame.draw.rect(pantalla, color if activo else GRIS, caja, 3 if activo else 1, border_radius=4)
        texto = nombres[i]
        if activo and int(tiempo * 2) % 2 == 0:
            texto += "|"                     # cursor que titila
        dibujar_texto(pantalla, texto, fuentes["grande"], BLANCO if activo else GRIS, caja.center)
    dibujar_texto(pantalla, "ENTER = listo     BORRAR = corregir     ESC = volver al inicio",
                  fuentes["media"], VERDE, (centro, 400))


def dibujar_carteles(pantalla, estado, juego, fuentes, hay_luz, umbral, tiempo, datos, color,
                     imagenes_inicio):
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
        inicio.dibujar_inicio(pantalla, fuentes, imagenes_inicio, tiempo, hay_luz, color,
                              datos["record"], umbral)
        return

    # En la cuenta regresiva y en los finales también cuelgan los faroles del dojo
    graficos.dibujar_farol(pantalla, imagenes_inicio["farol"], imagenes_inicio["halo_farol"], 50, 10, tiempo)
    graficos.dibujar_farol(pantalla, imagenes_inicio["farol"], imagenes_inicio["halo_farol"],
                           ANCHO - 50, 10, tiempo, 1.7)

    if estado == "cartel":
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
        # cada segundo se pinta un ensō (círculo de pincel) alrededor del número
        avance = 1 - (juego["cartel"] % 1)
        graficos.dibujar_enso(pantalla, (centro, medio + 124), 50, ROJO, 10, avance / 0.6)
        dibujar_texto(pantalla, str(segundos), fuentes["numero_grande"], BLANCO, (centro, medio + 122))

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
        dibujar_texto(pantalla, "ESPACIO = otra vez     2 = versus     ESC = inicio",
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
        dibujar_texto(pantalla, "ESPACIO = revancha     2 = otros nombres     1 = un jugador     ESC = inicio",
                      fuentes["media"], VERDE, (centro, ALTO - 35))


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

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
    fondo = graficos.crear_fondo(ANCHO, ALTO, COLOR_FONDO, OSCURIDAD_CENTRO, OSCURIDAD_BORDE)
    capa_cartel = crear_capa(CAPA_CARTEL)
    destello = crear_capa(COLOR_DESTELLO_BOMBA)
    # Las espadas de luz se dibujan en dos capas que después se suman a la pantalla:
    # una chica para el resplandor (se agranda y queda borrosa) y una nítida.
    capa_suave = pygame.Surface((ANCHO // 4, ALTO // 4))
    capa_nitida = pygame.Surface((ANCHO, ALTO))
    iconos_vida = {True: graficos.crear_vida(TAMANIO_VIDA, True),
                   False: graficos.crear_vida(TAMANIO_VIDA, False)}
    imagenes_inicio = inicio.crear_imagenes(fuentes)     # para las animaciones de la pantalla de inicio
    paneles = {
        "puntos": graficos.crear_panel(*PANEL_PUNTOS),
        "vidas": graficos.crear_panel(*PANEL_VIDAS),
        "versus": graficos.crear_panel(MITAD - MARGEN_PANEL_VERSUS, ALTO_PANEL_VERSUS),
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
            if evento.type == pygame.QUIT:
                corriendo = False
            elif (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
                  and estado not in ("intro", "tutorial", "menu")
                  and pygame.Rect(BOTON_INICIO).collidepoint(evento.pos)):
                # clic en el botón "INICIO" (si se estaba jugando, la partida se abandona)
                pygame.key.stop_text_input()
                estado = "menu"
            elif (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
                  and estado in ("intro", "tutorial")
                  and pygame.Rect(BOTON_SALTEAR).collidepoint(evento.pos)):
                estado = "menu"                 # clic en "SALTEAR": directo a la pantalla de inicio
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
                    tiempo_tutorial = inicio.pasar_tarjeta(tarjeta_tutorial, tiempo_tutorial)
                elif evento.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()
            elif estado == "nombres":
                # Mientras se escriben los nombres, el teclado es para escribir.
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    pygame.key.stop_text_input()
                    estado = "menu"
                elif evento.type in (pygame.KEYDOWN, pygame.TEXTINPUT):
                    cual_nombre = escribir_nombre(nombres, cual_nombre, evento)
                    if cual_nombre == 2:      # ya están los dos nombres: ¡a jugar!
                        pygame.key.stop_text_input()
                        juego = nueva_partida(2, nombres, datos["record"], COLORES_ESPADA[indice_color][1])
                        estado = "cartel"
            elif evento.type == pygame.KEYDOWN:
                puede_empezar = estado in ("menu", "perdiste", "fin_versus")
                if evento.key == pygame.K_ESCAPE:
                    if estado == "menu":
                        corriendo = False       # en la pantalla de inicio, ESC cierra el juego
                    else:
                        estado = "menu"         # en las demás, vuelve a la pantalla de inicio
                elif evento.key in (pygame.K_1, pygame.K_KP1) and puede_empezar:
                    juego = nueva_partida(1, nombres, datos["record"], COLORES_ESPADA[indice_color][1])
                    estado = "cartel"
                elif evento.key in (pygame.K_2, pygame.K_KP2) and puede_empezar:
                    cual_nombre = 0
                    estado = "nombres"
                    pygame.key.start_text_input()   # ahora sí, las teclas escriben
                elif evento.key == pygame.K_SPACE and puede_empezar:
                    # mismo modo que la última vez (en el versus, con los mismos nombres)
                    juego = nueva_partida(juego["modo"], nombres, datos["record"],
                                          COLORES_ESPADA[indice_color][1])
                    estado = "cartel"
                elif evento.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()   # en ventana aparece la X para cerrar
                elif evento.key == pygame.K_c:
                    # siguiente filtro de color (jugando solo, se aplica al instante)
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
            for nombre in inicio.sonidos_tutorial(tarjeta_tutorial, antes, tiempo_tutorial):
                sonidos[nombre].play()
            if tiempo_tutorial >= inicio.duracion_tarjeta(tarjeta_tutorial):
                # terminó de salir: entra la siguiente (o, si era la última, la pantalla de inicio)
                tarjeta_tutorial += 1
                tiempo_tutorial = 0.0
                if tarjeta_tutorial == len(inicio.TARJETAS):
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
        if estado == "intro":
            inicio.dibujar_intro(pantalla, capa_suave, capa_nitida, fuentes, imagenes_inicio, tiempo_intro)
            inicio.dibujar_boton_saltear(pantalla, fuentes)
        elif estado == "tutorial":
            inicio.dibujar_tutorial(pantalla, fuentes, imagenes_inicio, tarjeta_tutorial,
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
            # cómo volver a la pantalla de inicio: el botón, o mientras se juega solo un aviso chico
            if estado == "jugando" and not esta_pausado(juego):
                dibujar_texto(pantalla, "ESC = inicio", fuentes["texto"], GRIS, (18, ALTO - 30), False)
            elif estado != "menu":
                dibujar_boton_inicio(pantalla, fuentes)

            if ver_mascara and cuadro is not None:
                chica = vision.mascara_chica_rgb(cuadro, umbral, ANCHO // 4, ALTO // 4)
                pantalla.blit(a_superficie(chica), (ANCHO - ANCHO // 4 - 10, ALTO - ALTO // 4 - 10))

        pygame.display.flip()
        dt = min(reloj.tick(FPS) / 1000, DT_MAXIMO)  # tope por si un cuadro tarda mucho

    # Al cerrar la ventana se libera la cámara.
    cap.release()
    pygame.quit()


if __name__ == "__main__":
    main()
