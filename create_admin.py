from models import User
from firebase_config import db, auth_instance
import argparse

def create_admin_user(username, email, password):
    try:
        # Check if user already exists
        users_ref = db.collection('users')
        username_query = users_ref.where('username', '==', username).limit(1).get()
        email_query = users_ref.where('email', '==', email).limit(1).get()
        
        if len(list(username_query)):
            print("Error: Username already taken!")
            return
            
        if len(list(email_query)):
            print("Error: Email already registered!")
            return
        
        if len(password) < 6:
            print("Error: Password must be at least 6 characters long!")
            return
        
        # Create admin user
        user = User.create(
            email=email,
            password=password,
            username=username,
            is_admin=True
        )
        
        if user:
            print("\nAdmin user created successfully!")
            print(f"Username: {username}")
            print(f"Email: {email}")
            print("You can now log in with these credentials.")
        else:
            print("Error: Failed to create admin user!")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create an admin user for the CMS')
    parser.add_argument('username', help='Admin username')
    parser.add_argument('email', help='Admin email')
    parser.add_argument('password', help='Admin password')
    
    args = parser.parse_args()
    create_admin_user(args.username, args.email, args.password)
