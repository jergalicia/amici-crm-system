from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from models import db, User, Country

bp = Blueprint('users', __name__, url_prefix='/users')

@bp.route('/')
@login_required
def index():
    if current_user.role not in ['admin', 'coordinator']:
        flash('Acceso denegado.')
        return redirect(url_for('dashboard.index'))
    
    users = User.query.all()
    return render_template('users/index.html', users=users)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role != 'admin':
        flash('Solo administradores pueden crear usuarios.')
        return redirect(url_for('users.index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        country_id = request.form.get('country_id')
        
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.')
            return redirect(url_for('users.create'))
            
        if User.query.filter_by(email=email).first():
             flash('El email ya está registrado.')
             return redirect(url_for('users.create'))

        profile_photo = None
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                unique_filename = f"{timestamp}_{filename}"
                
                users_dir = current_app.config['USERS_FOLDER']
                os.makedirs(users_dir, exist_ok=True)
                
                file.save(os.path.join(users_dir, unique_filename))
                profile_photo = unique_filename

        new_user = User(
            username=username, 
            email=email, 
            role=role, 
            country_id=country_id,
            profile_photo=profile_photo
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Usuario {username} creado exitosamente.')
        return redirect(url_for('users.index'))

    countries = Country.query.all()
    return render_template('users/create.html', countries=countries)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role != 'admin':
        flash('Solo administradores pueden editar usuarios.')
        return redirect(url_for('users.index'))
        
    user = db.session.get(User, id)
    if not user:
        flash('Usuario no encontrado.')
        return redirect(url_for('users.index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']
        is_active = request.form['is_active'] == '1'
        
        # Check if username exists (excluding current user)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('El nombre de usuario ya existe.')
            return redirect(url_for('users.edit', id=id))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user.id:
            flash('El email ya está registrado.')
            return redirect(url_for('users.edit', id=id))

        user.username = username
        user.email = email
        user.role = role
        user.is_active = is_active
        user.country_id = request.form.get('country_id')
        
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename != '':
                # Delete old photo
                if user.profile_photo:
                    try:
                        os.remove(os.path.join(current_app.config['USERS_FOLDER'], user.profile_photo))
                    except:
                        pass
                
                filename = secure_filename(file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                unique_filename = f"{timestamp}_{filename}"
                
                users_dir = current_app.config['USERS_FOLDER']
                os.makedirs(users_dir, exist_ok=True)
                
                file.save(os.path.join(users_dir, unique_filename))
                user.profile_photo = unique_filename
        
        password = request.form['password']
        if password:
            user.set_password(password)
            
        db.session.commit()
        flash('Usuario actualizado correctamente.')
        return redirect(url_for('users.index'))

    countries = Country.query.all()
    return render_template('users/edit.html', user=user, countries=countries)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('Solo administradores pueden eliminar usuarios.')
        return redirect(url_for('users.index'))
        
    user = db.session.get(User, id)
    if not user:
        flash('Usuario no encontrado.')
        return redirect(url_for('users.index'))
        
    if user.id == current_user.id:
        flash('No puedes eliminar tu propio usuario.')
        return redirect(url_for('users.index'))

    if user.profile_photo:
        try:
            os.remove(os.path.join(current_app.config['USERS_FOLDER'], user.profile_photo))
        except:
            pass

    db.session.delete(user)
    db.session.commit()
    flash(f'Usuario {user.username} eliminado.')
    return redirect(url_for('users.index'))
