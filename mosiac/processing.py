import glob
from PIL import Image, ImageFilter
from scipy import spatial
import numpy as np
import pickle
import os
import random
import matplotlib.pyplot as plt
from mosiac import Tile, MainImage

random.seed(42)

def read_tile(file,conf ,session):
    if " " in file:
        os.rename(file, file.replace(" ", ""))
    file = file.replace(" ", "")
    image_path = file.split('/')[-1].split('\\')[-1]
    original_tile_path = (conf.tiles_photo_dir + image_path).replace('\\', '/')
    if 'jpg' in file.lower() or 'jpeg' in file.lower():

        tile_image = Image.open(file)
        tile_image_10 = tile_image.resize((10, 10))
        tile_image_15 = tile_image.resize((15, 15))
        tile_image_20 = tile_image.resize((20, 20))

        # Calculate dominant color
        search_tile = tile_image.resize((conf.search_size, conf.search_size))
        tile_shape = np.array(tile_image).shape

        if len(tile_shape) == 3 and tile_shape[2] == 3:
            tile = Tile(tile_path=original_tile_path, tile_pickle_10=pickle.dumps(tile_image_10), tile_pickle_15=pickle.dumps(tile_image_15), tile_pickle_20=pickle.dumps(tile_image_20), search_tile=pickle.dumps(search_tile))
            session.add(tile)
    else:
        os.remove(original_tile_path)



def make_tree(conf):
    tiles = Tile.query.with_entities(Tile.search_tile).all()
    tiles = [np.array(pickle.loads(tile[0])).flatten() for tile in tiles]
    tree = spatial.KDTree(np.array(tiles))
    conf.tree = pickle.dumps(tree)

def prepare_tiles(conf, session):
    for file in glob.glob(conf.tiles_photo_dir + '*'):
        read_tile(file, conf, session)
    make_tree(conf)



def make_image(main_photo_obj, conf, tree, tiles, paths):
    main_photo_path = main_photo_obj.main_photo_path
    tile_size = (conf.tile_size, conf.tile_size)
    main_photo = Image.open(main_photo_path)
    main_photo_obj.main_photo_width, main_photo_obj.main_photo_height = (main_photo.width, main_photo.height)

    closest_paths, main_photo, output = create_mosaic(conf, main_photo, paths, tile_size, tiles, tree)

    main_photo_obj.n_tiles_width, main_photo_obj.n_tiles_height = closest_paths.shape
    # Make main image the same size as output and get their avg
    main_photo = main_photo.resize((output.shape[1], output.shape[0]))
    # output = output.filter(ImageFilter.GaussianBlur(1))

    mixing_ratio = conf.mixing_ratio
    output = mixing_ratio * np.array(output) + (1 - mixing_ratio) * np.array(main_photo)
    # Save output
    output_path = conf.output_photo_dir + "output_" + main_photo_path.replace("\\", '/').split('/')[-1]
    plt.imsave(output_path, output / 255)

    main_photo_obj.closest_paths = pickle.dumps(closest_paths)
    main_photo_obj.output_photo_path = output_path

    return main_photo_obj


def create_mosaic(conf, main_photo, paths, tile_size, tiles, tree):
    width, height = main_photo.width, main_photo.height
    aspect_ratio = height / width
    new_width = conf.final_width
    # if main_photo.width > new_width:
    new_height = int(new_width * aspect_ratio)
    main_photo = main_photo.resize((new_width, new_height), Image.ANTIALIAS)
    width = int(np.round(main_photo.size[0] // tile_size[0]))
    height = int(np.round(main_photo.size[1] // tile_size[1]))
    resized_photo = np.array(main_photo.resize((width * conf.search_size, height * conf.search_size)))
    # Find closest tile photo for every pixel
    closest_tiles = np.zeros((width, height), dtype=np.uint32)
    closest_paths = np.zeros((width, height), dtype='object')
    output = np.zeros((tile_size[1] * height, tile_size[0] * width, 3))
    for i in range(width):
        for j in range(height):
            # Offset of tile
            x, y = i * conf.search_size, j * conf.search_size
            closestk = tree.query(resized_photo[y: y + conf.search_size, x: x + conf.search_size, :].flatten(), k=conf.k)
            closest = closestk[1] if conf.k == 1 else random.choice(closestk[1])
            closest_tiles[i, j] = closest
            closest_paths[i, j] = paths[closest]

            x, y = i * tile_size[0], j * tile_size[1]
            output[y: y + tile_size[1], x: x + tile_size[0], :] = tiles[closest]
    return closest_paths, main_photo, output

def get_tile_pickle(size):
    if size == 10:
        return Tile.tile_pickle_10
    elif size == 15:
        return Tile.tile_pickle_15
    else:
        return Tile.tile_pickle_20

def make_all_images(conf, session):
    # tiles = read_all_tiles(conf, session)
    tree = conf.tree

    paths, tiles = list(zip(*Tile.query.with_entities(Tile.tile_path, get_tile_pickle(conf.tile_size)).all()))
    paths = np.array(paths)
    tiles = np.array([pickle.loads(tile) for tile in tiles])
    for main_photo_obj in MainImage.query.all():
        main_photo_obj = make_image(main_photo_obj, conf, tree, tiles, paths)
        session.add(main_photo_obj)


def dump_to_pickle(*args):
    with open('dataPickle', 'wb') as f:
        pickle.dump(args,f)
