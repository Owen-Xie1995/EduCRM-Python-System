"""密碼僅儲存含隨機 salt 的 PBKDF2-SHA256 雜湊。"""
import hashlib
import hmac
import secrets

ALGORITHM = 'pbkdf2_sha256'
ITERATIONS = 600_000


class LegacyPasswordError(ValueError):
    pass


def is_password_hash(value):
    return isinstance(value, str) and value.startswith(ALGORITHM + '$')


def hash_password(password):
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError('新密碼至少需要 8 個字元')
    return hash_legacy_password(password)


def hash_legacy_password(password):
    """僅供明確執行的舊資料遷移，保留既有短密碼，之後應重設。"""
    if not isinstance(password, str) or not password:
        raise ValueError('空密碼無法遷移，請重設密碼')
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f'{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}'


def verify_password(password, encoded):
    if not is_password_hash(encoded) or not isinstance(password, str):
        return False
    try:
        algorithm, rounds, salt, expected = encoded.split('$')
        rounds = int(rounds)
        if not 100_000 <= rounds <= 2_000_000:
            return False
        salt = bytes.fromhex(salt)
        expected = bytes.fromhex(expected)
        if len(salt) != 16 or len(expected) != 32:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, rounds)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False
