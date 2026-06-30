from flask import Blueprint, jsonify, request
import uuid
from database import get_db_connection
from services.recommendation import RecommendationService

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/recommend', methods=['GET'])
def get_recommend_routes():
    try:
        theme = request.args.get('theme', '')
        duration = request.args.get('duration', 480, type=int)
        weather = request.args.get('weather', '')
        
        conn = get_db_connection()
        
        base_query = '''
            SELECT a.*, 
                   (SELECT COUNT(*) FROM comments c WHERE c.attraction_id = a.id) as comment_count,
                   (SELECT COUNT(*) FROM favorites f WHERE f.attraction_id = a.id) as favorite_count
            FROM attractions a
        '''
        
        conditions = []
        params = []
        
        if theme:
            base_query += ' JOIN attraction_tags at ON a.id = at.attraction_id'
            base_query += ' JOIN tags t ON at.tag_id = t.id'
            conditions.append("t.name = ?")
            params.append(theme)
        
        if weather:
            if '雨' in weather or '雪' in weather:
                conditions.append("(a.indoor = 1 OR a.area = '室内')")
        
        if duration and duration <= 240:
            conditions.append("a.recommended_duration <= ?")
            params.append(duration)
        
        if conditions:
            base_query += ' WHERE ' + ' AND '.join(conditions)
        
        base_query += ' GROUP BY a.id ORDER BY a.popularity DESC, a.rating DESC LIMIT 6'
        
        attractions = conn.execute(base_query, params).fetchall()
        
        attractions_with_tags = []
        for attr in attractions:
            tags = conn.execute('''
                SELECT t.* FROM tags t
                JOIN attraction_tags at ON t.id = at.tag_id
                WHERE at.attraction_id = ?
            ''', (attr['id'],)).fetchall()
            
            duration_minutes = attr['recommended_duration']
            formatted_duration = f"约{duration_minutes // 60}小时" if duration_minutes >= 60 else f"约{duration_minutes}分钟"
            
            attractions_with_tags.append({
                'id': attr['id'],
                'name': attr['name'],
                'desc': attr['description'],
                'image': attr['image_url'],
                'address': attr['address'],
                'open_time': attr['open_time'],
                'recommended_duration': attr['recommended_duration'],
                'formatted_duration': formatted_duration,
                'rating': attr['rating'],
                'popularity': attr['popularity'],
                'tags': [dict(t) for t in tags],
                'recommend_reason': '根据您的偏好推荐'
            })
        
        route_recommendation = {
            'theme': theme or '综合',
            'duration': duration,
            'weather': weather,
            'attractions': attractions_with_tags,
            'reason': f"基于您选择的\"{theme or '综合'}\"主题和{'天气' if weather else '热度'}条件推荐",
            'schedule': [],
            'tips': '根据您的偏好推荐的景点，祝您旅途愉快！'
        }
        
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': route_recommendation,
            'request_id': str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500

@routes_bp.route('/llm/recommend', methods=['POST'])
def get_llm_recommend():
    try:
        data = request.get_json() or {}
        user_preferences = data.get('preferences', {})
        weather_info = data.get('weather', {})
        
        rec_service = RecommendationService()
        recommendation = rec_service.get_recommendation(user_preferences, weather_info)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': recommendation,
            'request_id': str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500

@routes_bp.route('/custom', methods=['POST'])
def create_custom_route():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'code': 400,
                'message': 'Request body is required',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 400
        
        name = data.get('name', '').strip()
        if not name:
            return jsonify({
                'code': 400,
                'message': '路线名称不能为空',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 400
        
        attraction_ids = data.get('attraction_ids', [])
        if not attraction_ids or not isinstance(attraction_ids, list):
            return jsonify({
                'code': 400,
                'message': '请至少选择一个景点',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 400
        
        conn = get_db_connection()
        
        for aid in attraction_ids:
            attraction = conn.execute('SELECT id FROM attractions WHERE id = ?', (aid,)).fetchone()
            if not attraction:
                conn.close()
                return jsonify({
                    'code': 404,
                    'message': f'景点ID {aid} 不存在',
                    'data': None,
                    'request_id': str(uuid.uuid4())
                }), 404
        
        cursor = conn.execute('''
            INSERT INTO routes (name, description, theme, duration)
            VALUES (?, ?, ?, ?)
        ''', (
            name,
            data.get('description', ''),
            data.get('theme', ''),
            data.get('duration', 0)
        ))
        route_id = cursor.lastrowid
        
        for order, aid in enumerate(attraction_ids, 1):
            conn.execute('''
                INSERT INTO route_attractions (route_id, attraction_id, order_num)
                VALUES (?, ?, ?)
            ''', (route_id, aid, order))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': '路线创建成功',
            'data': {'id': route_id, 'name': name},
            'request_id': str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500

@routes_bp.route('/custom', methods=['GET'])
def get_custom_routes():
    try:
        conn = get_db_connection()
        
        routes = conn.execute('''
            SELECT r.*, 
                   GROUP_CONCAT(a.name, ', ') as attraction_names
            FROM routes r
            LEFT JOIN route_attractions ra ON r.id = ra.route_id
            LEFT JOIN attractions a ON ra.attraction_id = a.id
            GROUP BY r.id
            ORDER BY r.created_at DESC
        ''').fetchall()
        
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [dict(r) for r in routes],
            'request_id': str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500
