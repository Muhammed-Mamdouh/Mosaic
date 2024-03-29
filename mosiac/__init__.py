from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_ngrok import run_with_ngrok

import random
import pickle

random.seed(42)


start_over = True
if os.path.exists("instance/project.db"):
    start_over = False


app = Flask(__name__,template_folder='Templates',static_folder='static')
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['FLASH_MESSAGES'] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
# run_with_ngrok(app)

db = SQLAlchemy(app)

from mosiac.models import *
from mosiac.processing import make_all_images, prepare_tiles, make_image, dump_to_pickle, read_tile, make_tree


with app.app_context():
    db.create_all()

if start_over:
    conf = Configuration(main_photo_dir=r"mosiac/static/main_images/*", tiles_photo_dir=r"mosiac/static/tiles/", k=4, tile_size=10, search_size=5, mixing_ratio=0.6, final_width=1000, output_photo_dir=r"mosiac/static/output_images/", id=1)
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

        make_all_images(conf, session)
        session.commit()
        print(Configuration.query.all())

from mosiac import routes

