# модуль для отправки email

from flask_mail import Message
from app import mail
from flask import current_app
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
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
