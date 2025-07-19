from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/about')
def about():
    return render_template('index.html')

@main.route('/redirect')
def redirect():
    
    return render_template('index.html')