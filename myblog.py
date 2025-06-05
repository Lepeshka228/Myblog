import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
from app.models import User, Post

app = create_app()

@app.shell_context_processor        #регистрирует функцию как функцию контекста оболочки. Когда запускается команда flask shell, она будет вызывать эту функцию и регистрировать элементы, возвращаемые ею в сеансе оболочки. 
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Post': Post}
