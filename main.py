# main.py
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from db_session import SessionLocal, engine
from models import Base, User, Post
from pydantic import BaseModel, ConfigDict
from typing import List
from fastapi.templating import Jinja2Templates
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Монтирование статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

# Создание таблиц при запуске приложения (если ещё не созданы)
Base.metadata.create_all(bind=engine)

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic модели
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

    model_config = ConfigDict(from_attributes=True)

class UserOut(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class PostCreate(BaseModel):
    title: str
    content: str
    user_id: int

    model_config = ConfigDict(from_attributes=True)

class PostOut(BaseModel):
    id: int
    title: str
    content: str
    user_id: int
    user: UserOut

    model_config = ConfigDict(from_attributes=True)

# Маршрут для корневой страницы
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("base.html", {"request": request, "title": "Главная"})

# CRUD для пользователей

# Список пользователей
@app.get("/users/", response_class=HTMLResponse)
def read_users(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users, "title": "Пользователи"})

# Форма для создания пользователя
@app.get("/users/create/", response_class=HTMLResponse)
def create_user_form(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("create_user.html", {"request": request, "title": "Создать пользователя"})

# Обработка создания пользователя
@app.post("/users/create/", response_class=HTMLResponse)
def create_user(request: Request,
                username: str = Form(...),
                email: str = Form(...),
                password: str = Form(...),
                db: Session = Depends(get_db)):
    logger.info(f"Создание пользователя: {username}")
    # Проверка уникальности username и email
    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        error_message = "Пользователь с таким именем или email уже существует."
        return templates.TemplateResponse("create_user.html", {"request": request, "error": error_message, "title": "Создать пользователя"})
    
    new_user = User(username=username, email=email, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"Пользователь создан с id: {new_user.id}")
    return RedirectResponse(url="/users/", status_code=303)

# Форма для редактирования пользователя
@app.get("/users/edit/{user_id}/", response_class=HTMLResponse)
def edit_user_form(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("edit_user.html", {"request": request, "user": user, "title": "Редактировать пользователя"})

# Обработка редактирования пользователя
@app.post("/users/edit/{user_id}/", response_class=HTMLResponse)
def edit_user(request: Request,
              user_id: int,
              username: str = Form(...),
              email: str = Form(...),
              password: str = Form(None),
              db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверка уникальности username и email
    existing_user = db.query(User).filter(((User.username == username) | (User.email == email)) & (User.id != user_id)).first()
    if existing_user:
        error_message = "Пользователь с таким именем или email уже существует."
        return templates.TemplateResponse("edit_user.html", {"request": request, "user": user, "error": error_message, "title": "Редактировать пользователя"})
    
    user.username = username
    user.email = email
    if password:
        user.password = password
    db.commit()
    db.refresh(user)
    logger.info(f"Пользователь с id {user_id} обновлён")
    return RedirectResponse(url="/users/", status_code=303)

# Удаление пользователя
@app.post("/users/delete/{user_id}/", response_class=HTMLResponse)
def delete_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Удаляем посты пользователя
    posts_deleted = db.query(Post).filter(Post.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    logger.info(f"Пользователь с id {user_id} и его {posts_deleted} постов удалены")
    return RedirectResponse(url="/users/", status_code=303)

# CRUD для постов

# Список постов
@app.get("/posts/", response_class=HTMLResponse)
def read_posts(request: Request, db: Session = Depends(get_db)):
    posts = db.query(Post).all()
    return templates.TemplateResponse("posts.html", {"request": request, "posts": posts, "title": "Посты"})

# Форма для создания поста
@app.get("/posts/create/", response_class=HTMLResponse)
def create_post_form(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("create_post.html", {"request": request, "users": users, "title": "Создать пост"})

# Обработка создания поста
@app.post("/posts/create/", response_class=HTMLResponse)
def create_post(request: Request,
                title: str = Form(...),
                content: str = Form(...),
                user_id: int = Form(...),
                db: Session = Depends(get_db)):
    logger.info(f"Создание поста: {title} для пользователя с id {user_id}")
    # Проверка существования пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        error_message = "Автор с таким ID не существует."
        users = db.query(User).all()
        return templates.TemplateResponse("create_post.html", {"request": request, "users": users, "error": error_message, "title": "Создать пост"})
    
    new_post = Post(title=title, content=content, user_id=user_id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    logger.info(f"Пост создан с id: {new_post.id}")
    return RedirectResponse(url="/posts/", status_code=303)

# Форма для редактирования поста
@app.get("/posts/edit/{post_id}/", response_class=HTMLResponse)
def edit_post_form(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    users = db.query(User).all()
    return templates.TemplateResponse("edit_post.html", {"request": request, "post": post, "users": users, "title": "Редактировать пост"})

# Обработка редактирования поста
@app.post("/posts/edit/{post_id}/", response_class=HTMLResponse)
def edit_post(request: Request,
              post_id: int,
              title: str = Form(...),
              content: str = Form(...),
              user_id: int = Form(...),
              db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Проверка существования пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        error_message = "Автор с таким ID не существует."
        users = db.query(User).all()
        return templates.TemplateResponse("edit_post.html", {"request": request, "post": post, "users": users, "error": error_message, "title": "Редактировать пост"})
    
    post.title = title
    post.content = content
    post.user_id = user_id
    db.commit()
    db.refresh(post)
    logger.info(f"Пост с id {post_id} обновлён")
    return RedirectResponse(url="/posts/", status_code=303)

@app.post("/posts/delete/{post_id}/", response_class=HTMLResponse)
def delete_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    logger.info(f"Пост с id {post_id} удалён")
    return RedirectResponse(url="/posts/", status_code=303)
