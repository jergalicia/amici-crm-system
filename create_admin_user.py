from app import create_app
from models import db, User

app = create_app()

def create_users():
    with app.app_context():
        # Create 'admin' user
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin', email='real_admin@amici.com', role='admin', is_active=True)
            user.set_password('admin123')
            db.session.add(user)
            print("Created user 'admin' with password 'admin123'")
        else:
            print("User 'admin' already exists. Resetting password.")
            u = User.query.filter_by(username='admin').first()
            u.set_password('admin123')

        # Reset 'user_pa'
        user_pa = User.query.filter_by(username='user_pa').first()
        if user_pa:
            user_pa.set_password('123456')
            print("Reset 'user_pa' password to '123456'")
        
        db.session.commit()
        print("Done.")

if __name__ == '__main__':
    create_users()
