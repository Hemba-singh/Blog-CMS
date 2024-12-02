from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from models import Post, Category, User
from forms import PostForm, CategoryForm
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
from firebase_admin import storage, firestore

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Initialize Firestore client using Firebase Admin
db = firestore.client()

@admin_bp.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin dashboard.', 'danger')
        return redirect(url_for('blog.index'))
    
    # Get statistics from Firebase
    try:
        # Get total posts
        posts = Post.get_all(limit=1000)  # Adjust limit as needed
        total_posts = len(posts)
        published_posts = len([p for p in posts if p.is_published])
        
        return render_template('admin/dashboard.html', 
                           total_posts=total_posts, 
                           published_posts=published_posts)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return render_template('admin/dashboard.html', 
                           total_posts=0, 
                           published_posts=0)

@admin_bp.route('/posts')
@login_required
def list_posts():
    if not current_user.is_admin:
        flash('You do not have permission to manage posts.', 'danger')
        return redirect(url_for('blog.index'))
    
    try:
        posts = Post.get_all(limit=50, published_only=False)  # Get both published and draft posts
        return render_template('admin/posts/list.html', posts=posts)
    except Exception as e:
        flash(f'Error loading posts: {str(e)}', 'danger')
        return render_template('admin/posts/list.html', posts=[])

@admin_bp.route('/posts/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if not current_user.is_admin:
        flash('You do not have permission to create posts.', 'danger')
        return redirect(url_for('blog.index'))
    
    form = PostForm()
    
    if form.validate_on_submit():
        try:
            # Get action from form
            action = request.form.get('action', 'save_draft')
            is_published = True if action == 'publish' else False
            
            # Create post with featured image if provided
            post = Post.create(
                title=form.title.data,
                content=form.content.data,
                author=current_user,
                categories=form.categories.data,
                is_published=is_published,
                excerpt=form.excerpt.data,
                featured_image=form.featured_image.data if form.featured_image.data else None,
                meta_description=form.meta_description.data
            )
            
            if post:
                action_text = 'published' if is_published else 'saved as draft'
                flash(f'Post {action_text} successfully!', 'success')
                return redirect(url_for('admin.edit_post', post_id=post.id))
            else:
                flash('Error creating post.', 'danger')
        except Exception as e:
            flash(f'Error creating post: {str(e)}', 'danger')
    
    return render_template('admin/posts/editor.html', form=form)

@admin_bp.route('/posts/<post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    if not current_user.is_admin:
        flash('You do not have permission to edit posts.', 'danger')
        return redirect(url_for('blog.index'))
    
    post = Post.get(post_id)
    if not post:
        flash('Post not found.', 'danger')
        return redirect(url_for('admin.list_posts'))
    
    form = PostForm(obj=post)
    
    if form.validate_on_submit():
        try:
            # Get action from form
            action = request.form.get('action', 'save_draft')
            is_published = True if action == 'publish' else False
            
            # Update post
            success = post.update(
                title=form.title.data,
                content=form.content.data,
                categories=form.categories.data,
                is_published=is_published,
                excerpt=form.excerpt.data,
                featured_image=form.featured_image.data if form.featured_image.data else None,
                meta_description=form.meta_description.data
            )
            
            if success:
                action_text = 'published' if is_published else 'saved as draft'
                flash(f'Post {action_text} successfully!', 'success')
                return redirect(url_for('admin.edit_post', post_id=post.id))
            else:
                flash('Error updating post.', 'danger')
        except Exception as e:
            flash(f'Error updating post: {str(e)}', 'danger')
    
    return render_template('admin/posts/editor.html', form=form, post=post)

@admin_bp.route('/posts/<post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    if not current_user.is_admin:
        flash('You do not have permission to delete posts.', 'danger')
        return redirect(url_for('blog.index'))
    
    post = Post.get(post_id)
    if not post:
        flash('Post not found.', 'danger')
        return redirect(url_for('admin.list_posts'))
    
    try:
        if post.delete():
            flash('Post deleted successfully!', 'success')
        else:
            flash('Error deleting post.', 'danger')
    except Exception as e:
        flash(f'Error deleting post: {str(e)}', 'danger')
    
    return redirect(url_for('admin.list_posts'))

@admin_bp.route('/upload/image', methods=['POST'])
@login_required
def upload_image():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        filename = f"{timestamp}-{filename}"
        
        # Upload to Firestore
        doc_ref = db.collection('images').document(filename)
        doc_ref.set({
            'filename': filename,
            'content_type': file.content_type,
            'data': file.read()
        })
        
        return jsonify({
            'location': f'/admin/media/{filename}'  # TinyMCE expects the URL in the 'location' field
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/posts/<post_id>/preview')
@login_required
def preview_post(post_id):
    if not current_user.is_admin:
        flash('You do not have permission to preview posts.', 'danger')
        return redirect(url_for('blog.index'))
    
    post = Post.get(post_id)
    if not post:
        flash('Post not found.', 'danger')
        return redirect(url_for('admin.list_posts'))
    
    return render_template('blog/post.html', post=post, preview=True)

@admin_bp.route('/categories')
@login_required
def list_categories():
    if not current_user.is_admin:
        flash('You do not have permission to manage categories.', 'danger')
        return redirect(url_for('blog.index'))
    
    try:
        categories = Category.get_all()
        return render_template('admin/categories/list.html', categories=categories)
    except Exception as e:
        flash(f'Error loading categories: {str(e)}', 'danger')
        return render_template('admin/categories/list.html', categories=[])

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    if not current_user.is_admin:
        flash('You do not have permission to create categories.', 'danger')
        return redirect(url_for('blog.index'))
    
    form = CategoryForm()
    
    if form.validate_on_submit():
        try:
            category = Category.create(
                name=form.name.data,
                description=form.description.data
            )
            
            if category:
                flash('Category created successfully!', 'success')
                return redirect(url_for('admin.list_categories'))
            else:
                flash('Error creating category.', 'danger')
        except Exception as e:
            flash(f'Error creating category: {str(e)}', 'danger')
    
    return render_template('admin/categories/editor.html', form=form)

@admin_bp.route('/categories/<category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    if not current_user.is_admin:
        flash('You do not have permission to delete categories.', 'danger')
        return redirect(url_for('blog.index'))
    
    try:
        # Get the category
        categories = db.collection('categories').where('id', '==', category_id).limit(1).get()
        if not categories:
            flash('Category not found.', 'danger')
            return redirect(url_for('admin.list_categories'))
        
        category_doc = categories[0]
        category = Category(
            id=category_doc.id,
            name=category_doc.get('name'),
            description=category_doc.get('description')
        )
        
        if category.delete():
            flash('Category deleted successfully!', 'success')
        else:
            flash('Cannot delete category: it is being used by one or more posts.', 'danger')
    except Exception as e:
        flash(f'Error deleting category: {str(e)}', 'danger')
    
    return redirect(url_for('admin.list_categories'))

@admin_bp.route('/media')
@login_required
def media():
    if not current_user.is_admin:
        flash('You do not have permission to manage media.', 'danger')
        return redirect(url_for('blog.index'))
    
    try:
        # List all files in the media bucket
        images_ref = db.collection('images')
        images = images_ref.get()
        
        # Organize files by type
        media_files = []
        for image in images:
            media_files.append({
                'name': image.id,
                'url': f'/admin/media/{image.id}',
                'size': len(image.get('data')),
                'updated': image.update_time,
                'content_type': image.get('content_type')
            })
        
        return render_template('admin/media/list.html', media_files=media_files)
    except Exception as e:
        flash(f'Error loading media files: {str(e)}', 'danger')
        return render_template('admin/media/list.html', media_files=[])

@admin_bp.route('/media/<path:filename>', methods=['DELETE'])
@login_required
def delete_media(filename):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    try:
        # Delete file from Firestore
        doc_ref = db.collection('images').document(filename)
        doc_ref.delete()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('You do not have permission to manage users.', 'danger')
        return redirect(url_for('blog.index'))
    
    try:
        # Get all users from Firestore
        users_ref = db.collection('users')
        users_docs = users_ref.get()
        users = [User(
            uid=doc.id,
            username=doc.get('username'),
            email=doc.get('email'),
            is_admin=doc.get('is_admin', False)
        ) for doc in users_docs]
        
        return render_template('admin/users.html', users=users)
    except Exception as e:
        flash(f'Error loading users: {str(e)}', 'danger')
        return render_template('admin/users.html', users=[])

@admin_bp.route('/users/<user_id>/make-admin', methods=['POST'])
@login_required
def make_admin(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to manage users.', 'danger')
        return redirect(url_for('blog.index'))
    
    try:
        # Update user in Firestore
        user_ref = db.collection('users').document(user_id)
        user_ref.update({'is_admin': True})
        flash('User has been made an admin successfully!', 'success')
    except Exception as e:
        flash(f'Error updating user: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_users'))
