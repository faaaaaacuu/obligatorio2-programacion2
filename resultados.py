"""Guarda y lee los resultados en un archivo JSON (resultados.json), así el
récord y el historial del versus quedan guardados aunque se cierre el juego.

El archivo tiene esta forma:
    {
      "record": 42,
      "versus": [
        {"fecha": "14/11 15:30", "jugador1": "Ana", "frutas1": 23,
         "jugador2": "Facu", "frutas2": 18, "ganador": "Ana", "segundos": 95},
        ...
      ]
    }
"""

import json
import os
from datetime import datetime

from ajustes import ARCHIVO_RESULTADOS

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), ARCHIVO_RESULTADOS)


def cargar_resultados():
    """Lee el archivo y devuelve un diccionario con el récord y las partidas del
    versus. Si el archivo todavía no existe (o está roto), empieza de cero."""
    datos = {"record": 0, "versus": []}
    try:
        with open(RUTA, encoding="utf-8") as archivo:
            leidos = json.load(archivo)
        datos["record"] = int(leidos.get("record", 0))
        datos["versus"] = list(leidos.get("versus", []))
    except (OSError, ValueError, AttributeError):
        pass
    return datos


def guardar_resultados(datos):
    """Escribe los resultados en el archivo."""
    try:
        with open(RUTA, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
    except OSError:
        print("No se pudieron guardar los resultados en", RUTA)


def registrar_puntaje(datos, puntos):
    """Si el puntaje supera el récord, lo guarda. Devuelve True si es un récord nuevo."""
    if puntos <= datos["record"]:
        return False
    datos["record"] = puntos
    guardar_resultados(datos)
    return True


def registrar_versus(datos, uno, dos, ganador, segundos):
    """Agrega una partida del versus al historial y la guarda.
    `uno` y `dos` son los jugadores; `ganador` es el nombre del que ganó o "" si empataron."""
    datos["versus"].append({
        "fecha": datetime.now().strftime("%d/%m %H:%M"),
        "jugador1": uno.nombre, "frutas1": uno.cortadas,
        "jugador2": dos.nombre, "frutas2": dos.cortadas,
        "ganador": ganador,
        "segundos": int(segundos),
    })
    guardar_resultados(datos)


def historial_entre(partidas, nombre1, nombre2):
    """Cuenta las partidas que jugaron estas dos personas entre sí (sin importar
    quién estaba de cada lado). Devuelve (ganadas por nombre1, ganadas por nombre2, empates)."""
    ganadas1 = ganadas2 = empates = 0
    pareja = {nombre1.lower(), nombre2.lower()}
    for partida in partidas:
        if {partida["jugador1"].lower(), partida["jugador2"].lower()} != pareja:
            continue
        ganador = partida["ganador"].lower()
        if ganador == nombre1.lower():
            ganadas1 += 1
        elif ganador == nombre2.lower():
            ganadas2 += 1
        else:
            empates += 1
    return ganadas1, ganadas2, empates
