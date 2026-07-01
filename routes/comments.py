from flask import Blueprint, jsonify, request, g
import uuid
import re
from database import get_db_connection
from middleware.auth import login_required, admin_required

comments_bp = Blueprint('comments', __name__)

def validate_comment_data(data):
    errors = []
    
    if not data.get('attraction_id'):
        errors.append('景点ID不能为空')
    elif not isinstance(data.get('attraction_id'), int) or data['attraction_id'] <= 0:
        errors.append('景点ID格式不正确')
    
    content = data.get('content', '').strip()
    if not content:
        errors.append('评论内容不能为空')
    elif len(content) > 1000:
        errors.append('评论内容不能超过1000字')
    
    username = data.get('username', '游客').strip()
    if len(username) > 50:
        errors.append('用户名不能超过50字')
    
    rating = data.get('rating', 5)
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        errors.append('评分必须在1-5之间')
    
    return errors

def format_time(created_at):
    import datetime
    try:
        if isinstance(created_at, str):
            created_time = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        else:
            created_time = created_at
        
        now = datetime.datetime.now()
        diff = now - created_time
        
        if diff.days > 0:
            return f'{diff.days}天前'
        elif diff.seconds >= 3600:
            return f'{diff.seconds // 3600}小时前'
        elif diff.seconds >= 60:
            return f'{diff.seconds // 60}分钟前'
        else:
            return '刚刚'
    except:
        return str(created_at)

@comments_bp.route('', methods=['GET'])
def get_comments():
    try:
        attraction_id = request.args.get('attraction_id', type=int)
        user_id = request.args.get('user_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        page = max(1, page)
        per_page = max(1, min(per_page, 50))
        
        valid_sort_fields = ['created_at', 'rating', 'id']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'
        
        sort_order = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
        
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        
        conditions = []
        params = []
        
        if attraction_id:
            conditions.append('attraction_id = ?')
            params.append(attraction_id)
        
        if user_id:
            conditions.append('user_id = ?')
            params.append(user_id)
        
        if conditions:
            where_clause = ' WHERE ' + ' AND '.join(conditions)
        else:
            where_clause = ''
        
        total_query = f'SELECT COUNT(*) as count FROM comments{where_clause}'
        total = conn.execute(total_query, params).fetchone()['count']
        
        order_clause = f'ORDER BY {sort_by} {sort_order}'
        
        comments_query = f'''
            SELECT c.*, 
                   a.name as attraction_name,
                   a.image_url as attraction_image
            FROM comments c
            LEFT JOIN attractions a ON c.attraction_id = a.id
            {where_clause}
            {order_clause}
            LIMIT ? OFFSET ?
        '''
        
        comments = conn.execute(comments_query, params + [per_page, offset]).fetchall()
        
        conn.close()
        
        formatted_comments = []
        for c in comments:
            c_dict = dict(c)
            formatted_comments.append({
                'id': c_dict['id'],
                'user_id': c_dict.get('user_id'),
                'username': c_dict['username'],
                'content': c_dict['content'],
                'rating': c_dict['rating'],
                'rating_stars': '★' * int(c_dict['rating']),
                'created_at': c_dict['created_at'],
                'formatted_time': format_time(c_dict['created_at']),
                'attraction_id': c_dict['attraction_id'],
                'attraction_name': c_dict.get('attraction_name'),
                'attraction_image': c_dict.get('attraction_image')
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'items': formatted_comments,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page if total > 0 else 0,
                'sort_by': sort_by,
                'sort_order': sort_order.lower()
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

@comments_bp.route('', methods=['POST'])
@login_required
def create_comment():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'code': 400,
                'message': 'Request body is required',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 400
        
        errors = validate_comment_data(data)
        if errors:
            return jsonify({
                'code': 400,
                'message': '; '.join(errors),
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 400
        
        conn = get_db_connection()
        
        attraction = conn.execute('SELECT id FROM attractions WHERE id = ?', 
                                 (data['attraction_id'],)).fetchone()
        if not attraction:
            conn.close()
            return jsonify({
                'code': 404,
                'message': '景点不存在',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 404
        
        content = re.sub(r'<[^>]+>', '', data['content'].strip())
        
        user_id = g.current_user_id
        user = conn.execute('SELECT username, nickname FROM users WHERE id = ?', (user_id,)).fetchone()
        username = user['nickname'] or user['username'] if user else '游客'
        
        cursor = conn.execute('''
            INSERT INTO comments (attraction_id, user_id, username, content, rating, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
        ''', (
            data['attraction_id'],
            user_id,
            username[:50],
            content,
            data.get('rating', 5)
        ))
        
        conn.commit()
        comment_id = cursor.lastrowid
        
        new_comment = conn.execute('SELECT * FROM comments WHERE id = ?', (comment_id,)).fetchone()
        conn.close()
        
        formatted_comment = {
            'id': new_comment['id'],
            'username': new_comment['username'],
            'content': new_comment['content'],
            'rating': new_comment['rating'],
            'rating_stars': '★' * int(new_comment['rating']),
            'created_at': new_comment['created_at'],
            'formatted_time': '刚刚'
        }
        
        return jsonify({
            'code': 200,
            'message': '评论提交成功',
            'data': formatted_comment,
            'request_id': str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500

@comments_bp.route('/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    try:
        conn = get_db_connection()
        
        comment = conn.execute('SELECT * FROM comments WHERE id = ?', (comment_id,)).fetchone()
        
        if not comment:
            conn.close()
            return jsonify({
                'code': 404,
                'message': '评论不存在',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 404
        
        current_user_id = g.current_user_id
        
        user = conn.execute('SELECT role FROM users WHERE id = ?', (current_user_id,)).fetchone()
        is_admin = user and user['role'] in ('admin', 'super_admin')
        
        if comment['user_id'] != current_user_id and not is_admin:
            conn.close()
            return jsonify({
                'code': 403,
                'message': '无权删除此评论',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 403
        
        conn.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': '评论删除成功',
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
