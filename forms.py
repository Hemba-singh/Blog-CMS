from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectMultipleField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, URL, Optional
from models import User, Category
from firebase_config import db

class LoginForm(FlaskForm):
    email = StringField('Email', 
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Enter your email"}
    )
    password = PasswordField('Password', 
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter your password"}
    )
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
        validators=[DataRequired(), Length(min=3, max=50)],
        render_kw={"placeholder": "Choose a username"}
    )
    email = StringField('Email', 
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Enter your email"}
    )
    password = PasswordField('Password', 
        validators=[DataRequired(), Length(min=6)],
        render_kw={"placeholder": "Create a password"}
    )
    confirm_password = PasswordField('Confirm Password', 
        validators=[DataRequired(), EqualTo('password')],
        render_kw={"placeholder": "Confirm your password"}
    )
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        # Check if username exists in Firestore
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username.data).limit(1).get()
        if len(list(query)):
            raise ValidationError('That username is already taken. Please choose another.')

    def validate_email(self, email):
        # Check if email exists in Firestore
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email.data).limit(1).get()
        if len(list(query)):
            raise ValidationError('That email is already registered. Please use a different email.')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    image_url = StringField('Image URL', validators=[Optional(), URL()])
    featured_image = FileField('Featured Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    categories = SelectMultipleField('Categories', validators=[Optional()], coerce=str)
    tags = StringField('Tags (comma separated)', validators=[Optional()])
    is_published = BooleanField('Publish')
    excerpt = TextAreaField('Excerpt', validators=[Optional(), Length(max=500)])
    meta_description = TextAreaField('Meta Description', validators=[Optional(), Length(max=160)])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        # Dynamically populate categories from Firebase
        categories = Category.get_all()
        self.categories.choices = [(c.id, c.name) for c in categories]

    def get_tags_list(self):
        if self.tags.data:
            return [tag.strip() for tag in self.tags.data.split(',') if tag.strip()]
        return []

class CategoryForm(FlaskForm):
    name = StringField('Name', 
        validators=[DataRequired(), Length(max=50)],
        render_kw={"placeholder": "Enter category name"}
    )
    description = TextAreaField('Description', 
        validators=[Length(max=200)],
        render_kw={"placeholder": "Optional category description"}
    )
    submit = SubmitField('Create Category')
