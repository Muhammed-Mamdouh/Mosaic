from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

import random
import pickle

random.seed(42)


start_over = True
if os.path.exists("instance/project.db"):
    start_over = False


app = Flask(__name__,template_folder='Templates',static_folder='static')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

db = SQLAlchemy(app)

from mosiac.models import *
from mosiac.processing import make_all_images, prepare_tiles, make_image, dump_to_pickle, read_all_tiles, read_tile, resize_tile, make_tree


with app.app_context():
    db.create_all()

if start_over:
    conf = Configuration(main_photo_dir=r"mosiac/static/main_images/*", tiles_photo_dir=r"mosiac/static/tiles/", resized_tiles_photo_dir = r"mosiac/static/oj_tiles/", k=4, tile_width=15, tile_height=15, output_photo_dir=r"mosiac/static/output_images/", id=1)
else:
    with app.app_context():
        conf = Configuration.query.first()
session = db.session




# Image to be made into Mosaic
# main_photo_dir = r"mosiac/static/main_images/*"
#
# # Real tiling images
# tile_photos_path = r"mosiac/static/tiles/*"
#
# # Resized tiling images that will actually be used in tiling
# oj_tile_photos_path = r"mosiac/static/oj_tiles/"
#
# k = 5
#
# # tile size
# tile_size = (10, 10)
#
# # Mosaic Image output
# output_path = "mosiac/static/output_images/"


## uncomment to make any changes
if start_over:
    with app.app_context():
        session.add(conf)
        prepare_tiles(conf,session)

        tiles = read_all_tiles(conf, session)
        conf.tiles = pickle.dumps(tiles)

        make_all_images(conf, session)
        session.commit()
        print(Configuration.query.all())
# dump_to_pickle(main_photo_paths, widths, heights, tile_sizes, closest_paths_list, main_photo_sizes, output_names, tiles, tree, paths, original_paths)

# with open('./dataPickle', 'rb') as f:
#     main_photo_paths, widths, heights, tile_sizes, closest_paths_list, main_photo_sizes, output_names, tiles, tree, paths, original_paths = pickle.load(f)


from mosiac import routes

