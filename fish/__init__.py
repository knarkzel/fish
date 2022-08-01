import os
from flask import Flask, render_template, request, redirect, flash, session
import base64
import pathlib

root_folder = pathlib.Path(__file__).parent.resolve()
image_folder = os.path.join(root_folder, "static/images")

app = Flask(__name__)
app.secret_key = "821da87006d0296aea3c0f091a88c097d4709493f7a972566b444e33c3a948bb"

users = []
class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.id = base64.b64encode((username+password).encode("ascii"))
    def __eq__(self, other):
        return self.username == other.username

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User(username, password)
        if user in users:
            return user.id
        else:
            users.append(user)
            session["user_name"] = user.username
            session["user_id"] = user.id
            return redirect("/")
    else:
        return render_template("register.html")
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
    

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        login = User(username, password)
        for user in users:
            if user.id == login.id:
                session["user_name"] = user.username
                session["user_id"] = user.id   
                return redirect("/")
        return "wrong"
    else:
        return render_template("login.html")

@app.route("/")
def index():
    images = []
    for file in os.listdir(image_folder):
            if file != ".gitkeep":
                    images.append("/static/images/" + file)
    return render_template("index.html", images=images)

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        path = os.path.join(image_folder, file.filename)
        file.save(path)
        return redirect("/")
    else:
        return render_template("upload.html")




