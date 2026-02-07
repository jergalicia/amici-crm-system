from flask import Blueprint, render_template, send_from_directory, current_app, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import db, Manual
from datetime import datetime

bp = Blueprint('manuals', __name__, url_prefix='/manuals')

@bp.route('/')
@login_required
def index():
    query = Manual.query
    
    # Filter by role unless admin
    if current_user.role != 'admin':
        # Show manuals for 'all' or specific role
        query = query.filter(Manual.target_role.in_(['all', current_user.role]))
        
    manuals = query.order_by(Manual.name.asc()).all()
    return render_template('manuals/index.html', manuals=manuals)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('manuals.index'))

    if request.method == 'POST':
        name = request.form['name']
        target_role = request.form['target_role']
        
        # File Handling
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo.')
            return redirect(url_for('manuals.create'))
            
        file = request.files['file']
        
        if file.filename == '':
            flash('No se seleccionó ningún archivo.')
            return redirect(url_for('manuals.create'))
            
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            # Create unique filename to prevent overwrites
            timestamp = int(datetime.utcnow().timestamp())
            unique_filename = f"{timestamp}_{filename}"
            
            # Ensure directory exists
            manuals_dir = os.path.join(current_app.root_path, 'static', 'manuals')
            os.makedirs(manuals_dir, exist_ok=True)
            
            file.save(os.path.join(manuals_dir, unique_filename))
            
            new_manual = Manual(
                name=name,
                filename=unique_filename,
                target_role=target_role
            )
            
            db.session.add(new_manual)
            db.session.commit()
            
            flash('Manual subido exitosamente.')
            return redirect(url_for('manuals.index'))
        else:
            flash('Solo se permiten archivos PDF.')
            return redirect(url_for('manuals.create'))

    return render_template('manuals/create.html')

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('manuals.index'))
        
    manual = db.session.get(Manual, id)
    if not manual:
        flash('Manual no encontrado.')
        return redirect(url_for('manuals.index'))

    if request.method == 'POST':
        manual.name = request.form['name']
        manual.target_role = request.form['target_role']
        
        # Optional: Allow file update (simplified: only metadata update for now unless needed)
        # If file update is needed, handle 'file' input similar to create.
        
        db.session.commit()
        flash('Manual actualizado.')
        return redirect(url_for('manuals.index'))

    return render_template('manuals/edit.html', manual=manual)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('manuals.index'))
        
    manual = db.session.get(Manual, id)
    if manual:
        # Delete file from disk
        try:
            full_path = os.path.join(current_app.root_path, 'static', 'manuals', manual.filename)
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

        db.session.delete(manual)
        db.session.commit()
        flash('Manual eliminado.')
    
    return redirect(url_for('manuals.index'))

@bp.route('/view/<filename>')
@login_required
def view_pdf(filename):
    # Security: Ensure user has access to this file via DB check?
    # For now, relying on index filtering. Direct access check is better but optional for MVP if names are guarded.
    # Ideally: find manual by filename, check role.
    
    manual = Manual.query.filter_by(filename=filename).first()
    if manual:
        if current_user.role != 'admin' and manual.target_role not in ['all', current_user.role]:
             flash('No tienes permiso para ver este documento.')
             return redirect(url_for('manuals.index'))
             
    manuals_dir = os.path.join(current_app.root_path, 'static', 'manuals')
    return send_from_directory(manuals_dir, filename)
