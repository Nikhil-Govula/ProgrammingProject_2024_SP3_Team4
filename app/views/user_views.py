from flask import render_template

def render_index(user):
    return render_template('index.html', user=user)