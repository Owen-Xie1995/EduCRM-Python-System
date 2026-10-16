"""資料庫維護入口。請停止桌面程式並備份後執行遷移。"""
import argparse
from getpass import getpass

import mysql.connector

from config import database_config
from security import hash_password, hash_legacy_password, is_password_hash


def find_duplicate_enrollments(cursor):
    cursor.execute('''
        SELECT student_id, course_id, COUNT(*) FROM enrollments
        GROUP BY student_id, course_id HAVING COUNT(*) > 1
    ''')
    return cursor.fetchall()


def has_enrollment_unique_key(cursor):
    cursor.execute('''
        SELECT INDEX_NAME, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX)
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'enrollments' AND NON_UNIQUE = 0
        GROUP BY INDEX_NAME
    ''')
    return any(columns in ('student_id,course_id', 'course_id,student_id') for _, columns in cursor.fetchall())


def migrate(connection, apply=False):
    """先檢查重複選課；不刪資料。DDL 可重跑，密碼更新另外使用交易。"""
    cursor = connection.cursor()
    try:
        duplicates = find_duplicate_enrollments(cursor)
        if duplicates:
            raise ValueError(
                '發現重複選課，遷移尚未變更任何資料。請核對並自行處理後重跑：'
                + repr(duplicates)
            )
        cursor.execute('SELECT user_id, password FROM users')
        legacy = [(uid, password) for uid, password in cursor.fetchall()
                  if password and not is_password_hash(password)]
        if not apply:
            return len(legacy)
        if not has_enrollment_unique_key(cursor):
            cursor.execute('ALTER TABLE enrollments ADD UNIQUE KEY uq_student_course (student_id, course_id)')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS billing_runs (
                period CHAR(7) NOT NULL PRIMARY KEY,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        connection.start_transaction()
        try:
            for uid, password in legacy:
                cursor.execute('UPDATE users SET password=%s WHERE user_id=%s',
                               (hash_legacy_password(password), uid))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        return len(legacy)
    finally:
        cursor.close()


def set_password(connection, username, password):
    encoded = hash_password(password)
    cursor = connection.cursor()
    try:
        cursor.execute('UPDATE users SET password=%s WHERE username=%s', (encoded, username))
        if cursor.rowcount != 1:
            raise ValueError('找不到此帳號，請先確認 users 資料表')
        connection.commit()
    finally:
        cursor.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db-user', help='此次使用的維護帳號，密碼會另外詢問')
    commands = parser.add_subparsers(dest='command', required=True)
    migration = commands.add_parser('migrate', help='檢查或套用舊資料遷移')
    migration.add_argument('--apply', action='store_true', help='未指定時只檢查，不寫入')
    migration.add_argument('--backup-confirmed', action='store_true', help='確認已停止程式並完成可還原的備份')
    password = commands.add_parser('set-password', help='為既有帳號設定新密碼')
    password.add_argument('username')
    args = parser.parse_args()
    if args.command == 'migrate' and args.apply and not args.backup_confirmed:
        parser.error('套用前請先停止程式、備份資料，再加上 --backup-confirmed')
    config = database_config()
    if args.db_user:
        config['user'] = args.db_user
        config['password'] = getpass('維護帳號的資料庫密碼：')
    connection = mysql.connector.connect(**config, autocommit=True)
    try:
        if args.command == 'migrate':
            count = migrate(connection, apply=args.apply)
            print(f'遷移完成，已轉換 {count} 個舊密碼。' if args.apply else
                  f'檢查通過，有 {count} 個舊密碼待轉換；尚未寫入。')
        else:
            new_password = getpass('新密碼（至少 8 字元）：')
            if new_password != getpass('再次輸入：'):
                raise ValueError('兩次密碼不相同')
            set_password(connection, args.username, new_password)
            print('密碼已更新。')
    finally:
        connection.close()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, mysql.connector.Error) as exc:
        raise SystemExit(f'未完成：{exc}')
