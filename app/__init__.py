# -*- coding: utf-8 -*-

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment     # расширение для конвертации времени, работает только вместе с moment.js

import logging      # пакет python для ведения журналов
from logging.handlers import SMTPHandler, RotatingFileHandler
import os

# используется только в тестах; экземпляр приложения создаётся как глобальная переменная, с функцией потом разберёмся
#------------------------------------------------
def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)

    return app
#------------------------------------------------

app = Flask(__name__)   #экземпляр приложения 
app.config.from_object(Config)  #метод для чтения и применения конфигурации 

db = SQLAlchemy(app)        # БД 
migrate = Migrate(app, db)      # механизм миграции

login = LoginManager(app)
login.login_view = 'login'  #функция просмотра login (расширению Flask-Login надо указывать специально, иначе он не понимает)
login.login_message = "Пожалуйста, войдите, чтобы открыть эту страницу."    # замена дефолтной надписи (Flask-Login) при сработавшем @login_required

mail = Mail(app)        # экземпляр расштрения для отправки почты

bootstrap = Bootstrap(app)      # экземпляр bootstrap

moment = Moment(app)


# экземпляр SMTPHandler (только если приложение не в режиме отладки)
if not app.debug:

    # на почту
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Myblog Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)     # собственно экземпляр

    # в файл
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/myoblog.log', maxBytes=10240, backupCount=10)      #специальный класс для записи журнала
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Myblog startup')


from app import routes, models, errors
