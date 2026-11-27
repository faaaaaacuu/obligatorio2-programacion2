"""El jugador: su luz (la espada), su rastro, sus frutas, sus vidas y la bomba mortal.
"""

import math
import pygame
import random

import graficos
from ajustes import (ALTO, BLANCO, CHISPAS_AL_TIRAR_MORTAL, COLORES_EXPLOSION_MORTAL,
                     COLOR_BOMBA_MORTAL, DURACION_DESTELLO, DURACION_MENSAJE, FRUTAS_PARA_VIDA,
                     GIRO_MAXIMO_TRAZO, HUECO_MAXIMO_CORTE, LARGO_RASTRO, MOVIMIENTO_MINIMO, NEGRO,
                     RADIO_BOLA, RADIO_CHISPAS_TIRAR, REBOTE_EN_EL_BORDE, ROJO, TOLERANCIA_SIN_LUZ,
                     VELOCIDAD_CHISPAS_TIRAR, VENTANA_CIRCULO, VERDE, VIDAS, VIDAS_AL_TIRAR_BOMBA,
                     VUELTAS_PARA_BOMBA)
from objetos import (BombaMortal, Fruta, TextoFlotante, centro_de, contar_vueltas,
                     es_salto_imposible, pegar_centrado, salpicar)


class Jugador:
    """Una persona con su linterna. Tiene su zona de la pantalla (toda la
    pantalla si juega solo, una mitad en el versus), sus frutas, el rastro
    de su luz, sus vidas y sus puntos."""

    def __init__(self, nombre, color, x_min, x_max, frutas, con_bomba=False):
        """Crea un jugador con su nombre, el color de su espada, su zona de la pantalla
        (de x_min a x_max), sus tipos de fruta y si puede usar la bomba mortal."""
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
        se va achicando. Recién después se considera que no hay linterna.

        Si la luz "salta" a una velocidad imposible para una mano (un reflejo),
        ese cuadro se ignora, como si no se hubiera visto la luz."""
        if luz is not None and self.luz is not None:
            # tiempo desde la última posición buena: este cuadro + los que no se vio
            if es_salto_imposible(self.luz, luz, self.sin_luz + dt):
                luz = None
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
                                        COLORES_EXPLOSION_MORTAL, CHISPAS_AL_TIRAR_MORTAL,
                                        VELOCIDAD_CHISPAS_TIRAR, RADIO_CHISPAS_TIRAR))
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

    def mantener_en_zona(self, cosa, radio):
        """Si una fruta (o un pedazo, o una gota) se va a salir por un costado de
        la zona del jugador, rebota hacia adentro: así nada pasa al campo del rival."""
        if cosa.x - radio < self.x_min:
            cosa.x = self.x_min + radio
            cosa.vx = abs(cosa.vx) * REBOTE_EN_EL_BORDE
        elif cosa.x + radio > self.x_max:
            cosa.x = self.x_max - radio
            cosa.vx = -abs(cosa.vx) * REBOTE_EN_EL_BORDE

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
            self.mantener_en_zona(fruta, fruta.radio)
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
        for pedazo in self.pedazos:
            self.mantener_en_zona(pedazo, pedazo.radio)
        for particula in self.particulas:
            self.mantener_en_zona(particula, particula.radio)
        self.pedazos = [p for p in self.pedazos if not p.fuera_de_pantalla()]
        self.particulas = [p for p in self.particulas if p.viva()]
        self.textos = [t for t in self.textos if t.viva()]

    def dibujar(self, pantalla, fuente):
        """Dibuja sus frutas, los pedazos, el jugo, la bola si la está cargando
        y los "+1". (La espada de luz se dibuja aparte, en dibujar_brillo.)
        Todo se dibuja "recortado" a la zona del jugador (set_clip): aunque una
        imagen sea más grande, nunca se ve del lado del rival."""
        pantalla.set_clip(pygame.Rect(self.x_min, 0, self.x_max - self.x_min, ALTO))
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
        pantalla.set_clip(None)         # vuelve a dejar dibujar en toda la pantalla

    def dibujar_brillo(self, capa_suave, capa_nitida):
        """Dibuja la espada de luz en las capas de brillo (se suman a la pantalla)."""
        graficos.dibujar_espada(capa_suave, capa_nitida, self.rastro, self.color, self.luz)
