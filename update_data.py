from db_session import SessionLocal
from models import User, Post

session = SessionLocal()

alice = session.query(User).filter_by(username='alice').first()
alice.email = 'new_alice@example.com'
session.commit()

post_to_update = session.query(Post).filter_by(title='First Post').first()
post_to_update.content = "Updated content!"
session.commit()

session.close()
