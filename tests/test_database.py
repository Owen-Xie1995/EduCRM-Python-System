"""僅在明確指定 EDUCRM_TEST_MYSQL=1 時使用可清空的 *_test 資料庫。"""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from pathlib import Path
import unittest

import mysql.connector

from config import database_config
from database import DatabaseManager
from manage_database import migrate, set_password
from security import LegacyPasswordError, is_password_hash


@unittest.skipUnless(os.getenv('EDUCRM_TEST_MYSQL') == '1', '未指定獨立 MySQL 測試資料庫')
class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = database_config()
        if not config['database'].endswith('_test'):
            raise RuntimeError('整合測試只接受名稱以 _test 結尾的資料庫；測試會清空資料表')
        cls.connection = mysql.connector.connect(**config, autocommit=True)
        cls.cursor = cls.connection.cursor()
        cls.cursor.execute('SET FOREIGN_KEY_CHECKS=0')
        cls.cursor.execute('SHOW TABLES')
        for (table,) in cls.cursor.fetchall():
            cls.cursor.execute(f'DROP TABLE `{table.replace("`", "``")}`')
        cls.cursor.execute('SET FOREIGN_KEY_CHECKS=1')
        schema = Path(__file__).resolve().parents[1] / 'student_db.sql'
        for statement in schema.read_text().split(';'):
            if statement.strip():
                cls.cursor.execute(statement)
        cls.db = DatabaseManager(cls.connection)

    @classmethod
    def tearDownClass(cls):
        cls.cursor.close()
        cls.db.close()

    def setUp(self):
        self.cursor.execute('DELETE FROM attendance')
        self.cursor.execute('DELETE FROM payment_records')
        self.cursor.execute('DELETE FROM students_pro')
        self.cursor.execute('DELETE FROM courses')
        self.cursor.execute('DELETE FROM billing_runs')
        self.cursor.execute("UPDATE users SET password='' WHERE username='admin'")
        self.cursor.executemany('''
            INSERT INTO students_pro (student_id, name, parent_phone, status, tuition_balance)
            VALUES (%s, %s, '', %s, 10000)
        ''', [('S-A', '甲', '在學'), ('S-B', '乙', '在學'), ('S-C', '丙', '休學')])
        self.cursor.execute("INSERT INTO courses (course_id, course_name, base_fee) VALUES (1, '數學', 1000), (2, '英文', 2000)")
        for sid, course in [('S-A', 1), ('S-B', 2), ('S-C', 1)]:
            self.db.add_enrollment(sid, course)

    def balance(self, sid='S-A'):
        self.cursor.execute('SELECT tuition_balance FROM students_pro WHERE student_id=%s', (sid,))
        return self.cursor.fetchone()[0]

    def test_course_attendance_excludes_other_courses_and_inactive_students(self):
        self.assertEqual(self.db.fetch_course_students(1), [('S-A', '甲')])
        self.db.save_attendance(1, [('S-A', '出席')])
        with self.assertRaises(ValueError):
            self.db.save_attendance(1, [('S-B', '出席')])
        self.cursor.execute('SELECT student_id, status FROM attendance')
        self.assertEqual(self.cursor.fetchall(), [('S-A', '出席')])

    def test_duplicate_enrollment_rejected_and_not_double_billed(self):
        with self.assertRaises(ValueError):
            self.db.add_enrollment('S-A', 1)
        self.assertTrue(self.db.generate_smart_bills('2026-10'))
        self.assertEqual(self.balance(), 11000)

    def test_same_period_is_idempotent_next_period_can_bill(self):
        self.assertTrue(self.db.generate_smart_bills('2026-10'))
        self.assertFalse(self.db.generate_smart_bills('2026-10'))
        self.assertEqual(self.balance(), 11000)
        self.assertEqual(self.balance('S-C'), 10000)
        self.assertTrue(self.db.generate_smart_bills('2026-11'))
        self.assertEqual(self.balance(), 12000)

    def test_failed_bill_does_not_claim_period_or_partially_update_balances(self):
        self.cursor.execute('UPDATE students_pro SET tuition_balance=2147483647 WHERE student_id=%s', ('S-A',))
        with self.assertRaises(mysql.connector.Error):
            self.db.generate_smart_bills('2026-10')
        self.cursor.execute('SELECT COUNT(*) FROM billing_runs')
        self.assertEqual(self.cursor.fetchone()[0], 0)
        self.assertEqual(self.balance('S-B'), 10000)
        self.assertEqual(self.balance(), 2147483647)

    def test_payment_commits_balance_and_receipt_together(self):
        self.db.process_payment('S-A', '1500')
        self.assertEqual(self.balance(), 8500)
        self.cursor.execute('SELECT student_id, amount FROM payment_records')
        self.assertEqual(self.cursor.fetchall(), [('S-A', 1500)])

    def test_invalid_payment_and_overpayment_leave_balance_and_receipts_unchanged(self):
        for amount in ('-1', '0', 'abc', '10001'):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                self.db.process_payment('S-A', amount)
        with self.assertRaises(ValueError):
            self.db.process_payment('missing', '1')
        self.assertEqual(self.balance(), 10000)
        self.cursor.execute('SELECT COUNT(*) FROM payment_records')
        self.assertEqual(self.cursor.fetchone()[0], 0)

    def test_receipt_failure_rolls_back_balance_update(self):
        self.cursor.execute('ALTER TABLE payment_records RENAME TO payment_records_held')
        try:
            with self.assertRaises(mysql.connector.Error):
                self.db.process_payment('S-A', 1000)
            self.assertEqual(self.balance(), 10000)
        finally:
            self.cursor.execute('ALTER TABLE payment_records_held RENAME TO payment_records')

    def test_password_setup_and_legacy_migration(self):
        self.assertIsNone(self.db.authenticate('admin', ''))
        self.cursor.execute("UPDATE users SET password='1234' WHERE username='admin'")
        with self.assertRaises(LegacyPasswordError):
            self.db.authenticate('admin', '1234')
        self.assertEqual(migrate(self.connection, apply=False), 1)
        self.cursor.execute("SELECT password FROM users WHERE username='admin'")
        self.assertEqual(self.cursor.fetchone()[0], '1234')
        self.assertEqual(migrate(self.connection, apply=True), 1)
        self.cursor.execute("SELECT password FROM users WHERE username='admin'")
        self.assertTrue(is_password_hash(self.cursor.fetchone()[0]))
        self.assertEqual(self.db.authenticate('admin', '1234')[2], 'admin')
        self.assertIsNone(self.db.authenticate('admin', 'wrong'))
        self.assertEqual(migrate(self.connection, apply=True), 0)
        set_password(self.connection, 'admin', 'a-new-password')
        self.assertIsNone(self.db.authenticate('admin', '1234'))
        self.assertIsNotNone(self.db.authenticate('admin', 'a-new-password'))

    def test_migration_stops_without_deleting_duplicates_or_hashing_passwords(self):
        self.cursor.execute('ALTER TABLE enrollments DROP INDEX uq_student_course')
        try:
            self.db.add_enrollment('S-A', 1)
            self.cursor.execute("UPDATE users SET password='1234' WHERE username='admin'")
            with self.assertRaisesRegex(ValueError, '重複選課'):
                migrate(self.connection, apply=True)
            self.cursor.execute("SELECT password FROM users WHERE username='admin'")
            self.assertEqual(self.cursor.fetchone()[0], '1234')
            self.cursor.execute("SELECT COUNT(*) FROM enrollments WHERE student_id='S-A' AND course_id=1")
            self.assertEqual(self.cursor.fetchone()[0], 2)
        finally:
            # 測試資料可清空；正式遷移程式不會執行這個刪除。
            self.cursor.execute('DELETE FROM enrollments')
            self.cursor.execute('ALTER TABLE enrollments ADD UNIQUE KEY uq_student_course (student_id, course_id)')

    def test_concurrent_runs_cannot_bill_same_period_twice(self):
        barrier = Barrier(2)
        def bill():
            db = DatabaseManager()
            try:
                barrier.wait(timeout=10)
                return db.generate_smart_bills('2026-10')
            finally:
                db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: bill(), range(2)))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(self.balance(), 11000)

    def test_migration_adds_missing_schema_without_rewriting_existing_balances(self):
        self.cursor.execute('ALTER TABLE enrollments DROP INDEX uq_student_course')
        self.cursor.execute('DROP TABLE billing_runs')
        self.assertEqual(migrate(self.connection, apply=True), 0)
        self.assertEqual(self.balance(), 10000)
        with self.assertRaises(ValueError):
            self.db.add_enrollment('S-A', 1)
        self.assertTrue(self.db.generate_smart_bills('2026-10'))

    def test_empty_search_returns_empty_rows(self):
        self.assertEqual(self.db.search_students('不存在的學生'), [])


if __name__ == '__main__':
    unittest.main()
