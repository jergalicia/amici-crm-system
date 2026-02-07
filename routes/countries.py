from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Country

bp = Blueprint('countries', __name__, url_prefix='/countries')

@bp.route('/')
@login_required
def index():
    if current_user.role != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('dashboard.index'))
    
    countries = Country.query.all()
    return render_template('countries/index.html', countries=countries)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role != 'admin':
        flash('Solo administradores pueden crear países.')
        return redirect(url_for('countries.index'))

    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        
        if Country.query.filter_by(name=name).first():
            flash('El país ya existe.')
            return redirect(url_for('countries.create'))
            
        if Country.query.filter_by(code=code).first():
             flash('El código de país ya existe.')
             return redirect(url_for('countries.create'))

        new_country = Country(name=name, code=code)
        
        db.session.add(new_country)
        db.session.commit()
        
        flash(f'País {name} creado exitosamente.')
        return redirect(url_for('countries.index'))

    return render_template('countries/create.html')

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role != 'admin':
        flash('Solo administradores pueden editar países.')
        return redirect(url_for('countries.index'))
        
    country = db.session.get(Country, id)
    if not country:
        flash('País no encontrado.')
        return redirect(url_for('countries.index'))

    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        
        # Check for duplicates (excluding current)
        existing_name = Country.query.filter_by(name=name).first()
        if existing_name and existing_name.id != country.id:
            flash('El nombre de país ya existe.')
            return redirect(url_for('countries.edit', id=id))

        existing_code = Country.query.filter_by(code=code).first()
        if existing_code and existing_code.id != country.id:
            flash('El código de país ya existe.')
            return redirect(url_for('countries.edit', id=id))

        country.name = name
        country.code = code
        
        db.session.commit()
        flash('País actualizado correctamente.')
        return redirect(url_for('countries.index'))

    return render_template('countries/edit.html', country=country)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('Solo administradores pueden eliminar países.')
        return redirect(url_for('countries.index'))
        
    country = db.session.get(Country, id)
    if not country:
        flash('País no encontrado.')
        return redirect(url_for('countries.index'))

    # Check for dependent records
    if country.users.count() > 0:
        flash('No se puede eliminar: Hay usuarios asignados a este país.')
        return redirect(url_for('countries.index'))
        
    if country.editions.count() > 0:
        flash('No se puede eliminar: Hay ediciones asignadas a este país.')
        return redirect(url_for('countries.index'))
        
    if country.events.count() > 0:
         flash('No se puede eliminar: Hay eventos asignados a este país.')
         return redirect(url_for('countries.index'))

    db.session.delete(country)
    db.session.commit()
    flash(f'País {country.name} eliminado.')
    return redirect(url_for('countries.index'))
