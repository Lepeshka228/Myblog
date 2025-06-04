from flask import render_template
from app import app, db



#обработчик ошибки не найденной страницы
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404



#обработчик ошибки в сеансе БД
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()       # делаем откат при ошибке БД
    return render_template('500.html'), 500