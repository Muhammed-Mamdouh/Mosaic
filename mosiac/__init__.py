from flask import Flask

from mosiac.processing import make_all_images, prepare_tiles, make_image

import random
import pickle

random.seed(42)

# Sources and settings


# Image to be made into Mosaic
main_photo_dir = r"mosiac/static/main_images/*"

# Real tiling images
tile_photos_path = r"mosiac/static/tiles/*"

# Resized tiling images that will actually be used in tiling
oj_tile_photos_path = r"mosiac/static/oj_tiles/"

k = 15

# tile size
tile_size = (10, 10)

# Mosaic Image output
output_path = "mosiac/static/output_images/"


## uncomment to make any changes

# tree, paths, tiles = prepare_tiles(tile_photos_path, oj_tile_photos_path, tile_size)
#
# main_photo_paths, widths, heights, tile_sizes, closest_paths_list, main_photo_sizes, output_names, tiles = make_all_images(
#     main_photo_dir, output_path, tile_size, tree, k, paths, tiles)

with open('./dataPickle', 'rb') as f:
    main_photo_paths, widths, heights, tile_sizes, closest_paths_list, main_photo_sizes, output_names, tiles, tree, paths = pickle.load(f)

app = Flask(__name__,template_folder='Templates',static_folder='static')
from mosiac import routes
