# Fruit Ninja con el flash del celular

Obligatorio 2 de Programación 2.

Juego de cortar frutas hecho en Python con OpenCV donde **la linterna del celular es la navaja**.
La cámara de la computadora busca el punto de luz más brillante de la imagen y lo sigue.
Al mover el celular frente a la cámara, la luz deja un rastro, y las frutas que lo cruzan se cortan.

## Instalación

Se necesita Python 3.9 o más nuevo, una cámara web y un celular con linterna.

```bash
pip install -r requirements.txt
```

En macOS, la primera vez el sistema pide permiso para usar la cámara
(a la Terminal o a VS Code, según desde dónde se corra).

## Cómo se juega

```bash
python3 friutninja.py
```

1. Prender la linterna del celular y apuntarla hacia la cámara.
2. En el menú tiene que aparecer **"Flash detectado"** en verde.
3. Apretar **ESPACIO** para empezar y mover el celular como una espada.

- Cada fruta cortada suma un punto.
- Cortar una bomba resta una vida.
- Dejar caer una fruta sin cortarla también resta una vida.
- Si se terminan las vidas, se pierde la partida.

Funciona mejor en un cuarto con poca luz y sin lámparas o ventanas detrás del jugador.

## Niveles

Hay 5 niveles. En cada uno hay que cortar una cantidad de frutas para pasar al siguiente,
y las vidas se recargan a 3 al empezar cada nivel. Si se pasa el nivel 5, se gana.

| Nivel | Frutas para pasar | Frutas a la vez | Velocidad  | Bombas |
|-------|-------------------|-----------------|------------|--------|
| 1     | 8                 | 3               | muy lenta  | no     |
| 2     | 10                | 3               | lenta      | 10 %   |
| 3     | 12                | 4               | media      | 15 %   |
| 4     | 14                | 5               | rápida     | 18 %   |
| 5     | 16                | 6               | muy rápida | 22 %   |

En cada nivel las frutas también son un poco más chicas.
Los niveles se configuran en la lista `NIVELES` al principio de `friutninja.py`.

## Controles

| Tecla    | Acción                                                        |
|----------|---------------------------------------------------------------|
| ESPACIO  | Empezar / volver a jugar                                      |
| + / -    | Subir / bajar el umbral de brillo de la detección             |
| M        | Mostrar / ocultar lo que la cámara está tomando como "luz"    |
| Q o ESC  | Salir                                                         |

Si el juego detecta otras cosas como si fueran la linterna (lámparas, ventanas, la pantalla),
hay que subir el umbral con **+**. Si no detecta la linterna, hay que bajarlo con **-**.
La tecla **M** ayuda a ver qué está detectando.

## Cómo funciona la detección

En cada cuadro de la cámara:

1. La imagen se espeja (para que moverse a la derecha sea ir a la derecha en pantalla).
2. Se pasa a escala de grises y se desenfoca un poco para sacar ruido.
3. Se quedan solo los píxeles más brillantes que el umbral (`cv2.threshold`).
4. Se busca la mancha blanca más grande (`cv2.findContours`) y su centro es la posición de la navaja.

Para saber si una fruta se cortó, se calcula la distancia entre el centro de la fruta
y el segmento que recorrió la luz desde el cuadro anterior. Si esa distancia es menor que el
radio de la fruta, la fruta queda cortada.
