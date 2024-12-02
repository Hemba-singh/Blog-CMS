from firebase_config import db, auth_instance, storage_instance
from models import User, Post, Category
from datetime import datetime
import sys

def test_firebase_connection():
    print("Testing Firebase connection...")
    try:
        # Test Firestore connection
        collections = db.collections()
        print("[OK] Successfully connected to Firestore")
        print("Available collections:", [col.id for col in collections])
        return True
    except Exception as e:
        print("[ERROR] Failed to connect to Firebase:", str(e))
        return False

def test_create_post():
    print("\nTesting post creation...")
    try:
        post = Post.create(
            title="Test Post",
            content="This is a test post content with markdown support.\n\n## Heading 2\n\nSome more content.",
            author_id="test_author",
            categories=["test"],
            is_published=True,
            excerpt="This is a test excerpt",
            meta_description="Test post meta description"
        )
        if post:
            print("[OK] Successfully created post")
            print(f"Post ID: {post.id}")
            print(f"Post Slug: {post.slug}")
            return post
        else:
            print("[ERROR] Failed to create post")
            return None
    except Exception as e:
        print("[ERROR] Error creating post:", str(e))
        return None

def test_get_post(post):
    print("\nTesting post retrieval...")
    try:
        retrieved_post = Post.get(post.id)
        if retrieved_post:
            print("[OK] Successfully retrieved post")
            print(f"Title: {retrieved_post.title}")
            print(f"Content: {retrieved_post.content[:50]}...")
            return True
        else:
            print("[ERROR] Failed to retrieve post")
            return False
    except Exception as e:
        print("[ERROR] Error retrieving post:", str(e))
        return False

def test_update_post(post):
    print("\nTesting post update...")
    try:
        success = post.update(
            title="Updated Test Post",
            content="This is updated content",
            meta_description="Updated meta description"
        )
        if success:
            print("[OK] Successfully updated post")
            # Verify the update
            updated_post = Post.get(post.id)
            print(f"New Title: {updated_post.title}")
            return True
        else:
            print("[ERROR] Failed to update post")
            return False
    except Exception as e:
        print("[ERROR] Error updating post:", str(e))
        return False

def test_get_all_posts():
    print("\nTesting get all posts...")
    try:
        posts = Post.get_all(limit=5)
        print(f"[OK] Successfully retrieved {len(posts)} posts")
        for post in posts:
            print(f"- {post.title} ({post.created_at})")
        return True
    except Exception as e:
        print("[ERROR] Error retrieving posts:", str(e))
        return False

def test_delete_post(post):
    print("\nTesting post deletion...")
    try:
        if post.delete():
            print("[OK] Successfully deleted post")
            # Verify deletion
            deleted_post = Post.get(post.id)
            if deleted_post is None:
                print("[OK] Verified post deletion")
                return True
            else:
                print("[ERROR] Post still exists after deletion")
                return False
        else:
            print("[ERROR] Failed to delete post")
            return False
    except Exception as e:
        print("[ERROR] Error deleting post:", str(e))
        return False

def main():
    print("Starting Firebase integration tests...\n")
    
    # Test 1: Firebase Connection
    if not test_firebase_connection():
        print("\n[ERROR] Firebase connection test failed. Stopping tests.")
        sys.exit(1)
    
    # Test 2: Create Post
    post = test_create_post()
    if not post:
        print("\n[ERROR] Post creation test failed. Stopping tests.")
        sys.exit(1)
    
    # Test 3: Get Post
    if not test_get_post(post):
        print("\n[ERROR] Post retrieval test failed. Stopping tests.")
        sys.exit(1)
    
    # Test 4: Update Post
    if not test_update_post(post):
        print("\n[ERROR] Post update test failed. Stopping tests.")
        sys.exit(1)
    
    # Test 5: Get All Posts
    if not test_get_all_posts():
        print("\n[ERROR] Get all posts test failed. Stopping tests.")
        sys.exit(1)
    
    # Test 6: Delete Post
    if not test_delete_post(post):
        print("\n[ERROR] Post deletion test failed.")
        sys.exit(1)
    
    print("\n[SUCCESS] All tests completed successfully!")

if __name__ == "__main__":
    main()
