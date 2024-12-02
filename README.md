# Blog Content Management System

## Overview
This is a full-featured Blog Content Management System built with Flask, allowing users to create, edit, and manage blog posts.

## Features
- User Authentication
- Create, Read, Update, Delete (CRUD) Blog Posts
- Rich Text Editing
- Image Upload
- Draft and Published Post Management

## Setup Instructions

1. Clone the repository
2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create a `.env` file with:
```
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///blog.db
```

5. Initialize the database
```bash
python init_db.py
```

6. Run the application
```bash
flask run
```

## Technologies Used
- Flask
- SQLAlchemy
- Flask-Login
- Markdown
- Bootstrap (for frontend)

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.
