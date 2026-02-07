from app import db, create_app
from models import User

app = create_app()
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        u = User(username='admin', email='admin@amici.com', role='admin')
        u.set_password('admin123')
        db.session.add(u)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")
