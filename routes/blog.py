from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Post, Category
from forms import PostForm
from datetime import datetime

blog_bp = Blueprint('blog', __name__)

# Cache for category names to avoid multiple database calls
category_cache = {}

def get_category_name(category_id):
    """Helper function to get category name from cache or database"""
    if category_id not in category_cache:
        category = Category.get(category_id)
        category_cache[category_id] = category.name if category else 'Unknown'
    return category_cache[category_id]

@blog_bp.context_processor
def utility_processor():
    """Make helper functions available in templates"""
    return dict(get_category_name=get_category_name)

@blog_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * 10
    try:
        posts = Post.get_all(limit=10, offset=offset, published_only=True)
        return render_template('blog/index.html', posts=posts, page=page)
    except Exception as e:
        flash(f'Error loading posts: {str(e)}', 'error')
        return render_template('blog/index.html', posts=[], page=1)

@blog_bp.route('/post/<post_id>')
def view_post(post_id):
    try:
        post = Post.get(post_id)
        if post is None:
            flash('Post not found.', 'error')
            return redirect(url_for('blog.index'))
        
        if not post.is_published and (not current_user.is_authenticated or 
            (current_user.id != post.author_id and not current_user.is_admin)):
            flash('This post is not published.', 'error')
            return redirect(url_for('blog.index'))
        
        return render_template('blog/post.html', post=post)
    except Exception as e:
        flash(f'Error loading post: {str(e)}', 'error')
        return redirect(url_for('blog.index'))

@blog_bp.route('/category/<category_id>')
def category_posts(category_id):
    try:
        category = Category.get(category_id)
        if category is None:
            flash('Category not found.', 'error')
            return redirect(url_for('blog.index'))
        
        page = request.args.get('page', 1, type=int)
        offset = (page - 1) * 10
        posts = Post.get_by_category(category_id, limit=10, offset=offset, published_only=True)
        
        return render_template('blog/category_posts.html', 
                             category=category, 
                             posts=posts,
                             page=page)
    except Exception as e:
        flash(f'Error loading category posts: {str(e)}', 'error')
        return redirect(url_for('blog.index'))

@blog_bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def create_post():
    # Redirect to admin create post route
    if current_user.is_admin:
        return redirect(url_for('admin.create_post'))
    else:
        flash('You do not have permission to create posts.', 'danger')
        return redirect(url_for('blog.index'))

@blog_bp.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.get(post_id)
    
    # Ensure only the author can edit the post
    if post.author_id != current_user.id:
        flash('You do not have permission to edit this post.', 'danger')
        return redirect(url_for('blog.view_post', post_id=post.id))
    
    form = PostForm(obj=post)
    if form.validate_on_submit():
        try:
            post.update(
                title=form.title.data,
                content=form.content.data,
                categories=form.categories.data,
                is_published=form.is_published.data,
                excerpt=form.excerpt.data,
                meta_description=form.meta_description.data
            )
            
            flash('Your post has been updated!', 'success')
            return redirect(url_for('blog.view_post', post_id=post.id))
        except Exception as e:
            flash(f'Error updating post: {str(e)}', 'error')
    
    return render_template('blog/post_form.html', form=form, title='Update Post')

@blog_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.get(post_id)
    
    # Ensure only the author can delete the post
    if post.author_id != current_user.id:
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('blog.view_post', post_id=post.id))
    
    try:
        post.delete()
        flash('Your post has been deleted!', 'success')
        return redirect(url_for('blog.index'))
    except Exception as e:
        flash(f'Error deleting post: {str(e)}', 'error')
