"""MySQL 資料存取與需要交易保護的業務操作。"""
from datetime import datetime

import mysql.connector

from config import database_config
from security import LegacyPasswordError, hash_password, is_password_hash, verify_password
from validation import validate_billing_period, validate_payment_amount


class DatabaseManager:
    def __init__(self, connection=None):
        self.conn = connection or mysql.connector.connect(**database_config(), autocommit=True)
        self.cursor = self.conn.cursor()
        # 舊 SQL dump 會關閉嚴格模式，應用連線需拒絕截斷或超出範圍的數值。
        self.cursor.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION'")

    def close(self):
        self.cursor.close()
        self.conn.close()

    def authenticate(self, username, password):
        self.cursor.execute(
            "SELECT user_id, real_name, role, password FROM users WHERE username=%s",
            (username,),
        )
        user = self.cursor.fetchone()
        if not user:
            return None
        if user[3] and not is_password_hash(user[3]):
            raise LegacyPasswordError("此資料庫仍使用舊密碼格式，請先執行密碼遷移。")
        return user[:3] if verify_password(password, user[3]) else None

    def fetch_course_students(self, course_id):
        self.cursor.execute("""
            SELECT DISTINCT s.student_id, s.name
            FROM students_pro s JOIN enrollments e ON e.student_id = s.student_id
            WHERE e.course_id = %s AND s.status = '在學'
            ORDER BY s.student_id
        """, (course_id,))
        return self.cursor.fetchall()

    def add_enrollment(self, sid, course_id):
        try:
            self.cursor.execute(
                "INSERT INTO enrollments (student_id, course_id, enroll_date) VALUES (%s,%s,CURDATE())",
                (sid, course_id),
            )
            self.conn.commit()
        except mysql.connector.IntegrityError as exc:
            self.conn.rollback()
            if exc.errno == 1062:
                raise ValueError("該學生已加選過此課程") from exc
            raise

    def fetch_all_students(self):
        self.cursor.execute("""
            SELECT student_id, name, gender, phone, parent_phone, status, tuition_balance, create_time
            FROM students_pro ORDER BY create_time DESC
        """)
        return self.cursor.fetchall()

    def search_students(self, keyword):
        sql = """
            SELECT student_id, name, gender, phone, parent_phone, status, tuition_balance, create_time
            FROM students_pro
            WHERE student_id LIKE %s OR name LIKE %s OR phone LIKE %s OR parent_phone LIKE %s
        """
        like_kw = f"%{keyword}%"
        self.cursor.execute(sql, (like_kw, like_kw, like_kw, like_kw))
        return self.cursor.fetchall()

    def add_student(self, data):
        sql = "INSERT INTO students_pro (student_id, name, gender, phone, parent_phone, address, status, tuition_balance) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        self.cursor.execute(sql, data)
        self.conn.commit()

    def update_student(self, data, original_sid):
        sql = "UPDATE students_pro SET student_id=%s, name=%s, gender=%s, phone=%s, parent_phone=%s, address=%s, status=%s, tuition_balance=%s WHERE student_id=%s"
        self.cursor.execute(sql, data + (original_sid,))
        self.conn.commit()

    def delete_student(self, sid):
        self.cursor.execute("DELETE FROM students_pro WHERE student_id=%s", (sid,))
        self.conn.commit()

    def get_student_details(self, sid):
         self.cursor.execute("SELECT * FROM students_pro WHERE student_id=%s", (sid,))
         row = self.cursor.fetchone()
         return {"student_id": row[1], "name": row[2], "gender": row[3], "phone": row[4],
                 "parent_phone": row[5], "address": row[6], "status": row[7], "tuition_balance": row[8]} if row else None

    def fetch_all_courses(self):
        sql = """
            SELECT c.course_id, c.course_name, COALESCE(u.real_name, '未分配') as teacher_name, c.base_fee, c.description
            FROM courses c
            LEFT JOIN users u ON c.teacher_id = u.user_id
        """
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def get_dashboard_stats(self):
        self.cursor.execute("SELECT COUNT(*) FROM students_pro WHERE status='在學'")
        active_count = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT SUM(tuition_balance) FROM students_pro WHERE tuition_balance > 0")
        total_debt = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT COUNT(*) FROM students_pro")
        total_students = self.cursor.fetchone()[0]
        return active_count, total_debt, total_students

    def generate_smart_bills(self, period):
        """每個 YYYY-MM 帳期只對當下在學、已選課的學生產單一次。"""
        period = validate_billing_period(period)
        self.conn.start_transaction()
        try:
            try:
                self.cursor.execute("INSERT INTO billing_runs (period) VALUES (%s)", (period,))
            except mysql.connector.IntegrityError as exc:
                if exc.errno == 1062:
                    self.conn.rollback()
                    return False
                raise
            self.cursor.execute("""
                UPDATE students_pro s
                JOIN (
                    SELECT e.student_id, SUM(c.base_fee) AS total_fee
                    FROM enrollments e JOIN courses c ON e.course_id = c.course_id
                    GROUP BY e.student_id
                ) billing ON s.student_id = billing.student_id
                SET s.tuition_balance = s.tuition_balance + billing.total_fee
                WHERE s.status = '在學'
            """)
            self.conn.commit()
            return True
        except Exception:
            self.conn.rollback()
            raise

    # --- [疊加] 成績邏輯 ---
    def fetch_student_scores(self, sid):
        sql = "SELECT subject, score, exam_date FROM student_scores WHERE student_id = %s ORDER BY exam_date DESC"
        self.cursor.execute(sql, (sid,))
        return self.cursor.fetchall()

    def add_score(self, sid, subject, score):
        sql = "INSERT INTO student_scores (student_id, subject, score, exam_date) VALUES (%s, %s, %s, CURDATE())"
        self.cursor.execute(sql, (sid, subject, score))
        self.conn.commit()

    def check_in_out_logic(self, user_id):
        today = datetime.now().date()
        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute("SELECT log_id, check_in, check_out FROM work_attendance WHERE user_id=%s AND work_date=%s", (user_id, today))
        record = self.cursor.fetchone()
        if not record:
            self.cursor.execute("INSERT INTO work_attendance (user_id, check_in, work_date) VALUES (%s, %s, %s)", (user_id, now_time, today))
            self.conn.commit()
            return f"上班打卡成功！\n時間：{now_time}"
        elif record[2] is None:
            self.cursor.execute("UPDATE work_attendance SET check_out=%s WHERE log_id=%s", (now_time, record[0]))
            self.conn.commit()
            return f"下班打卡成功！\n時間：{now_time}"
        else:
            return "今日已完成上下班打卡。"

    def get_teacher_schedule(self, user_id):
        sql = """
            SELECT s.day_of_week, c.course_name, s.start_time, s.end_time
            FROM course_schedule s
            JOIN courses c ON s.course_id = c.course_id
            WHERE c.teacher_id = %s
            ORDER BY FIELD(day_of_week, '週一','週二','週三','週四','週五','週六','週日')
        """
        self.cursor.execute(sql, (user_id,))
        return self.cursor.fetchall()

    def process_payment(self, sid, pay_amount):
        amount = validate_payment_amount(pay_amount)
        self.conn.start_transaction()
        try:
            self.cursor.execute(
                "SELECT tuition_balance FROM students_pro WHERE student_id=%s FOR UPDATE", (sid,)
            )
            row = self.cursor.fetchone()
            if row is None:
                raise ValueError("找不到此學生")
            if amount > row[0]:
                raise ValueError("繳費金額不能超過目前欠款")
            self.cursor.execute(
                "UPDATE students_pro SET tuition_balance = tuition_balance - %s WHERE student_id = %s",
                (amount, sid),
            )
            self.cursor.execute(
                "INSERT INTO payment_records (student_id, amount) VALUES (%s, %s)", (sid, amount)
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def get_revenue_chart_data(self):
        sql = """
            SELECT DATE_FORMAT(pay_date, '%Y-%m') as m, SUM(amount)
            FROM payment_records
            GROUP BY m ORDER BY m ASC LIMIT 6
        """
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def save_attendance(self, course_id, attendance_list):
        allowed_statuses = {"出席", "缺席", "遲到", "請假"}
        self.conn.start_transaction()
        try:
            eligible = {sid for sid, _ in self.fetch_course_students(course_id)}
            seen = set()
            for sid, status in attendance_list:
                if sid not in eligible or sid in seen or status not in allowed_statuses:
                    raise ValueError("點名名單或狀態不正確，請重新開啟點名視窗")
                seen.add(sid)
            today = datetime.now().date()
            self.cursor.executemany(
                "INSERT INTO attendance (course_id, student_id, date, status) VALUES (%s, %s, %s, %s)",
                [(course_id, sid, today, status) for sid, status in attendance_list],
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def fetch_all_teachers(self):
        self.cursor.execute("SELECT user_id, username, real_name, role FROM users WHERE role IN ('staff', 'teacher', 'admin')")
        return self.cursor.fetchall()

    def add_teacher(self, username, password, real_name):
        sql = "INSERT INTO users (username, password, real_name, role) VALUES (%s, %s, %s, 'staff')"
        self.cursor.execute(sql, (username, hash_password(password), real_name))
        self.conn.commit()

    def update_teacher_data(self, uid, username, real_name):
        sql = "UPDATE users SET username=%s, real_name=%s WHERE user_id=%s"
        self.cursor.execute(sql, (username, real_name, uid))
        self.conn.commit()

    def delete_teacher(self, user_id):
        self.cursor.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
        self.conn.commit()

    def update_course_teacher(self, course_id, teacher_id):
        sql = "UPDATE courses SET teacher_id = %s WHERE course_id = %s"
        self.cursor.execute(sql, (teacher_id, course_id))
        self.conn.commit()

