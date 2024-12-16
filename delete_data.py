from db_session import SessionLocal
from models import User, Post

session = SessionLocal()

post_to_delete = session.query(Post).filter_by(title="Bob's first post").first()
if post_to_delete:
    session.delete(post_to_delete)
    session.commit()

charlie = session.query(User).filter_by(username='charlie').first()
if charlie:
    for p in charlie.posts:
        session.delete(p)
    session.delete(charlie)
    session.commit()

session.close()
