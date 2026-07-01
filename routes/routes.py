from flask import Blueprint, jsonify, request, g
import uuid
import json
from database import get_db_connection
from services.recommendation import RecommendationService
from middleware.auth import login_required

routes_bp = Blueprint('routes', __name__)

BREAKFAST_START = 7 * 60
BREAKFAST_END = 9 * 60 + 30
LUNCH_START = 11 * 60 + 30
LUNCH_END = 13 * 60 + 30
DINNER_START = 17 * 60 + 30
DINNER_END = 20 * 60
MAX_END_TIME = 22 * 60

DURATION_MAP = {
    '2小时': 120,
    '半天': 240,
    '全天': 480
}

def parse_duration(duration_str):
    if isinstance(duration_str, int):
        return duration_str
    if duration_str in DURATION_MAP:
        return DURATION_MAP[duration_str]
    try:
        return int(duration_str)
    except (ValueError, TypeError):
        return 480

def skip_meal_time(current_time):
    if BREAKFAST_START <= current_time < BREAKFAST_END:
        return BREAKFAST_END
    if LUNCH_START <= current_time < LUNCH_END:
        return LUNCH_END
    if DINNER_START <= current_time < DINNER_END:
        return DINNER_END
    return current_time

def save_recommendation_to_db(user_id, route_recommendation, query_type, user_preferences=None, weather_info=None):
    conn = get_db_connection()
    try:
        attractions = route_recommendation.get('attractions', [])
        attraction_ids = [a['id'] for a in attractions]
        
        preferences = user_preferences if user_preferences else route_recommendation.get('preferences', {})
        themes = preferences.get('themes', [])
        
        duration_str = preferences.get('duration', '全天')
        if isinstance(duration_str, int):
            for k, v in DURATION_MAP.items():
                if v == duration_str:
                    duration_str = k
                    break
        
        theme_str = ','.join(themes) if themes else route_recommendation.get('theme', '')
        theme_display = '、'.join(themes) if themes else theme_str
        
        if not theme_display:
            theme_display = '综合'
            theme_str = '综合'
        
        name = f'{theme_display}推荐路线'
        
        weather = weather_info if weather_info else route_recommendation.get('weather', '')
        if isinstance(weather, dict):
            weather = weather.get('weather', '')
        
        source = route_recommendation.get('source', '')
        if source == 'rule-based' and query_type == 'llm':
            query_type = 'simple'
        
        cursor = conn.execute('''
            INSERT INTO routes (user_id, name, description, theme, duration, difficulty, query_type, weather, result_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
        ''', (
            user_id,
            name,
            route_recommendation.get('reason', ''),
            theme_str,
            duration_str,
            'easy',
            query_type,
            weather,
            json.dumps(route_recommendation)
        ))
        route_id = cursor.lastrowid
        
        schedule = route_recommendation.get('schedule', [])
        schedule_map = {s.get('attraction_id'): s for s in schedule}
        
        for order, aid in enumerate(attraction_ids, 1):
            sched = schedule_map.get(aid, {})
            conn.execute('''
                INSERT INTO route_attractions (route_id, attraction_id, order_num, start_time, end_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (route_id, aid, order, sched.get('start_time'), sched.get('end_time')))
        
        conn.commit()
        return route_id
    finally:
        conn.close()

@routes_bp.route('/recommend', methods=['GET'])
@login_required
def get_recommend_routes():
    try:
        theme = request.args.get('theme', '')
        duration_str = request.args.get('duration', '全天')
        duration = parse_duration(duration_str)
        weather = request.args.get('weather', '')
        user_id = g.current_user_id
        
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
        
        conn.close()
        
        schedule = []
        current_time = 9 * 60
        remaining_time = duration
        scheduled_attractions = []
        
        target_num = 1
        
        if duration <= 120:
            target_num = 1
        elif duration <= 240:
            target_num = 2
        elif duration <= 360:
            target_num = 3
        else:
            target_num = 4
        
        target_num = min(target_num, len(attractions_with_tags))
        
        top_attrs = sorted(attractions_with_tags, key=lambda x: -x['popularity'])[:target_num]
        
        total_recommended = sum(a['recommended_duration'] for a in top_attrs)
        buffer_time = (target_num - 1) * 30
        available_time = duration - buffer_time
        
        if available_time <= 0:
            top_attrs = top_attrs[:1]
            available_time = duration
        
        ratio = min(1.0, available_time / total_recommended) if total_recommended > 0 else 1.0
        
        selected_ids = []
        for attr in top_attrs:
            adjusted_duration = max(30, int(attr['recommended_duration'] * ratio))
            attr_copy = attr.copy()
            attr_copy['recommended_duration'] = adjusted_duration
            attr_copy['formatted_duration'] = f"约{adjusted_duration // 60}小时" if adjusted_duration >= 60 else f"约{adjusted_duration}分钟"
            selected_ids.append(attr_copy)
        
        order = 1
        for attr in selected_ids:
            current_time = skip_meal_time(current_time)
            
            if current_time > MAX_END_TIME:
                current_time = MAX_END_TIME
            
            time_needed = attr['recommended_duration']
            end_time = current_time + time_needed
            
            if end_time > MAX_END_TIME:
                end_time = MAX_END_TIME
            
            start_hour = current_time // 60
            start_min = current_time % 60
            start_str = f"{start_hour:02d}:{start_min:02d}"
            
            end_hour = end_time // 60
            end_min = end_time % 60
            end_str = f"{end_hour:02d}:{end_min:02d}"
            
            schedule.append({
                'attraction_id': attr['id'],
                'order': order,
                'start_time': start_str,
                'end_time': end_str,
                'duration': end_time - current_time
            })
            
            scheduled_attractions.append(attr)
            current_time = end_time + 30
            order += 1
        
        total_duration = sum(s.get('duration', 0) for s in schedule)
        if len(schedule) > 1:
            total_duration += (len(schedule) - 1) * 30
        
        attractions_with_tags = scheduled_attractions
        
        route_recommendation = {
            'theme': theme or '综合',
            'duration': duration_str,
            'total_minutes': total_duration,
            'weather': weather,
            'attractions': attractions_with_tags,
            'reason': f"基于您选择的\"{theme or '综合'}\"主题和{'天气' if weather else '热度'}条件推荐",
            'schedule': schedule,
            'tips': '根据您的偏好推荐的景点，祝您旅途愉快！'
        }
        
        save_recommendation_to_db(user_id, route_recommendation, 'simple', {'duration': duration_str, 'themes': [theme] if theme else []})
        
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
@login_required
def get_llm_recommend():
    try:
        data = request.get_json() or {}
        user_preferences = data.get('preferences', {})
        weather_info = data.get('weather', {})
        user_id = g.current_user_id
        
        rec_service = RecommendationService()
        recommendation = rec_service.get_recommendation(user_preferences, weather_info)
        
        save_recommendation_to_db(user_id, recommendation, 'llm', user_preferences, weather_info)
        
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
@login_required
def create_custom_route():
    try:
        data = request.get_json()
        user_id = g.current_user_id
        
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
        
        attractions_info = {}
        for aid in attraction_ids:
            attraction = conn.execute('SELECT id, recommended_duration FROM attractions WHERE id = ?', (aid,)).fetchone()
            if not attraction:
                conn.close()
                return jsonify({
                    'code': 404,
                    'message': f'景点ID {aid} 不存在',
                    'data': None,
                    'request_id': str(uuid.uuid4())
                }), 404
            attractions_info[aid] = dict(attraction)
        
        current_time = 9 * 60
        scheduled_ids = []
        schedule_total = 0
        
        for aid in attraction_ids:
            current_time = skip_meal_time(current_time)
            
            if current_time > MAX_END_TIME:
                current_time = MAX_END_TIME
            
            dur_minutes = attractions_info[aid]['recommended_duration']
            end_time = current_time + dur_minutes
            
            if end_time > MAX_END_TIME:
                end_time = MAX_END_TIME
            
            scheduled_ids.append(aid)
            schedule_total += (end_time - current_time)
            current_time = end_time + 30
        
        if len(scheduled_ids) > 1:
            schedule_total += (len(scheduled_ids) - 1) * 30
        
        if schedule_total >= 60:
            duration_text = f"约{schedule_total // 60}小时"
            if schedule_total % 60 >= 30:
                duration_text += "半"
        else:
            duration_text = f"约{schedule_total}分钟"
        
        cursor = conn.execute('''
            INSERT INTO routes (user_id, name, description, theme, duration, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
        ''', (
            user_id,
            name,
            data.get('description', ''),
            data.get('theme', ''),
            duration_text
        ))
        route_id = cursor.lastrowid
        
        current_time = 9 * 60
        for order, aid in enumerate(scheduled_ids, 1):
            current_time = skip_meal_time(current_time)
            
            start_hour = current_time // 60
            start_min = current_time % 60
            start_str = f"{start_hour:02d}:{start_min:02d}"
            
            dur_minutes = attractions_info[aid]['recommended_duration']
            end_time = current_time + dur_minutes
            
            if end_time > MAX_END_TIME:
                end_time = MAX_END_TIME
            
            end_hour = end_time // 60
            end_min = end_time % 60
            end_str = f"{end_hour:02d}:{end_min:02d}"
            
            conn.execute('''
                INSERT INTO route_attractions (route_id, attraction_id, order_num, start_time, end_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (route_id, aid, order, start_str, end_str))
            
            current_time = end_time + 30
        
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
@login_required
def get_custom_routes():
    try:
        user_id = g.current_user_id
        conn = get_db_connection()
        
        routes = conn.execute('''
            SELECT r.*, 
                   GROUP_CONCAT(a.name, ', ') as attraction_names
            FROM routes r
            LEFT JOIN route_attractions ra ON r.id = ra.route_id
            LEFT JOIN attractions a ON ra.attraction_id = a.id
            WHERE r.user_id = ?
            GROUP BY r.id
            ORDER BY r.created_at DESC
        ''', (user_id,)).fetchall()
        
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
