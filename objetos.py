"""Clases del juego: las frutas (y bombas), los pedazos que quedan al
cortarlas, la bomba mortal del versus y el jugador (con su linterna, sus
frutas, vidas y puntos)."""

import math
import random

import pygame

from ajustes import (ALTO, ALTURA_MINIMA, ALTURA_MAXIMA, VELOCIDAD_LATERAL,
                     GIRO_PEDAZOS, MARGEN_CORTE,
                     VIDAS, TOLERANCIA_SIN_LUZ, MOVIMIENTO_MINIMO, LARGO_RASTRO,
                     GROSOR_RASTRO, RADIO_LUZ, DURACION_MENSAJE, DURACION_DESTELLO,
                     VENTANA_CIRCULO, VUELTAS_PARA_BOMBA, MOVIMIENTO_MINIMO_GIRO,
                     GIRO_MAXIMO_POR_PASO, RADIO_BOLA, RADIO_BOMBA_MORTAL,
                     GRAVEDAD_BOMBA_MORTAL, VIDAS_AL_TIRAR_BOMBA, COLOR_BOMBA_MORTAL,
                     BLANCO, ROJO, AMARILLO, GRIS_OSCURO, VERDE_HOJA)

MARRON = (110, 70, 30)


def distancia_punto_segmento(punto, inicio, fin):
    """Devuelve la distancia entre un punto y el segmento que va de `inicio` a `fin`.
    Sirve para saber si el recorrido de la luz pasó por encima de una fruta."""
    px, py = punto
    ax, ay = inicio
    bx, by = fin
    dx, dy = bx - ax, by - ay
    largo2 = dx * dx + dy * dy
    if largo2 == 0:
        return math.hypot(px - ax, py - ay)
    # t dice en qué parte del segmento está el punto más cercano (0 = inicio, 1 = fin)
    t = ((px - ax) * dx + (py - ay) * dy) / largo2
    t = max(0, min(1, t))
    cerca_x = ax + t * dx
    cerca_y = ay + t * dy
    return math.hypot(px - cerca_x, py - cerca_y)


def contar_vueltas(puntos):
    """Recorre el camino reciente de la luz y devuelve cuántas vueltas seguidas
    dio girando siempre para el mismo lado (1.0 = un círculo completo).

    Idea: al dibujar un círculo, la dirección en la que se mueve la luz va
    doblando de a poco y siempre para el mismo lado; después de una vuelta
    dobló 360°. Al cortar, en cambio, la luz va y vuelve: eso es un giro
    brusco, y un giro brusco vuelve la cuenta a cero."""
    if len(puntos) < 2:
        return 0.0
    giro_total = 0.0                # en radianes; positivo o negativo según el sentido
    direccion_anterior = None
    anterior = puntos[0]
    limite = math.radians(GIRO_MAXIMO_POR_PASO)
    for punto in puntos[1:]:
        dx = punto[0] - anterior[0]
        dy = punto[1] - anterior[1]
        if math.hypot(dx, dy) < MOVIMIENTO_MINIMO_GIRO:
            continue                # casi no se movió: espero a que se mueva más
        direccion = math.atan2(dy, dx)
        if direccion_anterior is not None:
            cambio = direccion - direccion_anterior
            # pasar de 179° a -179° es doblar 2°, no 358°: se corrige
            if cambio > math.pi:
                cambio -= 2 * math.pi
            elif cambio < -math.pi:
                cambio += 2 * math.pi
            if abs(cambio) > limite:
                giro_total = 0.0    # dobló de golpe: es un corte, no un círculo
            else:
                giro_total += cambio
        direccion_anterior = direccion
        anterior = punto
    return abs(giro_total) / (2 * math.pi)


def centro_de(puntos):
    """Devuelve el punto promedio de una lista de puntos (el centro del círculo)."""
    x = sum(p[0] for p in puntos) / len(puntos)
    y = sum(p[1] for p in puntos) / len(puntos)
    return (int(x), int(y))


class Fruta:
    """Una fruta (o una bomba) que sale desde abajo, sube y vuelve a caer.
    Aparece entre x_min y x_max (la zona del jugador al que le toca) y es
    de alguno de los tipos de `frutas` (cada jugador tiene las suyas)."""

    def __init__(self, reglas, x_min, x_max, frutas):
        self.radio = random.randint(*reglas["radio"])
        ancho_zona = x_max - x_min
        self.x = float(random.randint(int(x_min + ancho_zona * 0.15),
                                      int(x_max - ancho_zona * 0.15)))
        self.y = float(ALTO + self.radio)
        self.gravedad = reglas["gravedad"]
        self.bomba = random.random() < reglas["bombas"]
        self.mortal = False         # solo la BombaMortal lo tiene en True
        self.tipo = random.choice(frutas)
        self.lanzar(x_min, x_max)

    def lanzar(self, x_min, x_max):
        """Calcula la velocidad para que suba hasta una altura al azar."""
        # v = raíz(2 * g * altura) es la velocidad justa para llegar a esa altura.
        # Después la gravedad la hace caer.
        punto_mas_alto = ALTO * (1 - random.uniform(ALTURA_MINIMA, ALTURA_MAXIMA))
        subida = self.y - punto_mas_alto
        self.vy = -math.sqrt(2 * self.gravedad * subida)
        # Se mueve un poco de costado, siempre hacia el centro de su zona para no salirse.
        lado = 1 if self.x < (x_min + x_max) / 2 else -1
        self.vx = random.uniform(*VELOCIDAD_LATERAL) * lado

    def actualizar(self, dt):
        """Se mueve sola: la gravedad cambia la velocidad y la velocidad la posición."""
        self.vy += self.gravedad * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def se_cayo(self):
        """Devuelve True si ya bajó y salió por abajo de la pantalla."""
        return self.vy > 0 and self.y - self.radio > ALTO

    def fue_cortada(self, inicio, fin):
        """Devuelve True si el segmento que recorrió la luz pasa por la fruta."""
        distancia = distancia_punto_segmento((self.x, self.y), inicio, fin)
        return distancia < self.radio + MARGEN_CORTE

    def partir(self):
        """Devuelve las dos mitades de la fruta, que salen cada una para su lado."""
        return [Pedazo(self, -1), Pedazo(self, 1)]

    def dibujar(self, pantalla):
        x, y, r = int(self.x), int(self.y), self.radio
        if self.bomba:
            pygame.draw.circle(pantalla, GRIS_OSCURO, (x, y), r)
            pygame.draw.circle(pantalla, BLANCO, (x, y), r, 2)
            cruz = r // 3
            pygame.draw.line(pantalla, ROJO, (x - cruz, y - cruz), (x + cruz, y + cruz), 6)
            pygame.draw.line(pantalla, ROJO, (x + cruz, y - cruz), (x - cruz, y + cruz), 6)
            mecha = (x + 18, y - r - 14)
            pygame.draw.line(pantalla, AMARILLO, (x + 6, y - r + 2), mecha, 4)
            pygame.draw.circle(pantalla, AMARILLO, mecha, 5)
            return

        tipo = self.tipo["tipo"]
        color = self.tipo["color"]
        oscuro = tuple(c * 2 // 3 for c in color)

        if tipo == "uva":
            # racimo de 6 uvitas
            u = int(r * 0.4)
            for dx, dy in ((-1.6, -1.2), (0, -1.2), (1.6, -1.2), (-0.8, 0.3), (0.8, 0.3), (0, 1.8)):
                centro = (x + int(dx * u), y + int(dy * u))
                pygame.draw.circle(pantalla, color, centro, u)
                pygame.draw.circle(pantalla, BLANCO, centro, u, 1)
            pygame.draw.line(pantalla, MARRON, (x, y - int(2.2 * u)), (x + 4, y - r - 4), 4)
            return

        if tipo == "limon":
            # más ancho que alto, con dos puntitas
            rect = pygame.Rect(0, 0, 2 * r, int(1.5 * r))
            rect.center = (x, y)
            pygame.draw.circle(pantalla, color, (x - r, y), r // 5)
            pygame.draw.circle(pantalla, color, (x + r, y), r // 5)
            pygame.draw.ellipse(pantalla, color, rect)
            pygame.draw.ellipse(pantalla, BLANCO, rect, 2)
        else:
            pygame.draw.circle(pantalla, color, (x, y), r)
            if tipo == "sandia":
                # rayas verde oscuro
                for ancho in (0.35, 0.75):
                    rayas = pygame.Rect(0, 0, int(2 * r * ancho), 2 * r)
                    rayas.center = (x, y)
                    pygame.draw.ellipse(pantalla, oscuro, rayas, 4)
            elif tipo in ("naranja", "kiwi"):
                # puntitos en la cáscara
                for dx, dy in ((-0.4, 0.1), (0.3, 0.4), (0.1, -0.3), (-0.2, 0.55), (0.55, -0.1)):
                    pygame.draw.circle(pantalla, oscuro, (x + int(dx * r), y + int(dy * r)), 3)
            pygame.draw.circle(pantalla, BLANCO, (x, y), r, 2)

        if tipo != "kiwi":
            brillo = pygame.Rect(0, 0, r // 2, r // 3)
            brillo.center = (x - r // 3, y - r // 3)
            pygame.draw.ellipse(pantalla, BLANCO, brillo)
        if tipo in ("manzana", "naranja", "limon"):
            pygame.draw.line(pantalla, MARRON, (x, y - r + 4), (x + 3, y - r - 8), 3)
            hoja = pygame.Rect(0, 0, r // 2, r // 4)
            hoja.center = (x + r // 4, y - r - 4)
            pygame.draw.ellipse(pantalla, VERDE_HOJA, hoja)


class BombaMortal(Fruta):
    """La bomba que se carga girando la linterna. Aparece en la mitad del rival:
    si la corta, se queda sin vidas y pierde. Es una Fruta, pero se dibuja distinto."""

    def __init__(self, x_min, x_max):
        reglas = {"radio": (RADIO_BOMBA_MORTAL, RADIO_BOMBA_MORTAL),
                  "gravedad": GRAVEDAD_BOMBA_MORTAL, "bombas": 1}
        super().__init__(reglas, x_min, x_max, [None])
        self.mortal = True
        self.tiempo = 0.0           # para que titile

    def actualizar(self, dt):
        super().actualizar(dt)
        self.tiempo += dt

    def dibujar(self, pantalla):
        x, y, r = int(self.x), int(self.y), self.radio
        latido = int(6 * abs(math.sin(self.tiempo * 6)))
        pygame.draw.circle(pantalla, COLOR_BOMBA_MORTAL, (x, y), r + 6 + latido, 4)
        pygame.draw.circle(pantalla, (40, 0, 60), (x, y), r)
        pygame.draw.circle(pantalla, COLOR_BOMBA_MORTAL, (x, y), r // 2 + latido)
        pygame.draw.circle(pantalla, BLANCO, (x, y), r, 2)
        mecha = (x + 20, y - r - 16)
        pygame.draw.line(pantalla, AMARILLO, (x + 6, y - r + 2), mecha, 4)
        pygame.draw.circle(pantalla, ROJO if latido > 3 else AMARILLO, mecha, 6)


class Pedazo:
    """Media fruta que sale volando y cae después de un corte."""

    def __init__(self, fruta, lado):
        self.x = fruta.x
        self.y = fruta.y
        self.radio = fruta.radio
        self.color = fruta.tipo["color"]
        self.pulpa = fruta.tipo["pulpa"]
        self.gravedad = fruta.gravedad
        self.lado = lado                    # -1 = mitad izquierda, 1 = mitad derecha
        self.vx = fruta.vx + GIRO_PEDAZOS * lado
        self.vy = min(fruta.vy, 0) - 40     # saltan un poquito para arriba

    def actualizar(self, dt):
        self.vy += self.gravedad * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def fuera_de_pantalla(self):
        """Devuelve True cuando el pedazo ya cayó por abajo."""
        return self.y - self.radio > ALTO

    def dibujar(self, pantalla):
        centro = (int(self.x), int(self.y))
        izquierda = self.lado < 0
        # pygame puede dibujar solo algunos cuartos del círculo: así queda media fruta.
        # Primero la cáscara y encima, un poco más chica, la pulpa.
        for color, radio in ((self.color, self.radio), (self.pulpa, self.radio - 5)):
            pygame.draw.circle(pantalla, color, centro, radio,
                               draw_top_left=izquierda, draw_bottom_left=izquierda,
                               draw_top_right=not izquierda, draw_bottom_right=not izquierda)


class Jugador:
    """Una persona con su linterna. Tiene su zona de la pantalla (toda la
    pantalla si juega solo, una mitad en el versus), sus frutas, el rastro
    de su luz, sus vidas y sus puntos."""

    def __init__(self, nombre, color, x_min, x_max, frutas, con_bomba=False):
        self.nombre = nombre
        self.color = color          # color de su rastro de luz y de su texto
        self.x_min = x_min
        self.x_max = x_max
        self.tipos_de_fruta = frutas
        self.con_bomba = con_bomba  # la bomba mortal existe solo en el versus
        self.bomba_usada = False    # se puede usar una sola vez por partida
        self.puntos = 0
        self.reiniciar()

    def reiniciar(self):
        """Deja todo listo para empezar un nivel (los puntos se mantienen)."""
        self.frutas = []
        self.pedazos = []
        self.rastro = []
        self.camino = []            # posiciones recientes, para ver si gira en círculos
        self.carga = 0.0            # cuánto de la bola está cargado (0 a 1)
        self.centro_carga = None
        self.luz = None             # posición de la luz en este cuadro, o None
        self.luz_anterior = None
        self.cortadas = 0
        self.vidas = VIDAS
        self.espera = 0.5           # la primera fruta sale enseguida
        self.sin_luz = 0.0          # cuánto hace que la cámara no ve su linterna
        self.mensaje = ""
        self.mensaje_tiempo = 0.0
        self.destello = 0.0

    def perdio_la_luz(self):
        """Devuelve True si hace rato que la cámara no ve su linterna."""
        return self.sin_luz > TOLERANCIA_SIN_LUZ

    def mover_luz(self, luz, dt):
        """Guarda la nueva posición de la luz. Devuelve el segmento que recorrió
        desde el cuadro anterior, o None si no hubo un movimiento que corte."""
        self.luz = luz
        if luz is None:
            self.sin_luz += dt
            self.luz_anterior = None
            self.camino = []
            if self.rastro:
                self.rastro.pop(0)      # el rastro se va borrando de a poco
            return None

        self.sin_luz = 0.0
        segmento = None
        if self.luz_anterior is not None:
            movimiento = abs(luz[0] - self.luz_anterior[0]) + abs(luz[1] - self.luz_anterior[1])
            if movimiento >= MOVIMIENTO_MINIMO:
                segmento = (self.luz_anterior, luz)
        self.luz_anterior = luz
        self.rastro.append(luz)
        self.rastro = self.rastro[-LARGO_RASTRO:]
        self.camino.append(luz)
        self.camino = self.camino[-VENTANA_CIRCULO:]
        return segmento

    def cargar_bomba(self):
        """Si el jugador gira la linterna en círculos, se va cargando la bola.
        Devuelve True cuando la bola se completa y hay que mandarle la bomba al rival."""
        if not self.con_bomba or self.bomba_usada:
            return False
        vueltas = contar_vueltas(self.camino)
        self.carga = min(1.0, vueltas / VUELTAS_PARA_BOMBA)
        if self.camino:
            self.centro_carga = centro_de(self.camino[-30:])   # la bola se forma en el medio del círculo
        if self.carga < 1:
            return False
        self.bomba_usada = True
        self.vidas = min(self.vidas, VIDAS_AL_TIRAR_BOMBA)   # tirarla te deja con 1 vida
        self.camino = []
        self.carga = 0.0
        self.mostrar_mensaje("¡BOMBA LANZADA!")
        return True

    def recibir_bomba(self):
        """El rival me mandó su bomba mortal: aparece entre mis frutas."""
        self.frutas.append(BombaMortal(self.x_min, self.x_max))
        self.mostrar_mensaje("¡CUIDADO!")

    def mostrar_mensaje(self, texto):
        self.mensaje = texto
        self.mensaje_tiempo = DURACION_MENSAJE

    def actualizar(self, segmento, reglas, dt, sonidos):
        """Hace aparecer, mover, cortar y caer las frutas de este jugador."""
        self.mensaje_tiempo -= dt
        self.destello -= dt

        # Aparecen frutas nuevas (la lista crece).
        self.espera -= dt
        if self.espera <= 0 and len(self.frutas) < reglas["max_frutas"]:
            self.frutas.append(Fruta(reglas, self.x_min, self.x_max, self.tipos_de_fruta))
            self.espera = random.uniform(*reglas["espera"])

        # Mover frutas, ver si la luz las cortó o si se cayeron (la lista se achica).
        quedan = []
        for fruta in self.frutas:
            fruta.actualizar(dt)
            if segmento is not None and fruta.fue_cortada(*segmento):
                self.destello = DURACION_DESTELLO
                if fruta.mortal:
                    self.vidas = 0          # la bomba mortal te deja sin vidas
                    self.mostrar_mensaje("¡BOMBA MORTAL!")
                    sonidos["mortal"].play()
                elif fruta.bomba:
                    self.vidas -= 1
                    self.mostrar_mensaje("¡BOMBA!")
                    sonidos["bomba"].play()
                else:
                    self.destello = 0
                    self.puntos += 1
                    self.cortadas += 1
                    self.pedazos.extend(fruta.partir())
                    self.mostrar_mensaje("+1")
                    sonidos["corte"].play()
            elif fruta.se_cayo():
                if not fruta.bomba:     # dejar caer una bomba está bien
                    self.vidas -= 1
                    self.mostrar_mensaje("¡Se te cayó una!")
                    sonidos["caida"].play()
            else:
                quedan.append(fruta)
        self.frutas = quedan

        for pedazo in self.pedazos:
            pedazo.actualizar(dt)
        self.pedazos = [p for p in self.pedazos if not p.fuera_de_pantalla()]

    def dibujar(self, pantalla):
        """Dibuja sus frutas, los pedazos, la bola si la está cargando y la
        estela de la luz (más gruesa cuanto más nueva)."""
        for fruta in self.frutas:
            fruta.dibujar(pantalla)
        for pedazo in self.pedazos:
            pedazo.dibujar(pantalla)
        if self.carga > 0.5 and self.centro_carga is not None:
            radio = int(8 + RADIO_BOLA * self.carga)
            pygame.draw.circle(pantalla, COLOR_BOMBA_MORTAL, self.centro_carga, radio)
            pygame.draw.circle(pantalla, BLANCO, self.centro_carga, radio, 2)
        for i in range(1, len(self.rastro)):
            grosor = max(2, GROSOR_RASTRO * i // len(self.rastro))
            pygame.draw.line(pantalla, self.color, self.rastro[i - 1], self.rastro[i], grosor)
        if self.luz is not None:
            pygame.draw.circle(pantalla, AMARILLO, self.luz, RADIO_LUZ, 3)
