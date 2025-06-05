from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User
from app import db
import sqlalchemy as sa



#форма входа
class LoginForm(FlaskForm):
    username = StringField('Никнейм', validators=[DataRequired()])     # валидатор проверяет поведение, DataRequired проверяет что поле не пустое
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить')   # кнопка
    submit = SubmitField('Войти')     # кнопка подтверждения 



#форма регистрации
class RegistrationForm(FlaskForm):
    username = StringField('Никнейм', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField(
        'Повторить пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Регистрация')

    #проверяем не существует ли пользователя с таким именем 
    #Расширение WTForms будет считать все созданные мною методы начинающиеся с validate_... дополнением к своим стандартным
    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username==username.data))
        if user is not None:
            raise ValidationError('Такой никнейм уже зарегистрирован.')   #если совпадение с результатом из БД

    #проверяем не существует ли пользователя с таким email
    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Такой email уже зарегистрирован.')


# форма запроса сброса пароля
class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Подтвердить сброс пароля')


# форма сброса пароля
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Подтвердить смену пароля')