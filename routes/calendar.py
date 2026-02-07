from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db, Event
from datetime import datetime

bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@bp.route('/')
@login_required
def index():
    return render_template('calendar/index.html')

@bp.route('/api/events')
@login_required
def get_events():
    query = Event.query
    if current_user.country_id:
        query = query.filter_by(country_id=current_user.country_id)
    events = query.all()
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat() if event.end_time else None,
            'description': event.description,
            'location': event.location
        })
    return jsonify(events_data)

@bp.route('/api/events/create', methods=['POST'])
@login_required
def create_event():
    if current_user.role not in ['admin', 'coordinator']:
        return jsonify({'status': 'error', 'message': 'Permiso denegado'}), 403
    
    data = request.json
    try:
        new_event = Event(
            title=data['title'],
            start_time=datetime.fromisoformat(data['start']),
            end_time=datetime.fromisoformat(data['end']) if data.get('end') else None,
            description=data.get('description', ''),
            location=data.get('location', ''),
            country_id=current_user.country_id,
            created_by=current_user.id
        )
        db.session.add(new_event)
        db.session.commit()
        return jsonify({'status': 'success', 'id': new_event.id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
