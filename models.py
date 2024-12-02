from datetime import datetime
from flask_login import UserMixin
from firebase_admin import storage, firestore
from firebase_config import db, auth_instance
import uuid
import base64
from werkzeug.utils import secure_filename

class User(UserMixin):
    def __init__(self, uid, username, email, is_admin=False):
        self.id = uid
        self.username = username
        self.email = email
        self.is_admin = is_admin

    @staticmethod
    def get(user_id):
        try:
            user_doc = db.collection('users').document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                return User(
                    uid=user_id,
                    username=user_data.get('username'),
                    email=user_data.get('email'),
                    is_admin=user_data.get('is_admin', False)
                )
        except Exception as e:
            print(f"Error getting user: {e}")
        return None

    @staticmethod
    def create(email, password, username, is_admin=False):
        try:
            # Create user in Firebase Auth
            user = auth_instance.create_user_with_email_and_password(email, password)
            
            # Store additional user data in Firestore
            user_data = {
                'username': username,
                'email': email,
                'is_admin': is_admin,
                'created_at': datetime.utcnow().isoformat()
            }
            db.collection('users').document(user['localId']).set(user_data)
            
            return User(user['localId'], username, email, is_admin)
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

class Post:
    def __init__(self, id, title, content, author, categories=None, is_published=False, 
                 excerpt=None, featured_image=None, meta_description=None, timestamp=None):
        self.id = id
        self.title = title or ''
        self.content = content or ''
        self.author = author
        self.categories = categories or []
        self.is_published = bool(is_published)
        self.excerpt = excerpt or ''
        self.featured_image = featured_image or ''
        self.meta_description = meta_description or ''
        self.timestamp = timestamp
        # Handle timestamp
        if isinstance(timestamp, datetime):
            self.created_at = timestamp
        else:
            self.created_at = datetime.utcnow()

    @staticmethod
    def create(title, content, author, categories=None, is_published=False, 
               excerpt=None, featured_image=None, meta_description=None):
        try:
            post_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            # Handle featured image upload if provided
            featured_image_url = None
            if featured_image:
                try:
                    # Generate a unique filename
                    filename = f"posts/{post_id}/{secure_filename(featured_image.filename)}"
                    
                    # Upload to Firebase Storage
                    bucket = storage.bucket()
                    blob = bucket.blob(filename)
                    blob.upload_from_string(
                        featured_image.read(),
                        content_type=featured_image.content_type
                    )
                    
                    # Make the blob publicly accessible
                    blob.make_public()
                    featured_image_url = blob.public_url
                except Exception as e:
                    print(f"Error uploading image: {e}")
                    # Continue without the image if upload fails
                    pass
            
            post_data = {
                'title': title or '',
                'content': content or '',
                'author': {
                    'id': author.id,
                    'username': author.username,
                    'email': author.email
                } if author else {},
                'categories': categories or [],
                'is_published': bool(is_published),
                'excerpt': excerpt or '',
                'featured_image': featured_image_url or '',
                'meta_description': meta_description or '',
                'timestamp': current_time,
                'created_at': current_time,
                'updated_at': current_time
            }
            
            # Save to Firestore
            db.collection('posts').document(post_id).set(post_data)
            
            return Post(
                id=post_id,
                title=title,
                content=content,
                author=author,
                categories=categories,
                is_published=is_published,
                excerpt=excerpt,
                featured_image=featured_image_url,
                meta_description=meta_description,
                timestamp=current_time
            )
        except Exception as e:
            print(f"Error creating post: {e}")
            return None

    def update(self, title=None, content=None, categories=None, is_published=None, 
               excerpt=None, featured_image=None, meta_description=None):
        try:
            update_data = {}
            if title is not None:
                update_data['title'] = title
                self.title = title
            if content is not None:
                update_data['content'] = content
                self.content = content
            if categories is not None:
                update_data['categories'] = categories
                self.categories = categories
            if is_published is not None:
                update_data['is_published'] = is_published
                self.is_published = is_published
            if excerpt is not None:
                update_data['excerpt'] = excerpt
                self.excerpt = excerpt
            if featured_image is not None:
                # Handle featured image upload if provided
                featured_image_url = None
                if featured_image:
                    # Generate a unique filename
                    filename = f"posts/{self.id}/{secure_filename(featured_image.filename)}"
                    
                    # Upload to Firebase Storage
                    bucket = storage.bucket()
                    blob = bucket.blob(filename)
                    blob.upload_from_string(
                        featured_image.read(),
                        content_type=featured_image.content_type
                    )
                    
                    # Make the blob publicly accessible
                    blob.make_public()
                    featured_image_url = blob.public_url
                update_data['featured_image'] = featured_image_url
                self.featured_image = featured_image_url
            if meta_description is not None:
                update_data['meta_description'] = meta_description
                self.meta_description = meta_description
            
            update_data['timestamp'] = firestore.SERVER_TIMESTAMP
            self.timestamp = firestore.SERVER_TIMESTAMP
            
            db.collection('posts').document(self.id).update(update_data)
            return True
        except Exception as e:
            print(f"Error updating post: {e}")
            return False

    @staticmethod
    def get(post_id):
        try:
            post_doc = db.collection('posts').document(post_id).get()
            if post_doc.exists:
                post_data = post_doc.to_dict()
                
                # Create a User object from author data
                author_data = post_data.get('author', {})
                author = None
                if author_data:
                    author = User(
                        uid=author_data.get('id'),
                        username=author_data.get('username', 'Unknown'),
                        email=author_data.get('email', ''),
                        is_admin=False
                    )
                
                # Convert timestamp to datetime if it exists
                timestamp = post_data.get('timestamp')
                if isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp)
                elif not isinstance(timestamp, datetime):
                    timestamp = datetime.utcnow()
                
                return Post(
                    id=post_id,
                    title=post_data.get('title', ''),
                    content=post_data.get('content', ''),
                    author=author,
                    categories=post_data.get('categories', []),
                    is_published=post_data.get('is_published', False),
                    excerpt=post_data.get('excerpt'),
                    featured_image=post_data.get('featured_image'),
                    meta_description=post_data.get('meta_description'),
                    timestamp=timestamp
                )
        except Exception as e:
            print(f"Error getting post: {e}")
        return None

    @staticmethod
    def get_all(limit=10, offset=0, published_only=False):
        try:
            # Create base query
            query = db.collection('posts')
            
            # Add published filter if requested
            if published_only:
                query = query.where('is_published', '==', True)
            
            # Add ordering by timestamp
            query = query.order_by('timestamp', direction=firestore.Query.DESCENDING)
            
            # Get all documents up to offset + limit
            docs = query.limit(offset + limit).get()
            
            # Skip the first 'offset' documents
            posts = []
            for i, post_doc in enumerate(docs):
                if i < offset:
                    continue
                    
                post_data = post_doc.to_dict()
                
                # Create a User object from author data
                author_data = post_data.get('author', {})
                author = None
                if author_data:
                    author = User(
                        uid=author_data.get('id'),
                        username=author_data.get('username', 'Unknown'),
                        email=author_data.get('email', ''),
                        is_admin=False
                    )
                
                # Convert timestamp to datetime if it exists
                timestamp = post_data.get('timestamp')
                if isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp)
                elif not isinstance(timestamp, datetime):
                    timestamp = datetime.utcnow()
                
                posts.append(Post(
                    id=post_doc.id,
                    title=post_data.get('title', ''),
                    content=post_data.get('content', ''),
                    author=author,
                    categories=post_data.get('categories', []),
                    is_published=post_data.get('is_published', False),
                    excerpt=post_data.get('excerpt'),
                    featured_image=post_data.get('featured_image'),
                    meta_description=post_data.get('meta_description'),
                    timestamp=timestamp
                ))
            return posts
        except Exception as e:
            print(f"Error getting posts: {e}")
            return []

    def delete(self):
        try:
            # Delete the post document
            db.collection('posts').document(self.id).delete()
            return True
        except Exception as e:
            print(f"Error deleting post: {e}")
            return False

class Category:
    def __init__(self, id, name, description=None):
        self.id = id
        self.name = name
        self.description = description

    @staticmethod
    def create(name, description=None):
        try:
            category_id = str(uuid.uuid4())
            category_data = {
                'name': name,
                'description': description
            }
            
            db.collection('categories').document(category_id).set(category_data)
            return Category(category_id, name, description)
        except Exception as e:
            print(f"Error creating category: {e}")
            return None

    @staticmethod
    def get_all():
        try:
            categories = []
            for doc in db.collection('categories').stream():
                category_data = doc.to_dict()
                categories.append(Category(
                    id=doc.id,
                    name=category_data.get('name'),
                    description=category_data.get('description')
                ))
            return categories
        except Exception as e:
            print(f"Error getting categories: {e}")
            return []

    def delete(self):
        try:
            # Check if any posts are using this category
            posts = db.collection('posts').where('categories', 'array_contains', self.id).limit(1).get()
            if len(posts) > 0:
                return False
            
            db.collection('categories').document(self.id).delete()
            return True
        except Exception as e:
            print(f"Error deleting category: {e}")
            return False
