from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, Article, Edition, Country, ArticleImage, User
from werkzeug.utils import secure_filename
import os
from datetime import datetime

bp = Blueprint('articles', __name__, url_prefix='/articles')

@bp.route('/')
@login_required
def index():
    query = Article.query.join(Edition)
    
    if current_user.role != 'admin':
        if current_user.country_id:
            query = query.filter(Edition.country_id == current_user.country_id)
        else:
            query = query.filter(db.false()) # Return nothing
            
    articles = query.order_by(Article.id.desc()).all()
    return render_template('articles/index.html', articles=articles)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        edition_id = request.form['edition_id']
        
        # Validation
        if len(title) > 60:
            flash('El título no puede exceder los 60 caracteres.')
            return redirect(url_for('articles.create'))
        
        if len(content) > 600:
            flash('El contenido no puede exceder los 600 caracteres.')
            return redirect(url_for('articles.create'))
            
        author_id = current_user.id
        if current_user.role == 'admin' and request.form.get('author_id'):
            author_id = request.form.get('author_id')
            
        article = Article(
            title=title,
            content=content,
            edition_id=edition_id,
            author_id=author_id,
            status='draft',
            deadline=datetime.utcnow() # Default deadline
        )
        db.session.add(article)
        db.session.commit()
        
        # Handle Images
        images = request.files.getlist('images')
        saved_count = 0
        for image in images:
            if image and image.filename and saved_count < 5:
                filename = secure_filename(image.filename)
                # Create directory structure: static/uploads/articles/YYYY/MM/
                now = datetime.utcnow()
                relative_path = os.path.join('uploads', 'articles', str(now.year), str(now.month))
                absolute_path = os.path.join(current_app.root_path, 'static', relative_path)
                os.makedirs(absolute_path, exist_ok=True)
                
                # Save file
                unique_filename = f"{article.id}_{int(now.timestamp())}_{filename}"
                image.save(os.path.join(absolute_path, unique_filename))
                
                # DB Record
                db_image = ArticleImage(
                    article_id=article.id,
                    filename=os.path.join(relative_path, unique_filename).replace('\\', '/')
                )
                db.session.add(db_image)
                saved_count += 1
        
        db.session.commit()
        flash('Artículo creado exitosamente.')
        return redirect(url_for('articles.index'))

    # GET: Prepare data for form
    if current_user.role == 'admin':
        countries = Country.query.all()
        users = User.query.all() # Or filter by relevant roles
    else:
        countries = [current_user.country] if current_user.country else []
        users = []
        
    # Initial editions (loaded via JS usually, but for server side render if needed)
    editions = []
    if countries:
        editions = Edition.query.filter_by(country_id=countries[0].id).all()

    return render_template('articles/create.html', countries=countries, editions=editions, users=users)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    article = Article.query.get_or_404(id)
    
    # Access Control: Admins or Author logic?
    # Requirement: "Los periodistas crean lo mismo pero solo para el pais que ellos pertenecen."
    # Implies they can edit their country's articles? or only their own? 
    # Usually "Articles can be modified" implies broader access. 
    # Let's restrict non-admins to their country's articles.
    if current_user.role != 'admin':
         if not current_user.country or article.edition.country_id != current_user.country_id:
             flash('No tienes permiso para editar este artículo.')
             return redirect(url_for('articles.index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        edition_id = request.form['edition_id'] # Allow changing edition?
        
        # Admin Author Selection
        if current_user.role == 'admin':
             author_id = request.form.get('author_id')
             if author_id:
                 article.author_id = author_id

        if len(title) > 60:
            flash('El título no puede exceder los 60 caracteres.')
            return redirect(url_for('articles.edit', id=id))
            
        if len(content) > 600:
            flash('El contenido no puede exceder los 600 caracteres.')
            return redirect(url_for('articles.edit', id=id))
            
        article.title = title
        article.content = content
        article.edition_id = edition_id
        
        # Limit total images to 5. Check existing count.
        current_image_count = article.images.count()
        images = request.files.getlist('images')
        
        saved_count = 0
        images_to_add = 5 - current_image_count
        
        for image in images:
            if image and image.filename and saved_count < images_to_add:
                filename = secure_filename(image.filename)
                now = datetime.utcnow()
                relative_path = os.path.join('uploads', 'articles', str(now.year), str(now.month))
                absolute_path = os.path.join(current_app.root_path, 'static', relative_path)
                os.makedirs(absolute_path, exist_ok=True)
                
                unique_filename = f"{article.id}_{int(now.timestamp())}_{filename}"
                image.save(os.path.join(absolute_path, unique_filename))
                
                db_image = ArticleImage(
                    article_id=article.id,
                    filename=os.path.join(relative_path, unique_filename).replace('\\', '/')
                )
                db.session.add(db_image)
                saved_count += 1
        
        db.session.commit()
        flash('Artículo actualizado.')
        return redirect(url_for('articles.index'))
    
    # Prepare form data
    if current_user.role == 'admin':
        countries = Country.query.all()
        users = User.query.all()
    else:
        countries = [current_user.country] if current_user.country else []
        users = []
    
    # Get all editions for the article's country so the dropdown is populated correctly
    editions = Edition.query.filter_by(country_id=article.edition.country_id).all()

    return render_template('articles/edit.html', article=article, countries=countries, editions=editions, users=users)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    article = Article.query.get_or_404(id)
    
    if current_user.role != 'admin':
         if not current_user.country or article.edition.country_id != current_user.country_id:
             flash('No tienes permiso para eliminar este artículo.')
             return redirect(url_for('articles.index'))
             
    # Images are cascaded deletion in DB, but files remain on disk.
    # Cleanup files (Optional for now/MVP, but good practice)
    for image in article.images:
        try:
            full_path = os.path.join(current_app.root_path, 'static', image.filename)
            if os.path.exists(full_path):
                os.remove(full_path)
        except:
            pass # Ignore errors during deletion
            
    db.session.delete(article)
    db.session.commit()
    flash('Artículo eliminado.')
    return redirect(url_for('articles.index'))
