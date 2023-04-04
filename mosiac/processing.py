import glob
import sys

from PIL import Image
from scipy import spatial
import numpy as np
import pickle
import os
import random
import matplotlib.pyplot as plt
from mosiac import Tile, ResizedTile, MainImage

random.seed(42)

def read_tile(file,conf ,session):
    if 'jpg' in file.lower() or 'jpeg' in file.lower():
        if " " in file:
            os.rename(file, file.replace(" ", ""))
        file = file.replace(" ", "")
        image_path = file.split('/')[-1].split('\\')[-1]
        original_tile_path = (conf.tiles_photo_dir + image_path).replace('\\', '/')
        tile = Tile(tile_path=original_tile_path)
        session.add(tile)
    else:
        os.remove(file)

def read_all_tiles(conf, session):
    tiles = []
    for file in glob.glob(conf.resized_tiles_photo_dir + '*'):
        if 'jpg' in file.lower() or 'jpeg' in file.lower():
            tiles.append(Image.open(file))

    return tiles

def resize_tile(file, conf, session):
    if 'jpg' in file.lower() or 'jpeg' in file.lower():
        if " " in file:
            os.rename(file, file.replace(" ", ""))
        file = file.replace(" ", "")
        image_path = file.split('/')[-1].split('\\')[-1]
        tile_path = (conf.resized_tiles_photo_dir + image_path).replace('\\', '/')

        tile = Image.open(file)
        tile = tile.resize((conf.tile_width, conf.tile_height))

        # Calculate dominant color
        mean_color = np.array(tile).mean(axis=0).mean(axis=0)

        if mean_color.shape == (3,):
            re_tile = ResizedTile(tile_path=tile_path)
            tile.save(tile_path)
            session.add(re_tile)
            return mean_color
    else:
        os.remove(file)



def prepare_tiles(conf, session):
    # Clean oj_tile files
    for path in glob.glob(conf.resized_tiles_photo_dir + '*'):
        os.remove(path)
    colors = []
    for file in glob.glob(conf.tiles_photo_dir + '*'):
        read_tile(file, conf, session)
        color = resize_tile(file, conf, session)
        colors.append(color)


    # Import and resize all tiles
    # colors = ResizedTile.query.with_entities(ResizedTile.color).all()

    # # Calculate dominant color
    # colors = []
    # for tile in tiles:
    #     mean_color = np.array(tile).mean(axis=0).mean(axis=0)
    #     if mean_color.shape == (3,):
    #         colors.append(mean_color)

    tree = spatial.KDTree(np.stack(colors))

    return tree


def make_image(main_photo_obj, conf, tree, tiles, session):
    main_photo_path = main_photo_obj.main_photo_path
    main_photo = Image.open(main_photo_path)
    main_photo_obj.main_photo_width, main_photo_obj.main_photo_height = (main_photo.width, main_photo.height)
    width, height = main_photo.width, main_photo.height
    aspect_ratio = height / width
    new_width = 1000
    if main_photo.width > new_width:
        new_height = int(new_width * aspect_ratio)
        main_photo = main_photo.resize((new_width, new_height), Image.ANTIALIAS)
    main_photo_size = main_photo.size
    tile_size = (conf.tile_width, conf.tile_height)
    width = int(np.round(main_photo.size[0] // tile_size[0]))
    height = int(np.round(main_photo.size[1] // tile_size[1]))
    resized_photo = main_photo.resize((width, height))
    # Find closest tile photo for every pixel
    closest_tiles = np.zeros((width, height), dtype=np.uint32)
    closest_paths = np.zeros((width, height), dtype='object')
    paths = np.array(ResizedTile.query.with_entities(ResizedTile.tile_path).all())
    for i in range(width):
        for j in range(height):
            closestk = tree.query(resized_photo.getpixel((i, j)), k=conf.k)
            if conf.k == 1:
                closest = closestk[1]
            else:
                closest = random.choice(closestk[1])
            closest_tiles[i, j] = closest
            closest_paths[i, j] = paths[closest][0]

    # Create an output image
    output = Image.new('RGB', (tile_size[0] * width, tile_size[1] * height))
    # Draw tiles
    for i in range(width):
        for j in range(height):
            # Offset of tile
            x, y = i * tile_size[0], j * tile_size[1]
            # Index of tile
            index = closest_tiles[i, j]
            # Draw tile
            output.paste(tiles[index], (x, y))
    # Make main image the same size as output and get their avg
    main_photo = main_photo.resize(output.size)

    output = 0.4 * np.array(output) + 0.6 * np.array(main_photo)
    # Save output
    output_path = conf.output_photo_dir + "output_" + main_photo_path.replace("\\", '/').split('/')[-1]
    plt.imsave(output_path, output / 255)


    main_photo_obj.closest_paths = pickle.dumps(closest_paths)
    main_photo_obj.output_photo_path = output_path


    return main_photo_obj


def make_all_images(conf, session, tiles):
    # tiles = read_all_tiles(conf, session)
    print(sys.getsizeof(tiles))
    tree = conf.tree
    for main_photo_obj in MainImage.query.all():
        main_photo_obj = make_image(main_photo_obj, conf, tree, tiles, session)
        session.add(main_photo_obj)
        print(main_photo_obj)


def dump_to_pickle(*args):
    with open('dataPickle', 'wb') as f:
        pickle.dump(args,f)
