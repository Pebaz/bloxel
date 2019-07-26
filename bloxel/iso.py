r"""
{4}         .
      .{1}  |{4}  .
   .{1}  |  |  |{4}  .
.{1}  |  |  |  |  |{4}  .
.  .{1}  |  |  |{4}  .  .
.{2}  \{4}  .{1}  |{4}  .{3}  /{4}  .
.{2}  \  \{4}  .{3}  /  /{4}  .
.{2}  \  \{4}  .{3}  /  /{4}  .
.{2}  \  \{4}  .{3}  /  /{4}  .
   .{2}  \{4}  .{3}  /{4}  .
      .  .  .
         .

Isometric Bloxel Generator.

Usage:
    {0} [-o <out-path>] [-a | ([-nsew])] [-b <blockname>] <all-sides>
    {0} [-o <out-path>] [-a | ([-nsew])] -b <blockname> <up> <rest-sides>
    {0} [-o <out-path>] [-a | ([-nsew])] -b <blockname> <up> <down>
        <rest-sides>
    {0} [-o <out-path>] [-a | ([-nsew])] -b <blockname> <up> <down> <left>
        <right> <front> <back>
    {0} [-o <out-path>] [-a | ([-nsew])] -t <tex> <num-wide> <num-long>
        [<block-file>]
    {0} -c <filename> <red> <green> <blue> [<alpha>]
        [--width=<width> --height=<height>]
    {0} [-o <out-path>] [-a | ([-nsew])] -b <blockname> -B <blox-file>
    {0} -h | --help | -v | --version

Options:
    -o <out-path> --out-path=<out-path>
                    The path/name of the resulting image
    -h --help       Show this help message
    -v --version    Display version information
    -a --all-dirs   Output an image for north, south, east, and west
    -t <tex> --texture=<tex>
                    The texture map to use with batch processing
    -b <blockname> --block=<blockname>
                    The name of the output file with no extension
    -B <blox-file> --bloxel=<blox-file>
                    The filename of the bloxel file to render
    -c <filename> --create-texture=<filename>
                    Use the provided color to generate a plain texture filled
                    with said color
    -n --north      Output north shaded image. It is assumed that only north
                    will be outputted if no other flag is set
    -s --south      Output south shaded image
    -e --east       Output east shaded image
    -w --west       Output west shaded image
    --width=<width>
                    Specify created texture width [default: 16]
    --height=<height>
                    Specify created texture height [default: 16]

Arguments:
    <all-sides>     Image to use for every side of block
    <rest-sides>    Image to use for sides not specified
    <up>            Image to use for up side
    <down>          Image to use for down side
    <left>          Image to use for left side
    <right>         Image to use for right side
    <front>         Image to use for front side
    <back>          Image to use for back side
    <num-wide>      The number of images across
    <num-long>      The number of images down
    <block-file>    The batch processing file to use
    <width>         The width of the generated texture
    <height>        The height of the generated texture
    <filename>      The filename of the generated texture
    <red>           Red color value (0-255)
    <green>         Green color value (0-255)
    <blue>          Blue color value (0-255)
    <alpha>         Alpha value (0-255). If not specified, 255 is assumed
"""


__all__ = [
    'CLI',
    'Iso',
    'Directions',
    'Cornerstone',
    'BloxelSides',
    'Shade',
    'ColorTable',
    'IsoCoors',
]


import sys # Command line arguments
import random # Filenames
from pathlib import Path # For outputting images and naming ambiguous outputs
from functools import lru_cache # Cache inputs/outputs of functions
from docopt import docopt # CLI creation tool
from PIL import Image, ImageDraw, ImageOps
from . blockfile import *
from . terminal_colors import * # Terminal color constants


# Fix the docstring when using like a library
if __name__ == '__main__':
    # Map the color codes to the positions in the docstring
    __doc__ = __doc__.format(sys.argv[0], _CLRfr, _CLRfg, _CLRfb, _CLRreset)
else:
    # Map empty strings to color code positions in case help() is called on mod
    __doc__ = __doc__.format("iso.py", '', '', '', '')


class CLI:
    """
    Convenience class for creating bloxels based on certain command line
    arguments.
    """

    @staticmethod
    def create_texture(filename, r, g, b, a, width, height):
        """
        Creates a texture filled with the given (r, g, b, a) color values and
        saves it with the specified filename.

        Args:
            filename(str): the path and name to save the generated texture
            r(int): the red color value (0-255)
            g(int): the green color value (0-255)
            b(int): the blue color value (0-255)
            a(int): the alpha transparency value (0-255)
            width(int): the width of the generated texture
            height(int): the height of the generated texture
        """
        tex = Image.new('RGBA', (width, height))
        fill_image(tex, (r, g, b, a))
        tex.save(filename)

    @staticmethod
    def process_blockfile_batch(out_path, dirs, filename, texture, num_across,
        num_down):
        """
        Take a supplied input texture and generate a scalar bloxel from the
        instructions in the given blockfile.

        The blockfile contains texture coordinates and possibly block names for
        the generated blocks. The indexes are XY coordinates (0-num_across and
        0-num_down). These coordinates are used to crop out an inner texture to
        be used as the different sides of the output bloxel. Bloxels are saved
        in the given out_path.

        Args:
            out_path(str): the path (not filename) to save the textures
            dirs(list): booleans representing: [North, East, South, West]
            filename(str): the blockfile to open and process
            texture(str): the filename of the input texture
            num_across(int): the number of inner textures across
            num_down(int): the number of inner textures down

        Return:
            None if no output path is specified and the list of generated 
            textures if a path was supplied.
        """
        iso = Iso(4)
        texture = iso.get_texture(Path(texture), Directions.ALL)
        textures = []
        count = 0
        blockfile = BlockFile(filename, num_across, num_down)
        num_textures = blockfile.num_instructions * sum(dirs)

        print('-' * 30, '\n', 'Starting next side...', '\n', '-' * 30)

        for name, coordinates in blockfile.get_all():

            the_textures = []

            for indexes in coordinates:
                xx, yy = indexes
                x_start = xx * Iso.TEX_WIDTH
                y_start = yy * Iso.TEX_WIDTH
                x_end = x_start + Iso.TEX_WIDTH
                y_end = y_start + Iso.TEX_WIDTH
                tex = texture.crop((x_start, y_start, x_end, y_end))
                the_textures.append(tex)

            for dir in Directions.ALL:
                if not dirs[dir]:
                    continue

                count += 1

                # Fill in the rest of the sides for the bloxel creation
                less = 6 - len(the_textures)
                if less > 0:
                    the_textures.extend([the_textures[-1]] * less)

                bloxel = iso.get_scalar_bloxel(dir, *the_textures)

                if not out_path:
                    textures.append(bloxel)
                else:
                    iso.save(bloxel, dir, name, out_path)

                print(f'Bloxel {count} of {num_textures} done...')

        if not out_path:
            return textures

    @staticmethod
    def process_texture_batch(out_path, dirs, texture, num_across, num_down):
        """
        Create a scalar block with a random name from each texture in the
        texture map.

        For each inner texture, create a new bloxel with said texture for every
        side of it.

        Args:
            out_path(str): the path (not filename) to save the textures
            dirs(list): booleans representing: [North, East, South, West]
            texture(str): the filename of the input texture
            num_across(int): the number of inner textures across
            num_down(int): the number of inner textures down

        Return:
            None if no output path is specified and the list of generated 
            textures if a path was supplied.
        """
        iso = Iso(4)
        texture = iso.get_texture(Path(texture))
        textures = []
        characters = (
            'abcdefghijklmnopqrstuvwxyz'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            '1234567890'
        )

        num_textures = num_across * num_down * sum(dirs)
        count = 0

        for y in range(num_down):
            for x in range(num_across):

                # In this case, x and y are obtained from the blockfile
                
                x_start = x * Iso.TEX_WIDTH
                y_start = y * Iso.TEX_WIDTH
                x_end = x_start + (Iso.TEX_WIDTH)
                y_end = y_start + (Iso.TEX_WIDTH)

                tex = texture.crop((x_start, y_start, x_end, y_end))
                name = ''.join([random.choice(characters) for i in range(8)])

                for dir in Directions.ALL:
                    if not dirs[dir]:
                        continue

                    count += 1
                    bloxel = iso.get_scalar_bloxel(dir, *([tex] * 6))

                    if not out_path:
                        textures.append(bloxel)
                    else:
                        iso.save(bloxel, dir, name, out_path)

                    print(f'Bloxel {count} of {num_textures} done...')

        if not out_path:
            return textures

    @staticmethod
    def output_scalar_bloxel_up_down_rest(out_path, blockname, dirs, up, down,
        rest_sides):
        """
        Generate a scalar bloxel with the top side, the bottom side, and the
        image used for every other side.

        Generates a bloxel for each of the directions specified.

        Args:
            out_path(str): the path (not filename) to save the textures
            blockname(str): the name of the generated bloxel
            dirs(list): booleans representing: [North, East, South, West]
            up(str): the filename of the given side
            down(str): the filename of the given side
            rest_sides(str): the filename of the given side
        """
        iso = Iso(4)
        up = iso.get_texture(Path(up))
        down = iso.get_texture(Path(down))
        rest_sides = iso.get_texture(Path(rest_sides))

        for i in Directions.ALL:
            if dirs[i]:
                out = iso.get_scalar_bloxel(i, up, down, *([rest_sides] * 4))
                iso.save(out, i, blockname, out_path)

    @staticmethod
    def output_scalar_bloxel_up_rest(out_path, blockname, dirs, up,
        rest_sides):
        """
        Generate a scalar bloxel with the top side, and the image used for
        every other side.

        Generates a bloxel for each of the directions specified.

        Args:
            out_path(str): the path (not filename) to save the textures
            blockname(str): the name of the generated bloxel
            dirs(list): booleans representing: [North, East, South, West]
            up(str): the filename of the given side
            rest_sides(str): the filename of the given side
        """
        iso = Iso(4)
        up = iso.get_texture(Path(up))
        rest_sides = iso.get_texture(Path(rest_sides))

        for i in Directions.ALL:
            if dirs[i]:
                out = iso.get_scalar_bloxel(i, up, *([rest_sides] * 5))
                iso.save(out, i, blockname, out_path)

    @staticmethod
    def output_scalar_bloxel_all_sides(out_path, blockname, dirs, up, down,
        left, right, front, back):
        """
        Generate a scalar bloxel with the top, bottom, left, right, front and
        back sides.

        Generates a bloxel for each of the directions specified.

        Args:
            out_path(str): the path (not filename) to save the textures
            blockname(str): the name of the generated bloxel
            dirs(list): booleans representing: [North, East, South, West]
            up(str): the filename of the given side
            down(str): the filename of the given side
            left(str): the filename of the given side
            right(str): the filename of the given side
            front(str): the filename of the given side
            back(str): the filename of the given side
        """
        iso = Iso(4)
        up = iso.get_texture(Path(up))
        down = iso.get_texture(Path(down))
        left = iso.get_texture(Path(left))
        right = iso.get_texture(Path(right))
        front = iso.get_texture(Path(front))
        back = iso.get_texture(Path(back))

        for i in Directions.ALL:
            if dirs[i]:
                out = iso.get_scalar_bloxel(i, up, down, left, right, front,
                    back)
                iso.save(out, i, blockname, out_path)

    @staticmethod
    def output_scalar_bloxel_same_sides(out_path, blockname, dirs, all_sides):
        """
        Generate a scalar bloxel with the same image used for every side.

        Generates a bloxel for each of the directions specified.

        Args:
            out_path(str): the path (not filename) to save the textures
            blockname(str): the name of the generated bloxel
            dirs(list): booleans representing: [North, East, South, West]
            all_sides(str): the filename of the image used for all sides
        """
        infile = Path(all_sides)
        iso = Iso(4)
        all_sides = iso.get_texture(infile)

        for i in Directions.ALL:
            if dirs[i]:
                out = iso.get_scalar_bloxel(i, *([all_sides] * 6))
                iso.save(out, i, blockname if blockname else infile.stem,
                    out_path)

    @staticmethod
    def output_multipart_bloxel(out_path, blockname, dirs, bloxfile):
        """
        Generate a multipart bloxel using a bloxel-file containing XYZ
        coordinates and RGBA color values.
        """
        iso = Iso(4)

        for i in Directions.ALL:
            if dirs[i]:
                with open(bloxfile) as file:
                    xyzrgba_data = [
                        tuple(int(float(i)) for i in line.split())
                        for line in file.readlines()
                    ]
                out = iso.get_multipart_bloxel(i, xyzrgba_data)
                iso.save(out, i, blockname, out_path)
        

class Iso:
    """
    Used to generate bloxels with a given direction and input image.

    Also contains functionality to preload textures so that the colors within
    them can be cached for later use and speedier rendering.

    Attributes:
        TEX_WIDTH: the assumed width of the input textures.
        coors: the isometric coordinate generator.
        table_top: the table used for storing colors for this visible side.
        table_left: the table used for storing colors for this visible side.
        table_right: the table used for storing colors for this visible side.
    """
    TEX_WIDTH = 16

    def __init__(self, tile_width):
        """
        Initializes Iso with the given assumed tile width.
        """
        self.coors = IsoCoors(tile_width)
        self.table_top = ColorTable(Sides.TOP)
        self.table_left = ColorTable(Sides.LEFT)
        self.table_right = ColorTable(Sides.RIGHT)

    def seed_tables(self, texture, dir):
        """
        Gets colors from the image's pallet and adds it to the color tables.

        Args:
            texture(Image): the image to gather colors from
            dir(Directions): the direction to use when seeding the table
        """
        if dir == Directions.ALL:
            dirs = dir
        else:
            dirs = [dir]

        for color in texture.getcolors(100000):
            for direction in dirs:
                self.table_top.get(color[1], direction)
                self.table_left.get(color[1], direction)
                self.table_right.get(color[1], direction)

    def get_texture(self, filename, seed_direction=None):
        """
        Loads a texture from the given filename and returns it.

        Optionally seeds the color tables so that rendering is faster. This is
        typically used if the texture being loaded is a texture map.

        Args:
            filename(str): the filename of the texture to load
            seed_direction(Directions): the table to seed if any
        """
        texture = Image.open(filename)
        if seed_direction:
            self.seed_tables(texture, seed_direction)
        return texture

    def rotate_sides(self, dir, up, down, left, right, front, back):
        """
        Uses the direction to choose each logical bloxel side.

        Determines which order the sides will be in based on the given
        direction and returns them in a tuple.

        DIRECTION (UP, DOWN, LEFT, RIGHT, FRONT, BACK) ->
            NORTH (UP, DOWN, LEFT, RIGHT, FRONT, BACK)
            EAST  (UP, DOWN, BACK, FRONT, LEFT, RIGHT)
            SOUTH (UP, DOWN, RIGHT, LEFT, BACK, FRONT)
            WEST  (UP, DOWN, FRONT, BACK, LEFT, RIGHT)

        WHERE ->
            UP    is top
            DOWN  is bottom
            LEFT  is front left
            RIGHT is back right
            FRONT is back left
            BACK  is front right

        Args:
            dir(Directions): the direction to determine side ordering
            up(Image): the image used for this side of the bloxel
            down(Image): the image used for this side of the bloxel
            left(Image): the image used for this side of the bloxel
            right(Image): the image used for this side of the bloxel
            front(Image): the image used for this side of the bloxel
            back(Image): the image used for this side of the bloxel
        """
        if dir == Directions.NORTH:
            return (up, down, left, right, front, back)
        elif dir == Directions.EAST:
            return (up, down, back, front, left, right)
        elif dir == Directions.SOUTH:
            return (up, down, right, left, back, front)
        else: # West
            return (up, down, front, back, right, left)

    def get_scalar_bloxel(self, dir, up, down, left, right, front, back):
        """
        Return a bloxel texture from the supplied images.

        Args:
            dir(Directions): the direction to draw the bloxel on
            up(Image): the image to use for drawing this side
            down(Image): the image to use for drawing this side
            left(Image): the image to use for drawing this side
            right(Image): the image to use for drawing this side
            front(Image): the image to use for drawing this side
            back(Image): the image to use for drawing this side
        """
        
        up, down, left, right, front, back = self.rotate_sides(
            dir, up, down, left, right, front, back
        )

        '''
        Determine if any texture has an alpha channel and if that alpha channel
        contains any value less than 255 (full alpha).
        '''
        draw_all_sides = any([
            # See if any alpha value is below 255
            any([i[1][3] < 255 for i in img.getcolors(100000)])
            
            # For each texture
            for img in (up, down, left, right, front, back)

            # Only if that texture has an alpha channel
            if 'A' in img.mode
        ])

        canvas = Image.new('RGBA', (64, 64))

        def get_xy(width, height):
            """
            Convenience function to obtain a predefined set of coordinates.

            Args:
                width(int): the width of the texture being iterated through
                height(int): the height of the texture being iterated through

            Return:
                A tuple containing: (x, y, (x, y)).
                The `x` and `y` coordinates are indexes falling withing a 0-
                width and 0-height range. The inner tuple is provided for
                convenient iteration.
            """
            for x_pixel in range(width):
                for y_pixel in range(height):
                    yield x_pixel, y_pixel, (x_pixel, y_pixel)

        if draw_all_sides:
            # Draw the back top side
            for x_pixel, y_pixel, coors in get_xy(*[Iso.TEX_WIDTH] * 2):
                pxd = down.getpixel(coors)

                if dir == Directions.NORTH:
                    x, y = self.coors.get(x_pixel, y_pixel, -23)
                elif dir == Directions.EAST:
                    x, y = self.coors.get(y_pixel, x_pixel, -23)
                elif dir == Directions.SOUTH:
                    x, y = self.coors.get(
                        Iso.TEX_WIDTH - x_pixel - 1,
                        Iso.TEX_WIDTH - y_pixel - 1,
                        -23
                    )
                elif dir == Directions.WEST:
                    x, y = self.coors.get(
                        Iso.TEX_WIDTH - y_pixel - 1,
                        Iso.TEX_WIDTH - x_pixel - 1,
                        -23
                    )

                draw_image(x + 1, y + 1, self.table_top.get(pxd, dir), canvas)

            # Draw back right side
            for x_pixel, y_pixel, coors in get_xy(*[Iso.TEX_WIDTH] * 2):
                pxr = right.getpixel(coors)
                x, y = self.coors.get(16, Iso.TEX_WIDTH - x_pixel - 1,
                    Iso.TEX_WIDTH - y_pixel - 24)
                draw_image(x, y, self.table_left.get(pxr, dir), canvas)

            # Draw back left side
            for x_pixel, y_pixel, coors in get_xy(*[Iso.TEX_WIDTH] * 2):
                pxf = front.getpixel(coors)
                x, y = self.coors.get(Iso.TEX_WIDTH - x_pixel, 0,
                    Iso.TEX_WIDTH - y_pixel - 1)
                draw_image(-2 + x, 46 + y, self.table_right.get(pxf, dir),
                    canvas)

        # Draw right side
        for x_pixel, y_pixel, coors in get_xy(*[Iso.TEX_WIDTH] * 2):
            pxb = back.getpixel(coors)
            Cornerstone.get_right()
            x, y = self.coors.get(16 + x_pixel, 0,
                -Iso.TEX_WIDTH - 7 - y_pixel)
            draw_image(x, y + 1, self.table_right.get(pxb, dir), canvas)
            
        # Draw left side
        for x_pixel, y_pixel, coors in get_xy(*[Iso.TEX_WIDTH] * 2):
            pxl = left.getpixel(coors)
            x, y = self.coors.get(0, x_pixel, Iso.TEX_WIDTH - y_pixel - 1)
            draw_image(x, 46 + y, self.table_left.get(pxl, dir), canvas)

        # Draw top side
        for x_pixel, y_pixel, coors in get_xy(*[Iso.TEX_WIDTH] * 2):
            pxu = up.getpixel(coors)
            if dir == Directions.NORTH:
                x, y = self.coors.get(x_pixel, y_pixel, -8)
            elif dir == Directions.EAST:
                x, y = self.coors.get(y_pixel, x_pixel, -8)
            elif dir == Directions.SOUTH:
                x, y = self.coors.get(Iso.TEX_WIDTH - x_pixel - 1,
                    Iso.TEX_WIDTH - y_pixel - 1, -8)
            elif dir == Directions.WEST:
                x, y = self.coors.get(Iso.TEX_WIDTH - y_pixel - 1,
                    Iso.TEX_WIDTH - x_pixel - 1, -8)
            draw_image(x + 1, y - 1, self.table_top.get(pxu, dir), canvas)

        return canvas

    def get_multipart_bloxel(self, dir, bloxels):
        """
        Return a bloxel texture from the supplied bloxel filename.

        Args:
            dir(Direction): the direction to rotate to.
            xyzrgba_data(list): list of tuples containing interlieved xyz/rgba.

        Return:
            An Image that contains the Isometric representation of the bloxel.
        """
        # Sort bloxels by x + y - z coordinates (for layered drawing)

        if dir == Directions.NORTH:
            bloxels.sort(key=lambda b: b[0] - b[1] - b[2], reverse=True)

        elif dir == Directions.EAST:
            bloxels.sort(key=lambda b: b[2] + b[0] + b[1], reverse=False)

        elif dir == Directions.SOUTH:
            bloxels.sort(key=lambda b: b[0] + b[1] - b[2], reverse=False)

        elif dir == Directions.WEST:
            bloxels.sort(key=lambda b: b[0] + b[2] - b[1], reverse=True)

        canvas = Image.new('RGBA', (64, 64))

        for bloxel in bloxels:
            x, y, z, r, g, b, a = bloxel

            for i in range(dir):
                # TODO(pebaz): Do this before sorting
                x, z = Iso.TEX_WIDTH - z, x

            ix, iy = self.coors.get(x, z, y -23)

            if dir == Directions.NORTH:
                ix += 1; iy -= 1

            elif dir == Directions.EAST:
                ix -= 1; iy -= 0

            elif dir == Directions.SOUTH:
                ix -= 3; iy -= 1

            elif dir == Directions.WEST:
                ix -= 1; iy -= 2

            clr = (r, g, b, a)

            draw_image(ix - 1, iy + 1, self.table_left.get((0, 255, 0, 255), dir), canvas)
            draw_image(ix + 1, iy + 1, self.table_right.get((0, 0, 255, 255), dir), canvas)
            draw_image(ix, iy, self.table_top.get((255, 0, 0, 255), dir), canvas)

        return canvas

    def determine_visible_sides(self, dir, up, down, left, right, front, back):
        """
        Meant to save ALOT of time in deciding which of the given textures are
        visible, given the supplied direction.

        DIRECTION (LEFT VISIBLE, TOP VISIBLE, RIGHT VISIBLE) ->
            NORTH (LEFT,  UP, BACK)
            EAST  (BACK,  UP, RIGHT)
            SOUTH (RIGHT, UP, FRONT)
            WEST  (FRONT, UP, LEFT)

        Args:
            dir(Directions): the direction used in determining visible sides
            up(Image): the image for this side of the bloxel
            down(Image): the image for this side of the bloxel
            left(Image): the image for this side of the bloxel
            right(Image): the image for this side of the bloxel
            front(Image): the image for this side of the bloxel
            back(Image): the image for this side of the bloxel
        """
        if dir == Directions.NORTH:
            return (left, up, back)

        elif dir == Directions.EAST:
            return (back, up, right)

        elif dir == Directions.SOUTH:
            return (right, up, front)

        elif dir == Directions.WEST:
            return (front, up, left)

        else:
            raise Exception(f'Invalid direction supplied: {dir}')

    def save(self, texture, dir, blockname, path):
        """
        Saves a texture with a filename constructed from the given parts.

        Args:
            texture(Image): the texture to save
            dir(Direction): the direction to tag the image with
            blockname(str): the name of the generated block
            path(Path): the path (not file) to save the texture
        """
        texture.save(str(path / f'Bloxel-{blockname}-{"NESW"[dir]}.png'))


class Directions:
    """
    Enum specifying each direction and its associated value.
    """
    NORTH = 0
    EAST  = 1
    SOUTH = 2
    WEST  = 3
    ALL = [0, 1, 2, 3]


class Sides:
    """
    Enum specifying the sides of a given bloxel.
    """
    LEFT  = 0
    RIGHT = 1
    TOP   = 2
    ALL   = 3


class BloxelSides:
    """
    Enum specifying the individual sides of a bloxel and the associated value.
    """
    up = 0
    down = 1
    left = 2
    right = 3
    front = 4
    back = 5


class Cornerstone:
    """
    Since this is to process a request for a cornerstone, it is not necessary
    to handle the back sides or the bottom. Even when the cornerstone is
    transparent, the primitive is the cornerstone itself, not the back sides.
    """

    @staticmethod
    @lru_cache(maxsize=None)
    def get(color=(255, 255, 255, 255), dir=Directions.NORTH):
        """
        Returns a cornerstone using a given color and direction.
        . T T .
        L T T R
        L L R R
        . L R .

        Args:
            color(tuple): the color to tint the resulting cornerstone image
            dir(Directions): the direction to use for shading calculations

        Return:
            Cornerstone image with pixels shaded for the given direction.
        """
        
        if dir == Directions.NORTH:
            clr_left = Shade.get_shade(BloxelSides.left)
            clr_top = Shade.get_shade(BloxelSides.up)
            clr_right = Shade.get_shade(BloxelSides.back)

        elif dir == Directions.EAST:
            clr_left = Shade.get_shade(BloxelSides.back)
            clr_top = Shade.get_shade(BloxelSides.up)
            clr_right = Shade.get_shade(BloxelSides.right)

        elif dir == Directions.SOUTH:
            clr_left = Shade.get_shade(BloxelSides.right)
            clr_top = Shade.get_shade(BloxelSides.up)
            clr_right = Shade.get_shade(BloxelSides.front)

        elif dir == Directions.WEST:
            clr_left = Shade.get_shade(BloxelSides.front)
            clr_top = Shade.get_shade(BloxelSides.up)
            clr_right = Shade.get_shade(BloxelSides.left)

        img = Image.new('RGBA', (4, 4))

        # Left Side
        img.putpixel((0, 1), clr_left)
        img.putpixel((0, 2), clr_left)
        img.putpixel((1, 2), clr_left)
        img.putpixel((1, 3), clr_left)

        # Right Side
        img.putpixel((3, 1), clr_right)
        img.putpixel((3, 2), clr_right)
        img.putpixel((2, 2), clr_right)
        img.putpixel((2, 3), clr_right)

        # Top
        img.putpixel((1, 0), clr_top)
        img.putpixel((2, 0), clr_top)
        img.putpixel((1, 1), clr_top)
        img.putpixel((2, 1), clr_top)
        return tint_image(img, color)

    @staticmethod
    @lru_cache(maxsize=None)
    def get_left(color=(255, 255, 255, 255), dir=Directions.NORTH):
        """
        Returns the left side of a cornerstone using a given color/direction.
        . . . .
        # . . .
        # # . .
        . # . .

        Remember to add 1 to y when drawing.

        Args:
            color(tuple): the color to tint the resulting cornerstone image
            dir(Directions): the direction to use for shading calculations

        Return:
            Cornerstone image with pixels shaded for the given direction.
        """

        if dir == Directions.NORTH:
            clr_left = Shade.get_shade(BloxelSides.left)

        elif dir == Directions.EAST:
            clr_left = Shade.get_shade(BloxelSides.back)

        elif dir == Directions.SOUTH:
            clr_left = Shade.get_shade(BloxelSides.right)

        elif dir == Directions.WEST:
            clr_left = Shade.get_shade(BloxelSides.front)

        img = Image.new('RGBA', (2, 3))
        img.putpixel((0, 0), clr_left)
        img.putpixel((0, 1), clr_left)
        img.putpixel((1, 1), clr_left)
        img.putpixel((1, 2), clr_left)
        return tint_image(img, color)

    @staticmethod
    @lru_cache(maxsize=None)
    def get_right(color=(255, 255, 255, 255), dir=Directions.NORTH):
        """
        Returns the right side of a cornerstone using a given color/direction.
        . . . .
        . . . #
        . . # #
        . . # .

        Remember to add 2 to X and 1 to Y when drawing.

        Args:
            color(tuple): the color to tint the resulting cornerstone image
            dir(Directions): the direction to use for shading calculations

        Return:
            Cornerstone image with pixels shaded for the given direction.
        """

        if dir == Directions.NORTH:
            clr_right = Shade.get_shade(BloxelSides.back)

        elif dir == Directions.EAST:
            clr_right = Shade.get_shade(BloxelSides.right)

        elif dir == Directions.SOUTH:
            clr_right = Shade.get_shade(BloxelSides.front)

        elif dir == Directions.WEST:
            clr_right = Shade.get_shade(BloxelSides.left)

        img = Image.new('RGBA', (2, 3))
        img.putpixel((1, 0), clr_right)
        img.putpixel((1, 1), clr_right)
        img.putpixel((0, 1), clr_right)
        img.putpixel((0, 2), clr_right)
        return tint_image(img, color)

    @staticmethod
    @lru_cache(maxsize=None)
    def get_top(color=(255, 255, 255, 255), dir=Directions.NORTH):
        """
        Returns the top side of a cornerstone using the given color/direction.
        . # # .
        . # # .
        . . . .
        . . . .

        Remember, when drawing, to add 1 to X.

        Args:

        Return:
            Cornerstone image with pixels shaded for the given direction.
        """

        if dir == Directions.NORTH:
            clr_left, clr_top, clr_right = (240,) * 3, (255,) * 3, (225,) * 3

        elif dir == Directions.EAST:
            clr_left, clr_top, clr_right = (225,) * 3, (255,) * 3, (200,) * 3

        elif dir == Directions.SOUTH:
            clr_left, clr_top, clr_right = (200,) * 3, (255,) * 3, (215,) * 3

        elif dir == Directions.WEST:
            clr_left, clr_top, clr_right = (215,) * 3, (255,) * 3, (240,) * 3

        clr_top   = (255, 255, 255)
        img = Image.new('RGBA', (2, 2))
        img.putpixel((0, 0), clr_top)
        img.putpixel((1, 0), clr_top)
        img.putpixel((0, 1), clr_top)
        img.putpixel((1, 1), clr_top)
        return tint_image(img, color)


class Shade:
    """
    The shading class, given enough firepower from Rust, could gain feasibility
    for a real time lighting engine. This was initially the plan, but it was
    only supposed to be backed upon chunk load. This could revolutionize the
    engine if rust is able to do this fast enough.

    Sides:
        U = Up
        D = Down
        L = Left
        R = Right
        F = Front
        B = Bottom

    Colors:
        R = Red
        B = Blue
        O = Orange
        G = Green
        Y = Yellow
        P = Purple

    Side Ordering:                         U D L R F B
    Color Ordering (Per given side order): R B O G Y P

    Coloring per side per direction:

          N      E      S      W
        --------------------------
        \ R /  \ R /  \ R /  \ R /
        O | P  P | G  G | Y  Y | O
        --------------------------

    Shading levels per side per direction:

          N      E      S      W
        --------------------------
        \ 1 /  \ 1 /  \ 1 /  \ 1 /
        1 | 2  2 | 3  3 | 2  2 | 1
        --------------------------

    Attributes:
        WHITE: A 4-tuple used to create a shaded cornerstone.
        SHADE: The number of levels to decrease each side's colors by.
        MULTIPLYER: The number to multiply each side's shade by. This keeps the
            shade level of each side (see next) normalized rather than the
            actual shading value per side.
        SIDE_SHADING: A tuple containing the shade levels for: (up, down, left,
            right, front, back)
    """
    WHITE = 255, 255, 255, 255
    SHADE = 15
    MULTIPLYER = 1
    SIDE_SHADING = (0, 4, 1, 3, 2, 2)

    @staticmethod
    @lru_cache(maxsize=None)
    def get_shade(bloxel_side):
        """
        Args:
            dir(int): the direction obtained from `Directions`
            bloxel_side(int): the side number obtained from `BloxelSides`
        """
        return darken(
            Shade.WHITE,
            Shade.SHADE * Shade.SIDE_SHADING[bloxel_side] * Shade.MULTIPLYER
        )


class ColorTable:
    """
    Incrementally stores cornerstones of each requested color and specified
    direction so that future queries will be faster.

    Attributes:
        side: the side to prefer when caching and returning new cornerstone
            images.
        colors: a dictionary of cornerstone images mapped to RGBA color values.
    """
    def __init__(self, side=Sides.ALL):
        """
        Initializes ColorTable with a preferred side.
        """
        self.side = side
        self.colors = dict()

    def get(self, color, direction):
        """
        Retrieves a cornerstone's side with the proper shading or the entire
        cornerstone if every side is specified.

        If the color does not reside within the color table, it is created and
        cached.

        Args:
            color(tuple): either an RGB or RGBA color tuple
            direction(Directions): the direction used in shading calculations
        """
        index = (color, direction)

        if index not in self.colors:
            if self.side == Sides.TOP:
                self.colors[index] = Cornerstone.get_top(color, direction)
            elif self.side == Sides.LEFT:
                self.colors[index] = Cornerstone.get_left(color, direction)
            elif self.side == Sides.RIGHT:
                self.colors[index] = Cornerstone.get_right(color, direction)
            else:
                self.colors[index] = Cornerstone.get(color, direction)

        return self.colors[index]


class IsoCoors:
    """
    Instead of calculating isometric screen coordinates each time, either:
     * Calculate them all once and then cache them
     * Calculate them as needed and then hope some overlap
    """
    def __init__(self, tile_size):
        """
        Initializes the coordinate generator assuming the given tile size.
        """
        self.coors = dict()
        self.tile_size = tile_size

    def __getitem__(self, xyz):
        """
        Convenience method to retrieve isometric screen coordinates.

        Args:
            xyz(tuple): the key used to obtain coordinates from the coors dict
        """
        if xyz not in self.coors:
            self.coors[xyz] = self.__get_pos_from_vec3(*xyz)

        return self.coors[xyz]

    @lru_cache(maxsize=None)
    def get(self, x, y, z):
        """
        Retrieve isometric screen coodinates from the given 3D coordinates.

        Args:
            x(int): the integer value of the given coordinate axis
            y(int): the integer value of the given coordinate axis
            z(int): the integer value of the given coordinate axis

        Return:
            A 2-tuple with the x and y coordinate in isometric screenspace.
        """
        return self[(x, y, z)]

    def seed_coordinates(self, grid=16):
        """
        Calculates every isometric screen coodinate for a given grid size.

        Vastly faster if used on a large enough dataset. Overwrites any
        previously computed values but does not clear coordinates outside the
        given grid size.

        Args:
            grid(int): the cubic size of the grid (grid ** 3)
        """
        tmp = dict()
        for x in range(grid):
            for y in range(grid):
                for z in range(grid):
                    tmp[(x, y, z)] = self.__get_pos_from_vec3(x, y, z)
        self.coors = tmp

    @lru_cache(maxsize=None)
    def __get_pos_from_vec3(self, x, y, z):
        """
        Gets 2D screen coordinates from a vector3.

        Args:
            x(int): the integer value of the given coordinate axis
            y(int): the integer value of the given coordinate axis
            z(int): the integer value of the given coordinate axis

        Return:
            A 2-tuple with the x and y coordinate in isometric screenspace.
        """ 
        p25 = self.tile_size * 0.25
        p50 = self.tile_size * 0.50
        isox = x * p50 + y * p50
        isoy = -x * p25 + y * p25 - z * p50
        return int(isox), int(isoy)


def tint_image(src, color):
    """
    Equivalent to the 'Colorify' function in GIMP.

    Args:
        color(tuple): a 3 or 4-int tuple with RGB values from 0-255.

    Return:
        The tinted image.
    """
    _, _, _, alpha = src.split()
    gray = ImageOps.grayscale(src)
    result = ImageOps.colorize(gray, (0, 0, 0, 0), color)

    if len(color) > 3:
        for x in range(alpha.width):
             for y in range(alpha.height):
                apxl = color[3] if alpha.getpixel((x, y)) > 0 else 0
                alpha.putpixel((x, y), apxl)

    result.putalpha(alpha)
    return result


def fill_image(image, color):
    """
    Sets each pixel of the given image to this color.

    Args:
        color(tuple): a 3 or 4-int tuple with RGBA values from 0-255.
    """
    for y in range(image.height):
        for x in range(image.width):
            image.putpixel((x, y), color)


def draw_image(x, y, img1, img2):
    """
    Draws image img1 onto img2.

    Args:
        x(int): the x coordinate to place the upper-left corner of img1 at
        y(int): the y coordinate to place the upper-left corner of img1 at
        img1(Image): the image to draw ontop of img2
        img2(Image): the image underneath img1
    """
    # Does the top image contain an alpha channel?
    alpha = 'A' in img1.getbands()

    for y_pixel in range(img1.height):
        for x_pixel in range(img1.width):
            px = img1.getpixel((x_pixel, y_pixel))
            
            if alpha and px[3] == 0:
                continue
            
            new_x = x + x_pixel
            new_y = y + y_pixel

            if new_x >= 0 and new_x < img2.width:
                if new_y >= 0 and new_y < img2.height:
                    if alpha:
                        draw_pixel(new_x, new_y, px, img2)
                    else:
                        img2.putpixel((new_x, new_y), px)


@lru_cache(maxsize=None)
def lighten(color, shades=1):
    """
    Lightens a given color by a number of shades.

    Args:
        color(tuple): the RGBA color.
        shades(int): the number of shades to add to the color value.

    Return:
        The lightened color.
    """
    r, g, b, a = color
    return min(r + shades, 255), min(g + shades, 255), min(b + shades, 255), a


@lru_cache(maxsize=None)
def darken(color, shades=1):
    """
    Darkens a given color by a number of shades.

    Args:
        color(tuple): the RGBA color.
        shades(int): the number of shades to subtract from the color value.

    Return:
        The darkened color.
    """
    r, g, b, a = color
    return max(r - shades, 0), max(g - shades, 0), max(b - shades, 0), a


@lru_cache(maxsize=None)
def blend_color(a, b):
    """
    Blends two colors together by their alpha values.

    Args:
        a(tuple): the color to blend on top of b
        b(tuple): the color underneath a

    Return:
        The blended color.
    """
    if len(a) == 3:
        a = (*a, 255)

    if len(b) == 3:
        b = (*b, 255)

    barf = b[3] / 255
    brem = (255 - b[3]) / 255

    fred   = int(b[0] * barf + a[0] * brem)
    fgreen = int(b[1] * barf + a[1] * brem)
    fblue  = int(b[2] * barf + a[2] * brem)

    falpha = min(int(a[3]) + int(b[3]), 255)

    return (fred, fgreen, fblue, falpha)


def draw_pixel(x, y, pixel, img):
    """
    Draw `pixel` onto `img` at the specified coordinates.

    Args:
        x(int): x coordinate of draw
        y(int): y coordinate of draw
        pixel(tuple): red, green, blue, and optionally alpha
        img(Image): the Image to draw the pixel onto

    Raises:
        CoordinateOffGridException: If x or y is negative.
    """
    if x >= 0 and x < img.width and y >= 0 and y < img.height:
        img.putpixel((x, y), blend_color(img.getpixel((x, y)), pixel))
    else:
        '''
        # Uses the img to get the width/height for the error message
        throw CoordinateOffGridException(x, y, img)
        '''
        raise Exception(
            f'The coordinates ({x}, {y}) lay outside the image bounds '
            f'({img.width}, {img.height}).'
        )




def main(args=None):
    # Gather the command line arguments dictionary
    result = docopt(__doc__)

    # Populate all directions in `dirs/` if no direction was set
    if result['--all-dirs']:
        dirs = [True] * 4

    # Assume North is wanted if no other direction flag is set
    else:
        dirs = [result[i] for i in ['--north', '--east', '--south', '--west']]
        if not any(dirs):
            dirs = [True, False, False, False]

    # Preprocess the output path and make sure it doesn't point to a file
    out_path = Path(result['--out-path']) if result['--out-path'] else Path()
    if out_path and out_path.is_file():
        raise Exception(
            'Output path is a file. Only a path was needed.\n'
            f'Perhaps you meant: {out_path.parent}'
        )

    # Create every folder in the path if it does not exist 
    if not out_path.exists():
        out_path.mkdir(parents=True, exist_ok=True)

    # List of all side flags in `result` (given or not given)
    all_sides = ['<up>', '<down>', '<left>', '<right>', '<front>', '<back>']

    # -------------------------------------------------------------------------
    # Begin processing command line arguments:
    # -------------------------------------------------------------------------

    # Version string & logo
    if result['--version']:
        LOGO_ISO_BLOCK_END_INDEX = 343
        print(__doc__[:LOGO_ISO_BLOCK_END_INDEX])
        print('\nIsometric Bloxel Generator\nVersion 0.0.1')

    # Bloxel File with colors/positions of every bloxel in chunk
    elif result['--bloxel']:
        CLI.output_multipart_bloxel(
            out_path,
            result['--block'],
            dirs,
            result['--bloxel']
        )

    # Create texture filled with specified color
    elif result['--create-texture']:
        if not result['<alpha>']:
            result['<alpha>'] = 255
        
        # We know the file does not exist. Create it
        p = Path(result['--create-texture'])
        p.parent.mkdir(parents=True, exist_ok=True)

        CLI.create_texture(
            str(p),
            min(int(result['<red>']), 255),
            min(int(result['<green>']), 255),
            min(int(result['<blue>']), 255),
            min(int(result['<alpha>']), 255),
            int(result['--width']),
            int(result['--height']),
        )

    # Texture map with possible blockfile
    elif result['--texture']:

        # Create a scalar block from each and every texture in the texture map
        if not result['<block-file>']:
            CLI.process_texture_batch(out_path, dirs, result['--texture'],
                int(result['<num-wide>']), int(result['<num-long>'])
            )

        # Construct blocks according to the supplied blockfile
        else:
            CLI.process_blockfile_batch(out_path, dirs, result['<block-file>'],
                result['--texture'], int(result['<num-wide>']),
                int(result['<num-long>'])
            )

    # All sides have same image
    elif result['<all-sides>']:
        CLI.output_scalar_bloxel_same_sides(
            out_path,
            result['--block'],
            dirs,
            result['<all-sides>']
        )

    # Top and bottom with other sides different
    elif result['<up>'] and result['<down>'] and result['<rest-sides>']:
        CLI.output_scalar_bloxel_up_down_rest(
            out_path,
            result['--block'],
            dirs,
            result['<up>'],
            result['<down>'],
            result['<rest-sides>']
        )

    # Top with other sides different
    elif result['<up>'] and result['<rest-sides>']:
        CLI.output_scalar_bloxel_up_rest(
            out_path,
            result['--block'],
            dirs,
            result['<up>'],
            result['<rest-sides>']
        )

    # Every side specified
    elif all([i in result for i in all_sides]):
        CLI.output_scalar_bloxel_all_sides(
            out_path,
            result['--block'],
            dirs,
            result['<up>'],
            result['<down>'],
            result['<left>'],
            result['<right>'],
            result['<front>'],
            result['<back>']
        )


if __name__ == '__main__':
    main()
