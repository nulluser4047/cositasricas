"""Los Pilares de la Creación se forman en ASCII. Salí con Ctrl+C."""

from math import sin, tau
import os
import random
import shutil
import sys
from time import perf_counter, sleep


# Los contornos usan proporciones del cuadro para adaptarse a la terminal.
OUTLINES = (
    (
        (.055, 1.08), (.075, .94), (.13, .84), (.135, .76), (.17, .71),
        (.128, .61), (.10, .50), (.105, .41), (.117, .335), (.096, .28),
        (.105, .225), (.147, .180), (.198, .155), (.25, .089), (.299, .072),
        (.36, .101), (.374, .138), (.361, .188), (.318, .196), (.282, .295),
        (.26, .427), (.246, .484), (.271, .596), (.231, .705), (.258, .742),
        (.310, .685), (.338, .708), (.35, .747), (.341, .80), (.389, .902),
        (.438, 1.08),
    ),
    (
        (.442, 1.08), (.454, .95), (.474, .824), (.462, .71), (.478, .671),
        (.479, .615), (.511, .506), (.542, .409), (.571, .336), (.596, .313),
        (.614, .322), (.622, .361), (.642, .441), (.622, .54), (.616, .60),
        (.626, .681), (.616, .727), (.625, .779), (.66, .823), (.622, .958),
        (.630, 1.08),
    ),
    (
        (.635, 1.08), (.668, .952), (.716, .821), (.735, .730), (.728, .644),
        (.742, .614), (.756, .602), (.785, .637), (.805, .640), (.807, .672),
        (.782, .751), (.789, .801), (.840, .901), (.869, .980), (.875, 1.08),
    ),
    (
        (.568, .888), (.604, .834), (.641, .812), (.673, .819), (.705, .784),
        (.736, .789), (.761, .820), (.745, .864), (.716, .88), (.667, .870),
        (.622, .897), (.586, .916),
    ),
)

SKY_GLYPHS = "   ..,:~"
SKY_COLORS = (17, 23, 23, 24, 30, 37, 37, 43)
PILLAR_GLYPHS = ":;-=+*#%@"
PILLAR_COLORS = (52, 52, 58, 94, 130, 136, 172, 214, 229)
STAR_COLORS = (153, 189, 218, 230)
EMBEDDED_COLORS = (203, 216, 222)
MIST_GLYPHS = "   .,:;~"
MIST_COLORS = (23, 24, 30, 30, 37, 73, 101, 143)
GROWTH_GLYPHS = " .," + PILLAR_GLYPHS
GROWTH_COLORS = (24, 30, 58) + PILLAR_COLORS
FORMATION_SECONDS = 12.0


def scene_size():
    terminal = shutil.get_terminal_size(fallback=(100, 36))
    rows = max(1, min(42, terminal.lines - 1))
    columns = max(1, min(112, terminal.columns - 1, round(rows * 2.65)))
    return columns, max(1, min(rows, round(columns / 2.65)))


def rasterize(width, height):
    """Marca qué celdas quedan dentro de los contornos de los pilares."""
    silhouette = [[False] * width for _ in range(height)]
    for outline in OUTLINES:
        edges = list(zip(outline, outline[1:] + outline[:1]))
        for row, line in enumerate(silhouette):
            scan_y = (row + .5) / height
            crossings = sorted(
                x0 + (scan_y - y0) * (x1 - x0) / (y1 - y0)
                for (x0, y0), (x1, y1) in edges
                if min(y0, y1) <= scan_y < max(y0, y1)
            )
            for start, end in zip(crossings[::2], crossings[1::2]):
                first = max(0, round(start * width))
                last = min(width, round(end * width))
                if last > first:
                    line[first:last] = [True] * (last - first)
    return silhouette


def prepare_scene(width, height):
    """Guarda la textura y la ubicación de las estrellas para todos los cuadros."""
    rng = random.Random(210)
    silhouette = rasterize(width, height)
    texture = []
    sky_positions = []
    pillar_positions = []
    for y, row in enumerate(silhouette):
        for x, inside in enumerate(row):
            jitter = rng.uniform(-.06, .06)
            phase = x * .19 + y * .37 + sin(x * .14)
            # El promedio de celdas vecinas dibuja un contorno de gas difuso.
            nearby = [
                flag for line in silhouette[max(0, y - 2):y + 3]
                for flag in line[max(0, x - 4):x + 5]
            ]
            density = sum(nearby) / len(nearby)
            patch = .5 + .23 * sin(x * .11 - y * .22) + .18 * sin(y * .24 + x * .04)
            start = .29 + .26 * patch + .10 * (1 - density)
            if inside:
                open_above = y == 0 or not silhouette[y - 1][x]
                open_left = x == 0 or not row[x - 1]
                border_light = .36 * open_above + .19 * open_left
                shade = .51 + .13 * sin(x * .94 - y * .51) + border_light + jitter
                pillar_positions.append((x, y))
            else:
                shade = .32 + .14 * sin(x * .17 + y * .23) + .12 * sin(x * .09 - y * .49) + jitter
                sky_positions.append((x, y))
            texture.append((inside, shade, phase, density, start))

    # Las estrellas de fondo conservan su posición y titilan a ritmos distintos.
    stars = {}
    for x, y in rng.sample(sky_positions, min(len(sky_positions), max(6, width * height // 79))):
        stars[x, y] = (rng.random() * tau, rng.uniform(1.4, 3.8), rng.choice(STAR_COLORS), False)
    for relative_x, relative_y in ((.328, .597), (.855, .110), (.745, .232), (.486, .153), (.686, .409)):
        x, y = int(relative_x * width), int(relative_y * height)
        if not silhouette[y][x]:
            stars[x, y] = (rng.random() * tau, rng.uniform(1.4, 2.6), 230, True)
    count = min(len(pillar_positions), max(7, width * height // 170))
    for x, y in rng.sample(pillar_positions, count):
        stars[x, y] = (rng.random() * tau, rng.uniform(1.6, 3.9), rng.choice(EMBEDDED_COLORS), False)
    return texture, stars


def shade_index(shade, ramp):
    return max(0, min(len(ramp) - 1, int(shade * len(ramp))))


def smooth(value):
    fraction = max(0.0, min(1.0, value))
    return fraction * fraction * (3 - 2 * fraction)


def frame(width, height, texture, stars, seconds, color):
    """Dibuja polvo difuso, materia condensada y estrellas en el mismo cuadro."""
    lines = []
    last_color = None
    progress = min(1.0, seconds / FORMATION_SECONDS)
    mist_release = 1 - smooth((progress - .57) / .39)
    for y in range(height):
        row = []
        for x in range(width):
            inside, shade, phase, density, start = texture[y * width + x]
            drift = .15 * sin(phase - seconds * .57)
            sky_shade = .28 + .14 * sin(phase) if inside else shade
            level = shade_index(sky_shade + drift, SKY_GLYPHS)
            symbol, tint = SKY_GLYPHS[level], SKY_COLORS[level]

            soft_cloud = density * mist_release * smooth((progress - .04 - .34 * (start - .29)) / .36)
            mist_level = shade_index(soft_cloud * .94, MIST_GLYPHS)
            if MIST_GLYPHS[mist_level] != " ":
                symbol, tint = MIST_GLYPHS[mist_level], MIST_COLORS[mist_level]

            solid = smooth((progress - start) / .30) if inside else 0.0
            if solid:
                target = 3 + shade_index(shade, PILLAR_GLYPHS)
                visible = round(solid * target)
                if visible:
                    symbol, tint = GROWTH_GLYPHS[visible], GROWTH_COLORS[visible]

            star = stars.get((x, y))
            if star:
                star_phase, speed, star_tint, bright = star
                pulse = .5 + .5 * sin(seconds * speed + star_phase)
                if inside:
                    pulse *= smooth((solid - .38) / .62)
                    ramp = "  .*+"
                else:
                    ramp = "*+X" if bright else " .*+"
                spark = ramp[shade_index(pulse, ramp)]
                if spark != " ":
                    symbol, tint = spark, star_tint

            if color and symbol != " " and tint != last_color:
                row.append(f"\x1b[38;5;{tint}m")
                last_color = tint
            row.append(symbol)
        lines.append("".join(row))
    return "\n".join(lines)


def enable_ansi():
    """Activa las secuencias de la terminal y devuelve cómo restaurar su modo."""
    if not sys.stdout.isatty() or os.environ.get("TERM") == "dumb":
        return None
    if os.name != "nt":
        return lambda: None

    # En Windows habilito el soporte ANSI de la consola y guardo su modo actual.
    import ctypes
    from ctypes import wintypes

    console = ctypes.windll.kernel32
    console.GetStdHandle.restype = wintypes.HANDLE
    console.GetConsoleMode.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    console.SetConsoleMode.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    handle = console.GetStdHandle(-11)
    old_mode = wintypes.DWORD()
    if not console.GetConsoleMode(handle, ctypes.byref(old_mode)):
        return None
    if not console.SetConsoleMode(handle, old_mode.value | 0x0004):
        return None
    return lambda: console.SetConsoleMode(handle, old_mode.value)


def main():
    restore_mode = enable_ansi()
    width, height = scene_size()
    texture, stars = prepare_scene(width, height)
    if restore_mode is None:
        print(frame(width, height, texture, stars, FORMATION_SECONDS, color=False))
        return

    output = sys.stdout
    started = perf_counter()
    try:
        # Uso una pantalla aparte para recuperar la terminal al salir.
        output.write("\x1b[?1049h\x1b[?25l\x1b[2J")
        while True:
            new_size = scene_size()
            if new_size != (width, height):
                width, height = new_size
                texture, stars = prepare_scene(width, height)
                output.write("\x1b[2J")
            picture = frame(width, height, texture, stars, perf_counter() - started, color=True)
            output.write("\x1b[H" + picture + "\x1b[0m\x1b[J")
            output.flush()
            sleep(.10)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            output.write("\x1b[0m\x1b[?25h\x1b[?1049l")
            output.flush()
        finally:
            restore_mode()


if __name__ == "__main__":
    main()
