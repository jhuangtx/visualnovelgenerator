from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from secrets import token_hex
from datetime import datetime  # Add this import to the top of your app.py file
import os, sys
import json
import serverless_wsgi
from models import User, VisualNovel
from generate_script import generate_script
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = '501035'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define user loader function
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Add the lambda_handler function
def lambda_handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)

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

        existing_user = User.get_by_username(username)
        if existing_user:
            return jsonify({'error': 'Username already exists, please try another one'})

        hashed_password = generate_password_hash(password, method='sha256')

        # Add the created_at field when creating a new user instance
        user = User(username=username, password=hashed_password, created_at=datetime.utcnow())
        user.save()

        # Log the user in after successful registration
        login_user(user)
        return jsonify({'success': 'Registration successful. Redirecting to dashboard.'})  # Add this line
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)
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

@app.route('/generate_visual_novel', methods=['POST'])
@login_required
def generate_visual_novel():
    cost_per_request = 20

    if current_user.tokens < cost_per_request:
        return jsonify({'error': 'insufficient_tokens'})

    title = request.form.get('title').title()

    try:
        show_title, generated_dialogues, cover_image_key = generate_script(title_prompt=title, user_id=current_user.id)
    except Exception as e:
        app.logger.error(f"Error generating visual novel: {str(e)}")
        return jsonify({'error': 'generation_failed'})

    dialogues_str = json.dumps(generated_dialogues)


    visual_novel = VisualNovel(
        title=title,
        private=True,
        dialogues=dialogues_str,
        user_id=current_user.id,
        user_agent=request.headers.get('User-Agent'),
        ip_address=request.remote_addr,
        location="Unknown",
        created_dt=datetime.utcnow(),
        cover_image_bucket='visualnovelimages',
        cover_image_key=cover_image_key
    )
    visual_novel.save()

    current_user.tokens -= cost_per_request
    current_user.update({'tokens': current_user.tokens})

    return jsonify({'novel_id': visual_novel.id})

@app.route('/view_novel/<int:novel_id>')
def view_novel(novel_id):
    visual_novel = VisualNovel.get(novel_id)
    pages = [(dialogue['name'], dialogue['dialogue']) for dialogue in json.loads(visual_novel.dialogues)]
    return render_template('novel.html', novel=visual_novel, pages=pages)

@app.route('/dashboard')
@login_required
def dashboard():
    csrf_token = token_hex(16)
    session['csrf_token'] = csrf_token
    visual_novels = VisualNovel.get_all_by_user_id(current_user.id)

    cover_image_urls = {}
    for novel in visual_novels:
        if isinstance(novel.cover_image_key, (str, bytes)):
            cover_image_urls[novel.id] = f"https://{novel.cover_image_bucket}.s3.amazonaws.com/{novel.cover_image_key}"
        else:
            cover_image_urls[novel.id] = None

    return render_template('dashboard.html', visual_novels=visual_novels, csrf_token=csrf_token, user=current_user, cover_image_urls=cover_image_urls)  # Pass csrf_token, user and cover_image_urls to the template

@app.route('/public_novels')
def public_novels():
    public_novels = VisualNovel.get_all_public()
    public_novels_with_users = [(novel, User.get(novel.user_id)) for novel in public_novels]

    cover_image_urls = {}
    for novel in public_novels:
        if isinstance(novel.cover_image_key, (str, bytes)):
            cover_image_urls[novel.id] = f"https://{novel.cover_image_bucket}.s3.amazonaws.com/{novel.cover_image_key}"
        else:
            cover_image_urls[novel.id] = None

    return render_template('public_novels.html', public_novels=public_novels_with_users, cover_image_urls=cover_image_urls)



@app.route('/generator')
def generator():
    default_character_profiles = {
        "Character 1": {"name": "Alice", "gender": "female", "age": 28, "personality": "outgoing", "build": "slim", "hair_style": "long", "hair_color": "brown", "eye_color": "green"},
        "Character 2": {"name": "Bob", "gender": "male", "age": 32, "personality": "reserved", "build": "athletic", "hair_style": "short", "hair_color": "blonde", "eye_color": "blue"},
        "Character 3": {"name": "Carol", "gender": "female", "age": 25, "personality": "quirky", "build": "curvy", "hair_style": "bob", "hair_color": "red", "eye_color": "brown"},
        "Character 4": {"name": "Dave", "gender": "male", "age": 29, "personality": "confident", "build": "muscular", "hair_style": "shaved", "hair_color": "black", "eye_color": "hazel"},
    }
    return render_template('generator.html', default_character_profiles=json.dumps(default_character_profiles))

@app.route('/edit_novel/<string:novel_id>', methods=['GET', 'POST'])
@login_required
def edit_novel(novel_id):
    novel = VisualNovel.get(novel_id)
    
    if request.method == 'POST':
        # Use request.form.get() instead of 'private' in request.form
        novel.private = request.form.get('private') == 'true'
        novel.update({'private': novel.private})
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
    app.run()
    # app.run(debug=True)
