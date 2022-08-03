import os
from flask import Flask, render_template, request, redirect, flash, session
import base64
import folium
from exif import Image
from datetime import datetime
import hashlib
from PIL import Image as PILImage
import io
import secrets
import pickle

# database
db_path = "database.csv"

def load_database():
    if os.path.exists(db_path):
        with open(db_path, "rb") as file:
            return pickle.load(file)
    else:
        return {
            "users": {},
            "images": {},
        }

def save_database(db):
    with open(db_path, "wb") as file:
        pickle.dump(db, file)

# flask
db = load_database()
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# other
def hash(input):
    return hashlib.sha256(input.encode("utf-8")).hexdigest()

def get_user(request):
    username = request.form["username"]
    password = request.form["password"]
    return {
        "id": hash(username),
        "username": username,
        "password": hash(password),
    }

def set_session(user):
    session["id"] = user["id"]
    session["username"] = user["username"]

def extract_exif(path, filename):
    pos = []
    with open(path, "rb") as img_file:
        img = Image(img_file)
        for x in range(0, 2):
            ref = (img.gps_longitude_ref if x else img.gps_latitude_ref)
            new = (img.gps_longitude if x else img.gps_latitude)
            new = str(new).strip("()").split(",")
            new = [float(x) for x in new]
            new = (new[0]+new[1]/60.0+new[2]/3600.0) * (-1 if ref in ["S","W"] else 1)
            pos.append(new)
    image[filename] = {
        "pos": pos,
        "date": datetime.now()
    }

# routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = get_user(request)
        id = user["id"]
        if id in db["users"]:
            return render_template("error.html", message="User already exists.")
        else:
            db["users"][id] = user
            save_database(db)
            set_session(user)
            return redirect("/")
    else:
        return render_template("register.html")
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = get_user(request)
        id = user["id"]
        if id in db["users"] and db["users"][id]["password"] == user["password"]:
            set_session(user)
            return redirect("/")
        else:
            return render_template("error.html", message="Invalid username or password.")
    else:
        return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")
    
@app.route('/')
def index():
    images = []
    for file in os.listdir("./fish/static/images"):
        if file != ".gitkeep":
            images.append("/static/images/" + file)
    return render_template("index.html", images=images)

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # hash
        file = request.files["file"]
        bytes = file.read()
        hash = hashlib.sha256(bytes).hexdigest()

        # save as webp
        name = hash + ".webp"
        path = os.path.join("./fish/static/images", name)
        image = PILImage.open(io.BytesIO(bytes))
        image.save(path, format="webp")
        return redirect("/")
    else:
        return render_template('upload.html')

@app.route("/map")
def map():
    map = folium.Map(location=[50.5, 8], zoom_start=2)
    for file in os.listdir("./fish/static/images"):
        path = os.path.join("./fish/static/images", file)
        if file != ".gitkeep":
            extract_exif(path, file)
            folium.Marker(image[file]["pos"]).add_to(map)
    return render_template('map.html', map=map._repr_html_())
