from mosiac import app, widths, heights, make_image,closest_paths_list, output_names, main_photo_paths, main_photo_dir, output_path, original_paths, tile_sizes, main_photo_sizes, tile_size, tree,k, paths, tiles
from flask import render_template, request, jsonify



@app.route('/',methods=['GET','POST'])
@app.route('/home', methods=['GET','POST'])
def home_page():
    if request.method == 'POST':
        print("hey")
        f = request.files['file']
        f.save(main_photo_dir[:-1]+f.filename)
        main_photo_path = main_photo_dir[:-1]+f.filename
        output_name = output_path + "output_" + main_photo_path.replace("\\", '/').split('/')[-1]
        width, height, tile_size2, closest_paths, main_photo_size = make_image(main_photo_path, tile_size, tree, k, paths, tiles, output_name)
        main_photo_paths.append(main_photo_path)
        widths.append(width)
        heights.append(height)
        tile_sizes.append(tile_size2)
        closest_paths_list.append(closest_paths)
        main_photo_sizes.append(main_photo_size)
        output_names.append(output_name)
    main_photos = [r"../"+'/'.join(path.split('/')[1:]) for path in main_photo_paths]
    return render_template('home.html', main_photos=main_photos)

@app.route('/grid/<n>')
def grid_page(n):
    n = int(n)
    output_name = r"../"+'/'.join(output_names[n].replace(r'\\','/').split('/')[1:])
    main_image_name = r"../"+'/'.join(main_photo_paths[n].replace(r'\\','/').split('/')[1:])
    w = widths[n]
    max_width = str(100/w)+"%"

    h = heights[n]

    max_height = str(100 / h) + "%"
    image_width = str(tile_size[0] * w)
    image_height = str(tile_size[1] * h)

    l = 0
    closest_objects = closest_paths_list[n].copy()[:, :]
    for i in range(closest_paths_list[n].shape[0]):
        m = 0
        for j in range(closest_paths_list[n].shape[1]):
            closest_objects[i,j] = (r"../"+'/'.join(closest_paths_list[n][i,j].replace(r'\\','/').split('/')[1:]),n,l,m)
            m += 1
        l += 1

    return render_template('grid.html',data=closest_objects,max_width=max_width,max_height=max_height,output_name=output_name)


@app.route('/<n>/<l>/<m>', methods=['GET'])
def image_page(n, l, m):
    n = int(n)
    raw = closest_paths_list[n][int(l),int(m)]
    path = r"../../"+'/'.join(raw.replace(r'\\','/').split('/')[1:]).replace("oj_tiles","tiles")
    return render_template('image.html', path=path)

@app.route('/tiles', methods=['GET','POST'])
def tile_page():
    tile_photos = [r"../" + '/'.join(path.split('/')[1:]) for path in original_paths]
    return render_template('tiles.html', tile_photos=tile_photos)

@app.route('/tile_image/<n>')
def tile_image_page(n):
    n = int(n)
    path = original_paths[n]
    path = r"../" + '/'.join(path.split('/')[1:])
    return render_template('image.html', path=path)

@app.route('/delete-image', methods=['POST'])
def delete_image():
    path = request.json['path']
    # Delete the image at the given path
    # ...
    return jsonify(success=True)