"""La música de fondo (la arma generar_sonidos.py): una tranquila para el menú
y cuatro versiones épicas para la partida, cada una más rápida y cargada.
Durante la partida suena una más intensa cuanto más difícil está el juego, y
se pasa de una a otra con un fundido.
"""

import os

import pygame

from ajustes import ARCHIVOS_MUSICA, VOLUMEN_MUSICA, FUNDIDO_MUSICA_MS


class Musica:
    """Las versiones de la música y los dos canales donde suenan. Mientras una
    versión se apaga en un canal, la nueva entra en el otro (un "fundido")."""

    def __init__(self, carpeta):
        # Todas las versiones se cargan una sola vez, antes del bucle.
        # Si falta algún archivo, el juego sigue sin música.
        self.pistas = []
        for archivo in ARCHIVOS_MUSICA:
            ruta = os.path.join(carpeta, archivo)
            if not os.path.exists(ruta):
                self.pistas = []
                break
            self.pistas.append(pygame.mixer.Sound(ruta))
        # Se reservan los canales 0 y 1 para la música: así los efectos de sonido
        # nunca los usan y no la cortan.
        pygame.mixer.set_reserved(2)
        self.canales = [pygame.mixer.Channel(0), pygame.mixer.Channel(1)]
        self.cual = 0               # en qué canal está sonando ahora
        self.sonando = None         # qué versión (intensidad) está sonando

    def poner(self, intensidad):
        """Hace sonar la versión de esa intensidad, si no es la que ya suena."""
        if not self.pistas or intensidad == self.sonando:
            return
        self.canales[self.cual].fadeout(FUNDIDO_MUSICA_MS)       # la que suena se va apagando...
        self.cual = 1 - self.cual
        canal = self.canales[self.cual]
        canal.set_volume(VOLUMEN_MUSICA)
        canal.play(self.pistas[intensidad], loops=-1, fade_ms=FUNDIDO_MUSICA_MS)   # ...y entra la nueva
        self.sonando = intensidad
