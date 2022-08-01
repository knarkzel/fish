from flask import Flask, render_template


app = Flask(__name__)


@app.route('/')
def index():
        return render_template("index.html")

@app.route('/about')
def about():
        return render_template("about.html")

@app.route('/map')
def map():
        return render_template("map.html")

@app.route('/comments/')
def comments():
    comments = ['This is the first comment.',
                'This is the second comment.',
                'This is the third comment.',
                'gnome'
                ]

    return render_template('comments.html', comments=comments)