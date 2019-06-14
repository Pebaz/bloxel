# bloxel
Isometric Voxel Generator.

Can be used to take an input texture such as this one:

<img src="examples/res/Grass.png" width=128>



And turn it into a 2.5D Bloxel with this command:

```sh
bloxel "examples/res/Grass.png"
```

Resulting in this image:

<img src="examples/single-out/Bloxel-Grass-N.png" width=128>

Note that the sides have been properly shaded.

## Installation

```sh
pip install git+https://github.com/Pebaz/bloxel.git
```

Or if done via Git:

```sh
git clone https://github.com/Pebaz/bloxel.git
pip install -r requirements.txt
```

## Usage

```sh
bloxel [ -o <out-path>] [ -a | ([ -nsew])] [ -b <blockname>] <all-sides>
bloxel [ -o <out-path>] [ -a | ([ -nsew])] -b <blockname> <up> <rest-sides>
bloxel [ -o <out-path>] [ -a | ([ -nsew])] -b <blockname> <up> <down> <rest-sides>
bloxel [ -o <out-path>] [ -a | ([ -nsew])] -b <blockname> <up> <down> <left> <right> <front> <back>
bloxel [ -o <out-path>] [ -a | ([ -nsew])] -t <tex> <num-wide> <num-long> [<block-file>]
bloxel -c <filename> <red> <green> <blue> [<alpha>] [--width=<width> --height=<height>]
bloxel -h | --help | -v | --version
```

Bloxel is also designed to be imported as a library when needed:

```python
import bloxel

texture_size = 4
iso = bloxel.iso.Iso(texture_size)
grass = iso.get_texture('examples/res/Grass.png')
direction = bloxel.Directions.NORTH
bloxel = iso.get_scalar_bloxel(direction, *([grass] * 6))
# Saves file as: './Bloxel-Grass-N.png'
iso.save(bloxel, direction, 'Grass', '.')
```



### Single Texture

```sh
bloxel -b MyBlock Grass.png
```

### Single Texture Multiple Directions

```sh
bloxel -b MyBlock -nw Grass.png
```

### Multiple Textures

```sh
bloxel -b MyBlock Grass.png Dirt.png
```

### Multiple Textures Multiple Directions

```sh
bloxel -b MyBlock -ne Grass.png Dirt.png
```

### All Directions (North, South, East, West)

```sh
bloxel -b MyBlock -a Grass.png Dirt.png
```

### Generate Solid Color Image (Useful for making primitive blocks)

```sh
bloxel -c "BlueBlock.png" 0 0 255 --width=16 --height=16
```

### Texture Map

```sh
bloxel -o "examples/TexMap" -n -t "examples/Sample.png" 2 2
```

Given this texture map:

<img src="examples/Sample.png" width=128 />

Generate these four blocks and put them in `examples/TexMap/`

<img src="examples/TexMap/Bloxel-pdeoM6SD-N.png" width=64 />

<img src="examples/TexMap/Bloxel-qVFrb79W-N.png" width=64 />

<img src="examples/TexMap/Bloxel-rRhkjUB4-N.png" width=64 />

<img src="examples/TexMap/Bloxel-RzZDMSZM-N.png" width=64 />

### BlockFile

```sh
bloxel -t examples/res/Texture-Map.png 2 2 examples/example.blockfile -o examples/blockfile-out
```

A blockfile can enable a massive number of explicitly-named blocks to be created easily.  The need for this automation is because a texture map is literally an image that contains a grid of sub-images that get turned into bloxels. The generated bloxels have randomly-generated names so there must be a better way to name them. In addition, each sub-image is turned into a bloxel with that image being used for each side. Complex multi-image bloxels can be created easily by putting them into the blockfile to be read in one by one and generated.

Example blockfile syntax:

```python
0 # Grass
1 # Dirt
2 # Concrete
3 # Water
0 1 # Piston
0 2 # Oven
0 1 2 # Stove
0 1 2 3 # CrackedStone1
0 1 2 3 2 1 # CrackedStone2
```

Each line can be thought of as a different invocation of the CLI. The arguments are the same in regards to the chosen images and the name of the bloxel. Each number corresponds to the index of the image within the texture map. Everything after the `#` is the name of the bloxel (whitespace stripped off of the left and right sides). Lines with no `#` are given randomly-generated strings as names. If this is the input image:

<img src="examples/Sample.png" width=128 />

This is the sequence of the indexes go from left to right and top to bottom (just like reading):

```python
0 (Rune)
1 (Dirt)
2 (Colorful Tile)
3 (Stone Tile)
```

The result of a texture map + blockfile combo is a number of bloxels that have a name rather than being randomly-generated.