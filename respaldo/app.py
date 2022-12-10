import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from werkzeug.utils import secure_filename

from helpers import error, login_required

from datetime import datetime

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "static/uploads"
Session(app)

# Definimos las extenciones permitidas

ALLOWED_EXTENSIONS = set(["png", "jpg", "gif"])

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///coleccion.db")


# verificamos que el archivo tenga las extenciones correctas

def allowed_file(file):
    file = file.split('.')
    if file[1] in ALLOWED_EXTENSIONS:
        return True

    return False


def extencion(file):
    file = file.split('.')
    return file[1]


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():

    galeria_db = db.execute(
        "SELECT public.id, public.user_id, public.title, public.ruta, public.description, public.etiqueta, users.username, users.profile FROM public, users WHERE public.user_id = users.id LIMIT 20")




    return render_template("index.html", galeria=galeria_db)


@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            return error("must provide username", 403)

        elif not request.form.get("password"):
            return error("must provide password", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return error("invalid username and/or password", 403)

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
        # Ensure username was submitted
        if not request.form.get("username"):
            return error("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return error("must provide password", 400)

        elif not request.form.get("confirmation"):
            return error("must provide repeat", 400)

        # Query database for username
        usuario = request.form.get("username")
        print(usuario)
        contra = request.form.get("password")
        print(contra)
        repeat = request.form.get("confirmation")
        print(repeat)

        if contra != repeat:
            return error("Las contraseñas no son iguales")

        # Redirect user to home page

        # crear un hash

        hash = generate_password_hash(contra)

        try:
            new_user = db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)", usuario, hash)
        except:
            return error("Usuario ya existente")

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


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

        # utilizamos el archivo

        filename = secure_filename(file.filename)
        print(filename)
        archivo_name = f"{fecha}-{hora}{extencion(filename)}"

        if allowed_file(filename):
            print("permitido")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        # conectamos con la base de datos
        folder = "/static/uploads/"
        ruta = folder + filename
        print(ruta)

        tipo = extencion(filename)

        try:
            new_file = db.execute(
                "INSERT INTO public (user_id, title, ruta, etiqueta, description) VALUES (?, ?, ?, ?, ?)", user_id, titulo, ruta, tipo, description)
        except:
            return error("Archivo no existe")

        return redirect("/galeria")


@app.route("/galeria", methods=["GET"])
@login_required
def galeria():
    user_id = session["user_id"]

    galeria_db = db.execute(
        "SELECT * FROM public WHERE user_id = ?", user_id)
    print(galeria_db)
    return render_template("galeria.html", galeria=galeria_db)


@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]

    perfil_id = request.args.get('perfil')

    print(user_id)
    print(perfil_id)


    if perfil_id:
        perfil_db = db.execute(
            "SELECT * FROM users WHERE id = ?", perfil_id)

        return render_template("profilePublic.html", p=perfil_db)
    else:
        perfil_db = db.execute(
            "SELECT * FROM users WHERE id = ?", user_id)
        return render_template("profile.html", p=perfil_db)














@app.route("/search", methods=["POST"])
@login_required
def search():
    busqueda1 =  request.form.get("search")
    busqueda2 = busqueda1+"%"
    print(busqueda2)


    busqueda_db = db.execute(
    "SELECT public.title, public.ruta, public.description, public.etiqueta, users.username, users.profile FROM public, users WHERE public.user_id = users.id AND title LIKE ?", busqueda2)

    if len(busqueda_db) == 0:
        return error("No se encontro la publicacion", 400)

    return render_template("galeria.html", galeria=busqueda_db)



@app.route("/profile_update", methods=["GET", "POST"])
@login_required
def profile_update():

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

        if allowed_file(filename):
            print("permitido")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        # conectamos con la base de datos
        folder = "/static/uploads/"
        ruta = folder + filename
        print(ruta)

        tipo = extencion(filename)

        try:
            new_file = db.execute(
                "UPDATE users SET profile = ? WHERE id = ?", ruta, user_id)
        except:
            return error("Vuelve a intentarlo mas tarde")

        return redirect("/profile")

    return render_template("imagen.html", imagen = busqueda_db)



@app.route('/image')
def query_example():
    publicacion_id = request.args.get('public')
    image_db = db.execute(
        "SELECT * FROM public WHERE id = ?", publicacion_id)



    return render_template("imagen.html", imagen=image_db)

