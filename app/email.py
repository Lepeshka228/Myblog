# модуль для отправки email

from flask_mail import Message
from app import mail, app
from flask import render_template
from threading import Thread        # поточный процесс

# отправка email в контексте прилложения (иначе Thread не работает)(Вернее не работает Flask-Mail, ему нужен контекст)
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

# ф-ия отправки email
def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


# ф-ия отправки email для сброса пароля
def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[Myoblog] Смена пароля',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt', user=user, token=token),
               html_body=render_template('email/reset_password.html', user=user, token=token))