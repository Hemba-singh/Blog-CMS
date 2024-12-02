from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from forms import LoginForm, RegistrationForm
from firebase_config import auth_instance

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            # Authenticate with Firebase
            user_data = auth_instance.sign_in_with_email_and_password(form.email.data, form.password.data)
            
            # Get user from Firestore
            user = User.get(user_data['localId'])
            if user:
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('blog.index'))
            else:
                flash('Error retrieving user data. Please try again.', 'danger')
        except Exception as e:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create user in Firebase Auth and Firestore
            user = User.create(
                email=form.email.data,
                password=form.password.data,
                username=form.username.data
            )
            
            if user:
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Error creating user. Please try again.', 'danger')
        except Exception as e:
            flash(f'Registration unsuccessful: {str(e)}', 'danger')
    
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    try:
        # Sign out from Firebase
        auth_instance.current_user = None
        logout_user()
        flash('You have been logged out.', 'success')
    except Exception as e:
        flash('Error during logout.', 'danger')
    
    return redirect(url_for('blog.index'))
