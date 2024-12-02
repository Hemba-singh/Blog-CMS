from app import app, db
from models import User

def init_db():
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')  # Change this password in production!
            db.session.add(admin)
            db.session.commit()
            print('Admin user created successfully!')
        else:
            print('Admin user already exists.')

if __name__ == '__main__':
    init_db()
