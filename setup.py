"""
Usage:
pip install git+https://github.com/Pebaz/bloxel.git
"""

from distutils.core import setup

setup(
	name='bloxel',
	version='1.0',
	description='Isometric Voxel Generator',
	author='Samuel Wilder',
	packages=['bloxel'],
	install_requires=[
		'docopt',
        'PILLOW'
	],
    scripts=['bloxel.bat']
)