from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Edition, Article, User
from utils.drive_api import drive_service
from datetime import datetime

bp = Blueprint('edition', __name__, url_prefix='/editions')

@bp.route('/')
@login_required
def index():
    if current_user.role not in ['admin', 'coordinator']:
        flash('Acceso denegado.')
        return redirect(url_for('dashboard.index'))
    
    query = Edition.query
    if current_user.role != 'admin' and current_user.country_id:
        query = query.filter_by(country_id=current_user.country_id)
        
    editions = query.order_by(Edition.publication_date.desc()).all()
    return render_template('edition/index.html', editions=editions)

@bp.route('/<int:id>')
@login_required
def view(id):
    edition = db.session.get(Edition, id)
    if not edition:
        flash('Edición no encontrada.')
        return redirect(url_for('edition.index'))
        
    if current_user.country_id and edition.country_id != current_user.country_id:
        flash('No tienes permiso para ver esta edición.')
        return redirect(url_for('edition.index'))

    return render_template('edition/view.html', edition=edition)

@bp.route('/<int:id>/add_article', methods=['GET', 'POST'])
@login_required
def add_article(id):
    if current_user.role not in ['admin', 'coordinator']:
        flash('Acceso denegado.')
        return redirect(url_for('dashboard.index'))
    
    edition = db.session.get(Edition, id)
    if not edition:
        flash('Edición no encontrada.')
        return redirect(url_for('edition.index'))

    if request.method == 'POST':
        title = request.form['title']
        author_id = request.form['author_id']
        content = request.form['content']
        deadline_str = request.form['deadline']
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d')

        new_article = Article(
            title=title,
            content=content,
            author_id=author_id,
            edition_id=edition.id,
            deadline=deadline,
            status='assigned'
        )
        
        db.session.add(new_article)
        db.session.commit()
        
        flash(f'Artículo "{title}" asignado exitosamente.')
        return redirect(url_for('edition.view', id=edition.id))

    # Get list of journalists for the dropdown (filtered by country)
    journalists = User.query.filter_by(role='journalist')
    if current_user.country_id:
        journalists = journalists.filter_by(country_id=current_user.country_id)
    journalists = journalists.all()
    # Also include admins/coordinators if needed, but per requirement assign to journalist
    
    return render_template('edition/add_article.html', edition=edition, journalists=journalists)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role not in ['admin', 'coordinator']:
        flash('Acceso denegado.')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        title = request.form['title']
        date_str = request.form['publication_date']
        publication_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Determine Country
        country_id = current_user.country_id
        if current_user.role == 'admin':
            country_id = request.form.get('country_id') # Might be None if not sent
            
        if not country_id:
            flash('Error: Debes asignar un país a la edición.')
            return redirect(url_for('edition.create'))

        try:
            # Create Drive Folder
            drive_id = drive_service.create_edition_folders(title)

            new_edition = Edition(
                title=title,
                publication_date=publication_date,
                drive_folder_id=drive_id,
                country_id=country_id,
                status='planning'
            )
            
            db.session.add(new_edition)
            db.session.commit()
            
            flash(f'Edición "{title}" creada exitosamente. Carpeta en Drive generada.')
            return redirect(url_for('dashboard.index'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating edition: {e}") # Log to console
            flash(f'Error al crear la edición: {str(e)}')
            return redirect(url_for('edition.create'))

    # Prepare countries for dropdown
    from models import Country
    countries = []
    if current_user.role == 'admin':
        countries = Country.query.all()

    return render_template('edition/create.html', countries=countries)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role not in ['admin', 'coordinator']:
        flash('Acceso denegado.')
        return redirect(url_for('dashboard.index'))
        
    edition = db.session.get(Edition, id)
    if not edition:
        flash('Edición no encontrada.')
        return redirect(url_for('edition.index'))
        
    # Permission Check
    if current_user.role != 'admin' and current_user.country_id != edition.country_id:
        flash('No tienes permiso para editar esta edición.')
        return redirect(url_for('edition.index'))

    if request.method == 'POST':
        title = request.form['title']
        date_str = request.form['publication_date']
        publication_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        status = request.form['status']
        
        edition.title = title
        edition.publication_date = publication_date
        edition.status = status
        
        # Admin can change country (careful with existing articles!)
        if current_user.role == 'admin' and request.form.get('country_id'):
            edition.country_id = request.form.get('country_id')
            
        db.session.commit()
        flash('Edición actualizada exitosamente.')
        return redirect(url_for('edition.index'))

    # Prepare countries for dropdown
    from models import Country
    countries = []
    if current_user.role == 'admin':
        countries = Country.query.all()

    return render_template('edition/edit.html', edition=edition, countries=countries)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if current_user.role not in ['admin', 'coordinator']:
        flash('Acceso denegado.')
        return redirect(url_for('dashboard.index'))
        
    edition = db.session.get(Edition, id)
    if not edition:
        flash('Edición no encontrada.')
        return redirect(url_for('edition.index'))
        
    # Permission Check
    if current_user.role != 'admin' and current_user.country_id != edition.country_id:
        flash('No tienes permiso para eliminar esta edición.')
        return redirect(url_for('edition.index'))
        
    # Constraint Check: Cannot delete if it has articles
    if edition.articles:
        flash('No se puede eliminar la edición porque tiene artículos asignados. Elimina los artículos primero.')
        return redirect(url_for('edition.index'))
        
    try:
        db.session.delete(edition)
        db.session.commit()
        flash('Edición eliminada exitosamente.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la edición: {str(e)}')
        
    return redirect(url_for('edition.index'))
