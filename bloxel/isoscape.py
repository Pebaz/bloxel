import math
from tkinter.tix import MAX
import glm
import pyfastnoisesimd as fns
import numpy as np
from PIL import Image
from bloxel import iso as Iso

# TODO(pbz): Make this work with any cornerstone size
CORNERSTONE_SIZE = 4
IMG_SIZE = CORNERSTONE_SIZE * 64
MAX_TILES_AXIS = IMG_SIZE // CORNERSTONE_SIZE

iso = Iso.IsoCoors(CORNERSTONE_SIZE)

img = Image.new('RGBA', (IMG_SIZE, IMG_SIZE))

def _1():
    global iso, img

    bloxels = []

    center = MAX_TILES_AXIS // 2

    for x in range(MAX_TILES_AXIS):
        for y in range(MAX_TILES_AXIS):
            z = -MAX_TILES_AXIS

            if glm.distance(glm.vec2(x, y), glm.vec2(center, center)) > 32.0:
                continue

            tint = int((glm.simplex((x, y, z)) + 1) / 2 * 255)

            tint2 = int((glm.simplex((x, y)) + 1) / 2 * 255)

            bloxels.append((x, y, z + tint // 16, 255, tint, tint, tint2))

    bloxels.sort(key=lambda b: b[0] - b[1] - b[2], reverse=True)

    for bloxel in bloxels:
        x, y, z, r, g, b, a = bloxel
        stone = Iso.Cornerstone.get((r, g, b, a))
        coors = iso.get(x, y, z)
        Iso.draw_image(*coors, stone, img)


def _2():
    global iso, img

    radius = MAX_TILES_AXIS * 0.25
    center_dot = glm.vec2(MAX_TILES_AXIS / 2, MAX_TILES_AXIS / 2)

    def flare(x, y, h):
        nonlocal radius, center_dot
        "https://jobtalle.com/layered_voxel_rendering.html"

        pxy = glm.vec2(x, y)

        d = glm.distance(pxy, center_dot)
        # if d > radius:
        #     return 0
        # else:
        #     d /= radius
        d /= radius

        FLATNESS = 1
        height = h * ((math.cos(math.pi * d) + 1) / 2) ** FLATNESS
        return height  # Single Float from 0 to 1

    shape = [MAX_TILES_AXIS, MAX_TILES_AXIS, MAX_TILES_AXIS]

    # * To reproduce a finding, make sure to note the seed
    seed = np.random.randint(2**31)
    N_threads = 4

    perlin = fns.Noise(seed=seed, numWorkers=N_threads)
    perlin.frequency = 0.05
    perlin.noiseType = fns.NoiseType.Perlin
    perlin.fractal.octaves = 4
    perlin.fractal.lacunarity = 1.3
    perlin.fractal.gain = 0.35
    perlin.perturb.perturbType = fns.PerturbType.NoPerturb
    result = perlin.genAsGrid(shape)

    bloxels = []

    def norm(x):
        return (x + 1.0) / 2.0

    for x in range(MAX_TILES_AXIS):
        for y in range(MAX_TILES_AXIS):
            for z in range(MAX_TILES_AXIS):
                # z = -MAX_TILES_AXIS
                z = -z

                # if glm.distance(glm.vec2(x, y), center_dot) > radius:
                #     continue

                height_3d = norm(result[x][y][z])
                # height_3d = glm.simplex((x, y, z))
                # height_2d = glm.simplex((x, y))

                tint = int(height_3d * 255)
                # tint2 = int(height_2d * 255)

                # clr = tint, tint, tint
                clr = tint, tint, 255 - tint

                f = flare(x, y, height_3d)
                h = (height_3d * f * MAX_TILES_AXIS)
                # h = h / MAX_TILES_AXIS * MAX_TILES_AXIS
                h = int(h)

                bloxels.append((
                    x,
                    y,
                    -1.25 * MAX_TILES_AXIS + h,
                    *clr,
                    255
                ))

    bloxels.sort(key=lambda b: b[0] - b[1] - b[2], reverse=True)

    for bloxel in bloxels:
        x, y, z, r, g, b, a = bloxel
        stone = Iso.Cornerstone.get((r, g, b, a))
        coors = iso.get(x, y, z)
        Iso.draw_image(*coors, stone, img)


_2()


img.save('out.png')
