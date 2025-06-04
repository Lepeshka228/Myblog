from app import db, login, app
from time import time
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin       #дефолтный класс, чтоб не писать самому основные методы для логина (реализуются в модели User)
from hashlib import md5     #для аватарки (она получается из хэша эл почты)
import jwt      # JSON Web Token




# Таблица отношений многие ко многим для users
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)    # первичный ключ
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(160))        # информация о пользователе которую он вводит сам на стр своего профиля
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)     #время последнего посещения пользователя

    posts = db.relationship('Post', backref='author', lazy='dynamic')       # связь с табл post один ко многим 

    # самореферентная связь многие ко многим 
    # .c - атрибут для таблиц не определённых как модели
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')


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
            self.followed.append(user)

    # удаление подписчика
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    # информация о подписчике, существует ли он уже (0 если не сущ, 1 если существует)
    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0     # находит всех user.id (правая сторона) для 1 self.id (левая сторона)
    

    # запрос БД для вывода постов пользователей подписчиков
    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)       #отсортированный по времени (раньше здесь был order_by, но как оказалось его надо применять к итоговому рез (union)) и для действительного пользователя (self) список сообщений пользователей на которых он подписан
        own = Post.query.filter_by(user_id=self.id)          # список сообщений самого пользователя 
        return followed.union(own).order_by(Post.timestamp.desc())
    
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
            app.config['SECRET_KEY'], algorithm='HS256')    # utf-8 - специально для приложения (токен в виде послед. байтов)

    # ф-ия проверки токена (декодирования)
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)
    
    # Подсчет подписчиков
    def followers_count(self):
        return self.followers.count()
    # Подсчет подписок
    def following_count(self):
        return self.followed.count()




class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))       # внешний ключ на табл User, поле id

    def __repr__(self):
        return '<Post {}>'.format(self.body)    # метод для вывода поля body



@login.user_loader
def load_user(id):
    return User.query.get(int(id))      # функция загрузчика пользователя 
