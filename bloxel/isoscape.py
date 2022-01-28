import glm
from PIL import Image
from bloxel import iso as Iso

# TODO(pbz): Make this work with any cornerstone size
CORNERSTONE_SIZE = 4
IMG_SIZE = CORNERSTONE_SIZE * 64
MAX_TILES_AXIS = IMG_SIZE // CORNERSTONE_SIZE

iso = Iso.IsoCoors(CORNERSTONE_SIZE)

img = Image.new('RGBA', (IMG_SIZE, IMG_SIZE))

bloxels = []

center = MAX_TILES_AXIS // 2

for x in range(MAX_TILES_AXIS):
    for y in range(MAX_TILES_AXIS):
        z = -MAX_TILES_AXIS

        if glm.distance(glm.vec2(x, y), glm.vec2(center, center)) > 32.0:
            continue

        tint = int((glm.simplex((x, y, z)) + 1) / 2 * 255)
        bloxels.append((x, y, z + tint // 16, 255, tint, tint, 255))

bloxels.sort(key=lambda b: b[0] - b[1] - b[2], reverse=True)

for bloxel in bloxels:
    x, y, z, r, g, b, a = bloxel
    stone = Iso.Cornerstone.get((r, g, b, a))
    coors = iso.get(x, y, z)
    Iso.draw_image(*coors, stone, img)


img.save('out.png')
