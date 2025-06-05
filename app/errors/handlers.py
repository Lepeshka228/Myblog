from flask import render_template
from app import db
from app.errors import bp


#обработчик ошибки не найденной страницы
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


#обработчик ошибки в сеансе БД
@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()       # делаем откат при ошибке БД
    return render_template('errors/500.html'), 500