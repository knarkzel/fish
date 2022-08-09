import io
import os
import base64
import pickle
import folium
import secrets
import hashlib
import pathlib
import requests
from exif import Image
from datetime import datetime
from sqlitedict import SqliteDict
from PIL import ExifTags, Image as PILImage
from PIL.ExifTags import TAGS, GPSTAGS
from flask import Flask, render_template, request, redirect, flash, session

# folders
root_folder = pathlib.Path(__file__).parent.resolve()
image_folder = os.path.join(root_folder, "static/images")

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
            "comments": {},
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

def store_metadata(image, hash):
    # exif
    pos = []
    img = Image(image)
    for x in range(0, 2):
        ref = (img.gps_longitude_ref if x else img.gps_latitude_ref)
        new = (img.gps_longitude if x else img.gps_latitude)
        new = str(new).strip("()").split(",")
        new = [float(x) for x in new]
        new = (new[0]+new[1]/60.0+new[2]/3600.0) * (-1 if ref in ["S","W"] else 1)
        pos.append(new)
    date = datetime.now()
    location = requests.get(f"http://0.0.0.0:8080/{pos[0]}/{pos[1]}").text
    
    # username and exif + location
    info = {
        "username": session["username"],
        "id": session["id"],
        "pos": pos,
        "date": date,
        "location": location,
    }
    db["images"][hash + ".webp"] = info
    db["images"][hash + "-thumbnail.webp"] = info
    db["comments"][hash + ".webp"] = []
    save_database(db)

def generate_thumbnail(img, hash):
    w = img.size[0]
    h = img.size[1]
    max_res = 500
    if h > w:
        if w > max_res:
            length = max_res
        else:
            length = h
        rz_img = img.resize((length, int(h * (length / w)))) 
        loss = rz_img.size[1] - length
        thumb = rz_img.crop(
            box = (0, loss / 2, length, rz_img.size[1] - loss / 2))
    else:
        if h > max_res:
            length = max_res
        else:
            length = h
        rz_img = img.resize((int(w * (length / h)), length)) 
        loss = rz_img.size[0] - length
        thumb = rz_img.crop(
            box = (loss / 2, 0, rz_img.size[0] - loss / 2, length))
    name = hash + "-thumbnail.webp"
    path = os.path.join(image_folder, name)                
    thumb.save(path)    


def get_images(filter):
    images = []
    for file in os.listdir(image_folder):
        if file != ".gitkeep" and filter(file):
            images.append(file)
    return images

def get_thumbnail(image):
    if "thumbnail" in image:
        return image
    else:
        return image[0:image.index(".webp")] + "-thumbnail.webp"

def get_image(image):
    image = image.replace("-thumbnail", "")
    return image

def get_username(image):
    return db["images"][image]["username"]

def get_userid(image):
    return db["images"][image]["id"]

def get_location(image):
    return db["images"][image]["location"]

def get_comments(image):
    return db["comments"][image]

def sort_date(images):
    sort = []
    for name in images:
        sort.append([name, db["images"][name]["date"]])
    sort = sorted(sort, key = lambda x: x[1], reverse = True) # sorts by newest
    out = []
    for x in sort:
        out.append(str(x[0]))
    return out
    
def draw_map(filter):
    bounds = []
    map = folium.Map(attributionControl=False, max_bounds=True, zoomSnap=0.1)
    for file in os.listdir(image_folder):
        if file != ".gitkeep" and filter(file):
            bounds.append(db["images"][file]["pos"])
            position = db["images"][file]["pos"]
            location = db["images"][file]["location"]
            popup = render_template("popup.html", username=get_username(file), image=get_thumbnail(file), location=get_location(file))
            folium.Marker(position, popup).add_to(map)
    map.fit_bounds(bounds, padding=(200,200), max_zoom=14)
    return map

# routes
@app.route("/")
def index():
    images = get_images(lambda file: "thumbnail" in file)
    return render_template("index.html", images=sort_date(images))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
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

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
    
@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    missing = []
    if request.method == "POST":
        files = request.files.getlist("file")
        for file in files:
            # hash
            bytes = file.read()
            hash = hashlib.sha256(bytes).hexdigest()
        
            # save as webp
            name = hash + ".webp"
            path = os.path.join(image_folder, name)
            with PILImage.open(io.BytesIO(bytes)) as image:
                check = {
                    ExifTags.TAGS[k]
                    for k, v in image._getexif().items()
                    if k in ExifTags.TAGS
                }
                if "GPSInfo" in check:
                    image.save(path, format="webp")
                    generate_thumbnail(image, hash)
                    store_metadata(bytes, hash)
                else:
                    missing.append(file.filename)
        if len(missing):
            for name in missing:
                message = str(name + " ")
            message = message + "- missing GPS info, rest have been uploaded."
            return render_template("error.html", message=message)
        else:
            return redirect("/")
    else:
        return render_template("upload.html")

@app.route("/users/<username>")
def profile(username):
    id = hash(username)
    if id in db["users"]:
        images = get_images(lambda file: db["images"][file]["username"] == username and "thumbnail" in file)
        images = sort_date(images)
        return render_template("profile.html", user=db["users"][id], images=images, username=username)
    else:
        return render_template("error.html", message="User does not exist.")

@app.route("/images/<image>", methods=["GET", "POST"])
def view_image(image):
    print(db["comments"])

    if request.method == "POST":
        comment = request.form["comment"]
        db["comments"][image].append({ "content": comment, "username": session["username"], "time": datetime.now()})
        save_database(db)

        return redirect("/images/" + image)
    else:
        if "thumbnail" in image:
            return redirect(f"/images/{get_image(image)}")
        if image in db["images"]:
            return render_template("view_image.html", image=get_image(image), username=get_username(image), location=get_location(image), userid=get_userid(image), comments=get_comments(image))
        else:
            return render_template("error.html", message="Image does not exist.")

# map
@app.route("/map") 
def map():
    map = draw_map(lambda file: "thumbnail" not in file)
    return render_template("map.html", map=map._repr_html_())
    
@app.route("/map/images/<image>")
def map_image(image):
    map = draw_map(lambda file: str(image) in file)
    return render_template("map.html", map=map._repr_html_())

@app.route("/map/users/<username>")
def map_user(username):
    map = draw_map(lambda file: db["images"][file]["username"] == username)
    return render_template("map.html", map=map._repr_html_())

# delete
@app.route("/delete/images/<image>")
def delete_image(image):
    print(get_userid(image))
    print(session["id"])
    if session["id"] == get_userid(image):
        os.remove(image_folder + "/" + image)
        os.remove(image_folder + "/" + get_thumbnail(image))
        return redirect("/users/"+get_username(image))
    else:
        return render_template("error.html", message="No access.")
