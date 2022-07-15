from mosiac import app, widths, heights, closest_paths_list, output_names, main_photo_paths
from flask import render_template



@app.route('/')
@app.route('/home', methods=['GET'])
def home_page():
    main_photos = [r"../"+'/'.join(path.split('/')[1:]) for path in main_photo_paths]
    return render_template('home.html', main_photos=main_photos)

@app.route('/grid/<n>')
def grid_page(n):
    n = int(n)
    output_name = r"../"+'/'.join(output_names[n].replace(r'\\','/').split('/')[1:])
    w = widths[n]
    max_width = str(100/w)+"%"

    h = heights[n]
    max_height = str(100 / h) + "%"

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
