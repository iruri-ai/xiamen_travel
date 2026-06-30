from flask import Blueprint, jsonify, request
import uuid
from database import get_db_connection

attractions_bp = Blueprint('attractions', __name__)

@attractions_bp.route('', methods=['GET'])
def get_attractions():
    try:
        conn = get_db_connection()
        
        keyword = request.args.get('keyword', '')
        tag_ids = request.args.getlist('tag_id', type=int)
        area = request.args.get('area', '')
        sort_by = request.args.get('sort_by', 'popularity')
        sort_order = request.args.get('sort_order', 'DESC')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 6, type=int)
        
        offset = (page - 1) * per_page
        
        base_query = '''
            SELECT DISTINCT a.*, 
                   (SELECT COUNT(*) FROM comments c WHERE c.attraction_id = a.id) as comment_count,
                   (SELECT COUNT(*) FROM favorites f WHERE f.attraction_id = a.id) as favorite_count
            FROM attractions a
        '''
        
        conditions = []
        params = []
        
        if keyword:
            conditions.append("(a.name LIKE ? OR a.description LIKE ? OR a.address LIKE ?)")
            params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
        
        if area:
            conditions.append("a.area = ?")
            params.append(area)
        
        if tag_ids:
            for i, tid in enumerate(tag_ids):
                base_query += f' JOIN attraction_tags at{i} ON a.id = at{i}.attraction_id'
                conditions.append(f"at{i}.tag_id = ?")
                params.append(tid)
        
        if conditions:
            base_query += ' WHERE ' + ' AND '.join(conditions)
        
        valid_sort_fields = {
            'popularity': 'a.popularity',
            'rating': 'a.rating',
            'name': 'a.name',
            'created_at': 'a.created_at',
            'comment_count': '(SELECT COUNT(*) FROM comments c WHERE c.attraction_id = a.id)',
            'favorite_count': '(SELECT COUNT(*) FROM favorites f WHERE f.attraction_id = a.id)'
        }
        sort_field = valid_sort_fields.get(sort_by, 'a.popularity')
        sort_order = 'ASC' if sort_order.upper() == 'ASC' else 'DESC'
        base_query += f' ORDER BY {sort_field} {sort_order}'
        
        count_query = f'SELECT COUNT(DISTINCT a.id) as total FROM attractions a'
        if tag_ids:
            for i in range(len(tag_ids)):
                count_query += f' JOIN attraction_tags at{i} ON a.id = at{i}.attraction_id'
        if conditions:
            count_query += ' WHERE ' + ' AND '.join(conditions)
        
        total = conn.execute(count_query, params).fetchone()['total']
        
        base_query += f' LIMIT {per_page} OFFSET {offset}'
        
        attractions = conn.execute(base_query, params).fetchall()
        
        result = []
        for attr in attractions:
            tags = conn.execute('''
                SELECT t.* FROM tags t
                JOIN attraction_tags at ON t.id = at.tag_id
                WHERE at.attraction_id = ?
            ''', (attr['id'],)).fetchall()
            
            duration_minutes = attr['recommended_duration']
            formatted_duration = f"约{duration_minutes // 60}小时" if duration_minutes >= 60 else f"约{duration_minutes}分钟"
            
            result.append({
                'id': attr['id'],
                'name': attr['name'],
                'desc': attr['description'],
                'image': attr['image_url'],
                'address': attr['address'],
                'open_time': attr['open_time'],
                'recommended_duration': attr['recommended_duration'],
                'formatted_duration': formatted_duration,
                'rating': attr['rating'],
                'rating_stars': '★' * int(attr['rating']),
                'popularity': attr['popularity'],
                'area': attr['area'],
                'price': attr['price'],
                'ticket_info': '免费' if attr['price'] == 0 else f'¥{attr["price"]}',
                'comment_count': attr['comment_count'],
                'favorite_count': attr['favorite_count'],
                'tags': [dict(t) for t in tags],
                'tag_names': [t['name'] for t in tags]
            })
        
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'items': result,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            },
            'request_id': str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500

@attractions_bp.route('/<int:attraction_id>', methods=['GET'])
def get_attraction(attraction_id):
    try:
        conn = get_db_connection()
        
        attraction = conn.execute('SELECT * FROM attractions WHERE id = ?', (attraction_id,)).fetchone()
        
        if not attraction:
            conn.close()
            return jsonify({
                'code': 404,
                'message': 'Attraction not found',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 404
        
        tags = conn.execute('''
            SELECT t.* FROM tags t
            JOIN attraction_tags at ON t.id = at.tag_id
            WHERE at.attraction_id = ?
        ''', (attraction_id,)).fetchall()
        
        comment_count = conn.execute(
            'SELECT COUNT(*) as count FROM comments WHERE attraction_id = ?',
            (attraction_id,)
        ).fetchone()['count']
        
        favorite_count = conn.execute(
            'SELECT COUNT(*) as count FROM favorites WHERE attraction_id = ?',
            (attraction_id,)
        ).fetchone()['count']
        
        duration_minutes = attraction['recommended_duration']
        formatted_duration = f"约{duration_minutes // 60}小时" if duration_minutes >= 60 else f"约{duration_minutes}分钟"
        
        result = {
            'id': attraction['id'],
            'name': attraction['name'],
            'desc': attraction['description'],
            'image': attraction['image_url'],
            'address': attraction['address'],
            'open_time': attraction['open_time'],
            'recommended_duration': attraction['recommended_duration'],
            'formatted_duration': formatted_duration,
            'rating': attraction['rating'],
            'rating_stars': '★' * int(attraction['rating']),
            'popularity': attraction['popularity'],
            'area': attraction['area'],
            'price': attraction['price'],
            'ticket_info': '免费' if attraction['price'] == 0 else f'¥{attraction["price"]}',
            'latitude': attraction['latitude'],
            'longitude': attraction['longitude'],
            'comment_count': comment_count,
            'favorite_count': favorite_count,
            'tags': [dict(t) for t in tags],
            'tag_names': [t['name'] for t in tags]
        }
        
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result,
            'request_id': str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500

@attractions_bp.route('/areas', methods=['GET'])
def get_areas():
    try:
        conn = get_db_connection()
        areas = conn.execute('SELECT DISTINCT area FROM attractions WHERE area IS NOT NULL').fetchall()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [a['area'] for a in areas],
            'request_id': str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500
