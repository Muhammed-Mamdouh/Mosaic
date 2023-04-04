
from mosiac import app, conf, db, MainImage, Tile, ResizedTile, make_image, read_tile, resize_tile
from flask import render_template, request, jsonify
import pickle
import numpy as np



@app.route('/',methods=['GET','POST'])
@app.route('/home', methods=['GET','POST'])
def home_page():
    if request.method == 'POST':
        print("hey")
        f = request.files['file']
        f.save(conf.main_photo_dir[:-1]+f.filename)
        main_photo_path = conf.main_photo_dir[:-1]+f.filename
        main_photo_obj = MainImage(main_photo_path=main_photo_path)
        with app.app_context():
            session = db.session
            tree = pickle.loads(conf.tree)
            tiles = pickle.loads(conf.tiles)
            main_photo_obj = make_image(main_photo_obj, conf, tree, tiles, session)
            session.add(main_photo_obj)
            session.commit()

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
    raw = pickle.loads(main_photo_obj.closest_paths)[int(l),int(m)]

    path = r"../../"+'/'.join(raw.replace(r'\\','/').split('/')[1:]).replace("oj_tiles","tiles")
    return render_template('image.html', path=path)

@app.route('/tiles', methods=['GET','POST'])
def tile_page():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'Upload':
            f = request.files['file']
            f.save(conf.tiles_photo_dir + f.filename)
            session = db.session
            with app.app_context():
                f_name = conf.tiles_photo_dir+f.filename
                read_tile(f_name, conf, session)
                color = resize_tile(f_name, conf, session)
                session.commit()

        elif action == 'Delete':
            print("in tile post")
            path = request.form.get('path')
            # Delete the image at the given path
            # ...
            with app.app_context():
                tile = Tile.query.filter_by(id=path).first()
                # re_tile = ResizedTile.query.filter_by(tile_path=path).first()
                print(path, tile)
                db.session.delete(tile)
                # # db.session.delete(re_tile)
                db.session.commit()
            return jsonify(success=True)
    tile_photos = [(id ,r"../" + '/'.join(path.split('/')[1:])) for id, path in reversed(Tile.query.with_entities(Tile.id, Tile.tile_path).all())]
    return render_template('tiles.html', tile_photos=tile_photos)

@app.route('/tile_image/<n>')
def tile_image_page(n):
    n = int(n)
    id, path = Tile.query.with_entities(Tile.id, Tile.tile_path).filter_by(id=n).first()
    path = r"../" + '/'.join(path.split('/')[1:])
    return render_template('image.html', id=id, path=path)

@app.route('/delete-image', methods=['POST'])
def delete_image():
    path = request.json['path']
    # Delete the image at the given path
    # ...
    with app.app_context():
        tile = Tile.query.filter_by(id=path).first()
        # re_tile = ResizedTile.query.filter_by(tile_path=path).first()
        print(path ,tile)
        db.session.delete(tile)
        # # db.session.delete(re_tile)
        db.session.commit()
    tile_page()
    return jsonify(success=True)