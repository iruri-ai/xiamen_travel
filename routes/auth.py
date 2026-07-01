"""
用户认证路由
提供：注册、登录、刷新 Token、获取当前用户信息
"""
from flask import Blueprint, jsonify, request, g
import uuid
import re
from middleware.auth import login_required
from database import get_db_connection
from services.auth_service import (
    create_user,
    authenticate_user,
    refresh_access_token,
    get_user_by_id
)

auth_bp = Blueprint('auth', __name__)


def success_response(data=None, message='success', code=200):
    """统一成功响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': data,
        'request_id': str(uuid.uuid4())
    })


def error_response(message, code=400):
    """统一错误响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': None,
        'request_id': str(uuid.uuid4())
    }), code


# -----------------------------------------------------------
# POST /api/auth/register - 用户注册
# -----------------------------------------------------------
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册
    ---
    请求体（JSON）:
        username: str (必填, 2-50字符)
        password: str (必填, 不少于6位)
        email:    str (可选, 邮箱格式)
        nickname: str (可选, 默认同 username)
    返回:
        成功: { code: 200, message: '注册成功', data: { user, access_token, ... } }
        失败: { code: 4xx, message: '错误说明', data: null }
    """
    try:
        data = request.get_json()
        if not data:
            return error_response('请求体不能为空', 400)

        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip() or None
        nickname = data.get('nickname', '').strip() or None

        # 必填字段检查
        if not username:
            return error_response('用户名不能为空', 400)
        if not password:
            return error_response('密码不能为空', 400)

        success, message, user = create_user(username, password, email, nickname)
        if not success:
            return error_response(message, 409 if '已被' in message else 400)

        # 注册成功后自动登录
        log_success, log_message, token_data = authenticate_user(username, password)
        if log_success:
            return success_response(token_data, '注册成功')
        else:
            return success_response({'user': user}, '注册成功，请登录')

    except Exception as e:
        return error_response(f'注册失败: {str(e)}', 500)


# -----------------------------------------------------------
# POST /api/auth/login - 用户登录
# -----------------------------------------------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    ---
    请求体（JSON）:
        username: str (必填, 支持用户名或邮箱)
        password: str (必填)
    返回:
        成功: { code: 200, message: '登录成功',
                data: { access_token, refresh_token, token_type, expires_in, user } }
        失败: { code: 4xx, message: '错误说明', data: null }
    """
    try:
        data = request.get_json()
        if not data:
            return error_response('请求体不能为空', 400)

        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username:
            return error_response('用户名不能为空', 400)
        if not password:
            return error_response('密码不能为空', 400)

        success, message, token_data = authenticate_user(username, password)
        if not success:
            return error_response(message, 401)

        return success_response(token_data, '登录成功')

    except Exception as e:
        return error_response(f'登录失败: {str(e)}', 500)


# -----------------------------------------------------------
# POST /api/auth/refresh - 刷新 Access Token
# -----------------------------------------------------------
@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    刷新 Token
    ---
    请求体（JSON）:
        refresh_token: str (必填)
    返回:
        成功: { code: 200, message: 'Token 刷新成功', data: { access_token, refresh_token, ... } }
        失败: { code: 4xx, message: '错误说明', data: null }
    """
    try:
        data = request.get_json()
        if not data or not data.get('refresh_token'):
            return error_response('refresh_token 不能为空', 400)

        success, message, token_data = refresh_access_token(data['refresh_token'])
        if not success:
            return error_response(message, 401)

        return success_response(token_data, 'Token 刷新成功')

    except Exception as e:
        return error_response(f'刷新失败: {str(e)}', 500)


# -----------------------------------------------------------
# GET /api/auth/me - 获取当前登录用户信息
# -----------------------------------------------------------
@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """
    获取当前登录用户信息（需要 Authorization: Bearer <token>）
    ---
    返回: { code: 200, data: { id, username, email, nickname, avatar_url, role, ... } }
    """
    user = get_user_by_id(g.current_user_id)
    if not user:
        return error_response('用户不存在', 404)
    return success_response(user)


# -----------------------------------------------------------
# PUT /api/auth/profile - 更新用户资料（昵称、邮箱等）
# -----------------------------------------------------------
@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        if not data:
            return error_response('请求体不能为空', 400)
        
        user_id = g.current_user_id
        
        conn = get_db_connection()
        
        updates = []
        params = []
        
        if 'nickname' in data:
            nickname = data['nickname'].strip()
            if len(nickname) > 50:
                conn.close()
                return error_response('昵称长度不能超过50个字符', 400)
            updates.append('nickname = ?')
            params.append(nickname)
            
            c_cursor = conn.execute('UPDATE comments SET username = ? WHERE user_id = ?', (nickname[:50], user_id))
            c_count = c_cursor.rowcount
            conn.commit()
        
        if 'email' in data:
            email = data['email'].strip()
            if email and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                conn.close()
                return error_response('邮箱格式不正确', 400)
            
            if email:
                existing = conn.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, user_id)).fetchone()
                if existing:
                    conn.close()
                    return error_response('该邮箱已被使用', 409)
            
            updates.append('email = ?')
            params.append(email)
        
        if 'phone' in data:
            updates.append('phone = ?')
            params.append(data['phone'].strip())
        
        if 'avatar_url' in data:
            updates.append('avatar_url = ?')
            params.append(data['avatar_url'].strip())
        
        if not updates:
            conn.close()
            return error_response('没有需要更新的字段', 400)
        
        updates.append("updated_at = datetime('now', 'localtime')")
        params.append(user_id)
        
        query = f'UPDATE users SET {", ".join(updates)} WHERE id = ?'
        conn.execute(query, params)
        conn.commit()
        
        user = conn.execute(
            'SELECT id, username, email, nickname, avatar_url, phone, role, status, last_login_at, created_at FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
        conn.close()
        
        result = dict(user) if user else {}
        if 'nickname' in data:
            result['comments_updated'] = c_count
            result['nickname_used'] = nickname[:50]
        
        return success_response(result, '更新成功')
        
    except Exception as e:
        return error_response(f'更新失败: {str(e)}', 500)


# -----------------------------------------------------------
# POST /api/auth/logout - 退出登录（客户端删除 Token 即可）
# -----------------------------------------------------------
@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    退出登录（客户端端删除 Token 即可，此接口仅用于通知服务端）
    ---
    返回: { code: 200, message: '退出成功' }
    """
    return success_response(None, '退出成功')
