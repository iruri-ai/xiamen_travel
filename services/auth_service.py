"""
用户认证服务
提供：密码哈希、JWT Token 生成/验证、用户注册/登录/查询
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from database import get_db_connection

load_dotenv()

# JWT 配置
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'xiamen-travel-jwt-secret-key-2026')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRES = 3600 * 24       # 24 小时
JWT_REFRESH_TOKEN_EXPIRES = 3600 * 24 * 7  # 7 天


def hash_password(password: str) -> str:
    """对密码进行哈希处理"""
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return check_password_hash(password_hash, password)


def generate_access_token(user_id: int, role: str) -> str:
    """生成访问令牌（Access Token）"""
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user_id),
        'role': role,
        'type': 'access',
        'jti': str(uuid.uuid4()),
        'iat': now,
        'exp': now + timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def generate_refresh_token(user_id: int) -> str:
    """生成刷新令牌（Refresh Token）"""
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user_id),
        'type': 'refresh',
        'jti': str(uuid.uuid4()),
        'iat': now,
        'exp': now + timedelta(seconds=JWT_REFRESH_TOKEN_EXPIRES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """验证 Token，返回 payload（验证失败返回 None）"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_by_id(user_id: int):
    """根据用户 ID 获取用户信息"""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT id, username, email, nickname, avatar_url, phone, role, status, last_login_at, created_at '
        'FROM users WHERE id = ?', (user_id,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_username(username: str):
    """根据用户名获取用户信息"""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT id, username, email, nickname, avatar_url, phone, role, status, last_login_at, created_at '
        'FROM users WHERE username = ?', (username,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_email(email: str):
    """根据邮箱获取用户信息"""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT id, username, email, nickname, avatar_url, phone, role, status, last_login_at, created_at '
        'FROM users WHERE email = ?', (email,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def create_user(username: str, password: str, email: str = None, nickname: str = None):
    """
    创建新用户
    返回: (success, message, user_dict)
    """
    # 参数验证
    username = username.strip()
    if len(username) < 2 or len(username) > 50:
        return False, '用户名长度必须在2-50个字符之间', None

    if len(password) < 6:
        return False, '密码长度不能少于6位', None

    if email:
        email = email.strip()
        if '@' not in email or '.' not in email:
            return False, '邮箱格式不正确', None

    conn = get_db_connection()
    try:
        # 检查用户名是否已存在
        existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            return False, '用户名已被注册', None

        # 检查邮箱是否已存在
        if email:
            existing_email = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            if existing_email:
                return False, '邮箱已被注册', None

        # 创建用户
        password_hash = hash_password(password)
        nickname = nickname or username

        cursor = conn.execute('''
            INSERT INTO users (username, email, password_hash, nickname, role, status)
            VALUES (?, ?, ?, ?, 'user', 'active')
        ''', (username, email, password_hash, nickname))

        user_id = cursor.lastrowid

        # 默认分配普通用户角色
        user_role = conn.execute('SELECT id FROM roles WHERE code = ?', ('user',)).fetchone()
        if user_role:
            conn.execute('INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)',
                         (user_id, user_role['id']))

        conn.commit()

        user = get_user_by_id(user_id)
        return True, '注册成功', user

    except Exception as e:
        conn.rollback()
        return False, f'注册失败: {str(e)}', None
    finally:
        conn.close()


def authenticate_user(username: str, password: str):
    """
    验证用户登录
    返回: (success, message, token_data)
    """
    conn = get_db_connection()
    try:
        user = conn.execute(
            'SELECT id, username, email, nickname, avatar_url, role, status, password_hash '
            'FROM users WHERE username = ? OR email = ?',
            (username, username)
        ).fetchone()

        if not user:
            return False, '用户名或密码错误', None

        # 检查状态
        if user['status'] != 'active':
            return False, '账号已被禁用或已停用', None

        # 验证密码
        if not verify_password(password, user['password_hash']):
            return False, '用户名或密码错误', None

        # 更新最后登录时间
        conn.execute("UPDATE users SET last_login_at = datetime('now', 'localtime') WHERE id = ?", (user['id'],))
        conn.commit()

        # 生成 Token
        user_id = user['id']
        access_token = generate_access_token(user_id, user['role'])
        refresh_token = generate_refresh_token(user_id)

        user_data = {
            'id': user_id,
            'username': user['username'],
            'email': user['email'],
            'nickname': user['nickname'],
            'avatar_url': user['avatar_url'],
            'role': user['role'],
        }

        token_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': JWT_ACCESS_TOKEN_EXPIRES,
            'user': user_data
        }

        return True, '登录成功', token_data

    except Exception as e:
        return False, f'登录失败: {str(e)}', None
    finally:
        conn.close()


def refresh_access_token(refresh_token: str):
    """
    使用 Refresh Token 刷新 Access Token
    返回: (success, message, token_data)
    """
    payload = verify_token(refresh_token)
    if not payload:
        return False, 'Refresh Token 无效或已过期', None

    if payload.get('type') != 'refresh':
        return False, 'Token 类型错误', None

    user_id = int(payload['sub'])
    user = get_user_by_id(user_id)
    if not user:
        return False, '用户不存在', None

    if user['status'] != 'active':
        return False, '账号已被禁用', None

    new_access_token = generate_access_token(user_id, user['role'])
    new_refresh_token = generate_refresh_token(user_id)

    return True, 'Token 刷新成功', {
        'access_token': new_access_token,
        'refresh_token': new_refresh_token,
        'token_type': 'Bearer',
        'expires_in': JWT_ACCESS_TOKEN_EXPIRES,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'nickname': user['nickname'],
            'avatar_url': user['avatar_url'],
            'role': user['role'],
        }
    }
