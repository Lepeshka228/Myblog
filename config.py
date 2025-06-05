import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'the_most_secret_key_you_have_ever_seen'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')      # местоположение БД
    SQLALCHEMY_TRACK_MODIFICATIONS = False      # отключение функции оповещения приложения об изменениях БД

    #данные сервера эл почты (для отправки ошибок)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['romanovsasa26@gmail.com']

    POSTS_PER_PAGE = 10      # кол-во постов при разбиении страниц
    FOLLOWERS_PER_PAGE = 20     # кол-во подписчиков при разбиении страниц


#---------------------------------------------------------------------------
class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Тестовая БД в памяти
    TESTING = True
#---------------------------------------------------------------------------
