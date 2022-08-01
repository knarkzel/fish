import os
from flask import Flask, render_template, request, redirect, flash, session
import base64



app = Flask(__name__)
app.secret_key = "good-secret_key"

users = []
class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.id = base64.b64encode((username+password).encode("ascii"))
    def __eq__(self, other):
        return self.username == other.username







@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
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
        
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")
    

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        login = User(username, password)
        for user in users:
            if user.id == login.id:
                session["user_name"] = user.username
                session["user_id"] = user.id   
                return redirect("/")
        return "wrong"
    else:
        return render_template("login.html")

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




