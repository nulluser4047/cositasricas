"""Una nebulosa difusa se condensa hasta formar los Pilares de la Creación."""

from array import array
from dataclasses import dataclass
from math import exp, sin, tau
import random
from struct import pack
from time import perf_counter
import tkinter as tk
from zlib import compress, crc32


WIDTH, HEIGHT = 760, 570
FRAME_MS = 33
FORMATION_SECONDS = 12.0
FORMATION_FPS = 12

# Coordenadas de 0 a 1. El borde inferior de cada pilar queda fuera del cuadro.
OUTLINES = (
    (
        (.055, 1.08), (.074, .937), (.109, .878), (.134, .824), (.134, .760),
        (.169, .710), (.150, .648), (.125, .615), (.113, .551), (.097, .496),
        (.104, .425), (.117, .335), (.094, .282), (.103, .224), (.146, .182),
        (.198, .154), (.235, .116), (.246, .088), (.275, .079), (.299, .072),
        (.326, .085), (.360, .102), (.374, .138), (.361, .188), (.318, .196),
        (.300, .242), (.282, .295), (.274, .359), (.260, .427), (.246, .484),
        (.262, .542), (.271, .596), (.247, .653), (.231, .705), (.258, .742),
        (.281, .729), (.310, .685), (.332, .698), (.350, .747), (.340, .793),
        (.351, .850), (.389, .903), (.415, .974), (.438, 1.08),
    ),
    (
        (.442, 1.08), (.454, .949), (.462, .886), (.473, .823), (.464, .767),
        (.463, .709), (.478, .672), (.479, .617), (.504, .563), (.511, .507),
        (.534, .457), (.542, .409), (.560, .368), (.572, .333), (.596, .313),
        (.612, .322), (.622, .361), (.634, .400), (.642, .441), (.626, .511),
        (.617, .574), (.619, .627), (.626, .682), (.616, .725), (.625, .777),
        (.660, .823), (.638, .887), (.621, .958), (.630, 1.08),
    ),
    (
        (.635, 1.08), (.666, .951), (.695, .876), (.716, .821), (.729, .780),
        (.736, .730), (.733, .680), (.728, .644), (.742, .614), (.756, .602),
        (.773, .622), (.786, .637), (.805, .640), (.807, .673), (.795, .712),
        (.783, .751), (.788, .801), (.809, .843), (.839, .899), (.852, .950),
        (.873, 1.08),
    ),
    (
        (.568, .888), (.602, .835), (.640, .812), (.675, .819), (.705, .784),
        (.736, .789), (.761, .820), (.747, .863), (.716, .880), (.667, .870),
        (.627, .897), (.586, .917),
    ),
)


def unit(value):
    return max(0.0, min(1.0, value))


def smooth(value):
    fraction = unit(value)
    return fraction * fraction * (3 - 2 * fraction)


def curve(points, width, height):
    """Interpola la silueta para dibujar curvas entre los puntos de referencia."""
    vertices = []
    for index, point in enumerate(points):
        previous = points[index - 1]
        following = points[(index + 1) % len(points)]
        later = points[(index + 2) % len(points)]
        for step in range(5):
            u = step / 5
            coordinates = []
            for a, b, c, d in zip(previous, point, following, later):
                value = b + .5 * u * (
                    c - a + u * (2 * a - 5 * b + 4 * c - d + u * (3 * b - a - 3 * c + d))
                )
                coordinates.append(value)
            vertices.append((coordinates[0] * width, coordinates[1] * height))
    return vertices


def pillar_mask(width, height):
    """Rellena los espacios de cada fila que quedan dentro de las siluetas."""
    mask = bytearray(width * height)
    for outline in OUTLINES:
        vertices = curve(outline, width, height)
        segments = list(zip(vertices, vertices[1:] + vertices[:1]))
        for row in range(height):
            scan_y = row + .5
            crossings = sorted(
                x0 + (scan_y - y0) * (x1 - x0) / (y1 - y0)
                for (x0, y0), (x1, y1) in segments
                if min(y0, y1) <= scan_y < max(y0, y1)
            )
            for left, right in zip(crossings[::2], crossings[1::2]):
                start = max(0, round(left))
                end = min(width, round(right))
                if end > start:
                    offset = row * width
                    mask[offset + start:offset + end] = b"\x01" * (end - start)
    return mask


def edge_distance(mask, width, height):
    """Distancia aproximada al contorno, positiva dentro de los pilares."""
    distance = [width + height] * len(mask)
    for y in range(height):
        for x in range(width):
            index = y * width + x
            if x + 1 < width and mask[index] != mask[index + 1]:
                distance[index] = distance[index + 1] = 0
            if y + 1 < height and mask[index] != mask[index + width]:
                distance[index] = distance[index + width] = 0

    # Las dos pasadas propagan la distancia desde el borde a todo el dibujo.
    for direction in (1, -1):
        rows = range(height) if direction == 1 else range(height - 1, -1, -1)
        columns = range(width) if direction == 1 else range(width - 1, -1, -1)
        for y in rows:
            previous_row = y - direction
            for x in columns:
                index = y * width + x
                best = distance[index]
                if best == 0:
                    continue
                previous_column = x - direction
                if 0 <= previous_column < width:
                    best = min(best, distance[index - direction] + 3)
                if 0 <= previous_row < height:
                    neighbor = previous_row * width + x
                    best = min(best, distance[neighbor] + 3)
                    if x > 0:
                        best = min(best, distance[neighbor - 1] + 4)
                    if x + 1 < width:
                        best = min(best, distance[neighbor + 1] + 4)
                distance[index] = best

    return array("f", (
        (value / 3 + .5) * (1 if inside else -1)
        for value, inside in zip(distance, mask)
    ))


def texture(width, height, spacing_x, spacing_y, rng):
    """Crea nubes suaves interpolando una grilla de valores al azar."""
    columns = width // spacing_x + 2
    rows = height // spacing_y + 2
    grid = [[rng.random() for _ in range(columns)] for _ in range(rows)]

    def axis_weights(length, spacing):
        weights = []
        for pixel in range(length):
            cell, offset = divmod(pixel, spacing)
            fraction = offset / spacing
            weights.append((cell, fraction * fraction * (3 - 2 * fraction)))
        return weights

    horizontal = axis_weights(width, spacing_x)
    samples = array("f")
    for cell_y, fraction_y in axis_weights(height, spacing_y):
        upper, lower = grid[cell_y:cell_y + 2]
        row = [a + (b - a) * fraction_y for a, b in zip(upper, lower)]
        samples.extend(row[x] + (row[x + 1] - row[x]) * f for x, f in horizontal)
    return samples


def glow_profile(length, center, spread):
    return [exp(-.5 * ((pixel / length - center) / spread) ** 2) for pixel in range(length)]


def illuminate(x, y, width, height, distance, depth):
    """Resalta los bordes que miran hacia la luz de arriba a la izquierda."""
    if abs(depth) > 84:
        return 0.0
    row = y * width
    vertical = distance[min(height - 1, y + 2) * width + x] - distance[max(0, y - 2) * width + x]
    horizontal = distance[row + min(width - 1, x + 2)] - distance[row + max(0, x - 2)]
    facing = unit(.35 + .135 * vertical + .085 * horizontal)
    broad_glow = exp(-abs(depth) / 20)
    bright_rim = exp(-abs(depth) / 5)
    return .08 * broad_glow + facing * (.36 * broad_glow + .43 * bright_rim)


@dataclass
class Nebula:
    sky: bytearray
    finished: bytearray
    opaque: bytearray
    mist: bytes
    reveal: bytes


def paint_nebula(width, height):
    """Pinta el cielo y los pilares. Guarda cuándo empieza a definirse cada zona."""
    rng = random.Random(27)
    distance = edge_distance(pillar_mask(width, height), width, height)
    cloud = texture(width, height, 132, 103, rng)
    turbulence = texture(width, height, 39, 27, rng)
    fibers = texture(width, height, 19, 79, rng)
    detail = texture(width, height, 6, 8, rng)
    left_x = glow_profile(width, .28, .095)
    left_y = glow_profile(height, .13, .14)
    center_x = glow_profile(width, .58, .075)
    center_y = glow_profile(height, .36, .14)
    base_x = glow_profile(width, .46, .28)
    base_y = glow_profile(height, .92, .12)
    sky = bytearray(width * height * 3)
    finished = bytearray(width * height * 3)
    opaque = bytearray(width * height)
    mist_codes = bytearray(width * height)
    reveal_codes = bytearray(width * height)

    for y in range(height):
        for x in range(width):
            index = y * width + x
            broad, medium, fine = cloud[index], turbulence[index], detail[index]
            fiber = fibers[index]
            grain = (rng.random() - .5) * .038
            wave = .5 + .5 * sin(y * .027 + x * .012 + medium * 5)
            fringe = (medium - .5) * 13 + (fiber - .5) * 9 + (fine - .5) * 5
            depth = distance[index] + fringe
            rim = illuminate(x, y, width, height, distance, depth) * (.8 + .4 * fine)
            left_light = left_x[x] * left_y[y]
            center_light = center_x[x] * center_y[y]
            base_light = base_x[x] * base_y[y]
            mist = unit(.66 * broad + .29 * medium + .12 * fiber + .06 * fine
                        + .13 * wave + .20 * left_light + .24 * center_light
                        + .25 * base_light - .21 + grain)
            sky_red, sky_green, sky_blue = 6 + 65 * mist, 12 + 149 * mist, 22 + 140 * mist
            offset = index * 3
            sky[offset:offset + 3] = bytes((int(sky_red), int(sky_green), int(sky_blue)))

            if depth > 0:
                opaque[index] = 1
                folds = .47 * medium + .29 * fiber + .17 * fine + .07 * wave
                light = unit(.028 + .33 * folds + rim * (1.0 + .22 * left_light)
                             + .20 * left_light + .10 * center_light + .07 * base_light + grain)
                red = 17 + 238 * light
                green = 6 + 222 * light ** 1.54
                blue = 8 + 164 * light ** 2.45
            else:
                red = sky_red + 100 * rim
                green = sky_green + 96 * rim
                blue = sky_blue + 61 * rim

            finished[offset:offset + 3] = bytes((
                min(255, int(red)), min(255, int(green)), min(255, int(blue))
            ))
            # El gas ocupa un contorno ancho. La textura llega más tarde y por zonas.
            patch = .48 * broad + .33 * medium + .19 * (1 - y / height)
            density = round(15 * smooth((distance[index] + 51 + (broad - .5) * 25) / 108))
            mist_codes[index] = 16 * density + round(15 * patch)
            if depth > 0 or rim > 0:
                edge_delay = .12 * (1 - unit(depth / 25))
                reveal_start = .27 + .27 * patch + edge_delay
                reveal_codes[index] = 1 + round(254 * reveal_start)
    return Nebula(sky, finished, opaque, bytes(mist_codes), bytes(reveal_codes))


def png_chunk(kind, payload):
    return pack(">I", len(payload)) + kind + payload + pack(">I", crc32(kind + payload))


def png_header(width, height, color_type):
    size = pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", size)


def png_rows(pixels, width, height, channels):
    stride = width * channels
    rows = b"".join(b"\0" + pixels[row * stride:(row + 1) * stride] for row in range(height))
    return png_chunk(b"IDAT", compress(rows, level=1)) + png_chunk(b"IEND", b"")


def solid_opacity(progress, reveal_code):
    if reveal_code == 0:
        return 0.0
    start = (reveal_code - 1) / 254
    return smooth((progress - start) / .30)


class Formation:
    """Genera las dos capas de transición con transparencia para Tkinter."""

    def __init__(self, width, height, scene):
        self.width = width
        self.height = height
        self.reveal = scene.reveal
        self.mist_header = png_header(width, height, 3)
        palette = bytearray()
        for level in range(16):
            density = level / 15
            tint = bytes((int(133 - 73 * density), int(178 - 135 * density), int(158 - 121 * density)))
            palette.extend(tint * 16)
        self.mist_header += png_chunk(b"PLTE", palette)
        self.mist_rows = png_rows(scene.mist, width, height, 1)
        self.solid_header = png_header(width, height, 6)
        self.solid_rgba = bytearray(width * height * 4)
        for channel in range(3):
            self.solid_rgba[channel::4] = scene.finished[channel::3]

    def layers(self, progress):
        # El polvo se acumula primero y se disipa al quedar definidos los pilares.
        mist_release = 1 - smooth((progress - .57) / .39)
        mist_alpha = bytes(
            round(198 * (code // 16) / 15 * mist_release
                  * smooth((progress - .03 - .19 * (code % 16) / 15) / .31))
            for code in range(256)
        )
        mist = self.mist_header + png_chunk(b"tRNS", mist_alpha) + self.mist_rows

        # Una tabla de opacidades permite actualizar todas las zonas a la vez.
        solid_alpha = bytes(round(255 * solid_opacity(progress, code)) for code in range(256))
        self.solid_rgba[3::4] = self.reveal.translate(solid_alpha)
        solid = self.solid_header + png_rows(self.solid_rgba, self.width, self.height, 4)
        return mist, solid


@dataclass(frozen=True)
class Star:
    x: int
    y: int
    radius: float
    color: tuple
    phase: float
    speed: float
    flare: float = 0.0


def scatter_stars(width, height, opaque):
    rng = random.Random(700)
    tints = ((220, 248, 255), (255, 214, 239), (255, 245, 208), (182, 216, 255))
    stars = []
    for x, y, radius, flare, color in (
        (.328, .597, 3.0, 23, tints[1]),
        (.855, .110, 1.75, 11, tints[1]),
        (.745, .232, 1.65, 10, tints[0]),
        (.486, .153, 1.55, 8, tints[3]),
        (.686, .409, 1.35, 7, tints[1]),
        (.927, .701, 1.20, 7, tints[0]),
        (.317, .484, 1.20, 6, tints[0]),
    ):
        px, py = round(x * width), round(y * height)
        if not opaque[py * width + px]:
            stars.append(Star(px, py, radius, color, rng.random() * tau, rng.uniform(1.4, 3.5), flare))

    for _ in range(460):
        x, y = rng.randrange(3, width - 3), rng.randrange(3, height - 3)
        if not opaque[y * width + x]:
            radius = .32 + 1.04 * rng.random() ** 3
            stars.append(Star(x, y, radius, rng.choice(tints), rng.random() * tau, rng.uniform(1.6, 4.9)))
        if len(stars) == 236:
            break
    return stars


def embedded_stars(width, height, opaque):
    """Enciende estrellas cálidas dentro de las tres columnas de polvo."""
    rng = random.Random(812)
    tints = ((255, 119, 109), (255, 182, 111), (255, 231, 176))
    anchors = (
        (.217, .171), (.169, .377), (.223, .536), (.199, .902),
        (.571, .397), (.553, .542), (.510, .675), (.583, .791),
        (.770, .657), (.775, .819), (.794, .938),
    )
    positions = [(int(x * width), int(y * height), 1.65) for x, y in anchors]
    positions.extend(
        (rng.randrange(3, width - 3), rng.randrange(3, height - 3), rng.uniform(.70, 1.23))
        for _ in range(240)
    )
    stars = []
    for x, y, radius in positions:
        index = y * width + x
        if all(opaque[index + offset] for offset in (0, -2, 2, -2 * width, 2 * width)):
            stars.append(Star(x, y, radius, rng.choice(tints), rng.random() * tau, rng.uniform(1.7, 4.4)))
        if len(stars) == 34:
            break
    return stars


def paint_halos(pixels, opaque, width, height, stars):
    """Las estrellas grandes iluminan la nube que tienen alrededor."""
    for star in stars:
        if not star.flare:
            continue
        extent = int(star.flare * 1.25)
        for y in range(max(0, star.y - extent), min(height, star.y + extent + 1)):
            for x in range(max(0, star.x - extent), min(width, star.x + extent + 1)):
                index = y * width + x
                if opaque[index]:
                    continue
                squared = (x - star.x) ** 2 + (y - star.y) ** 2
                glow = .50 * exp(-squared / (2 * (star.radius * 1.45) ** 2))
                glow += .31 * exp(-squared / (2 * (star.flare / 2.6) ** 2))
                for channel, tint in enumerate(star.color):
                    offset = index * 3 + channel
                    pixels[offset] = int(pixels[offset] + (tint - pixels[offset]) * glow)


def mixed_color(background, tint, amount):
    color = tuple(round(a + (b - a) * amount) for a, b in zip(background, tint))
    return "#{:02x}{:02x}{:02x}".format(*color)


def main():
    scene = paint_nebula(WIDTH, HEIGHT)
    sky_stars = scatter_stars(WIDTH, HEIGHT, scene.opaque)
    paint_halos(scene.sky, scene.opaque, WIDTH, HEIGHT, sky_stars)
    paint_halos(scene.finished, scene.opaque, WIDTH, HEIGHT, sky_stars)
    stars = sky_stars + embedded_stars(WIDTH, HEIGHT, scene.opaque)
    formation = Formation(WIDTH, HEIGHT, scene)

    window = tk.Tk()
    window.title("Pilares de la Creación")
    window.resizable(False, False)
    window.bind("<Escape>", lambda event: window.destroy())
    canvas = tk.Canvas(window, width=WIDTH, height=HEIGHT, highlightthickness=0, bg="#071119")
    canvas.pack()
    ppm_header = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")
    image = tk.PhotoImage(data=ppm_header + scene.sky, format="ppm")
    canvas.create_image(0, 0, anchor="nw", image=image)
    mist_image = tk.PhotoImage(width=WIDTH, height=HEIGHT)
    solid_image = tk.PhotoImage(width=WIDTH, height=HEIGHT)
    mist_item = canvas.create_image(0, 0, anchor="nw", image=mist_image)
    solid_item = canvas.create_image(0, 0, anchor="nw", image=solid_image)

    lights = []
    for star in stars:
        rays = []
        if star.flare:
            rays = [canvas.create_line(0, 0, 0, 0) for _ in range(4)]
        dot = canvas.create_oval(0, 0, 0, 0, outline="")
        index = star.y * WIDTH + star.x
        delay = scene.reveal[index] if scene.opaque[index] else 0
        background = scene.finished[index * 3:index * 3 + 3]
        lights.append((star, dot, rays, background, delay))

    rng = random.Random(19)
    particles = [
        (canvas.create_oval(0, 0, 0, 0, outline=""), rng.randrange(WIDTH),
         rng.uniform(.43, 1.0) * HEIGHT, rng.uniform(.6, 3.3), rng.random() * tau)
        for _ in range(54)
    ]
    started = perf_counter()
    last_formation_frame = -1
    formed = False

    def animate():
        nonlocal last_formation_frame, formed
        seconds = perf_counter() - started
        progress = unit(seconds / FORMATION_SECONDS)
        formation_frame = int(seconds * FORMATION_FPS)
        if not formed and progress >= 1:
            image.configure(data=ppm_header + scene.finished, format="ppm")
            canvas.delete(mist_item, solid_item)
            formed = True
        elif not formed and formation_frame != last_formation_frame:
            mist, solid = formation.layers(progress)
            mist_image.blank()
            solid_image.blank()
            mist_image.configure(data=mist, format="png")
            solid_image.configure(data=solid, format="png")
            last_formation_frame = formation_frame

        for star, dot, rays, background, delay in lights:
            # Las estrellas embebidas aparecen al condensarse el polvo de esa zona.
            visible = smooth((solid_opacity(progress, delay) - .27) / .65) if delay else 1.0
            if visible == 0:
                canvas.itemconfigure(dot, state="hidden")
                continue
            twinkle = .5 + .5 * sin(seconds * star.speed + star.phase)
            radius = star.radius * (.72 + .34 * twinkle)
            canvas.coords(dot, star.x - radius, star.y - radius, star.x + radius, star.y + radius)
            color = mixed_color(background, star.color, visible * (.37 + .61 * twinkle))
            canvas.itemconfigure(dot, fill=color, state="normal")
            if rays:
                ray = star.flare * (.79 + .25 * twinkle)
                offsets = ((ray, 0), (0, ray), (ray * .53, ray * .53), (ray * .53, -ray * .53))
                for index, ((dx, dy), item) in enumerate(zip(offsets, rays)):
                    strength = .52 if index < 2 else .30
                    canvas.coords(item, star.x - dx, star.y - dy, star.x + dx, star.y + dy)
                    canvas.itemconfigure(item, fill=mixed_color(background, star.color, strength * (.43 + .57 * twinkle)))

        # Los granitos de polvo ascienden despacio y se balancean con la nube.
        for item, origin_x, origin_y, speed, phase in particles:
            x = (origin_x + seconds * speed * .45 + 6 * sin(seconds * .37 + phase)) % WIDTH
            y = (origin_y - seconds * speed) % HEIGHT
            index = int(y) * WIDTH + int(x)
            if scene.opaque[index]:
                canvas.itemconfigure(item, state="hidden")
                continue
            size = .49 + .32 * (.5 + .5 * sin(seconds * 1.3 + phase))
            dust_color = mixed_color(scene.sky[index * 3:index * 3 + 3], (145, 217, 200), .29)
            canvas.coords(item, x - size, y - size, x + size, y + size)
            canvas.itemconfigure(item, fill=dust_color, state="normal")
        window.after(FRAME_MS, animate)

    animate()
    window.mainloop()


if __name__ == "__main__":
    main()
