import os
from mosiac import app, db, Configuration, MainImage, Tile, make_image, read_tile, make_tree
from flask import render_template, request, redirect, url_for, flash
import pickle
import numpy as np
import uuid
import itertools


# Helper methods

def delete_image(ID):
    with app.app_context():
        mainImage = MainImage.query.filter_by(id=ID).first()
        os.remove(mainImage.main_photo_path)
        os.remove(mainImage.output_photo_path)
        db.session.delete(mainImage)
        db.session.commit()

def is_jpg(file_name):
    return ('.jpg' in file_name.lower()) or ('.jpeg' in file_name.lower())

def get_tile_pickle(size):
    if size == 10:
        return Tile.tile_pickle_10
    elif size == 15:
        return Tile.tile_pickle_15
    else:
        return Tile.tile_pickle_20

def Upload_main_images(files):
    if files[0].filename:
        conf = Configuration.query.filter_by(id=1).first()

        paths, tiles = list(
            zip(*Tile.query.with_entities(Tile.tile_path, get_tile_pickle(conf.tile_size)).all()))
        paths = np.array(paths)
        tiles = np.array([pickle.loads(tile) for tile in tiles])
        for f in files:
            if is_jpg(f.filename):
                main_photo_path = conf.main_photo_dir[:-1] + str(uuid.uuid4()) + '.' + f.filename.split('.')[-1]
                f.save(main_photo_path)
                main_photo_obj = MainImage(main_photo_path=main_photo_path)
                with app.app_context():
                    session = db.session
                    tree = pickle.loads(conf.tree)
                    main_photo_obj = make_image(main_photo_obj, conf, tree, tiles, paths)
                    session.add(main_photo_obj)
                    session.commit()


def upload_tiles(files):
    for f in files:
        conf = Configuration.query.filter_by(id=1).first()
        f.save(conf.tiles_photo_dir + f.filename)
        session = db.session
        with app.app_context():
            f_name = conf.tiles_photo_dir + f.filename
            read_tile(f_name, conf, session)
            session.commit()


def delete_tile(ID):
    with app.app_context():
        tile = Tile.query.filter_by(id=ID).first()
        os.remove(tile.tile_path)
        db.session.delete(tile)
        db.session.commit()


def update_tree():
    conf = Configuration.query.filter_by(id=1).first()
    session = db.session()
    with app.app_context():
        make_tree(conf)
        session.commit()


def get_next_prev(n):
    all_ids = MainImage.query.with_entities(MainImage.id).all()
    all_ids_sorted = sorted(list(*zip(*all_ids)))
    if n in all_ids_sorted:
        idx = all_ids_sorted.index(n)
        next_idx = idx + 1
        prev_idx = idx - 1
        if idx == len(all_ids_sorted) - 1:
            next_idx = 0
        elif idx == 0:
            prev_idx = len(all_ids_sorted) - 1
        return all_ids_sorted[prev_idx], all_ids_sorted[next_idx]
    return all_ids_sorted[n], all_ids_sorted[n]



# Controller methods

@app.route('/',methods=['GET','POST'])
@app.route('/home', methods=['GET','POST'])
def home_page():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'Upload':
            files = request.files.getlist('files[]')
            Upload_main_images(files)
            return redirect(url_for('home_page'))
        elif action == 'Delete':
            ID = request.form.get('path')
            delete_image(ID)
            return redirect(url_for('home_page'))
    else:
        main_images = MainImage.query.with_entities(MainImage.main_photo_path, MainImage.id).all()
        main_photos = [(id, r"../"+'/'.join(path.split('/')[1:])) for path, id in reversed(main_images)]
        return render_template('home.html', main_photos=main_photos)


@app.route('/grid/<n>')
def grid_page(n):
    n = int(n)
    main_photo_obj = MainImage.query.filter_by(id=n).first()
    prev_n, next_n = get_next_prev(n)
    if main_photo_obj:
        output_name = r"../"+'/'.join(main_photo_obj.output_photo_path.replace(r'\\','/').split('/')[1:])
        w, h = main_photo_obj.n_tiles_width, main_photo_obj.n_tiles_height
        closest_objects = np.empty((w, h), dtype='object')
        max_width = str(100/w)+"%"
        max_height = str(100 / h) + "%"
        for col, row in itertools.product(range(w), range(h)):
            closest_objects[col, row] = (n, col, row)

        return render_template('grid.html',data=closest_objects,max_width=max_width,max_height=max_height,output_name=output_name, prev=prev_n, next=next_n)
    else:
        return redirect(url_for('home_page'))


@app.route('/<n>/<l>/<m>', methods=['GET'])
def image_page(n, l, m):
    n = int(n)
    main_photo_obj = MainImage.query.filter_by(id=n).first()
    raw = pickle.loads(main_photo_obj.closest_paths)[int(l), int(m)]
    path = r"../../"+'/'.join(raw.replace(r'\\','/').split('/')[1:])
    return render_template('image.html', path=path)


@app.route('/tiles', methods=['GET', 'POST'])
def tile_page():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'Upload':
            files = request.files.getlist('files[]')
            if files[0].filename:
                upload_tiles(files)
        elif action == 'Delete':
            ID = request.form.get('path')
            delete_tile(ID)
        elif action == "Update Tree":
            update_tree()

        return redirect(url_for('tile_page'))

    tile_photos = [(id, r"../" + '/'.join(path.split('/')[1:])) for id, path in
                   reversed(Tile.query.with_entities(Tile.id, Tile.tile_path).all())]
    return render_template('tiles.html', tile_photos=tile_photos)


@app.route('/tile_image/<n>')
def tile_image_page(n):
    n = int(n)
    id, path = Tile.query.with_entities(Tile.id, Tile.tile_path).filter_by(id=n).first()
    path = r"../" + '/'.join(path.split('/')[1:])
    return render_template('image.html', id=id, path=path)


@app.route('/edit_configuration')
def edit_configuration():
    with app.app_context():
        config = Configuration.query.get(1)
    return render_template('conf.html', config=config)


@app.route('/update_configuration', methods=['POST'])
def update_configuration():
    with app.app_context():
        config = Configuration.query.get(1)
        config.k = int(request.form['k'])
        config.tile_size = int(request.form['tile_size'])
        config.mixing_ratio = float(request.form['mixing_ratio'])
        config.final_width = int(request.form['final_width'])

        db.session.commit()
    flash('Configuration updated successfully!', 'success')
    return redirect(url_for('edit_configuration'))