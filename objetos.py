"""Clases del juego: las frutas (y bombas), los pedazos que quedan al
cortarlas, las partículas (jugo y explosiones), los textos que flotan, la
bomba mortal del versus y el jugador (con su linterna, frutas, vidas y puntos)."""

import math
import random

import pygame

import graficos
from ajustes import (ALTO, ALTURA_MAXIMA, ALTURA_MINIMA, CHISPAS_POR_BOMBA, COLORES_EXPLOSION,
                     COLORES_EXPLOSION_MORTAL, COLOR_BOMBA_MORTAL, DURACION_TEXTO_FLOTANTE,
                     EMPUJE_PARTICULAS, GIRO_MAXIMO_POR_PASO, GIRO_PEDAZOS, GOTAS_POR_CORTE,
                     GRAVEDAD_BOMBA_MORTAL, GRAVEDAD_PARTICULAS, MARGEN_CORTE,
                     MOVIMIENTO_MINIMO_GIRO, NEGRO, RADIO_BOMBA_MORTAL, RADIO_CHISPAS,
                     RADIO_CHISPAS_MORTAL, RADIO_JUGO, SALTO_PEDAZOS, SEPARACION_PEDAZOS,
                     VELOCIDAD_CHISPAS, VELOCIDAD_CHISPAS_MORTAL, VELOCIDAD_GIRO, VELOCIDAD_JUGO,
                     VELOCIDAD_LATERAL, VELOCIDAD_MAXIMA_LUZ, VELOCIDAD_TEXTO_FLOTANTE,
                     VIDA_PARTICULAS)


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


def es_salto_imposible(desde, hasta, segundos):
    """Devuelve True si ir de `desde` a `hasta` en esos segundos es más rápido de lo
    que una mano puede mover la linterna (VELOCIDAD_MAXIMA_LUZ). Pasa cuando la
    cámara confunde la linterna con un reflejo que aparece lejos de golpe."""
    distancia = math.hypot(hasta[0] - desde[0], hasta[1] - desde[1])
    return distancia > VELOCIDAD_MAXIMA_LUZ * segundos


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


def salpicar(x, y, colores, cantidad, velocidad, radio):
    """Devuelve una lista de partículas que salen disparadas desde (x, y)."""
    return [Particula(x, y, random.choice(colores), velocidad, radio) for _ in range(cantidad)]


def pegar_centrado(pantalla, imagen, x, y, angulo=0):
    """Gira la imagen `angulo` grados y la pega con su centro en (x, y)."""
    if angulo:
        imagen = pygame.transform.rotozoom(imagen, angulo, 1)
    pantalla.blit(imagen, imagen.get_rect(center=(int(x), int(y))))


class Fruta:
    """Una fruta (o una bomba) que sale desde abajo, sube girando y vuelve a caer.
    Aparece entre x_min y x_max (la zona del jugador al que le toca) y es
    de alguno de los tipos de `frutas` (cada jugador tiene las suyas)."""

    def __init__(self, reglas, x_min, x_max, frutas):
        """Crea una fruta (o una bomba, según la probabilidad del nivel) abajo de la
        pantalla, entre x_min y x_max, con la velocidad justa para subir y volver a caer."""
        self.radio = random.randint(*reglas["radio"])
        ancho_zona = x_max - x_min
        self.x = float(random.randint(int(x_min + ancho_zona * 0.15),
                                      int(x_max - ancho_zona * 0.15)))
        self.y = float(ALTO + self.radio)
        self.gravedad = reglas["gravedad"]
        self.bomba = random.random() < reglas["bombas"]
        self.mortal = False         # solo la BombaMortal lo tiene en True
        self.tipo = random.choice(frutas)
        self.angulo = random.uniform(0, 360)
        if self.bomba:
            self.angulo = 0
            self.giro = 0           # las bombas no giran, así la mecha queda arriba
            self.imagen = graficos.crear_imagen_bomba(self.radio)
        else:
            self.giro = random.uniform(*VELOCIDAD_GIRO) * random.choice((-1, 1))
            self.imagen = graficos.crear_imagen_fruta(self.tipo, self.radio)
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
        self.angulo += self.giro * dt

    def se_cayo(self):
        """Devuelve True si ya bajó y salió por abajo de la pantalla."""
        return self.vy > 0 and self.y - self.radio > ALTO

    def fue_cortada(self, inicio, fin):
        """Devuelve True si el segmento que recorrió la luz pasa por la fruta."""
        distancia = distancia_punto_segmento((self.x, self.y), inicio, fin)
        return distancia < self.radio + MARGEN_CORTE

    def partir(self, inicio, fin):
        """Devuelve las dos mitades de la fruta. El corte sigue la dirección en
        la que se movió la luz, y cada mitad sale para su lado."""
        dx, dy = fin[0] - inicio[0], fin[1] - inicio[1]
        # Ángulo para que la línea del corte quede paralela al movimiento de la luz
        angulo = math.degrees(math.atan2(dx, dy))
        return [Pedazo(self, -1, angulo), Pedazo(self, 1, angulo)]

    def explotar(self):
        """Devuelve las partículas de la explosión (bomba) o del jugo (fruta)."""
        if self.mortal:
            return salpicar(self.x, self.y, COLORES_EXPLOSION_MORTAL, CHISPAS_POR_BOMBA * 2,
                            VELOCIDAD_CHISPAS_MORTAL, RADIO_CHISPAS_MORTAL)
        if self.bomba:
            return salpicar(self.x, self.y, COLORES_EXPLOSION, CHISPAS_POR_BOMBA, VELOCIDAD_CHISPAS, RADIO_CHISPAS)
        colores = [self.tipo["pulpa"], self.tipo["color"]]
        return salpicar(self.x, self.y, colores, GOTAS_POR_CORTE, VELOCIDAD_JUGO, RADIO_JUGO)

    def dibujar(self, pantalla):
        """Dibuja la fruta girada; si es una bomba, también la chispa de la mecha."""
        pegar_centrado(pantalla, self.imagen, self.x, self.y, self.angulo)
        if self.bomba:
            mx, my = graficos.punta_de_mecha(self.radio)
            graficos.dibujar_chispa(pantalla, self.x + mx, self.y + my)


class BombaMortal(Fruta):
    """La bomba que se carga girando la linterna. Aparece en la mitad del rival:
    si la corta, se queda sin vidas y pierde. Es una Fruta, pero se dibuja distinto."""

    def __init__(self, x_min, x_max):
        """Crea la bomba mortal en la zona del rival: más grande, más lenta y con un halo violeta."""
        reglas = {"radio": (RADIO_BOMBA_MORTAL, RADIO_BOMBA_MORTAL),
                  "gravedad": GRAVEDAD_BOMBA_MORTAL, "bombas": 1}
        super().__init__(reglas, x_min, x_max, [None])
        self.mortal = True
        self.imagen = graficos.crear_imagen_bomba(self.radio, mortal=True)
        self.halo = graficos.crear_halo(self.radio * 2, COLOR_BOMBA_MORTAL)
        self.tiempo = 0.0           # para que el halo "lata"

    def actualizar(self, dt):
        """Se mueve como cualquier fruta y avanza el tiempo para que el halo lata."""
        super().actualizar(dt)
        self.tiempo += dt

    def dibujar(self, pantalla):
        """Dibuja el halo, que se prende y se apaga, y encima la bomba."""
        self.halo.set_alpha(int(155 + 100 * math.sin(self.tiempo * 7)))
        pegar_centrado(pantalla, self.halo, self.x, self.y)
        super().dibujar(pantalla)


class Pedazo:
    """Media fruta que sale volando, girando, después de un corte."""

    def __init__(self, fruta, lado, angulo):
        """Crea una de las dos mitades de `fruta`. `lado` es -1 o 1 (para qué lado sale)
        y `angulo` es la dirección del corte."""
        self.x = fruta.x
        self.y = fruta.y
        self.radio = fruta.radio
        self.gravedad = fruta.gravedad
        self.imagen = graficos.crear_imagen_mitad(fruta.tipo, fruta.radio, lado)
        self.angulo = angulo
        self.giro = random.uniform(*GIRO_PEDAZOS) * lado
        # Cada mitad se aleja del corte hacia su lado (perpendicular al corte).
        a = math.radians(angulo)
        self.vx = fruta.vx + SEPARACION_PEDAZOS * lado * math.cos(a)
        self.vy = min(fruta.vy, 0) - SALTO_PEDAZOS - SEPARACION_PEDAZOS * lado * math.sin(a)

    def actualizar(self, dt):
        """Cae con la gravedad y gira mientras se aleja del corte."""
        self.vy += self.gravedad * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angulo += self.giro * dt

    def fuera_de_pantalla(self):
        """Devuelve True cuando el pedazo ya cayó por abajo."""
        return self.y - self.radio > ALTO

    def dibujar(self, pantalla):
        """Dibuja la mitad girada en su posición."""
        pegar_centrado(pantalla, self.imagen, self.x, self.y, self.angulo)


class Particula:
    """Una gotita de jugo o una chispa de explosión: sale disparada, cae y se achica."""

    def __init__(self, x, y, color, velocidad, radio):
        """Crea una gota o chispa que sale para un lado al azar, con una rapidez
        y un tamaño elegidos dentro de los rangos `velocidad` y `radio`."""
        angulo = random.uniform(0, 2 * math.pi)
        rapidez = random.uniform(*velocidad)
        self.x, self.y = x, y
        self.vx = math.cos(angulo) * rapidez
        self.vy = math.sin(angulo) * rapidez - EMPUJE_PARTICULAS   # un poco hacia arriba
        self.color = color
        self.radio = random.uniform(*radio)
        self.vida = random.uniform(*VIDA_PARTICULAS)           # segundos que dura
        self.edad = 0.0

    def actualizar(self, dt):
        """Cae con la gravedad y suma tiempo a su edad."""
        self.vy += GRAVEDAD_PARTICULAS * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.edad += dt

    def viva(self):
        """Devuelve True mientras no se terminó su tiempo de vida."""
        return self.edad < self.vida

    def dibujar(self, pantalla):
        """Dibuja la partícula como un círculo que se achica a medida que envejece."""
        radio = self.radio * (1 - self.edad / self.vida)   # se va achicando
        if radio >= 1:
            pygame.draw.circle(pantalla, self.color, (int(self.x), int(self.y)), radio)


class TextoFlotante:
    """Un texto (como "+1") que sube desde la fruta cortada y se desvanece."""

    def __init__(self, x, y, texto, color):
        """Crea un texto (por ejemplo "+1") en (x, y) con su color."""
        self.x, self.y = x, y
        self.texto = texto
        self.color = color
        self.edad = 0.0

    def actualizar(self, dt):
        """Sube despacio y suma tiempo a su edad."""
        self.y -= VELOCIDAD_TEXTO_FLOTANTE * dt
        self.edad += dt

    def viva(self):
        """Devuelve True mientras se tiene que seguir viendo."""
        return self.edad < DURACION_TEXTO_FLOTANTE

    def dibujar(self, pantalla, fuente):
        """Dibuja el texto con sombra; se va haciendo transparente hasta desaparecer."""
        transparencia = int(255 * (1 - self.edad / DURACION_TEXTO_FLOTANTE))
        for color, corrida in ((NEGRO, 2), (self.color, 0)):
            imagen = fuente.render(self.texto, True, color)
            imagen.set_alpha(transparencia)
            pantalla.blit(imagen, imagen.get_rect(center=(int(self.x) + corrida, int(self.y) + corrida)))
