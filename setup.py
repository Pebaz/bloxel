"""
Usage:
pip install git+https://github.com/Pebaz/bloxel.git
"""

from distutils.core import setup

setup(
	name='bloxel',
	version='1.2.2',
	description='Isometric Voxel Generator',
	author='Samuel Wilder',
	packages=['bloxel'],
	install_requires=[
		'Pillow>=6.2.2',
		'docopt==0.6.2'
	],
	entry_points={
		'console_scripts' : [
			'bloxel=bloxel.iso:main'
		]
	}
)
