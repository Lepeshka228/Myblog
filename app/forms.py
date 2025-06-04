from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User



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
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Такой никнейм уже зарегистрирован.')   #если совпадение с результатом из БД

    #проверяем не существует ли пользователя с таким email
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Такой email уже зарегистрирован.')
        


#форма редактирования about_me в профиле
class EditProfileForm(FlaskForm):
    username = StringField('Никнейм', validators=[DataRequired()])  #возможность изменить username
    about_me = TextAreaField('О себе', validators=[Length(min=0, max=160)])
    submit = SubmitField('Подтвердить')     #кнопка подтверждения изменений

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Этот никнейм уже существует.')



# форма написания поста
class PostForm(FlaskForm):
    post = TextAreaField('Напишите что у вас нового', validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Отправить')


# форма запроса сброса пароля
class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Подтвердить сброс пароля')


# форма сброса пароля
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Подтвердить смену пароля')


#не знаю зачем надо, но без неё не работает ссылка на профиль чужого пользователя (эта форма должна быть в user)
class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')