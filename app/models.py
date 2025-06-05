from app import db, login
from flask import current_app
from time import time
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin       #дефолтный класс, чтоб не писать самому основные методы для логина (реализуются в модели User)
from hashlib import md5     #для аватарки (она получается из хэша эл почты)
import jwt      # JSON Web Token
import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional




# Таблица отношений многие ко многим для users
followers = sa.Table('followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True)
)



class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)     # первичный ключ
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author')

    # самореферентная связь многие ко многим 
    # .c - атрибут для таблиц не определённых как модели

    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)       #метод установки пароля
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)        #метод проверки пароля


    def __repr__(self):
        return '<User {}>'.format(self.username)        #метод для вывода информации о username (просто полезно для отладки)
    
    #генерирует URL адрес аватар для пользователя
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=monsterid&s={}'.format(digest, size)
    
    # добавление подписчика
    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    # удаление подписчика
    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    # информация о подписчике, существует ли он уже (0 если не сущ, 1 если существует)
    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None     # находит всех user.id (правая сторона) для 1 self.id (левая сторона)
    
    # запрос БД для вывода постов пользователей подписчиков
    def following_posts(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id,
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )
    
    # список подписчиков
    def list_followers(self):
        return User.query.join(followers, (followers.c.follower_id == User.id)).filter(followers.c.followed_id == self.id)

    # список подписок
    def list_following(self):
        return User.query.join(followers, (followers.c.followed_id == User.id)).filter(followers.c.follower_id == self.id) 
    

    # ф-ия генерации токена для сброса пароля (время жизни 600 сек)
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')    # utf-8 - специально для приложения (токен в виде послед. байтов)

    # ф-ия проверки токена (декодирования)
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except Exception:
            return
        return db.session.get(User, id)
    
    # Подсчет подписчиков
    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(self.followers.select().subquery())
        return db.session.scalar(query)
    # Подсчет подписок
    def following_count(self):
        query = sa.select(sa.func.count()).select_from(self.following.select().subquery())
        return db.session.scalar(query)




class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)       # внешний ключ на табл User, поле id
    author: so.Mapped[User] = so.relationship(back_populates='posts')

    def __repr__(self):
        return '<Post {}>'.format(self.body)    # метод для вывода поля body



@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))      # функция загрузчика пользователя 
