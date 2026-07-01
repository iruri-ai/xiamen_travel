from flask import Blueprint, jsonify, request
import uuid
from database import get_db_connection
from middleware.auth import admin_required

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


@attractions_bp.route('', methods=['POST'])
@admin_required
def create_attraction():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求体不能为空', 'data': None, 'request_id': str(uuid.uuid4())}), 400

        name = data.get('name', '').strip()
        if not name:
            return jsonify({'code': 400, 'message': '景点名称不能为空', 'data': None, 'request_id': str(uuid.uuid4())}), 400

        conn = get_db_connection()

        existing = conn.execute('SELECT id FROM attractions WHERE name = ?', (name,)).fetchone()
        if existing:
            conn.close()
            return jsonify({'code': 409, 'message': '景点名称已存在', 'data': None, 'request_id': str(uuid.uuid4())}), 409

        cursor = conn.execute('INSERT INTO attractions (name, description, image_url, address, open_time, recommended_duration, rating, popularity, area, price, latitude, longitude, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime(\'now\', \'localtime\'), datetime(\'now\', \'localtime\'))', (name, data.get('description', ''), data.get('image_url', ''), data.get('address', ''), data.get('open_time', ''), data.get('recommended_duration', 120), data.get('rating', 0.0), data.get('popularity', 0), data.get('area', ''), data.get('price', 0.0), data.get('latitude'), data.get('longitude')))

        attraction_id = cursor.lastrowid

        tags = data.get('tags', [])
        if isinstance(tags, list):
            for tag_name in tags:
                tag_name = tag_name.strip()
                if tag_name:
                    tag = conn.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).fetchone()
                    if not tag:
                        tag_cursor = conn.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                        tag_id = tag_cursor.lastrowid
                    else:
                        tag_id = tag['id']

                    conn.execute('INSERT OR IGNORE INTO attraction_tags (attraction_id, tag_id) VALUES (?, ?)', (attraction_id, tag_id))

        conn.commit()
        conn.close()

        return jsonify({'code': 200, 'message': '景点创建成功', 'data': {'id': attraction_id, 'name': name}, 'request_id': str(uuid.uuid4())})

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None, 'request_id': str(uuid.uuid4())}), 500


@attractions_bp.route('/<int:attraction_id>', methods=['PUT'])
@admin_required
def update_attraction(attraction_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求体不能为空', 'data': None, 'request_id': str(uuid.uuid4())}), 400

        conn = get_db_connection()

        attraction = conn.execute('SELECT id, name FROM attractions WHERE id = ?', (attraction_id,)).fetchone()
        if not attraction:
            conn.close()
            return jsonify({'code': 404, 'message': '景点不存在', 'data': None, 'request_id': str(uuid.uuid4())}), 404

        if 'name' in data:
            new_name = data['name'].strip()
            if not new_name:
                conn.close()
                return jsonify({'code': 400, 'message': '景点名称不能为空', 'data': None, 'request_id': str(uuid.uuid4())}), 400

            existing = conn.execute('SELECT id FROM attractions WHERE name = ? AND id != ?', (new_name, attraction_id)).fetchone()
            if existing:
                conn.close()
                return jsonify({'code': 409, 'message': '景点名称已存在', 'data': None, 'request_id': str(uuid.uuid4())}), 409

        updates = []
        params = []

        if 'name' in data:
            updates.append('name = ?')
            params.append(data['name'].strip())
        if 'description' in data:
            updates.append('description = ?')
            params.append(data['description'])
        if 'image_url' in data:
            updates.append('image_url = ?')
            params.append(data['image_url'])
        if 'address' in data:
            updates.append('address = ?')
            params.append(data['address'])
        if 'open_time' in data:
            updates.append('open_time = ?')
            params.append(data['open_time'])
        if 'recommended_duration' in data:
            updates.append('recommended_duration = ?')
            params.append(data['recommended_duration'])
        if 'rating' in data:
            updates.append('rating = ?')
            params.append(data['rating'])
        if 'popularity' in data:
            updates.append('popularity = ?')
            params.append(data['popularity'])
        if 'area' in data:
            updates.append('area = ?')
            params.append(data['area'])
        if 'price' in data:
            updates.append('price = ?')
            params.append(data['price'])
        if 'latitude' in data:
            updates.append('latitude = ?')
            params.append(data['latitude'])
        if 'longitude' in data:
            updates.append('longitude = ?')
            params.append(data['longitude'])

        updates.append("updated_at = datetime('now', 'localtime')")
        params.append(attraction_id)

        query = f'UPDATE attractions SET {", ".join(updates)} WHERE id = ?'
        conn.execute(query, params)

        if 'tags' in data:
            conn.execute('DELETE FROM attraction_tags WHERE attraction_id = ?', (attraction_id,))
            tags = data['tags']
            if isinstance(tags, list):
                for tag_name in tags:
                    tag_name = tag_name.strip()
                    if tag_name:
                        tag = conn.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).fetchone()
                        if not tag:
                            tag_cursor = conn.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                            tag_id = tag_cursor.lastrowid
                        else:
                            tag_id = tag['id']

                        conn.execute('INSERT INTO attraction_tags (attraction_id, tag_id) VALUES (?, ?)', (attraction_id, tag_id))

        conn.commit()
        conn.close()

        return jsonify({'code': 200, 'message': '景点更新成功', 'data': {'id': attraction_id}, 'request_id': str(uuid.uuid4())})

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None, 'request_id': str(uuid.uuid4())}), 500


@attractions_bp.route('/<int:attraction_id>', methods=['DELETE'])
@admin_required
def delete_attraction(attraction_id):
    try:
        conn = get_db_connection()

        attraction = conn.execute('SELECT id, name FROM attractions WHERE id = ?', (attraction_id,)).fetchone()
        if not attraction:
            conn.close()
            return jsonify({'code': 404, 'message': '景点不存在', 'data': None, 'request_id': str(uuid.uuid4())}), 404

        conn.execute('DELETE FROM attraction_tags WHERE attraction_id = ?', (attraction_id,))
        conn.execute('DELETE FROM comments WHERE attraction_id = ?', (attraction_id,))
        conn.execute('DELETE FROM favorites WHERE attraction_id = ?', (attraction_id,))
        conn.execute('DELETE FROM route_attractions WHERE attraction_id = ?', (attraction_id,))
        conn.execute('DELETE FROM attractions WHERE id = ?', (attraction_id,))

        conn.commit()
        conn.close()

        return jsonify({'code': 200, 'message': '景点删除成功', 'data': {'id': attraction_id}, 'request_id': str(uuid.uuid4())})

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None, 'request_id': str(uuid.uuid4())}), 500
