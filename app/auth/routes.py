from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlsplit
import sqlalchemy as sa
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from app.auth.email import send_password_reset_email




# страница входа
@bp.route('/login', methods=['GET', 'POST'])
def login():
    #проверяем не хочет ли уже зарегестрированный пользователь снова попасть на стр регистрации
    #переменная current_user - объект пользователя
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()

    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))    # загрузка пользователя из БД. username приходит из формы и сравнивается с username из БД
        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя пользователя или пароль')
            return redirect(url_for('auth.login'))       #проверяет соответствие username и хэш пароля
        login_user(user, remember=form.remember_me.data)    #если порядок, то функция login_user регистрирует пользователя. теперь для пользователя установлена одна переменная current_user для всех стр.

        next_page = request.args.get('next')    #содержимое строки запроса (для аргумента next)
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.index')    #возвращает на индекс если не установлен next или next подозрительный (выходит за пределы приложения(проверка netloc))
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Вход', form=form)



@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))       #функция выхода



#страница регистрации
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))       #для тех кто уже в сеансе регистрация не нужна
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)     #переменная содержит username и email из формы
        user.set_password(form.password.data)       #установка пароля из формы
        db.session.add(user)    #добавляем пользователя в БД
        db.session.commit()     #сохраняем данные
        flash('Поздравляем, вы зарегистрированы!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Регистрация', form=form)


# ф-ия запроса сброса пароля
@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash('Проверьте свой email для продолжения операции')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Сброс пароля', form=form)


# ф-ия сброса пароля
@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))   # если токен не действителен
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Пароль изменен')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
