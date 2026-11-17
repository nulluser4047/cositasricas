# Draws a spiral galaxy in layers of colored dots.
# import loads a module, a collection of tools you can use in your program.
# Call a function with the module name and a dot, as in math.cos(...).

import turtle  # Tools for drawing in a window.
import colorsys  # Functions for converting colors.
import math  # Sine, cosine, and constants such as pi.
import random  # Random numbers for varying positions, sizes, and brightness.

random.seed(7)  # Uses the same random sequence each time to reproduce the drawing.
TILT = 0.45  # Rotation angle of the galaxy, in radians.

# The Turtle window is the canvas for the drawing.
screen = turtle.Screen()
screen.setup(780, 480)  # Window width and height in pixels.
screen.bgcolor("#03030b")  # Dark background given as a hex color.
screen.colormode(1.0)  # Each RGB component uses a value from 0 to 1.

t = turtle.Turtle()  # Creates the turtle that moves around the window.
t.hideturtle()  # Hides the turtle cursor.
t.speed(0)  # Selects Turtle's fastest movement setting.
t.penup()  # Lifts the pen while moving between points.

# Converts HSV (hue, saturation, value) to RGB (red, green, blue).
# Saturation is set to 0.7. The brightness v defaults to 1.0.
def glow(h, v=1.0):
    # h % 1 wraps the hue around the same color wheel.
    return colorsys.hsv_to_rgb(h % 1, 0.7, v)

# Moves the cursor to a galaxy point after scaling and rotating its position.
def place(x, y):
    y *= 0.55  # Scales the vertical coordinate to 55% for an oval shape.
    # The cosine and sine of the angle turn the point around the center.
    c, s = math.cos(TILT), math.sin(TILT)
    t.goto(x * c - y * s, x * s + y * c)

# Scatters 140 white stars across the background.
def stars():
    for _ in range(140):
        # x and y measure horizontal and vertical position from the window's center.
        x = random.randint(-385, 385)
        y = random.randint(-235, 235)
        t.goto(x, y)  # Moves the turtle to those coordinates.
        # dot takes a size and a color. randint picks 1, 2, or 3 for the size.
        t.dot(random.randint(1, 3), "white")

# Adds 700 dim violet dust points around the center.
def dust():
    for _ in range(700):
        # gauss gives r values near zero more often. 120 sets the spread.
        # The angle a spans nearly a full turn. Cosine and sine give x and y.
        r = random.gauss(0, 120)
        a = random.uniform(0, 6.283)
        place(r * math.cos(a), r * math.sin(a))
        t.dot(random.randint(2, 4), glow(0.7, 0.3))

# Draws four spiral arms with count dots in each arm.
def arms(count):
    for i in range(count):
        for k in range(4):
            d = i / count  # Progress from the center toward the edge.
            # Each arm starts a quarter turn past the previous one.
            # The d * 5.5 term curves the arm as the radius increases.
            a = k * math.pi / 2 + d * 5.5
            r = 10 + d * 290  # The radius grows along the arm.
            s = 4 + d * 26  # The spread grows toward the edge.
            # Random offsets in x and y give the spiral some width.
            x = r * math.cos(a) + random.gauss(0, s)
            y = r * math.sin(a) + random.gauss(0, s)
            place(x, y)
            # The hue changes along the arm. Brightness and size vary randomly.
            hue = 0.13 - d * 0.55
            v = random.uniform(0.6, 1)
            size = random.randint(2, 4)
            t.dot(size, glow(hue, v))

# Clusters 260 golden dots near the center to light up the core.
def core():
    for _ in range(260):
        r = random.gauss(0, 26)
        a = random.uniform(0, 6.283)
        place(r * math.cos(a), r * math.sin(a))
        t.dot(random.randint(2, 5), glow(0.12))

# Scatters 40 larger white sparkles across the galaxy.
def sparkle():
    for _ in range(40):
        r = random.gauss(0, 150)
        a = random.uniform(0, 6.283)
        place(r * math.cos(a), r * math.sin(a))
        t.dot(random.randint(5, 8), "white")

# These calls draw the layers in order, from the backdrop to the bright highlights.
stars()
dust()
arms(900)  # 900 dots per arm. The four arms get 3,600 dots in total.
core()
sparkle()
t.goto(0, 0)  # Returns to the center of the window.
t.dot(26, "#fff3c4")  # Adds a large, bright dot in the middle.
turtle.done()  # Keeps the window open until you close it.
