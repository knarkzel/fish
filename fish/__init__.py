import os
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

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
        file = request.files["file"]
        path = os.path.join("./fish/static/images", file.filename)
        file.save(path)
        return redirect("/")
    else:
        return render_template('upload.html')
