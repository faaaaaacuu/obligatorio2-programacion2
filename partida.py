"""La partida: cómo empieza, cómo avanza cada cuadro, cómo termina, y lo que se
dibuja encima (puntos, vidas, nombres, carteles de pausa y de fin).
"""

import math
import pygame

import graficos
import inicio
import interfaz
import resultados
from ajustes import (ACHIQUE_ESPERA, ALTO, ALTO_TECLA_CHICA, ALTO_TECLA_MEDIA, AMARILLO, ANCHO,
                     AUMENTO_BOMBAS, AUMENTO_GRAVEDAD, BLANCO, BOTON_INICIO, CAJA_NOMBRE,
                     COLOR_BOMBA_MORTAL, COLOR_JUGADOR_1, COLOR_JUGADOR_2, DURACION_CARTEL,
                     DURACION_DESTELLO, DURACION_MENSAJE, ESCALA_FRUTAS_VERSUS, FRUTAS_JUGADOR_1,
                     FRUTAS_JUGADOR_2, FRUTAS_POR_NIVEL, GRIS, LACA, LARGO_MAXIMO_NOMBRE, MITAD,
                     NIVELES, NIVEL_INICIAL_VERSUS, NIVEL_MINIMO_MUSICA, PARTIDAS_EN_PANTALLA,
                     RADIO_MINIMO, ROJO, SEGUNDOS_POR_NIVEL, TOPE_BOMBAS, TOPE_ESPERA,
                     TOPE_GRAVEDAD, TOPE_MAX_FRUTAS, VIDAS)
from interfaz import (dibujar_atajos, dibujar_tecla_chica, dibujar_texto)
from jugador import Jugador


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
        "pausa": None,              # None, "manual" (tecla P o se cambió de ventana) o "salir" (pregunta si abandonar)
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
    """Devuelve True si la partida está frenada: porque el jugador la pausó, porque se
    está preguntando si abandonarla o porque la cámara perdió la linterna de alguien."""
    if juego["pausa"] is not None:
        return True
    return any(jugador.perdio_la_luz() for jugador in juego["jugadores"])


# Teclas que se dibujan con una palabra o un símbolo, y la tecla de verdad que representan.
TECLAS_CON_NOMBRE = {"ESC": pygame.K_ESCAPE, "ESPACIO": pygame.K_SPACE, "ENTER": pygame.K_RETURN,
                     "BORRAR": pygame.K_BACKSPACE, "←": pygame.K_LEFT, "→": pygame.K_RIGHT,
                     "+": pygame.K_PLUS, "-": pygame.K_MINUS}


def tecla_de(etiqueta):
    """Devuelve el código de pygame de una tecla dibujada ("ESC", "R", "1"...)."""
    if etiqueta in TECLAS_CON_NOMBRE:
        return TECLAS_CON_NOMBRE[etiqueta]
    return pygame.key.key_code(etiqueta.lower())


def apretar(etiqueta):
    """Hace de cuenta que se apretó una tecla: así un clic en un botón hace
    exactamente lo mismo que su tecla, sin repetir la lógica."""
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=tecla_de(etiqueta), mod=0,
                                         unicode="", scancode=0))


def es_salir_del_sistema(evento):
    """Devuelve True si es Cmd+Q (Mac) o Ctrl+Q (Windows/Linux): cerrar el programa."""
    return (evento.type == pygame.KEYDOWN and evento.key == pygame.K_q
            and bool(evento.mod & (pygame.KMOD_META | pygame.KMOD_CTRL)))


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
    interfaz.registrar_zona(boton, "ESC")         # hacer clic es como apretar ESC
    encima = boton.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(pantalla, LACA, boton, border_radius=4)
    pygame.draw.rect(pantalla, BLANCO if encima else AMARILLO, boton, 2 if encima else 1, border_radius=4)
    # una flechita hacia la izquierda
    x, y = boton.left + 18, boton.centery
    pygame.draw.polygon(pantalla, AMARILLO, [(x - 7, y), (x + 4, y - 7), (x + 4, y + 7)])
    dibujar_texto(pantalla, "INICIO", fuentes["media"], BLANCO if encima else AMARILLO,
                  (boton.left + 32, boton.centery - fuentes["media"].get_height() // 2), False)
    dibujar_tecla_chica(pantalla, fuentes["texto"], "ESC", boton.right - 44, boton.centery - 11, 20, GRIS)


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


def dibujar_carteles(pantalla, estado, juego, fuentes, hay_luz, umbral, tiempo, datos, color,
                     imagenes_inicio):
    """Escribe los textos que corresponden a cada estado (menú, cuenta regresiva, final)."""
    centro = ANCHO // 2
    medio = ALTO // 2
    if estado == "jugando":
        if juego["pausa"] == "salir":
            # como cualquier programa: antes de perder lo hecho, pregunta
            dibujar_texto(pantalla, "¿ABANDONAR LA PARTIDA?", fuentes["grande"], AMARILLO, (centro, medio - 50))
            dibujar_texto(pantalla, "Lo que llevás jugado no se guarda", fuentes["chica"], BLANCO,
                          (centro, medio - 5))
            dibujar_atajos(pantalla, [(("S",), "sí, abandonar"), (("N",), "no, seguir")], fuentes["media"],
                           fuentes["chica"], ALTO_TECLA_MEDIA, BLANCO, AMARILLO, (centro, medio + 55))
        elif juego["pausa"] == "manual":
            dibujar_texto(pantalla, "PAUSA", fuentes["grande"], AMARILLO, (centro, medio - 50))
            dibujar_atajos(pantalla, [(("P",), "seguir"), (("ESC",), "abandonar")], fuentes["media"],
                           fuentes["chica"], ALTO_TECLA_MEDIA, BLANCO, AMARILLO, (centro, medio + 20))
        elif esta_pausado(juego):
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
    interfaz.dibujar_farol(pantalla, imagenes_inicio["farol"], imagenes_inicio["halo_farol"], 50, 10, tiempo)
    interfaz.dibujar_farol(pantalla, imagenes_inicio["farol"], imagenes_inicio["halo_farol"],
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
        interfaz.dibujar_enso(pantalla, (centro, medio + 124), 50, ROJO, 10, avance / 0.6)
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
        atajos = [(("ESPACIO",), "otra vez"), (("2",), "versus"), (("ESC",), "inicio")]
        dibujar_atajos(pantalla, atajos, fuentes["media"], fuentes["chica"], ALTO_TECLA_MEDIA, BLANCO,
                       AMARILLO, (centro, medio + 130))

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
        atajos = [(("ESPACIO",), "revancha"), (("2",), "otros nombres"), (("1",), "un jugador"),
                  (("ESC",), "inicio")]
        dibujar_atajos(pantalla, atajos, fuentes["media"], fuentes["chica"], ALTO_TECLA_MEDIA, BLANCO,
                       AMARILLO, (centro, ALTO - 35))
