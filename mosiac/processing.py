import glob
from PIL import Image
from scipy import spatial
import numpy as np
import pickle
import os
import random
import matplotlib.pyplot as plt

random.seed(42)


def prepare_tiles(tile_photos_path, oj_tile_photos_path, tile_size):
    # Clean oj_tile files

    for path in glob.glob(oj_tile_photos_path + '*'):
        os.remove(path)

    # Get all tiles
    tile_paths = []
    for file in glob.glob(tile_photos_path):
        if " " in file:
            os.rename(file, file.replace(" ", ""))
        tile_paths.append(file.replace(" ", ""))

    # Import and resize all tiles
    tiles = []
    paths = []
    colors = []
    for path in tile_paths:
        image_path = path.split('/')[-1].split('\\')[-1]
        tile = Image.open(path)
        tile_path = (oj_tile_photos_path + image_path).replace('\\','/')
        tile = tile.resize(tile_size)

        # Calculate dominant color
        mean_color = np.array(tile).mean(axis=0).mean(axis=0)
        if mean_color.shape == (3,):
            colors.append(mean_color)

        tile.save(tile_path)
        tiles.append(tile)
        paths.append(tile_path)

    # # Calculate dominant color
    # colors = []
    # for tile in tiles:
    #     mean_color = np.array(tile).mean(axis=0).mean(axis=0)
    #     if mean_color.shape == (3,):
    #         colors.append(mean_color)

    tree = spatial.KDTree(np.stack(colors))

    return tree, paths, tiles


def make_image(main_photo_path, tile_size, tree, k, paths, tiles, output_path):
    main_photo = Image.open(main_photo_path)
    main_photo_size = main_photo.size
    width = int(np.round(main_photo.size[0] // tile_size[0]))
    height = int(np.round(main_photo.size[1] // tile_size[1]))
    resized_photo = main_photo.resize((width, height))
    # Find closest tile photo for every pixel
    closest_tiles = np.zeros((width, height), dtype=np.uint32)
    closest_paths = np.zeros((width, height), dtype='object')
    for i in range(width):
        for j in range(height):
            closestk = tree.query(resized_photo.getpixel((i, j)), k=k)
            if k == 1:
                closest = closestk[1]
            else:
                closest = random.choice(closestk[1])
            closest_tiles[i, j] = closest
            closest_paths[i, j] = paths[closest]
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
    output = 0.5 * np.array(output) + 0.5 * np.array(main_photo)
    # Save output
    plt.imsave(output_path, output / 255)

    return width, height, tile_size, closest_paths, main_photo_size


def make_all_images(main_photo_dir, output_path, tile_size, tree, k, paths, tiles):
    main_photo_paths = []
    widths = []
    heights = []
    tile_sizes = []
    closest_paths_list = []
    main_photo_sizes = []
    output_names = []
    for main_photo_path in glob.glob(main_photo_dir):
        main_photo_path = main_photo_path.replace("\\",'/')
        output_name = output_path + "output_" + main_photo_path.replace("\\",'/').split('/')[-1]
        width, height, tile_size, closest_paths, main_photo_size = make_image(main_photo_path, tile_size, tree,
                                                                                      k, paths, tiles, output_name)
        main_photo_paths.append(main_photo_path)
        widths.append(width)
        heights.append(height)
        tile_sizes.append(tile_size)
        closest_paths_list.append(closest_paths)
        main_photo_sizes.append(main_photo_size)
        output_names.append(output_name)
    with open('dataPickle', 'ab') as f:
        pickle.dump((main_photo_paths, widths, heights, tile_sizes, closest_paths_list, main_photo_sizes, output_names),f)
    return main_photo_paths, widths, heights, tile_sizes, closest_paths_list, main_photo_sizes, output_names
