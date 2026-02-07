from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import db, Embassy, EmbassyList, Country
from datetime import datetime

bp = Blueprint('embassies', __name__, url_prefix='/embassies')

# --- LISTS MANAGEMENT ---

@bp.route('/')
@login_required
def index():
    # Show all Lists, grouped by Country
    query = EmbassyList.query
    
    if current_user.role not in ['admin', 'coordinator']:
        if current_user.country_id:
            query = query.filter_by(country_id=current_user.country_id)
        else:
            query = query.filter_by(id=-1) 
            
    lists = query.join(Country).order_by(Country.name, EmbassyList.name).all()
    return render_template('embassies/index.html', lists=lists)

@bp.route('/create_list', methods=['GET', 'POST'])
@login_required
def create_list():
    if current_user.role not in ['admin', 'coordinator']:
        flash('Acceso denegado.')
        return redirect(url_for('embassies.index'))

    if request.method == 'POST':
        name = request.form['name']
        country_id = request.form['country_id']
        
        new_list = EmbassyList(name=name, country_id=country_id)
        db.session.add(new_list)
        db.session.commit()
        
        flash('Lista creada exitosamente.')
        return redirect(url_for('embassies.index'))

    countries = Country.query.order_by(Country.name).all()
    return render_template('embassies/create_list.html', countries=countries)

@bp.route('/list/<int:id>', methods=['GET'])
@login_required
def view_list(id):
    embassy_list = db.session.get(EmbassyList, id)
    if not embassy_list:
        flash('Lista no encontrada.')
        return redirect(url_for('embassies.index'))
        
    # Permission Check
    if current_user.role not in ['admin', 'coordinator']:
        if current_user.country_id != embassy_list.country_id:
            flash('Acceso denegado.')
            return redirect(url_for('embassies.index'))

    return render_template('embassies/view_list.html', embassy_list=embassy_list)

@bp.route('/list/<int:id>/delete', methods=['POST'])
@login_required
def delete_list(id):
    if current_user.role not in ['admin', 'coordinator']:
        flash('Acceso denegado.')
        return redirect(url_for('embassies.index'))

    embassy_list = db.session.get(EmbassyList, id)
    if embassy_list:
        # Optional: Clean up photos of items in list before deleting?
        # Cascade take care of DB records, but files remain. 
        # For simplicity, we skip file cleanup for now or iterate.
        for item in embassy_list.items:
             if item.photo_filename:
                try:
                    os.remove(os.path.join(current_app.config['EMBASSIES_FOLDER'], item.photo_filename))
                except:
                    pass

        db.session.delete(embassy_list)
        db.session.commit()
        flash('Lista eliminada.')
    
    return redirect(url_for('embassies.index'))


# --- ITEMS MANAGEMENT ---

@bp.route('/list/<int:list_id>/create_member', methods=['GET', 'POST'])
@login_required
def create_member(list_id):
    if current_user.role not in ['admin', 'coordinator']:
        flash('Acceso denegado.')
        return redirect(url_for('embassies.index'))
    
    embassy_list = db.session.get(EmbassyList, list_id)
    if not embassy_list:
        flash('Lista no encontrada.')
        return redirect(url_for('embassies.index'))

    if request.method == 'POST':
        name = request.form['name']
        ambassador_name = request.form['ambassador_name']
        phone = request.form['phone']
        email = request.form['email']
        instagram = request.form['instagram']
        
        photo_filename = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                unique_filename = f"{timestamp}_{filename}"
                
                embassies_dir = current_app.config['EMBASSIES_FOLDER']
                os.makedirs(embassies_dir, exist_ok=True)
                
                file.save(os.path.join(embassies_dir, unique_filename))
                photo_filename = unique_filename

        new_item = Embassy(
            list_id=list_id,
            name=name,
            ambassador_name=ambassador_name,
            phone=phone,
            email=email,
            instagram=instagram,
            photo_filename=photo_filename
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        flash('Registro agregado exitosamente.')
        return redirect(url_for('embassies.view_list', id=list_id))

    return render_template('embassies/create_member.html', embassy_list=embassy_list)

@bp.route('/member/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_member(id):
    if current_user.role not in ['admin', 'coordinator']:
        flash('Acceso denegado.')
        return redirect(url_for('embassies.index'))
        
    embassy = db.session.get(Embassy, id)
    if not embassy:
        flash('Registro no encontrado.')
        return redirect(url_for('embassies.index'))

    if request.method == 'POST':
        embassy.name = request.form['name']
        embassy.ambassador_name = request.form['ambassador_name']
        embassy.phone = request.form['phone']
        embassy.email = request.form['email']
        embassy.instagram = request.form['instagram']
        
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                if embassy.photo_filename:
                    try:
                        os.remove(os.path.join(current_app.config['EMBASSIES_FOLDER'], embassy.photo_filename))
                    except:
                        pass
                
                filename = secure_filename(file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                unique_filename = f"{timestamp}_{filename}"
                file.save(os.path.join(current_app.config['EMBASSIES_FOLDER'], unique_filename))
                embassy.photo_filename = unique_filename
        
        db.session.commit()
        flash('Registro actualizado.')
        return redirect(url_for('embassies.view_list', id=embassy.list_id))

    return render_template('embassies/edit.html', embassy=embassy)

@bp.route('/member/<int:id>/delete', methods=['POST'])
@login_required
def delete_member(id):
    if current_user.role not in ['admin', 'coordinator']:
        flash('Acceso denegado.')
        return redirect(url_for('embassies.index'))
        
    embassy = db.session.get(Embassy, id)
    list_id = embassy.list_id if embassy else None
    
    if embassy:
        if embassy.photo_filename:
            try:
                os.remove(os.path.join(current_app.config['EMBASSIES_FOLDER'], embassy.photo_filename))
            except:
                pass
        db.session.delete(embassy)
        db.session.commit()
        flash('Registro eliminado.')
    
    if list_id:
        return redirect(url_for('embassies.view_list', id=list_id))
    return redirect(url_for('embassies.index'))
