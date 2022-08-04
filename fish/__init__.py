import io
import os
import base64
import pickle
import folium
import secrets
import hashlib
import pathlib
from exif import Image
from datetime import datetime
from PIL import Image as PILImage
from flask import Flask, render_template, request, redirect, flash, session
from geopy.geocoders import Nominatim

# geopy
geolocator = Nominatim(user_agent="fish_visualizer")

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

    # username and exif
    info = {
        "username": session["username"],
        "pos": pos,
        "date": date,
    }
    db["images"][hash + ".webp"] = info
    db["images"][hash + "-thumbnail.webp"] = info
    save_database(db)
    
def generate_thumbnail(img, hash):
    # thumbnail
    w = img.size[0]
    h = img.size[1]
    max_res = 500
    if h > w:
        if w > max_res:
            length = max_res
        else:
            length = w
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
            path = os.path.join("./fish/static/images", name)                
            thumb.save(path)    

def get_images(filter):
    images = []
    for file in os.listdir(image_folder):
        if file != ".gitkeep" and filter(file):
            images.append(file)
    return images

def get_thumbnail(image):
    image = image[0:image.index(".webp")] + "-thumbnail.webp"
    return image

def get_image(image):
    image = image.replace("-thumbnail", "")
    return image

def get_location(image):
    list = db["images"][image]["pos"]
    position = ",".join([str(item) for item in list])
    location = geolocator.reverse(position)
    address = location.raw["address"]
    return {
        "city": address.get("city", ""),
        "state": address.get("state", ""),
        "country": address.get("country", ""),
    }

def get_username(image):
    return db["images"][image]["username"]

# routes
@app.route("/")
def index():
    images = get_images(lambda file: "thumbnail" in file)
    return render_template("index.html", images=images)

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
        generate_thumbnail(image, hash)
        store_metadata(bytes, hash)
        return redirect("/")
    else:
        return render_template("upload.html")

@app.route("/map") 
def map():
    pos = []
    xpos = []
    ypos = []
    for file in os.listdir(image_folder):
        if file != ".gitkeep" and "thumbnail" not in file:  
            pos.append(db["images"][file]["pos"])
    for loc in pos:
        xpos.append(loc[0])
        ypos.append(loc[1])
    center = [sum(xpos)/len(xpos), sum(ypos)/len(xpos)]
    
    # remove decimals, probably dont need
    simple = []
    for y in range(0,len(pos)):
        tmp2 = [int(x) for x in pos[y]]
        simple.append(tmp2)
    print(simple)


    # x1 = simple[0][0]
    # y1 = simple[0][1]
    # x2 = simple[1][0]
    # y2 = simple[1][1]
    # dist = ((((x2 - x1 )**2) + ((y2-y1)**2) )**0.5)
    # print(dist)

    # if len(simple) > 2:
    #     for i in range(0,len(simple)):
    #         z1 = simple []
    #         z2 =
    #         lol2 = 
    #         dist = ((((x2 - x1 )**2) + ((y2-y1)**2) )**0.5)
    #         if dist 
    
    map = folium.Map(location=center, zoom_start=3)
    for file in os.listdir(image_folder):
        if file != ".gitkeep" and "thumbnail" not in file:   
            folium.Marker(
                db["images"][file]["pos"],
                popup = "<a href='/users/" + db["images"][file]["username"] + "' target='_blank'>"
                + "<h1>" + db["images"][file]["username"] + ", " + str(db["images"][file]["pos"]) + "<img src=/static/images/" + get_thumbnail(file) + " width=250 height=250></a>"
                ).add_to(map)        
    return render_template("map.html", map=map._repr_html_())

@app.route("/users/<username>")
def profile(username):
    id = hash(username)
    if id in db["users"]:
        images = get_images(lambda file: db["images"][file]["username"] == username and "thumbnail" in file)
        return render_template("profile.html", user=db["users"][id], images=images)
    else:
        return render_template("error.html", message="User does not exist.")

@app.route("/images/<image>")
def view_image(image):
    if "thumbnail" in image:
        return redirect(f"/images/{get_image(image)}")
    if image in db["images"]:
        return render_template("view_image.html", image=get_image(image), username=get_username(image), **get_location(image))
    else:
        return render_template("error.html", message="Image does not exist.")

