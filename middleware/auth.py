"""
认证中间件
提供：login_required / admin_required / optional_login 装饰器
"""
from functools import wraps
from flask import request, jsonify, g
import uuid
from services.auth_service import verify_token, get_user_by_id


def login_required(f):
    """要求用户必须登录的装饰器（从请求头 Authorization: Bearer <token> 获取）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'code': 401,
                'message': '未提供有效的身份验证令牌',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 401

        token = auth_header[7:]
        payload = verify_token(token)
        if not payload:
            return jsonify({
                'code': 401,
                'message': '令牌无效或已过期',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 401

        if payload.get('type') != 'access':
            return jsonify({
                'code': 401,
                'message': '令牌类型错误',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 401

        user_id = int(payload['sub'])
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({
                'code': 401,
                'message': '用户不存在',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 401

        if user['status'] != 'active':
            return jsonify({
                'code': 403,
                'message': '账号已被禁用',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 403

        # 将当前用户信息注入 g 对象
        g.current_user = user
        g.current_user_id = user['id']
        g.current_user_role = user['role']

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """要求用户是管理员的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 先验证登录
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'code': 401,
                'message': '未提供有效的身份验证令牌',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 401

        token = auth_header[7:]
        payload = verify_token(token)
        if not payload:
            return jsonify({
                'code': 401,
                'message': '令牌无效或已过期',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 401

        if payload.get('type') != 'access':
            return jsonify({
                'code': 401,
                'message': '令牌类型错误',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 401

        user_id = int(payload['sub'])
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({
                'code': 401,
                'message': '用户不存在',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 401

        if user['status'] != 'active':
            return jsonify({
                'code': 403,
                'message': '账号已被禁用',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 403

        # 检查角色
        if user['role'] not in ('admin', 'super_admin'):
            return jsonify({
                'code': 403,
                'message': '权限不足，需要管理员权限',
                'data': None,
                'request_id': str(uuid.uuid4())
            }), 403

        g.current_user = user
        g.current_user_id = user['id']
        g.current_user_role = user['role']

        return f(*args, **kwargs)

    return decorated_function


def optional_login(f):
    """
    可选登录装饰器
    如果提供了有效的 Token，则将用户信息注入 g 对象
    如果没有提供 Token，g.current_user 为 None，继续执行
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            payload = verify_token(token)
            if payload and payload.get('type') == 'access':
                user_id = int(payload['sub'])
                user = get_user_by_id(user_id)
                if user and user['status'] == 'active':
                    g.current_user = user
                    g.current_user_id = user['id']
                    g.current_user_role = user['role']
                    return f(*args, **kwargs)

        # 未登录或 Token 无效
        g.current_user = None
        g.current_user_id = None
        g.current_user_role = None
        return f(*args, **kwargs)

    return decorated_function
