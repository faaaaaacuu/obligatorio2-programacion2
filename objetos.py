"""Clases del juego: las frutas (y bombas), los pedazos que quedan al
cortarlas y el jugador (con su linterna, sus frutas, vidas y puntos)."""

import math
import random

import pygame

from ajustes import (ALTO, ALTURA_MINIMA, ALTURA_MAXIMA, VELOCIDAD_LATERAL,
                     GIRO_PEDAZOS, MARGEN_CORTE, COLORES_FRUTAS,
                     VIDAS, TOLERANCIA_SIN_LUZ, MOVIMIENTO_MINIMO, LARGO_RASTRO,
                     GROSOR_RASTRO, RADIO_LUZ, DURACION_MENSAJE, DURACION_DESTELLO,
                     BLANCO, ROJO, AMARILLO, GRIS_OSCURO, VERDE_HOJA)


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


class Fruta:
    """Una fruta (o una bomba) que sale desde abajo, sube y vuelve a caer.
    Aparece entre x_min y x_max (la zona del jugador al que le toca)."""

    def __init__(self, reglas, x_min, x_max):
        self.radio = random.randint(*reglas["radio"])
        ancho_zona = x_max - x_min
        self.x = float(random.randint(int(x_min + ancho_zona * 0.15),
                                      int(x_max - ancho_zona * 0.15)))
        self.y = float(ALTO + self.radio)
        self.gravedad = reglas["gravedad"]
        self.bomba = random.random() < reglas["bombas"]
        self.color = random.choice(COLORES_FRUTAS)
        # Elijo hasta qué altura sube y calculo la velocidad justa para llegar
        # ahí (v = raíz(2 * g * altura)). Después la gravedad la hace caer.
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
        centro = (int(self.x), int(self.y))
        if self.bomba:
            pygame.draw.circle(pantalla, GRIS_OSCURO, centro, self.radio)
            pygame.draw.circle(pantalla, BLANCO, centro, self.radio, 2)
            cruz = self.radio // 3
            pygame.draw.line(pantalla, ROJO, (centro[0] - cruz, centro[1] - cruz),
                             (centro[0] + cruz, centro[1] + cruz), 6)
            pygame.draw.line(pantalla, ROJO, (centro[0] + cruz, centro[1] - cruz),
                             (centro[0] - cruz, centro[1] + cruz), 6)
            mecha = (centro[0] + 18, centro[1] - self.radio - 14)
            pygame.draw.line(pantalla, AMARILLO, (centro[0] + 6, centro[1] - self.radio + 2), mecha, 4)
            pygame.draw.circle(pantalla, AMARILLO, mecha, 5)
            return

        pygame.draw.circle(pantalla, self.color, centro, self.radio)
        pygame.draw.circle(pantalla, BLANCO, centro, self.radio, 2)
        # brillo y hojita
        brillo = pygame.Rect(0, 0, self.radio // 2, self.radio // 3)
        brillo.center = (centro[0] - self.radio // 3, centro[1] - self.radio // 3)
        pygame.draw.ellipse(pantalla, BLANCO, brillo)
        hoja = pygame.Rect(0, 0, self.radio // 2, self.radio // 4)
        hoja.center = (centro[0] + self.radio // 5, centro[1] - self.radio - 3)
        pygame.draw.ellipse(pantalla, VERDE_HOJA, hoja)


class Pedazo:
    """Media fruta que sale volando y cae después de un corte."""

    def __init__(self, fruta, lado):
        self.x = fruta.x
        self.y = fruta.y
        self.radio = fruta.radio
        self.color = fruta.color
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
        # pygame puede dibujar solo algunos cuartos del círculo: así queda media fruta
        pygame.draw.circle(pantalla, self.color, centro, self.radio,
                           draw_top_left=izquierda, draw_bottom_left=izquierda,
                           draw_top_right=not izquierda, draw_bottom_right=not izquierda)
        # el corte se ve más claro, como la pulpa
        pygame.draw.line(pantalla, BLANCO, (centro[0], centro[1] - self.radio),
                         (centro[0], centro[1] + self.radio), 3)


class Jugador:
    """Una persona con su linterna. Tiene su zona de la pantalla (toda la
    pantalla si juega solo, una mitad en el versus), sus frutas, el rastro
    de su luz, sus vidas y sus puntos."""

    def __init__(self, nombre, color, x_min, x_max):
        self.nombre = nombre
        self.color = color          # color de su rastro de luz y de su texto
        self.x_min = x_min
        self.x_max = x_max
        self.puntos = 0
        self.reiniciar()

    def reiniciar(self):
        """Deja todo listo para empezar un nivel (los puntos se mantienen)."""
        self.frutas = []
        self.pedazos = []
        self.rastro = []
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
        return segmento

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
            self.frutas.append(Fruta(reglas, self.x_min, self.x_max))
            self.espera = random.uniform(*reglas["espera"])

        # Mover frutas, ver si la luz las cortó o si se cayeron (la lista se achica).
        quedan = []
        for fruta in self.frutas:
            fruta.actualizar(dt)
            if segmento is not None and fruta.fue_cortada(*segmento):
                if fruta.bomba:
                    self.vidas -= 1
                    self.destello = DURACION_DESTELLO
                    self.mostrar_mensaje("¡BOMBA!")
                    sonidos["bomba"].play()
                else:
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
        """Dibuja sus frutas, los pedazos y la estela de la luz (más gruesa cuanto más nueva)."""
        for fruta in self.frutas:
            fruta.dibujar(pantalla)
        for pedazo in self.pedazos:
            pedazo.dibujar(pantalla)
        for i in range(1, len(self.rastro)):
            grosor = max(2, GROSOR_RASTRO * i // len(self.rastro))
            pygame.draw.line(pantalla, self.color, self.rastro[i - 1], self.rastro[i], grosor)
        if self.luz is not None:
            pygame.draw.circle(pantalla, AMARILLO, self.luz, RADIO_LUZ, 3)
