"""基于 Supabase 的账号注册/登录：app_accounts 表存用户名与密码哈希。"""
import os
import re
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# 用户名规则：与现有 account_name 一致，便于作为 users.id
USERNAME_PATTERN = re.compile(r"^[\w\s\u4e00-\u9fa5-]+$")
USERNAME_MIN_LEN = 1
USERNAME_MAX_LEN = 20
PASSWORD_MIN_LEN = 8


def _get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ValueError("需要设置 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY")
    from supabase import create_client
    return create_client(url, key)


# bcrypt 最多 72 字节，超出部分截断（与 passlib+bcrypt5 兼容性问题的规避）
BCRYPT_MAX_BYTES = 72


def _hash_password(password: str) -> str:
    import bcrypt
    raw = password.encode("utf-8")
    if len(raw) > BCRYPT_MAX_BYTES:
        raw = raw[:BCRYPT_MAX_BYTES]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(raw, salt).decode("ascii")


def _verify_password(plain: str, hashed: str) -> bool:
    import bcrypt
    try:
        raw = plain.encode("utf-8")
        if len(raw) > BCRYPT_MAX_BYTES:
            raw = raw[:BCRYPT_MAX_BYTES]
        return bcrypt.checkpw(raw, hashed.encode("ascii"))
    except Exception:
        return False


def validate_username(username: str) -> Optional[str]:
    """校验用户名格式，不符合则返回错误信息。"""
    if not username or not username.strip():
        return "用户名不能为空"
    if not USERNAME_PATTERN.match(username):
        return "用户名只能包含字母、数字、中文、下划线和连字符"
    if len(username) > USERNAME_MAX_LEN:
        return f"用户名不能超过{USERNAME_MAX_LEN}个字符"
    return None


def validate_password(password: str) -> Optional[str]:
    """校验密码长度，不符合则返回错误信息。"""
    if len(password) < PASSWORD_MIN_LEN:
        return f"密码至少{PASSWORD_MIN_LEN}个字符"
    return None


def register_account(username: str, password: str) -> Tuple[bool, str]:
    """
    注册账号：写入 app_accounts。用户名需唯一。
    返回 (成功, 消息)。
    """
    err = validate_username(username)
    if err:
        return False, err
    err = validate_password(password)
    if err:
        return False, err
    try:
        client = _get_supabase()
        r = client.table("app_accounts").select("username").eq("username", username).execute()
        if r.data and len(r.data) > 0:
            return False, "该用户名已被使用"
        password_hash = _hash_password(password)
        client.table("app_accounts").insert({
            "username": username.strip(),
            "password_hash": password_hash,
        }).execute()
        return True, "注册成功"
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False, "该用户名已被使用"
        logger.exception("register_account: %s", e)
        return False, "注册失败，请稍后重试"


def verify_account(username: str, password: str) -> Tuple[bool, str]:
    """
    验证账号：查 app_accounts 并校验密码。
    返回 (是否通过, 错误信息，通过时错误信息为空)。
    """
    if not username or not username.strip():
        return False, "请输入用户名"
    if not password:
        return False, "请输入密码"
    try:
        client = _get_supabase()
        r = client.table("app_accounts").select("username, password_hash").eq("username", username.strip()).execute()
        if not r.data or len(r.data) == 0:
            return False, "用户名或密码错误"
        row = r.data[0]
        if not _verify_password(password, row["password_hash"]):
            return False, "用户名或密码错误"
        return True, ""
    except Exception as e:
        logger.exception("verify_account: %s", e)
        return False, "登录失败，请稍后重试"
