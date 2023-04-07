
from mosiac import app, db, Configuration, MainImage, Tile, make_image, read_tile, make_tree
from flask import render_template, request, jsonify, redirect, url_for, flash
import pickle
import numpy as np



@app.route('/',methods=['GET','POST'])
@app.route('/home', methods=['GET','POST'])
def home_page():
    conf = Configuration.query.filter_by(id=1).first()
    if request.method == 'POST':
        print("hey")
        files = request.files.getlist('files[]')
        if files[0].filename:
            paths, tiles = list(
                zip(*Tile.query.with_entities(Tile.resized_tile_path, Tile.tile_pickle).all()))
            paths = np.array(paths)
            tiles = np.array([pickle.loads(tile) for tile in tiles])
            for f in files:
                main_photo_path = conf.main_photo_dir[:-1] + f.filename
                f.save(conf.main_photo_dir[:-1]+f.filename)
                main_photo_obj = MainImage(main_photo_path=main_photo_path)
                with app.app_context():
                    session = db.session
                    tree = pickle.loads(conf.tree)
                    print("in hooome", tree.n)

                    main_photo_obj = make_image(main_photo_obj, conf, tree, tiles, paths)
                    session.add(main_photo_obj)
                    session.commit()
        return redirect(url_for('home_page'))
    else:
        main_photos = [(r"../"+'/'.join(path.split('/')[1:]), id) for path, id in MainImage.query.with_entities(MainImage.main_photo_path, MainImage.id).all()]
        return render_template('home.html', main_photos=main_photos)

@app.route('/grid/<n>')
def grid_page(n):
    n = int(n)
    main_photo_obj = MainImage.query.filter_by(id=n+1).first()
    output_name = r"../"+'/'.join(main_photo_obj.output_photo_path.replace(r'\\','/').split('/')[1:])

    closest_paths = pickle.loads(main_photo_obj.closest_paths)
    closest_objects = closest_paths.copy()[:, :]
    w,h = closest_objects.shape
    max_width = str(100/w)+"%"

    max_height = str(100 / h) + "%"
    print(w,h)
    l = 0

    print(closest_objects.shape, closest_objects[0,0])
    for i in range(closest_paths.shape[0]):
        m = 0
        for j in range(closest_paths.shape[1]):
            closest_objects[i,j] = (r"../"+'/'.join(closest_paths[i,j].replace(r'\\','/').split('/')[1:]),n,l,m)
            m += 1
        l += 1

    return render_template('grid.html',data=closest_objects,max_width=max_width,max_height=max_height,output_name=output_name)


@app.route('/<n>/<l>/<m>', methods=['GET'])
def image_page(n, l, m):
    n = int(n)
    main_photo_obj = MainImage.query.filter_by(id=n + 1).first()
    raw = pickle.loads(main_photo_obj.closest_paths)[int(l), int(m)]
    conf = Configuration.query.get(1)
    resized_tiles_photo_dir = '/'.join(conf.resized_tiles_photo_dir.split('/')[1:])
    tiles_photo_dir = '/'.join(conf.tiles_photo_dir.split('/')[1:])
    path = r"../../"+'/'.join(raw.replace(r'\\','/').split('/')[1:]).replace(resized_tiles_photo_dir, tiles_photo_dir)
    return render_template('image.html', path=path)

@app.route('/tiles', methods=['GET','POST'])
def tile_page():

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'Upload':
            files = request.files.getlist('files[]')
            if files[0].filename:
                for f in files:
                    conf = Configuration.query.filter_by(id=1).first()
                    f.save(conf.tiles_photo_dir + f.filename)
                    session = db.session
                    with app.app_context():
                        f_name = conf.tiles_photo_dir+f.filename
                        read_tile(f_name, conf, session)
                        session.commit()


        elif action == 'Delete':
            print("in tile post")
            path = request.form.get('path')
            # Delete the image at the given path
            # ...
            with app.app_context():
                tile = Tile.query.filter_by(id=path).first()
                db.session.delete(tile)
                db.session.commit()
        elif action == "Update Tree":
            conf = Configuration.query.filter_by(id=1).first()
            session = db.session()
            with app.app_context():
                make_tree(conf)
                session.commit()
            conf = Configuration.query.filter_by(id=1).first()
            t = pickle.loads(conf.tree)

        return redirect(url_for('tile_page'))
    tile_photos = [(id ,r"../" + '/'.join(path.split('/')[1:])) for id, path in reversed(Tile.query.with_entities(Tile.id, Tile.tile_path).all())]
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
        config.main_photo_dir = request.form['main_photo_dir']
        config.tiles_photo_dir = request.form['tiles_photo_dir']
        config.resized_tiles_photo_dir = request.form['resized_tiles_photo_dir']
        config.k = int(request.form['k'])
        config.tile_width = int(request.form['tile_width'])
        config.tile_height = int(request.form['tile_height'])
        config.output_photo_dir = request.form['output_photo_dir']

        db.session.commit()
    flash('Configuration updated successfully!', 'success')
    return redirect(url_for('edit_configuration'))