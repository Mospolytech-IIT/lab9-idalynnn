from db_session import SessionLocal
from models import User, Post

session = SessionLocal()

users = session.query(User).all()
for user in users:
    print(user.id, user.username, user.email)

posts = session.query(Post).all()
for post in posts:
    print(post.id, post.title, post.content, post.user.username)

alice = session.query(User).filter_by(username='alice').first()
alice_posts = session.query(Post).filter_by(user_id=alice.id).all()
for post in alice_posts:
    print(post.id, post.title)

session.close()
