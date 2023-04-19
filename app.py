from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime  # Add this import to the top of your app.py file
import os, sys
import json
from models import db, User, VisualNovel
from generate_script import generate_script, post_process_dialogue
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = '501035'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///visual_novels.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define user loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        secret_access_code = request.form['secret_access_code']
        if secret_access_code != "mysecret123":
            return jsonify({'error': 'Invalid secret access code'})
        
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')

        # Add the created_at field when creating a new user instance
        user = User(username=username, password=hashed_password, created_at=datetime.utcnow())

        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/save_novel', methods=['POST'])
@login_required
def save_novel():
    novel_id = request.form['novel_id']
    novel = VisualNovel.query.get_or_404(novel_id)
    novel.user_id = current_user.id
    novel.private = True if request.form.get('private') == 'on' else False
    db.session.commit()
    return redirect(url_for('view_novel', novel_id=novel.id))

@app.route('/generate_visual_novel', methods=['POST'])
@login_required  # Add the login_required decorator to ensure the user is logged in
def generate_visual_novel():
    # Define the cost per request
    cost_per_request = 6

    # Check if the user has enough tokens
    if current_user.tokens < cost_per_request:
        return jsonify({'error': 'insufficient_tokens'})

    # Deduct tokens from the user's account
    current_user.tokens -= cost_per_request
    db.session.commit()

    title = request.form.get('title')  # Use get instead of ['title']

    character_profiles = json.loads(request.form.get('character_profiles', '{}'))  # New line to receive character profiles
    # print(character_profiles)
    # print('STOP HERE')
    # sys.exit()
    show_title, generated_dialogues_tuples, image_url, character_urls = generate_script(title_prompt=title,character_profiles=character_profiles)

    dialogues_str = ';'.join([f"{dialogue_tuple[0]}:{dialogue_tuple[1]}" for dialogue_tuple in generated_dialogues_tuples])

    visual_novel = VisualNovel(
        title=title,
        dialogues=dialogues_str,
        user_id=current_user.id,
        user_agent=request.headers.get('User-Agent'),
        ip_address=request.remote_addr,
        location="Unknown",  # Replace with actual location data if available
        image_url=image_url,
        character_urls=json.dumps(character_urls)
    )
    db.session.add(visual_novel)
    db.session.commit()

    return jsonify({'novel_id': visual_novel.id})

@app.route('/view_novel/<int:novel_id>')
def view_novel(novel_id):
    visual_novel = VisualNovel.query.get_or_404(novel_id)
    pages = [dialogue.split(':', 1) for dialogue in visual_novel.dialogues.split(';')]
    return render_template('novel.html', novel=visual_novel, pages=pages)

@app.route('/dashboard')
@login_required
def dashboard():
    visual_novels = VisualNovel.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', visual_novels=visual_novels)

@app.route('/public_novels')
def public_novels():
    public_novels = VisualNovel.query.filter_by(private=False).all()
    return render_template('public_novels.html', public_novels=public_novels)

@app.route('/generator')
def generator():
    default_character_profiles = {
        "Character 1": {"name": "Alice", "gender": "female", "age": 28, "personality": "outgoing", "build": "slim", "hair_style": "long", "hair_color": "brown", "eye_color": "green"},
        "Character 2": {"name": "Bob", "gender": "male", "age": 32, "personality": "reserved", "build": "athletic", "hair_style": "short", "hair_color": "blonde", "eye_color": "blue"},
        "Character 3": {"name": "Carol", "gender": "female", "age": 25, "personality": "quirky", "build": "curvy", "hair_style": "bob", "hair_color": "red", "eye_color": "brown"},
        "Character 4": {"name": "Dave", "gender": "male", "age": 29, "personality": "confident", "build": "muscular", "hair_style": "shaved", "hair_color": "black", "eye_color": "hazel"},
    }
    return render_template('generator.html', default_character_profiles=json.dumps(default_character_profiles))

@app.route('/edit_novel/<int:novel_id>', methods=['GET', 'POST'])
@login_required
def edit_novel(novel_id):
    novel = VisualNovel.query.get_or_404(novel_id)

    if request.method == 'POST':
        novel.private = 'private' in request.form
        db.session.commit()
        flash('Novel updated successfully.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_novel.html', novel=novel)

@app.route('/user_details', methods=['GET', 'POST'])
@login_required
def user_details():
    if request.method == 'POST':
        # Save user image and other details
        pass
    return render_template('user_details.html')

if __name__ == '__main__':
    app.run(debug=True)

