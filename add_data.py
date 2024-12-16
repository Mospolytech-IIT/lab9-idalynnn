from db_session import SessionLocal
from models import User, Post

session = SessionLocal()

user1 = User(username="alice", email="alice@example.com", password="secret1")
user2 = User(username="bob", email="bob@example.com", password="secret2")
user3 = User(username="charlie", email="charlie@example.com", password="secret3")

session.add_all([user1, user2, user3])
session.commit()

post1 = Post(title="First Post", content="Hello World!", user_id=user1.id)
post2 = Post(title="Alice's second post", content="Some content here.", user_id=user1.id)
post3 = Post(title="Bob's first post", content="Post by Bob.", user_id=user2.id)

session.add_all([post1, post2, post3])
session.commit()

session.close()
