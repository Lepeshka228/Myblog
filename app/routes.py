from app import app, db
from flask import render_template, flash, redirect, url_for, request
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm, EmptyForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post
from werkzeug.urls import url_parse
from datetime import datetime
from app.email import send_password_reset_email



@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required         #страница доступна только вошедшим пользователям 
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Сообщение опубликовано!')
        return redirect(url_for('index'))       # переадресация необходима т.к. на request нужен response при POST запросе
        # если пользователь захочет обновить стр, то браузер вернёт последний запрос, который был POST из формы, т.е. форма будет отправляться ещё раз, чтобы этого избежать возвращаем redirect на ту же стр, а это запрос GET

    page = request.args.get('page', 1, type=int)
    #posts = current_user.followed_posts().all()     # все сообщение пользователей, на которых подписан current_user + сообщения самого current_user (см User()); .all() - фактически просто запускает запрос
    posts = current_user.followed_posts().paginate(
            page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)      # .paginate() - разбивка на страницы. error_out=False - при запросе не существующей страницы не будет ошибки

    # ссылки на следующую и предыдущую
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    
    return render_template('index.html', title='Главная', form=form,  posts=posts.items, next_url=next_url, prev_url=prev_url)



@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
            page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    
    # ссылки на следующую и предыдущую
    next_url = url_for('explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) if posts.has_prev else None
    
    return render_template('index.html', title='Глобальная', posts=posts.items, next_url=next_url, prev_url=prev_url)



# страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    #проверяем не хочет ли уже зарегестрированный пользователь снова попасть на стр регистрации
    #переменная current_user - объект пользователя
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()    # загрузка пользователя из БД. username приходит из формы и сравнивается с username из БД
        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя пользователя или пароль')
            return redirect(url_for('login'))       #проверяет соответствие username и хэш пароля
        login_user(user, remember=form.remember_me.data)    #если порядок, то функция login_user регистрирует пользователя. теперь для пользователя установлена одна переменная current_user для всех стр.

        next_page = request.args.get('next')    #содержимое строки запроса (для аргумента next)
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')    #возвращает на индекс если не установлен next или next подозрительный (выходит за пределы приложения(проверка netloc))
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))       #функция выхода



#страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))       #для тех кто уже в сеансе регистрация не нужна
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)     #переменная содержит username и email из формы
        user.set_password(form.password.data)       #установка пароля из формы
        db.session.add(user)    #добавляем пользователя в БД
        db.session.commit()     #сохраняем данные
        flash('Поздравляем, вы зарегистрированы!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)



#страница профиля пользователя
@app.route('/user/<username>')      #<username> - динамич компонента URL адреса (т. к. для каждого пользователя своя страница)
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()       # first_or_404 - то же что first, но если совпадений нет возвращает ошибку 404 вместо None
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
            page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    
    list_followers = user.list_followers().paginate(
                    page=page, per_page=app.config['FOLLOWERS_PER_PAGE'], error_out=False)
    list_following = user.list_following().paginate(
                    page=page, per_page=app.config['FOLLOWERS_PER_PAGE'], error_out=False)
    
    # ссылки на следующую и предыдущую
    next_url = url_for('user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) if posts.has_prev else None    

    form = EmptyForm()
    
    return render_template('user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url, list_followers=list_followers, list_following=list_following, form=form)



# стрница редактирования профиля
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)

    #если данные удовлетворяют валидатору изменения записываются в БД
    if form.validate_on_submit():
        current_user.username = form.username.data      # данные из формы копируются в объект пользователя
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Изменения сохранены.')
        return redirect(url_for('edit_profile'))
    
    #если данные не удовлетворяют (запрос POST) - выводит ошибку;
    #если запрос GET (тогда нужно ответить предоставив исходную форму шаблона)
    elif request.method == 'GET':
        form.username.data = current_user.username      #заполняем поля формы данными из БД (это гарантирует, что эти поля формы имеют текущие данные, хранящиеся для пользователя)
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Edit Profile', form=form)



# функция запоминания времени посещения и заноса его в БД
@app.before_request     # декоратор для вызова последующей ф-ии (before_request) перед запросом любой функции просмотра 
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


    
# ф-ия подписки
@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Пользователь {} не найден.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('Вы не можете подписаться на себя')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('Вы подписаны на {}!'.format(username))
    return redirect(url_for('user', username=username))



# ф-ия отписки
@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Пользователь {} не найден.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('Вы не можете отписаться от себя')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('Вы отписались от {}.'.format(username))
    return redirect(url_for('user', username=username))



# ф-ия запроса сброса пароля
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Проверьте свой email для продолжения операции')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Сброс пароля', form=form)


# ф-ия сброса пароля
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))   # если токен не действителен
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Пароль изменен')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

