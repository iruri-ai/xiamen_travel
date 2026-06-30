from flask import Blueprint, jsonify, request
import uuid
from database import get_db_connection

favorites_bp = Blueprint('favorites', __name__)

@favorites_bp.route('', methods=['GET'])
def get_favorites():
    try:
        user_id = request.args.get('user_id', 'anonymous')
        
        conn = get_db_connection()
        
        favorites = conn.execute('''
            SELECT f.*, a.name as attraction_name, a.image_url, a.address, a.rating
            FROM favorites f
            JOIN attractions a ON f.attraction_id = a.id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
        ''', (user_id,)).fetchall()
        
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [dict(f) for f in favorites],
            'request_id': str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500

@favorites_bp.route('', methods=['POST'])
def add_favorite():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'code': 400,
                'message': 'Request body is required',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 400
        
        attraction_id = data.get('attraction_id')
        user_id = data.get('user_id', 'anonymous')
        
        if not attraction_id or not isinstance(attraction_id, int) or attraction_id <= 0:
            return jsonify({
                'code': 400,
                'message': 'Invalid attraction_id',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 400
        
        conn = get_db_connection()
        
        attraction = conn.execute('SELECT id FROM attractions WHERE id = ?', 
                                 (attraction_id,)).fetchone()
        if not attraction:
            conn.close()
            return jsonify({
                'code': 404,
                'message': '景点不存在',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 404
        
        existing = conn.execute(
            'SELECT id FROM favorites WHERE attraction_id = ? AND user_id = ?',
            (attraction_id, user_id)
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({
                'code': 409,
                'message': '已经收藏过了',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 409
        
        cursor = conn.execute('''
            INSERT INTO favorites (attraction_id, user_id)
            VALUES (?, ?)
        ''', (attraction_id, user_id))
        
        conn.commit()
        favorite_id = cursor.lastrowid
        
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': '收藏成功',
            'data': {'id': favorite_id, 'attraction_id': attraction_id},
            'request_id': str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500

@favorites_bp.route('/<int:favorite_id>', methods=['DELETE'])
def delete_favorite(favorite_id):
    try:
        conn = get_db_connection()
        
        favorite = conn.execute('SELECT * FROM favorites WHERE id = ?', (favorite_id,)).fetchone()
        
        if not favorite:
            conn.close()
            return jsonify({
                'code': 404,
                'message': '收藏记录不存在',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 404
        
        user_id = request.args.get('user_id', 'anonymous')
        if favorite['user_id'] != user_id and user_id != 'admin':
            conn.close()
            return jsonify({
                'code': 403,
                'message': '无权删除此收藏',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 403
        
        conn.execute('DELETE FROM favorites WHERE id = ?', (favorite_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': '取消收藏成功',
            'data': None,
            'request_id': str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500
