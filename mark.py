import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps




def error(message, code=400, image_route="/static/error.png"):


    return render_template("error.html", top=code, bottom=message, img=image_route), code


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function





