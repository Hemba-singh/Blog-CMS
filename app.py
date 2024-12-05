from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
import markdown
import os
from dotenv import load_dotenv

from firebase_config import db, auth_instance, storage_instance
from models import User, Post, Category
from forms import LoginForm, RegistrationForm, PostForm, CategoryForm
from routes.admin import admin_bp
from routes.blog import blog_bp
from routes.auth import auth_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(blog_bp)
app.register_blueprint(auth_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            # Authenticate with Firebase
            user = auth_instance.sign_in_with_email_and_password(form.email.data, form.password.data)
            user_obj = User.get(user['localId'])
            if user_obj:
                login_user(user_obj)
                flash('Logged in successfully.', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
        except Exception as e:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User.create(
                email=form.email.data,
                password=form.password.data,
                username=form.username.data
            )
            if user:
                login_user(user)
                flash('Registration successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Registration failed. Please try again.', 'error')
        except Exception as e:
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Blog routes
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.get_all(limit=10, offset=(page-1)*10)
    return render_template('index.html', posts=posts, page=page)

@app.route('/post/<post_id>')
def view_post(post_id):
    post = Post.get(post_id)
    if post is None:
        flash('Post not found.', 'error')
        return redirect(url_for('index'))
    
    # Convert markdown to HTML
    post.content = markdown.markdown(post.content)
    return render_template('post.html', post=post)

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    form.categories.choices = [(c.id, c.name) for c in Category.get_all()]
    
    if form.validate_on_submit():
        try:
            post = Post.create(
                title=form.title.data,
                content=form.content.data,
                author_id=current_user.id,
                categories=form.categories.data,
                is_published=form.is_published.data
            )
            if post:
                flash('Post created successfully!', 'success')
                return redirect(url_for('view_post', post_id=post.id))
            else:
                flash('Failed to create post. Please try again.', 'error')
        except Exception as e:
            flash('Failed to create post. Please try again.', 'error')
    
    return render_template('post_form.html', form=form, title='New Post')

@app.route('/post/<post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.get(post_id)
    if post is None:
        flash('Post not found.', 'error')
        return redirect(url_for('index'))
    
    if post.author_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this post.', 'error')
        return redirect(url_for('index'))
    
    form = PostForm(obj=post)
    form.categories.choices = [(c.id, c.name) for c in Category.get_all()]
    
    if form.validate_on_submit():
        try:
            if post.update(
                title=form.title.data,
                content=form.content.data,
                is_published=form.is_published.data,
                categories=form.categories.data
            ):
                flash('Post updated successfully!', 'success')
                return redirect(url_for('view_post', post_id=post.id))
            else:
                flash('Failed to update post. Please try again.', 'error')
        except Exception as e:
            flash('Failed to update post. Please try again.', 'error')
    
    return render_template('post_form.html', form=form, title='Edit Post')

@app.route('/post/<post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.get(post_id)
    if post is None:
        flash('Post not found.', 'error')
        return redirect(url_for('index'))
    
    if post.author_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this post.', 'error')
        return redirect(url_for('index'))
    
    if post.delete():
        flash('Post deleted successfully!', 'success')
    else:
        flash('Failed to delete post. Please try again.', 'error')
    
    return redirect(url_for('index'))

# Category routes
@app.route('/categories')
@login_required
def list_categories():
    if not current_user.is_admin:
        flash('You do not have permission to manage categories.', 'error')
        return redirect(url_for('index'))
    
    categories = Category.get_all()
    return render_template('categories.html', categories=categories)

@app.route('/category/new', methods=['GET', 'POST'])
@login_required
def new_category():
    if not current_user.is_admin:
        flash('You do not have permission to create categories.', 'error')
        return redirect(url_for('index'))
    
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category.create(
            name=form.name.data,
            description=form.description.data
        )
        if category:
            flash('Category created successfully!', 'success')
            return redirect(url_for('list_categories'))
        else:
            flash('Failed to create category. Please try again.', 'error')
    
    return render_template('category_form.html', form=form, title='New Category')

@app.route('/category/<category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    if not current_user.is_admin:
        flash('You do not have permission to delete categories.', 'error')
        return redirect(url_for('index'))
    
    category = Category.get(category_id)
    if category is None:
        flash('Category not found.', 'error')
        return redirect(url_for('list_categories'))
    
    if category.delete():
        flash('Category deleted successfully!', 'success')
    else:
        flash('Cannot delete category as it is being used by posts.', 'error')
    
    return redirect(url_for('list_categories'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
