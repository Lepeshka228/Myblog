from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_required
import sqlalchemy as sa
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm
from app.models import User, Post
from app.main import bp



@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required         #страница доступна только вошедшим пользователям 
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Сообщение опубликовано!')
        return redirect(url_for('main.index'))       # переадресация необходима т.к. на request нужен response при POST запросе
        # если пользователь захочет обновить стр, то браузер вернёт последний запрос, который был POST из формы, т.е. форма будет отправляться ещё раз, чтобы этого избежать возвращаем redirect на ту же стр, а это запрос GET

    page = request.args.get('page', 1, type=int)
    #posts = current_user.followed_posts().all()     # все сообщение пользователей, на которых подписан current_user + сообщения самого current_user (см User()); .all() - фактически просто запускает запрос
    posts = db.paginate(current_user.following_posts(), page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)      # .paginate() - разбивка на страницы. error_out=False - при запросе не существующей страницы не будет ошибки

    # ссылки на следующую и предыдущую
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    
    return render_template('index.html', title='Главная', form=form,  posts=posts.items, next_url=next_url, prev_url=prev_url)



@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    
    # ссылки на следующую и предыдущую
    next_url = url_for('mian.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    
    return render_template('index.html', title='Глобальная', posts=posts.items, next_url=next_url, prev_url=prev_url)


#страница профиля пользователя
@bp.route('/user/<username>')      #<username> - динамич компонента URL адреса (т. к. для каждого пользователя своя страница)
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))       # first_or_404 - то же что first, но если совпадений нет возвращает ошибку 404 вместо None
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    
    list_followers = user.list_followers().paginate(
                    page=page, per_page=current_app.config['FOLLOWERS_PER_PAGE'], error_out=False)
    list_following = user.list_following().paginate(
                    page=page, per_page=current_app.config['FOLLOWERS_PER_PAGE'], error_out=False)
    
    # ссылки на следующую и предыдущую
    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None    

    form = EmptyForm()
    
    return render_template('user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url, list_followers=list_followers, list_following=list_following, form=form)



# стрница редактирования профиля
@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)

    #если данные удовлетворяют валидатору изменения записываются в БД
    if form.validate_on_submit():
        current_user.username = form.username.data      # данные из формы копируются в объект пользователя
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Изменения сохранены.')
        return redirect(url_for('main.edit_profile'))
    
    #если данные не удовлетворяют (запрос POST) - выводит ошибку;
    #если запрос GET (тогда нужно ответить предоставив исходную форму шаблона)
    elif request.method == 'GET':
        form.username.data = current_user.username      #заполняем поля формы данными из БД (это гарантирует, что эти поля формы имеют текущие данные, хранящиеся для пользователя)
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Редактировать профиль', form=form)



# функция запоминания времени посещения и заноса его в БД
@bp.before_request     # декоратор для вызова последующей ф-ии (before_request) перед запросом любой функции просмотра 
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


    
# ф-ия подписки
@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == username))
        if user is None:
            flash('Пользователь {} не найден.'.format(username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('Вы не можете подписаться на себя')
            return redirect(url_for('main.user', username=username))
        
        current_user.follow(user)
        db.session.commit()
        flash('Вы подписаны на {}!'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))



# ф-ия отписки
@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == username))
        if user is None:
            flash('Пользователь {} не найден.'.format(username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('Вы не можете отписаться от себя')
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('Вы отписались от {}.'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))