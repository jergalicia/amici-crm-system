from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20))  # 'admin', 'coordinator', 'journalist', 'photographer', 'designer', 'community_manager'
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    profile_photo = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Edition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    publication_date = db.Column(db.Date)
    drive_folder_id = db.Column(db.String(100))
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    status = db.Column(db.String(20), default='planning')  # planning, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    content = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    edition_id = db.Column(db.Integer, db.ForeignKey('edition.id'))
    status = db.Column(db.String(20), default='draft') # draft, review, approved, layout, done
    deadline = db.Column(db.DateTime)
    
    author = db.relationship('User', backref='articles')
    edition = db.relationship('Edition', backref='articles')
    images = db.relationship('ArticleImage', backref='article', lazy='dynamic', cascade='all, delete-orphan')

class ArticleImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    filename = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    code = db.Column(db.String(10), unique=True) # e.g., PA, ES, DO

    users = db.relationship('User', backref='country', lazy='dynamic')
    editions = db.relationship('Edition', backref='country', lazy='dynamic')
    events = db.relationship('Event', backref='country', lazy='dynamic')

class Manual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    target_role = db.Column(db.String(50), nullable=False) # 'all', 'journalist', 'photographer', etc.
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmbassyList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False) # e.g. "Embajada", "Consulado", "ONG"
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    country = db.relationship('Country', backref=db.backref('embassy_lists', lazy='dynamic'))
    items = db.relationship('Embassy', backref='list', lazy='dynamic', cascade="all, delete-orphan")

class Embassy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('embassy_list.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False) # "Embajador Juan Perez" or just the name of the entity if different
    ambassador_name = db.Column(db.String(100))
    photo_filename = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    instagram = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
