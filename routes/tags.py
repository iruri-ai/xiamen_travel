from flask import Blueprint, jsonify
import uuid
from database import get_db_connection

tags_bp = Blueprint('tags', __name__)

@tags_bp.route('', methods=['GET'])
def get_tags():
    try:
        conn = get_db_connection()
        tags = conn.execute('SELECT * FROM tags ORDER BY id').fetchall()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [dict(t) for t in tags],
            'request_id': str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500
