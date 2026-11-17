# Dibuja una galaxia en espiral por capas de puntos de distintos colores.
# import carga un módulo, un conjunto de herramientas listas para usar.
# Podés llamar a una función con módulo.función, como en math.cos(...).

import turtle  # Herramientas para dibujar en una ventana.
import colorsys  # Funciones para convertir colores.
import math  # Seno, coseno y constantes como pi.
import random  # Números al azar para variar posiciones, tamaños y brillo.

random.seed(7)  # Fija la secuencia de números al azar para repetir el dibujo.
TILT = 0.45  # Ángulo de rotación de la galaxia, en radianes.

# La ventana de Turtle sirve de lienzo para el dibujo.
screen = turtle.Screen()
screen.setup(780, 480)  # Ancho y alto de la ventana en píxeles.
screen.bgcolor("#03030b")  # Fondo oscuro en formato hexadecimal.
screen.colormode(1.0)  # Cada componente de RGB usa valores de 0 a 1.

t = turtle.Turtle()  # Crea la tortuguita que se mueve por la ventana.
t.hideturtle()  # Oculta el cursor de la tortuga.
t.speed(0)  # Usa el modo de movimiento más rápido de Turtle.
t.penup()  # Levanta el lápiz durante los desplazamientos.

# Convierte HSV (tono, saturación y brillo) a RGB (rojo, verde y azul).
# Se usa una saturación de 0.7. El brillo v vale 1.0 por defecto.
def glow(h, v=1.0):
    # h % 1 hace que el tono vuelva a recorrer el mismo ciclo de colores.
    return colorsys.hsv_to_rgb(h % 1, 0.7, v)

# Mueve el cursor a un punto de la galaxia después de achatarlo y rotarlo.
def place(x, y):
    y *= 0.55  # Reduce la altura al 55 % para dar una forma ovalada.
    # El coseno y el seno del ángulo permiten girar x e y alrededor del centro.
    c, s = math.cos(TILT), math.sin(TILT)
    t.goto(x * c - y * s, x * s + y * c)

# Reparte 140 estrellas blancas por el fondo.
def stars():
    for _ in range(140):
        # x mide la posición horizontal e y la vertical desde el centro de la ventana.
        x = random.randint(-385, 385)
        y = random.randint(-235, 235)
        t.goto(x, y)  # Mueve la tortuguita a esas coordenadas.
        # dot recibe un tamaño y un color. randint elige 1, 2 o 3 para el tamaño.
        t.dot(random.randint(1, 3), "white")

# Agrega 700 puntos de polvo violeta tenue alrededor del centro.
def dust():
    for _ in range(700):
        # gauss elige r con más frecuencia cerca de cero. 120 indica la dispersión.
        # El ángulo a abarca casi una vuelta. Con coseno y seno obtenemos x e y.
        r = random.gauss(0, 120)
        a = random.uniform(0, 6.283)
        place(r * math.cos(a), r * math.sin(a))
        t.dot(random.randint(2, 4), glow(0.7, 0.3))

# Dibuja cuatro brazos en espiral con count puntos en cada uno.
def arms(count):
    for i in range(count):
        for k in range(4):
            d = i / count  # Avance desde el centro hacia el borde.
            # Cada brazo empieza un cuarto de vuelta más adelante que el anterior.
            # El término d * 5.5 curva el brazo a medida que crece el radio.
            a = k * math.pi / 2 + d * 5.5
            r = 10 + d * 290  # El radio aumenta al avanzar por el brazo.
            s = 4 + d * 26  # La dispersión aumenta hacia el borde.
            # Las variaciones al azar en x e y le dan grosor a la espiral.
            x = r * math.cos(a) + random.gauss(0, s)
            y = r * math.sin(a) + random.gauss(0, s)
            place(x, y)
            # El tono cambia con el avance. El brillo y el tamaño varían al azar.
            hue = 0.13 - d * 0.55
            v = random.uniform(0.6, 1)
            size = random.randint(2, 4)
            t.dot(size, glow(hue, v))

# Concentra 260 puntos dorados cerca del centro para iluminar el núcleo.
def core():
    for _ in range(260):
        r = random.gauss(0, 26)
        a = random.uniform(0, 6.283)
        place(r * math.cos(a), r * math.sin(a))
        t.dot(random.randint(2, 5), glow(0.12))

# Añade 40 destellos blancos más grandes repartidos por la galaxia.
def sparkle():
    for _ in range(40):
        r = random.gauss(0, 150)
        a = random.uniform(0, 6.283)
        place(r * math.cos(a), r * math.sin(a))
        t.dot(random.randint(5, 8), "white")

# Estas llamadas dibujan las capas en orden, del fondo a los destellos.
stars()
dust()
arms(900)  # 900 puntos por brazo. En total son 3.600 puntos en los cuatro brazos.
core()
sparkle()
t.goto(0, 0)  # Vuelve al centro de la ventana.
t.dot(26, "#fff3c4")  # Agrega un punto grande de luz en el centro.
turtle.done()  # Mantiene la ventana abierta hasta que la cierres.
