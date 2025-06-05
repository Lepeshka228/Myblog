from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length
from app.models import User
import sqlalchemy as sa
from app import db


#форма редактирования about_me в профиле
class EditProfileForm(FlaskForm):
    username = StringField('Никнейм', validators=[DataRequired()])  #возможность изменить username
    about_me = TextAreaField('О себе', validators=[Length(min=0, max=160)])
    submit = SubmitField('Подтвердить')     #кнопка подтверждения изменений

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(User.username == username.data))
            if user is not None:
                raise ValidationError('Этот никнейм уже существует.')



# форма написания поста
class PostForm(FlaskForm):
    post = TextAreaField('Напишите что у вас нового', validators=[DataRequired(), Length(min=1, max=240)])
    submit = SubmitField('Отправить')


#не знаю зачем надо, но без неё не работает ссылка на профиль чужого пользователя (эта форма должна быть в user)
class EmptyForm(FlaskForm):
    submit = SubmitField('Подтвердить')