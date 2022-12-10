import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from werkzeug.utils import secure_filename

from mark import error, login_required
from datetime import datetime


app = Flask(__name__)


app.config["TEMPLATES_AUTO_RELOAD"] = True


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "static/uploads"
Session(app)
# Definimos las extenciones permitidas

ALLOWED_EXTENSIONS = set(["png", "jpg", "gif"])

db = SQL("sqlite:///coleccion.db")


# Esta función se usa para verificar si un archivo dado tiene una extensión permitida en una lista de extensiones permitidas. En la primera línea, se divide el nombre del archivo en una lista en función del carácter '.' (punto). Luego, se verifica si la segunda parte de la lista (la extensión del archivo) está en la lista de extensiones permitidas. Si es así, se devuelve True. Si no, se devuelve False.
def allowed_file(file):
    return file.endswith(tuple(ALLOWED_EXTENSIONS))


def extencion(file):
    file = file.split('.')
    return file[1]




@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response





@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            return error("Debes colocar un Apodo", 403)

        elif not request.form.get("password"):
            return error("Debes colocar una contraseña", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return error("Apodo o contraseña incorrecta", 403)

        session["user_id"] = rows[0]["id"]

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("username"):
            return error("Debes colocar un Apodo", 400)

        elif not request.form.get("password"):
            return error("Debes colocar una contraseña", 400)

        elif not request.form.get("confirmation"):
            return error("Debes colocar la repeticion de tu contraseña", 400)

        elif not request.form.get("correo"):
            return error("Debes colocar un correo", 400)

        usuario = request.form.get("username")
        contra = request.form.get("password")
        repeat = request.form.get("confirmation")
        correo = request.form.get("correo")

        if contra != repeat:
            return error("Las contraseñas no son iguales")

        # crear un hash

        hash = generate_password_hash(contra)

        try:
            new_user = db.execute(
                "INSERT INTO users (username, hash, correo) VALUES (?, ?, ?)", usuario, hash, correo)
        except:
            return error("Usuario ya existente")

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/")
@login_required
def index():
    user_id = session["user_id"]

    galeria_db = db.execute(
        "SELECT  likes.liked, public.likes ,public.id, public.user_id, public.title, public.ruta, public.description, users.username, users.profile FROM public INNER JOIN users ON public.user_id = users.id LEFT JOIN (SELECT likes.like as liked, public.id AS public,  users.username FROM public LEFT  JOIN likes ON public.id = likes.public_id INNER JOIN users ON public.user_id = users.id WHERE likes.user_id = ?) AS likes ON likes.public = public.id", user_id)

    return render_template("index.html", galeria=galeria_db)


@app.route("/save", methods=["GET", "POST"])
@login_required
def save():

    user_id = session["user_id"]

    if request.method == "GET":
        return render_template("save.html")

    else:
        d = datetime.now()
        fecha = d.strftime('%d-%m-%Y')
        hora = d.strftime('%H-%M-%S')

        titulo = request.form.get("title")
        description = request.form.get("description")

        if not titulo:
            return error("Debe ingresar un titulo", 400)

        file = request.files.get("file")

        if not file:
            return error("Debe ingresar un archivo", 400)

        privacidad = request.form.get("privacidad")


        # utilizamos el archivo

        filename = secure_filename(file.filename)
        archivo_name = f"image-{fecha}-{hora}-{user_id}.{extencion(filename)}"

        if allowed_file(filename):
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], archivo_name))
        else:
            return error("Archivo no permitido")

        # conectamos con la base de datos
        folder = "/static/uploads/"
        ruta = folder + archivo_name


        if privacidad == "private":
            try:
                new_file = db.execute(
                    "INSERT INTO private (user_id, title, ruta, description, privacidad) VALUES (?, ?, ?, ?, ?)", user_id, titulo, ruta, description, privacidad)
            except:
                return error("Archivo no fue subido correctamente")

        else:
            try:
                new_file = db.execute(
                    "INSERT INTO public (user_id, title, ruta, description, privacidad) VALUES (?, ?, ?, ?, ?)", user_id, titulo, ruta, description, privacidad)
            except:
                return error("Archivo no fue subido correctamente")

        return redirect("/galeria")


@app.route("/galeria", methods=["GET"])
@login_required
def galeria():
    user_id = session["user_id"]

    galeria_db = db.execute(
        "SELECT * FROM public WHERE user_id = ?", user_id)
    galeria_private_db = db.execute(
        "SELECT * FROM private WHERE user_id = ?", user_id)
    geleria_favorite_db = db.execute(
        "SELECT likes.like,  public.id, public.user_id, public.title, public.ruta, public.description, users.username, users.profile FROM public LEFT  JOIN likes ON public.id = likes.public_id INNER JOIN users ON public.user_id = users.id WHERE likes.user_id = ?", user_id
    )

    return render_template("galeria.html", galeria=galeria_db, galeria_p=galeria_private_db, galeria_f=geleria_favorite_db)


@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]

    perfil_id = request.args.get('perfil')



    if perfil_id:
        publicaciones_db = db.execute(
            "SELECT  public.likes ,public.id, public.user_id, public.title, public.ruta, public.description, users.username, users.profile FROM public  INNER JOIN users ON public.user_id = users.id WHERE public.user_id = ?", perfil_id
        )
        perfil_db = db.execute(
            "SELECT * FROM users WHERE id = ?", perfil_id)

        return render_template("profilePublic.html", p=perfil_db , galeria=publicaciones_db)
    else:
        perfil_db = db.execute(
            "SELECT * FROM users WHERE id = ?", user_id)
        return render_template("profile.html", p=perfil_db)

@app.route("/search", methods=["POST"])
@login_required
def search():
    user_id = session["user_id"]
    busqueda1 = request.form.get("search")
    busqueda2 = "%"+busqueda1+"%"

    busqueda_db = db.execute(
        "SELECT  likes.liked, public.likes ,public.id, public.user_id, public.title, public.ruta, public.description, users.username, users.profile FROM public INNER JOIN users ON public.user_id = users.id LEFT JOIN (SELECT likes.like as liked, public.id AS public,  users.username FROM public LEFT  JOIN likes ON public.id = likes.public_id INNER JOIN users ON public.user_id = users.id WHERE likes.user_id = ?) AS likes ON likes.public = public.id WHERE public.title LIKE ?", user_id, busqueda2)
    if len(busqueda_db) == 0:
        return error("No se encontro la publicacion", 400)

    return render_template("index.html", galeria=busqueda_db)


@app.route("/profile_update", methods=["GET", "POST"])
@login_required
def profile_update():
    d = datetime.now()
    fecha = d.strftime('%d-%m-%Y')
    hora = d.strftime('%H-%M-%S')

    user_id = session["user_id"]

    if request.method == "GET":
        return render_template("profile.html")

    else:

        file = request.files.get("file")

        if not file:
            return error("Debe ingresar un archivo", 400)

        # utilizamos el archivo

        filename = secure_filename(file.filename)
        print(filename)
        archivo_name = f"perfil-{fecha}-{hora}.{extencion(filename)}"


        if allowed_file(filename):
            print("permitido")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], archivo_name))



        # conectamos con la base de datos
        folder = "/static/uploads/"
        ruta = folder + archivo_name
        print(ruta)

        tipo = extencion(filename)

        try:
            new_file = db.execute(
                "UPDATE users SET profile = ? WHERE id = ?", ruta, user_id)
        except:
            return error("Vuelve a intentarlo mas tarde")

        return redirect("/profile")


@app.route('/image')
@login_required
def image_function():
    user_id = session["user_id"]
    publicacion_id = request.args.get('public')

    perfil_local = db.execute(
        "SELECT profile FROM users WHERE id = ?", user_id)

    image_db = db.execute(
        "SELECT public.id, public.title, public.ruta, public.description, users.username, users.profile, users.id AS user_id FROM public INNER JOIN users ON public.user_id=users.id WHERE public.id = ?", publicacion_id)

    comentarios_db = db.execute(
        "SELECT comentarios.comentario, comentarios.date, comentarios.id, users.username, users.profile, users.id AS usuario, public.id AS publicacion FROM comentarios INNER JOIN users ON users.id = comentarios.user_id INNER JOIN public ON public.id = comentarios.public_id WHERE public.id = ? ORDER BY comentarios.date", publicacion_id
    )

    return render_template("imagen.html", imagen=image_db, publicacion=publicacion_id, comentarios = comentarios_db, usuario=perfil_local)


@app.route('/like')
@login_required
def like_public():
    publicacion_id = request.args.get('public')
    user_id = session["user_id"]

    p23 = db.execute(
        "SELECT * FROM likes WHERE user_id = ? AND public_id = ?", user_id, publicacion_id
    )
    likes = db.execute(
        "SELECT likes FROM public WHERE id = ?", publicacion_id
    )
    l = likes[0]['likes']
    total = l + 1


    if len(p23) == 0:
        try:
            new_like = db.execute(
                "INSERT INTO likes (user_id, public_id, like) VALUES (?, ?, ?)", user_id, publicacion_id, 'true')
            morelike = db.execute(
                "UPDATE public SET likes = ? WHERE id = ? ", total, publicacion_id
            )

        except:
            return error("A ocurrido un error inesperado")
    else:

        return redirect("/")

    return redirect("/")


@app.route('/unlike')
@login_required
def deletelike_public():
    publicacion_id = request.args.get('public')
    user_id = session["user_id"]

    p23 = db.execute(
        "SELECT * FROM likes WHERE user_id = ? AND public_id = ?", user_id, publicacion_id
    )
    likes = db.execute(
        "SELECT likes FROM public WHERE id = ?", publicacion_id
    )
    l = likes[0]['likes']
    total = l - 1
    print(len(p23))
    if len(p23) >= 1:
        try:
            dlete_like = db.execute(
                "DELETE FROM likes WHERE public_id = ? AND user_id = ?", publicacion_id, user_id)

            minuslike = db.execute(
                "UPDATE public SET likes = ? WHERE id = ? ", total, publicacion_id
            )


        except:
            return error("A ocurrido un error inesperado")
    else:

        return error('esta repetido')

    return redirect("/galeria")


@app.route('/delete')
@login_required
def delete_public():
    publicacion_id = request.args.get('public')
    user_id = session["user_id"]

    try:
        delete = db.execute(
            "DELETE FROM public WHERE id = ? AND user_id = ?", publicacion_id, user_id)

    except:
        return error("A ocurrido un error inesperado")

    return redirect('/galeria')


@app.route('/vue')
def vue_page():

    return render_template("vuep.html")


@app.route("/comentar", methods=["GET", "POST"])
@login_required
def comentar():

    user_id = session["user_id"]

    publicacion = request.args.get('public')

    print(publicacion)


    if request.method == "GET":
        return error("No debe de ver este error")

    else:
        comentario = request.form.get("comentario")

        if not comentario:
            return error("Debe ingresar un comentario", 400)
        print(comentario)

        try:
            new_file = db.execute(
                "INSERT INTO comentarios (user_id, public_id, comentario) VALUES (?, ?, ?)", user_id, publicacion, comentario)
        except:
            return error("Comentario invalido")

        return redirect(f"/image?public={publicacion}")


@app.route('/deletecomentario')
@login_required
def delete_comentario():
    comentario_id = request.args.get('comentario')
    user_id = session["user_id"]
    publicacion = request.args.get('public')
    print(publicacion)

    try:
        delete = db.execute(
            "DELETE FROM comentarios WHERE id = ? AND user_id = ?", comentario_id, user_id)

    except:
        return error("A ocurrido un error inesperado")

    return redirect(f"/image?public={publicacion}")

@app.route('/deletep')
@login_required
def delete_private():
    publicacion_id = request.args.get('private')
    user_id = session["user_id"]

    try:
        delete = db.execute(
            "DELETE FROM private WHERE id = ? AND user_id = ?", publicacion_id, user_id)

    except:
        return error("A ocurrido un error inesperado")

    return redirect('/galeria')


