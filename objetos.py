"""Clases del juego: las frutas (y bombas), los pedazos que quedan al
cortarlas, las partículas (jugo y explosiones), los textos que flotan, la
bomba mortal del versus y el jugador (con su linterna, frutas, vidas y puntos)."""

import math
import random

import pygame

import graficos
from ajustes import (ALTO, ALTURA_MINIMA, ALTURA_MAXIMA, VELOCIDAD_LATERAL,
                     VELOCIDAD_GIRO, SEPARACION_PEDAZOS, MARGEN_CORTE,
                     VIDAS, TOLERANCIA_SIN_LUZ, HUECO_MAXIMO_CORTE, MOVIMIENTO_MINIMO, LARGO_RASTRO,
                     DURACION_MENSAJE, DURACION_DESTELLO, DURACION_TEXTO_FLOTANTE,
                     VENTANA_CIRCULO, VUELTAS_PARA_BOMBA, MOVIMIENTO_MINIMO_GIRO,
                     GIRO_MAXIMO_POR_PASO, RADIO_BOLA, RADIO_BOMBA_MORTAL,
                     GRAVEDAD_BOMBA_MORTAL, VIDAS_AL_TIRAR_BOMBA, COLOR_BOMBA_MORTAL,
                     GOTAS_POR_CORTE, CHISPAS_POR_BOMBA, GRAVEDAD_PARTICULAS,
                     FRUTAS_PARA_VIDA, GIRO_MAXIMO_TRAZO,
                     BLANCO, NEGRO, ROJO, VERDE)

COLORES_EXPLOSION = [(255, 140, 30), (255, 220, 60), (255, 255, 255), (90, 90, 90)]
COLORES_EXPLOSION_MORTAL = [COLOR_BOMBA_MORTAL, (230, 160, 255), (255, 255, 255)]


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
                            (100, 500), (4, 10))
        if self.bomba:
            return salpicar(self.x, self.y, COLORES_EXPLOSION, CHISPAS_POR_BOMBA, (100, 420), (3, 9))
        colores = [self.tipo["pulpa"], self.tipo["color"]]
        return salpicar(self.x, self.y, colores, GOTAS_POR_CORTE, (80, 280), (3, 7))

    def dibujar(self, pantalla):
        pegar_centrado(pantalla, self.imagen, self.x, self.y, self.angulo)
        if self.bomba:
            mx, my = graficos.punta_de_mecha(self.radio)
            graficos.dibujar_chispa(pantalla, self.x + mx, self.y + my)


class BombaMortal(Fruta):
    """La bomba que se carga girando la linterna. Aparece en la mitad del rival:
    si la corta, se queda sin vidas y pierde. Es una Fruta, pero se dibuja distinto."""

    def __init__(self, x_min, x_max):
        reglas = {"radio": (RADIO_BOMBA_MORTAL, RADIO_BOMBA_MORTAL),
                  "gravedad": GRAVEDAD_BOMBA_MORTAL, "bombas": 1}
        super().__init__(reglas, x_min, x_max, [None])
        self.mortal = True
        self.imagen = graficos.crear_imagen_bomba(self.radio, mortal=True)
        self.halo = graficos.crear_halo(self.radio * 2, COLOR_BOMBA_MORTAL)
        self.tiempo = 0.0           # para que el halo "lata"

    def actualizar(self, dt):
        super().actualizar(dt)
        self.tiempo += dt

    def dibujar(self, pantalla):
        self.halo.set_alpha(int(155 + 100 * math.sin(self.tiempo * 7)))
        pegar_centrado(pantalla, self.halo, self.x, self.y)
        super().dibujar(pantalla)


class Pedazo:
    """Media fruta que sale volando, girando, después de un corte."""

    def __init__(self, fruta, lado, angulo):
        self.x = fruta.x
        self.y = fruta.y
        self.radio = fruta.radio
        self.gravedad = fruta.gravedad
        self.imagen = graficos.crear_imagen_mitad(fruta.tipo, fruta.radio, lado)
        self.angulo = angulo
        self.giro = random.uniform(60, 180) * lado
        # Cada mitad se aleja del corte hacia su lado (perpendicular al corte).
        a = math.radians(angulo)
        self.vx = fruta.vx + SEPARACION_PEDAZOS * lado * math.cos(a)
        self.vy = min(fruta.vy, 0) - 40 - SEPARACION_PEDAZOS * lado * math.sin(a)

    def actualizar(self, dt):
        self.vy += self.gravedad * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angulo += self.giro * dt

    def fuera_de_pantalla(self):
        """Devuelve True cuando el pedazo ya cayó por abajo."""
        return self.y - self.radio > ALTO

    def dibujar(self, pantalla):
        pegar_centrado(pantalla, self.imagen, self.x, self.y, self.angulo)


class Particula:
    """Una gotita de jugo o una chispa de explosión: sale disparada, cae y se achica."""

    def __init__(self, x, y, color, velocidad, radio):
        angulo = random.uniform(0, 2 * math.pi)
        rapidez = random.uniform(*velocidad)
        self.x, self.y = x, y
        self.vx = math.cos(angulo) * rapidez
        self.vy = math.sin(angulo) * rapidez - 120     # un poco hacia arriba
        self.color = color
        self.radio = random.uniform(*radio)
        self.vida = random.uniform(0.4, 0.9)           # segundos que dura
        self.edad = 0.0

    def actualizar(self, dt):
        self.vy += GRAVEDAD_PARTICULAS * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.edad += dt

    def viva(self):
        """Devuelve True mientras no se terminó su tiempo de vida."""
        return self.edad < self.vida

    def dibujar(self, pantalla):
        radio = self.radio * (1 - self.edad / self.vida)   # se va achicando
        if radio >= 1:
            pygame.draw.circle(pantalla, self.color, (int(self.x), int(self.y)), radio)


class TextoFlotante:
    """Un texto (como "+1") que sube desde la fruta cortada y se desvanece."""

    def __init__(self, x, y, texto, color):
        self.x, self.y = x, y
        self.texto = texto
        self.color = color
        self.edad = 0.0

    def actualizar(self, dt):
        self.y -= 70 * dt
        self.edad += dt

    def viva(self):
        """Devuelve True mientras se tiene que seguir viendo."""
        return self.edad < DURACION_TEXTO_FLOTANTE

    def dibujar(self, pantalla, fuente):
        transparencia = int(255 * (1 - self.edad / DURACION_TEXTO_FLOTANTE))
        for color, corrida in ((NEGRO, 2), (self.color, 0)):
            imagen = fuente.render(self.texto, True, color)
            imagen.set_alpha(transparencia)
            pantalla.blit(imagen, imagen.get_rect(center=(int(self.x) + corrida, int(self.y) + corrida)))


class Jugador:
    """Una persona con su linterna. Tiene su zona de la pantalla (toda la
    pantalla si juega solo, una mitad en el versus), sus frutas, el rastro
    de su luz, sus vidas y sus puntos."""

    def __init__(self, nombre, color, x_min, x_max, frutas, con_bomba=False):
        self.nombre = nombre
        self.color = color          # color de su espada de luz y de su texto
        self.x_min = x_min
        self.x_max = x_max
        self.tipos_de_fruta = frutas
        self.con_bomba = con_bomba  # la bomba mortal existe solo en el versus
        self.bomba_usada = False    # se puede usar una sola vez por partida
        self.halo_bola = graficos.crear_halo(RADIO_BOLA * 2, COLOR_BOMBA_MORTAL)
        self.puntos = 0
        self.reiniciar()

    def reiniciar(self):
        """Deja todo listo para empezar un nivel (los puntos se mantienen)."""
        self.frutas = []
        self.pedazos = []
        self.particulas = []
        self.textos = []
        self.rastro = []
        self.camino = []            # posiciones recientes, para ver si gira en círculos
        self.carga = 0.0            # cuánto de la bola está cargado (0 a 1)
        self.centro_carga = None
        self.luz = None             # posición de la luz en este cuadro, o None
        self.luz_anterior = None
        self.frutas_en_trazo = 0    # frutas cortadas en el trazo actual (para el combo)
        self.direccion_trazo = None
        self.cortadas = 0
        self.vidas = VIDAS
        self.espera = 0.5           # la primera fruta sale enseguida
        self.sin_luz = 0.0          # cuánto hace que la cámara no ve su linterna
        self.mensaje = ""
        self.mensaje_color = ROJO
        self.mensaje_tiempo = 0.0
        self.destello = 0.0

    def perdio_la_luz(self):
        """Devuelve True si hace rato que la cámara no ve su linterna."""
        return self.sin_luz > TOLERANCIA_SIN_LUZ

    def mover_luz(self, luz, dt):
        """Guarda la nueva posición de la luz. Devuelve el segmento que recorrió
        desde el cuadro anterior, o None si no hubo un movimiento que corte.

        Si la cámara no ve la luz, no se la da por perdida enseguida: durante
        TOLERANCIA_SIN_LUZ segundos el punto se queda donde estaba y la estela
        se va achicando. Recién después se considera que no hay linterna."""
        if luz is None:
            self.sin_luz += dt
            if self.rastro:
                self.rastro.pop(0)      # la estela se va borrando de a poco
            if self.perdio_la_luz():
                self.luz = None
                self.luz_anterior = None
                self.camino = []
            return None

        hueco = self.sin_luz            # cuánto tiempo estuvo sin verse
        self.sin_luz = 0.0
        self.luz = luz
        if hueco > HUECO_MAXIMO_CORTE:
            # desapareció un buen rato: empieza un trazo nuevo (no une los dos lugares)
            self.luz_anterior = None
            self.rastro = []
            self.camino = []
        segmento = None
        if self.luz_anterior is not None:
            movimiento = abs(luz[0] - self.luz_anterior[0]) + abs(luz[1] - self.luz_anterior[1])
            if movimiento >= MOVIMIENTO_MINIMO:
                segmento = (self.luz_anterior, luz)
        self.seguir_trazo(segmento)
        self.luz_anterior = luz
        self.rastro.append(luz)
        self.rastro = self.rastro[-LARGO_RASTRO:]
        self.camino.append(luz)
        self.camino = self.camino[-VENTANA_CIRCULO:]
        return segmento

    def seguir_trazo(self, segmento):
        """Lleva la cuenta del trazo actual: un movimiento seguido de la luz.
        Si la luz se frena, se pierde o dobla de golpe (por ejemplo, va y vuelve),
        termina el trazo y la cuenta de frutas vuelve a cero."""
        if segmento is None:
            self.frutas_en_trazo = 0
            self.direccion_trazo = None
            return
        (ax, ay), (bx, by) = segmento
        direccion = math.atan2(by - ay, bx - ax)
        if self.direccion_trazo is not None:
            cambio = abs(direccion - self.direccion_trazo) % (2 * math.pi)
            cambio = min(cambio, 2 * math.pi - cambio)     # el ángulo más corto entre las dos
            if cambio > math.radians(GIRO_MAXIMO_TRAZO):
                self.frutas_en_trazo = 0
        self.direccion_trazo = direccion

    def premiar_combo(self, sonidos):
        """Cortó FRUTAS_PARA_VIDA frutas en un solo trazo: si le faltan vidas, gana una."""
        if 0 < self.vidas < VIDAS:
            self.vidas += 1
            self.mostrar_mensaje("¡TRIPLE! +1 VIDA", VERDE, DURACION_MENSAJE * 2.5)
            sonidos["vida"].play()
        else:
            self.mostrar_mensaje("¡TRIPLE!", VERDE, DURACION_MENSAJE * 2)

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
        self.particulas.extend(salpicar(self.centro_carga[0], self.centro_carga[1],
                                        COLORES_EXPLOSION_MORTAL, 25, (100, 350), (3, 8)))
        self.camino = []
        self.carga = 0.0
        self.mostrar_mensaje("¡BOMBA LANZADA!")
        return True

    def recibir_bomba(self):
        """El rival me mandó su bomba mortal: aparece entre mis frutas."""
        self.frutas.append(BombaMortal(self.x_min, self.x_max))
        self.mostrar_mensaje("¡CUIDADO!")

    def mostrar_mensaje(self, texto, color=ROJO, duracion=DURACION_MENSAJE):
        """Muestra un cartel grande en la zona del jugador durante un ratito."""
        self.mensaje = texto
        self.mensaje_color = color
        self.mensaje_tiempo = duracion

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
                self.particulas.extend(fruta.explotar())
                if fruta.mortal:
                    self.vidas = 0          # la bomba mortal te deja sin vidas
                    self.destello = DURACION_DESTELLO * 3
                    self.mostrar_mensaje("¡BOMBA MORTAL!")
                    sonidos["mortal"].play()
                elif fruta.bomba:
                    self.vidas -= 1
                    self.destello = DURACION_DESTELLO
                    self.mostrar_mensaje("¡BOMBA!")
                    sonidos["bomba"].play()
                else:
                    self.puntos += 1
                    self.cortadas += 1
                    self.pedazos.extend(fruta.partir(*segmento))
                    self.textos.append(TextoFlotante(fruta.x, fruta.y - fruta.radio, "+1", self.color))
                    sonidos["corte"].play()
                    self.frutas_en_trazo += 1
                    if self.frutas_en_trazo == FRUTAS_PARA_VIDA:
                        self.premiar_combo(sonidos)
            elif fruta.se_cayo():
                if not fruta.bomba:     # dejar caer una bomba está bien
                    self.vidas -= 1
                    self.mostrar_mensaje("¡Se te cayó una!")
                    sonidos["caida"].play()
            else:
                quedan.append(fruta)
        self.frutas = quedan

        # Pedazos, partículas y textos: se mueven y se borran cuando terminan.
        for cosa in self.pedazos + self.particulas + self.textos:
            cosa.actualizar(dt)
        self.pedazos = [p for p in self.pedazos if not p.fuera_de_pantalla()]
        self.particulas = [p for p in self.particulas if p.viva()]
        self.textos = [t for t in self.textos if t.viva()]

    def dibujar(self, pantalla, fuente):
        """Dibuja sus frutas, los pedazos, el jugo, la bola si la está cargando
        y los "+1". (La espada de luz se dibuja aparte, en dibujar_brillo.)"""
        for pedazo in self.pedazos:
            pedazo.dibujar(pantalla)
        for fruta in self.frutas:
            fruta.dibujar(pantalla)
        for particula in self.particulas:
            particula.dibujar(pantalla)
        if self.carga > 0.5 and self.centro_carga is not None:
            x, y = self.centro_carga
            radio = int(8 + RADIO_BOLA * self.carga)
            halo = pygame.transform.smoothscale(self.halo_bola, (radio * 4, radio * 4))
            pegar_centrado(pantalla, halo, x, y)
            pygame.draw.circle(pantalla, NEGRO, (x, y), radio + 2)
            graficos.ovalo_con_volumen(pantalla, (x, y), radio * 2, radio * 2, COLOR_BOMBA_MORTAL, 6)
            # anillo que muestra cuánto falta para completarla
            anillo = pygame.Rect(0, 0, radio * 2 + 18, radio * 2 + 18)
            anillo.center = (x, y)
            pygame.draw.arc(pantalla, BLANCO, anillo, math.pi / 2,
                            math.pi / 2 + 2 * math.pi * self.carga, 4)
        for texto in self.textos:
            texto.dibujar(pantalla, fuente)

    def dibujar_brillo(self, capa_suave, capa_nitida):
        """Dibuja la espada de luz en las capas de brillo (se suman a la pantalla)."""
        graficos.dibujar_espada(capa_suave, capa_nitida, self.rastro, self.color, self.luz)
