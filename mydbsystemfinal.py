import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog, simpledialog
import mysql.connector
from datetime import datetime

from database import DatabaseManager
from exports import export_students
from security import LegacyPasswordError

THEME_NAME = "flatly"

# ================== 登入視窗 ==================
class LoginWindow(tb.Toplevel):
    def __init__(self, parent, on_success):
        super().__init__(master=parent)
        self.title("系統登入 - EduCRM Pro")
        self.geometry("400x550")
        self.resizable(False, False)
        self.on_success = on_success
        self.db = parent.db
        self.protocol("WM_DELETE_WINDOW", parent.destroy)
        self.setup_ui()
        self.place_window_center()

    def place_window_center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f'+{x}+{y}')

    def setup_ui(self):
        container = tb.Frame(self, padding=40)
        container.pack(fill=BOTH, expand=True)
        tb.Label(container, text="🔑", font=("Arial", 60)).pack(pady=10)
        tb.Label(container, text="員工登入系統", font=("微軟正黑體", 18, "bold")).pack(pady=20)

        tb.Label(container, text="使用者帳號").pack(anchor=W)
        self.user_entry = tb.Entry(container)
        self.user_entry.pack(fill=X, pady=(5, 15))

        tb.Label(container, text="登入密碼").pack(anchor=W)
        self.pwd_entry = tb.Entry(container, show="*")
        self.pwd_entry.pack(fill=X, pady=(5, 30))

        tb.Button(container, text="立即登入", bootstyle="primary", command=self.check_login).pack(fill=X)
        self.bind('<Return>', lambda e: self.check_login())

    def check_login(self):
        username = self.user_entry.get().strip()
        password = self.pwd_entry.get()
        try:
            user = self.db.authenticate(username, password)
        except LegacyPasswordError as exc:
            messagebox.showerror("需要更新資料庫", str(exc))
            return
        except mysql.connector.Error:
            messagebox.showerror("登入失敗", "無法讀取帳號資料，請檢查資料庫連線。")
            return
        if user:
            messagebox.showinfo("成功", f"歡迎回來，{user[1]}！")
            self.on_success(user[0], user[2])
            self.destroy()
        else:
            messagebox.showerror("錯誤", "帳號或密碼不正確")

# ================== 輔助對話框 ==================
class StudentFormDialog(tb.Toplevel):
    def __init__(self, parent, title, callback, is_edit=False):
        super().__init__(master=parent)
        self.title(title)
        self.geometry("500x680")
        self.callback = callback
        self.is_edit = is_edit
        self.parent_app = parent
        self.original_sid = None
        self.entries = {}
        self.setup_form()
        self.grab_set()

    def setup_form(self):
        container = tb.Frame(self, padding=20)
        container.pack(fill=BOTH, expand=True)
        fields = [("學號", "student_id"), ("姓名", "name"), ("性別", "gender"),
                  ("電話", "phone"), ("家長電話", "parent_phone"), ("地址", "address"),
                  ("狀態", "status"), ("欠款", "tuition_balance")]

        for label, key in fields:
            f = tb.Frame(container); f.pack(fill=X, pady=5)
            tb.Label(f, text=label, width=12).pack(side=LEFT)
            if key == "gender": e = tb.Combobox(f, values=["男", "女", "其他"], state="readonly")
            elif key == "status": e = tb.Combobox(f, values=["在學", "休學", "退班", "畢業"], state="readonly")
            else: e = tb.Entry(f)
            e.pack(side=LEFT, fill=X, expand=True); self.entries[key] = e
        tb.Button(container, text="儲存資料", bootstyle="success", command=self.save).pack(pady=30, fill=X)

    def load_data(self, data):
        self.original_sid = data['student_id']
        for k, v in data.items():
            if k in self.entries:
                if isinstance(self.entries[k], tb.Combobox): self.entries[k].set(v)
                else: self.entries[k].insert(0, str(v) if v is not None else "")
        return self

    def save(self):
        vals = [self.entries[k].get() for k in ["student_id", "name", "gender", "phone", "parent_phone", "address", "status", "tuition_balance"]]
        if not vals[0] or not vals[1]:
            messagebox.showwarning("必填", "學號與姓名不能為空"); return
        try:
            if self.is_edit: self.callback(tuple(vals), self.original_sid)
            else: self.callback(tuple(vals))
        except (ValueError, mysql.connector.Error) as exc:
            messagebox.showerror("儲存失敗", str(exc))
            return
        self.parent_app.load_student_data(); self.destroy()

class TeacherFormDialog(tb.Toplevel):
    def __init__(self, parent, title, callback, data=None):
        super().__init__(master=parent)
        self.title(title); self.geometry("400x450"); self.callback = callback; self.data = data
        self.setup_ui(); self.grab_set()

    def setup_ui(self):
        container = tb.Frame(self, padding=20); container.pack(fill=BOTH, expand=True)
        tb.Label(container, text="帳號:").pack(anchor=W, pady=5); self.u_ent = tb.Entry(container); self.u_ent.pack(fill=X, pady=5)
        tb.Label(container, text="姓名:").pack(anchor=W, pady=5); self.n_ent = tb.Entry(container); self.n_ent.pack(fill=X, pady=5)
        if not self.data:
            tb.Label(container, text="密碼（至少 8 個字元）:").pack(anchor=W, pady=5); self.p_ent = tb.Entry(container, show="*"); self.p_ent.pack(fill=X, pady=5)
        if self.data:
            self.u_ent.insert(0, self.data[1]); self.n_ent.insert(0, self.data[2])
        tb.Button(container, text="儲存資料", bootstyle="success", command=self.save).pack(pady=20, fill=X)

    def save(self):
        u, n = self.u_ent.get(), self.n_ent.get()
        if not u.strip() or not n.strip():
            messagebox.showwarning("必填", "帳號與姓名不能為空")
            return
        try:
            if self.data: self.callback(self.data[0], u.strip(), n.strip())
            else: self.callback(u.strip(), self.p_ent.get(), n.strip())
        except mysql.connector.IntegrityError as exc:
            message = "此帳號已被使用，請改用其他帳號。" if exc.errno == 1062 else str(exc)
            messagebox.showerror("儲存失敗", message)
            return
        except (ValueError, mysql.connector.Error) as exc:
            messagebox.showerror("儲存失敗", str(exc))
            return
        self.destroy()

class AttendanceDialog(tb.Toplevel):
    def __init__(self, parent, course_id, course_name, db):
        super().__init__(master=parent)
        self.title(f"今日點名 - {course_name}"); self.geometry("450x700")
        self.db, self.course_id, self.course_name = db, course_id, course_name
        self.student_status = {}; self.container = tb.Frame(self, padding=20); self.container.pack(fill=BOTH, expand=True)
        self.setup_ui(); self.grab_set()

    def setup_ui(self):
        tb.Label(self.container, text=f"【{self.course_name}】", font=("微軟正黑體", 18, "bold")).pack(pady=10)
        list_frame = tb.Frame(self.container); list_frame.pack(fill=BOTH, expand=True, pady=10)
        self.student_names = dict(self.db.fetch_course_students(self.course_id))
        for sid, name in self.student_names.items():
            row = tb.Frame(list_frame); row.pack(fill=X, pady=8)
            tb.Label(row, text=name, width=12, font=("微軟正黑體", 12), anchor=CENTER).pack(side=LEFT, expand=True)
            var = tb.StringVar(value="出席"); self.student_status[sid] = var
            tb.Combobox(row, textvariable=var, values=["出席", "缺席", "遲到", "請假"], state="readonly", width=10).pack(side=RIGHT, expand=True)
        tb.Button(self.container, text="✅ 完成並開啟檢視模式", bootstyle="primary", command=self.submit).pack(pady=20, fill=X)

    def submit(self):
        data = [(sid, var.get()) for sid, var in self.student_status.items()]
        try:
            self.db.save_attendance(self.course_id, data)
        except (ValueError, mysql.connector.Error) as exc:
            messagebox.showerror("點名失敗", str(exc))
            return
        for w in self.container.winfo_children(): w.destroy()
        tb.Label(self.container, text="請學生核對點名狀態", font=("微軟正黑體", 20, "bold"), bootstyle="success").pack(pady=20)
        for sid, status in data:
            name = self.student_names[sid]
            f = tb.Frame(self.container); f.pack(fill=X, pady=5)
            tb.Label(f, text=f"{name}：", font=("微軟正黑體", 16)).pack(side=LEFT, padx=(60,0))
            tb.Label(f, text=status, font=("微軟正黑體", 16, "bold"), bootstyle="success" if status=="出席" else "danger").pack(side=LEFT)
        tb.Button(self.container, text="確認無誤，關閉視窗", bootstyle="secondary-outline", command=self.destroy).pack(pady=20, fill=X)

# ================== [疊加] 選課管理視窗 ==================
class StudentCourseDialog(tb.Toplevel):
    def __init__(self, parent, sid, name, db):
        super().__init__(master=parent)
        self.title(f"選課管理 - {name}"); self.geometry("450x600")
        self.db, self.sid = db, sid
        container = tb.Frame(self, padding=20); container.pack(fill=BOTH, expand=True)
        tb.Label(container, text="目前已選課程", font=("微軟正黑體", 14, "bold")).pack(pady=10)
        self.tree = tb.Treeview(container, columns=("id", "name"), show="headings", height=5)
        self.tree.heading("id", text="ID"); self.tree.heading("name", text="課程名稱"); self.tree.pack(fill=X, pady=10)
        tb.Button(container, text="❌ 移除選取課程", bootstyle="danger-link", command=self.remove_course).pack()
        tb.Separator(container).pack(pady=20)
        tb.Label(container, text="加選新課程：").pack(anchor=W)
        courses = self.db.fetch_all_courses()
        self.c_map = {f"{c[1]} (${c[3]})": c[0] for c in courses}
        self.c_combo = tb.Combobox(container, values=list(self.c_map.keys()), state="readonly")
        self.c_combo.pack(fill=X, pady=5)
        tb.Button(container, text="➕ 確認加選", bootstyle="success", command=self.add_course).pack(fill=X, pady=10)
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        sql = "SELECT c.course_id, c.course_name FROM enrollments e JOIN courses c ON e.course_id = c.course_id WHERE e.student_id = %s"
        self.db.cursor.execute(sql, (self.sid,))
        for r in self.db.cursor.fetchall(): self.tree.insert("", END, values=r)

    def add_course(self):
        sel = self.c_combo.get()
        if sel:
            try:
                self.db.add_enrollment(self.sid, self.c_map[sel])
                self.refresh()
            except ValueError as exc:
                messagebox.showwarning("無法加選", str(exc))
            except mysql.connector.Error:
                messagebox.showerror("加選失敗", "請檢查資料庫連線或課程資料。")

    def remove_course(self):
        sel = self.tree.selection()
        if sel:
            cid = self.tree.item(sel[0])['values'][0]
            self.db.cursor.execute("DELETE FROM enrollments WHERE student_id=%s AND course_id=%s", (self.sid, cid))
            self.db.conn.commit(); self.refresh()

# ================== 主應用程式 ==================
class EduCRMApp(tb.Window):
    def __init__(self, database):
        super().__init__(themename=THEME_NAME)
        self.title("EduCRM Pro - 智慧管理系統"); self.geometry("1280x800")
        self.db = database; self.current_role = "staff"; self.current_user_id = None
        self.setup_layout()

    def login_success(self, uid, role):
        self.current_user_id = uid; self.current_role = role; self.deiconify(); self.show_dashboard()

    def setup_layout(self):
        self.sidebar = tb.Frame(self, bootstyle="dark", width=240); self.sidebar.pack(side=LEFT, fill=Y); self.sidebar.pack_propagate(False)
        tb.Label(self.sidebar, text="EduCRM Pro", font=("Microsoft JhengHei", 22, "bold"), bootstyle="inverse-dark").pack(pady=40)
        self.nav_container = tb.Frame(self.sidebar, bootstyle="dark"); self.nav_container.pack(fill=BOTH, expand=True)
        self.content_area = tb.Frame(self, padding=30); self.content_area.pack(side=RIGHT, fill=BOTH, expand=True)

    def refresh_nav(self):
        for w in self.nav_container.winfo_children(): w.destroy()
        nav_items = [
            ("📊 營運儀表板", self.show_dashboard),
            ("👥 學生資料管理", self.show_student_list),
            ("📈 學生成績管理", self.show_score_management),
            ("📚 課程班級管理", self.show_course_list),
            ("📅 老師週課表", self.show_my_schedule),
            ("📝 點名系統", self.show_attendance_page),
            ("⏰ 員工上下班打卡", self.staff_clock_action)
        ]
        if self.current_role == "admin":
            nav_items.append(("👨‍🏫 老師帳號管理", self.show_teacher_list))
            nav_items.append(("💰 智慧產生帳單", self.auto_bill_action))

        for text, cmd in nav_items:
            tb.Button(self.nav_container, text=text, bootstyle="link-light", command=cmd).pack(fill=X, pady=10, padx=20, anchor="w")

        tb.Separator(self.nav_container, bootstyle="secondary").pack(pady=20, padx=20)
        tb.Button(self.nav_container, text="🚪 登出系統", bootstyle="danger-link", command=self.logout_action).pack(fill=X, pady=10, padx=20, anchor="w")

    def clear_content(self):
        for widget in self.content_area.winfo_children(): widget.destroy()

    def show_dashboard(self):
        self.clear_content(); self.refresh_nav()
        active, debt, total = self.db.get_dashboard_stats()
        cards = tb.Frame(self.content_area); cards.pack(fill=X)
        self.create_kpi_card(cards, "在學人數", f"{active} 人", "primary", 0)
        self.create_kpi_card(cards, "總學員數", f"{total} 人", "info", 1)
        debt_display = f"${debt:,}" if self.current_role == "admin" else "****"
        self.create_kpi_card(cards, "待收學費", debt_display, "danger", 2)

        if self.current_role == "admin":
            tb.Label(self.content_area, text="📈 營收成長趨勢 (實時流水帳)", font=("微軟正黑體", 18, "bold")).pack(anchor=W, pady=(40, 10))
            chart_container = tb.Frame(self.content_area, bootstyle="light", padding=20); chart_container.pack(fill=X)
            data = self.db.get_revenue_chart_data()
            target = 100000
            for month, val in (data if data else [("無資料", 0)]):
                row = tb.Frame(chart_container, bootstyle="light"); row.pack(fill=X, pady=5)
                tb.Label(row, text=month, width=12).pack(side=LEFT)
                percent = (val/target)*100
                b_style = "warning" if percent>=100 else "success" if percent>=70 else "info" if percent>=30 else "secondary"
                tb.Progressbar(row, value=min(percent, 100), bootstyle=b_style, length=500).pack(side=LEFT, padx=10)
                tb.Label(row, text=f"${val:,}", font=("Arial", 10, "bold"), bootstyle=b_style).pack(side=LEFT)

    def create_kpi_card(self, parent, title, value, color, idx):
        card = tb.Frame(parent, bootstyle=color, padding=25); card.pack(side=LEFT, expand=True, fill=BOTH, padx=(0, 20) if idx < 2 else 0)
        tb.Label(card, text=title, font=("微軟正黑體", 14), bootstyle=f"inverse-{color}").pack(anchor=W)
        tb.Label(card, text=value, font=("Arial", 32, "bold"), bootstyle=f"inverse-{color}").pack(anchor=W, pady=(10,0))

    def logout_action(self):
        if messagebox.askyesno("登出", "確定登出？"): self.current_user_id=None; self.withdraw(); LoginWindow(self, on_success=self.login_success)

    def auto_bill_action(self):
        period = simpledialog.askstring("產生帳單", "帳期（YYYY-MM）：", initialvalue=datetime.now().strftime("%Y-%m"), parent=self)
        if period is None:
            return
        if not messagebox.askyesno("確認產單", f"依目前在學學生的選課，產生 {period} 帳單？同一帳期只能產生一次。"):
            return
        try:
            created = self.db.generate_smart_bills(period)
        except (ValueError, mysql.connector.Error) as exc:
            messagebox.showerror("產單失敗", str(exc))
            return
        messagebox.showinfo("產單結果", "已完成產單" if created else "此帳期已產生過帳單，欠款未變更")
        self.show_dashboard()

    def show_score_management(self):
        self.clear_content()
        tb.Label(self.content_area, text="📈 學生成績管理", font=("微軟正黑體", 26, "bold")).pack(anchor=W, pady=(0, 20))
        f = tb.Frame(self.content_area); f.pack(fill=X, pady=10)
        self.score_sid_combo = tb.Combobox(f, values=[f"{s[1]} ({s[0]})" for s in self.db.fetch_all_students()], state="readonly")
        self.score_sid_combo.pack(side=LEFT, padx=10)
        tb.Button(f, text="查詢", command=self.refresh_score_list).pack(side=LEFT)
        tb.Button(f, text="+ 登錄分數", bootstyle="success", command=self.open_add_score_dialog).pack(side=RIGHT)
        self.score_tree = tb.Treeview(self.content_area, columns=("subj", "score", "date"), show="headings", bootstyle="info")
        for c, h in zip(self.score_tree["columns"], ["科目", "分數", "日期"]): self.score_tree.heading(c, text=h)
        self.score_tree.pack(fill=BOTH, expand=True, pady=20)

    def refresh_score_list(self):
        if not self.score_sid_combo.get(): return
        sid = self.score_sid_combo.get().split("(")[1].replace(")", "")
        for item in self.score_tree.get_children(): self.score_tree.delete(item)
        for r in self.db.fetch_student_scores(sid): self.score_tree.insert("", END, values=r)

    def open_add_score_dialog(self):
        if not self.score_sid_combo.get(): return
        sid = self.score_sid_combo.get().split("(")[1].replace(")", "")
        top = tb.Toplevel(master=self); top.title("登錄"); top.geometry("300x250")
        tb.Label(top, text="科目:").pack(); subj = tb.Entry(top); subj.pack()
        tb.Label(top, text="分數:").pack(); score = tb.Entry(top); score.pack()
        def save(): self.db.add_score(sid, subj.get(), score.get()); top.destroy(); self.refresh_score_list()
        tb.Button(top, text="存檔", command=save, bootstyle="success").pack(pady=20)

    def staff_clock_action(self): messagebox.showinfo("打卡", self.db.check_in_out_logic(self.current_user_id))

    def show_my_schedule(self):
        self.clear_content(); tb.Label(self.content_area, text="我的課表", font=("微軟正黑體", 26, "bold")).pack(anchor=W, pady=(0, 20))
        tree = tb.Treeview(self.content_area, columns=("day", "course", "time"), show="headings", bootstyle="secondary")
        for c, h in zip(tree["columns"], ["星期", "課程", "時段"]): tree.heading(c, text=h)
        tree.pack(fill=BOTH, expand=True)
        for d in self.db.get_teacher_schedule(self.current_user_id): tree.insert("", END, values=(d[0], d[1], f"{d[2]}-{d[3]}"))

    def show_student_list(self):
        self.clear_content(); toolbar = tb.Frame(self.content_area); toolbar.pack(fill=X, pady=(0, 20))
        tb.Label(toolbar, text="學生資料管理", font=("微軟正黑體", 26, "bold")).pack(side=LEFT)
        btn_frame = tb.Frame(toolbar); btn_frame.pack(side=RIGHT); self.search_var = tb.StringVar()
        tb.Entry(btn_frame, textvariable=self.search_var, width=15).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="🔍", command=self.perform_search).pack(side=LEFT)
        tb.Button(btn_frame, text="匯出 Excel", command=self.export_to_excel).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="+ 新增", bootstyle="success", command=self.open_add_student_dialog).pack(side=LEFT, padx=5)
        self.setup_student_treeview(); self.load_student_data()

    def setup_student_treeview(self):
        cols = ("sid", "name", "gender", "phone", "p_phone", "status", "debt", "time")
        self.tree = tb.Treeview(self.content_area, columns=cols, show="headings", bootstyle="primary")
        for col, head in zip(cols, ["學號", "姓名", "性別", "電話", "家長", "狀態", "欠款", "時間"]):
            self.tree.heading(col, text=head); self.tree.column(col, width=100, anchor=CENTER)
        self.tree.pack(fill=BOTH, expand=True); self.tree.bind("<Double-1>", self.open_edit_student_dialog)

        # --- [疊加按鈕] ---
        action = tb.Frame(self.content_area, padding=(0, 10, 0, 0)); action.pack(fill=X)
        tb.Button(action, text="📚 課程管理", bootstyle="info-outline", command=self.open_student_course_dialog).pack(side=RIGHT, padx=5)
        tb.Button(action, text="💰 繳費", bootstyle="success-outline", command=self.open_pay_dialog).pack(side=RIGHT)
        if self.current_role == "admin": tb.Button(action, text="刪除", bootstyle="danger", command=self.delete_selected_student).pack(side=RIGHT, padx=5)

    def open_student_course_dialog(self):
        sel = self.tree.selection()
        if sel: StudentCourseDialog(self, self.tree.item(sel[0])['values'][0], self.tree.item(sel[0])['values'][1], self.db)

    def open_pay_dialog(self):
        sel = self.tree.selection()
        if not sel: return
        sid, name = self.tree.item(sel[0])['values'][:2]
        top = tb.Toplevel(master=self); top.title(f"繳費-{name}"); top.geometry("300x200")
        tb.Label(top, text="金額:").pack(pady=10); amt = tb.Entry(top); amt.pack()
        def confirm():
            try:
                self.db.process_payment(sid, amt.get())
            except ValueError as exc:
                messagebox.showwarning("金額不正確", str(exc))
                return
            except mysql.connector.Error:
                messagebox.showerror("繳費失敗", "繳費未完成，請檢查資料庫連線後重試。")
                return
            messagebox.showinfo("成功", "已收訖")
            top.destroy()
            self.load_student_data()
        tb.Button(top, text="確認", command=confirm, bootstyle="success").pack(pady=20)

    def load_student_data(self, data=None):
        for item in self.tree.get_children(): self.tree.delete(item)
        for r in (self.db.fetch_all_students() if data is None else data):
            row = list(r); row[6] = f"${row[6]:,}" if self.current_role=="admin" else "***"
            self.tree.insert("", END, values=row)

    def show_teacher_list(self):
        self.clear_content(); toolbar = tb.Frame(self.content_area); toolbar.pack(fill=X, pady=(0, 20))
        tb.Label(toolbar, text="老師管理", font=("微軟正黑體", 26, "bold")).pack(side=LEFT)
        tb.Button(toolbar, text="+ 新增老師", bootstyle="success", command=self.open_add_teacher_dialog).pack(side=RIGHT)
        self.teacher_tree = tb.Treeview(self.content_area, columns=("id", "username", "name", "role"), show="headings", bootstyle="info")
        for c, h in zip(self.teacher_tree["columns"], ["ID", "帳號", "姓名", "權限"]): self.teacher_tree.heading(c, text=h)
        self.teacher_tree.pack(fill=BOTH, expand=True); self.teacher_tree.bind("<Double-1>", self.open_edit_teacher_dialog)
        self.load_teacher_data()

    def load_teacher_data(self):
        for i in self.teacher_tree.get_children(): self.teacher_tree.delete(i)
        for r in self.db.fetch_all_teachers(): self.teacher_tree.insert("", END, values=r)

    def open_add_teacher_dialog(self): TeacherFormDialog(self, "新增", self.add_teacher_callback)
    def add_teacher_callback(self, u, p, n): self.db.add_teacher(u, p, n); self.load_teacher_data()
    def open_edit_teacher_dialog(self, e):
        sel = self.teacher_tree.selection()
        if sel: TeacherFormDialog(self, "修改", self.edit_teacher_callback, data=self.teacher_tree.item(sel[0])['values'])
    def edit_teacher_callback(self, uid, u, n): self.db.update_teacher_data(uid, u, n); self.load_teacher_data()

    def show_course_list(self):
        self.clear_content(); tb.Label(self.content_area, text="課程管理", font=("微軟正黑體", 26, "bold")).pack(anchor=W, pady=(0, 20))
        self.course_tree = tb.Treeview(self.content_area, columns=("id", "name", "teacher", "fee", "desc"), show="headings", bootstyle="info")
        for c, h in zip(self.course_tree["columns"], ["ID", "課程", "老師", "學費", "描述"]): self.course_tree.heading(c, text=h)
        self.course_tree.pack(fill=BOTH, expand=True)
        if self.current_role == "admin": self.course_tree.bind("<Double-1>", self.open_edit_course_teacher)
        for c in self.db.fetch_all_courses(): self.course_tree.insert("", END, values=c)

    def open_edit_course_teacher(self, e):
        sel = self.course_tree.selection()
        if not sel: return
        top = tb.Toplevel(master=self); top.title("更改老師"); top.geometry("300x300")
        combo = tb.Combobox(top, values=[f"{t[2]} (ID:{t[0]})" for t in self.db.fetch_all_teachers()], state="readonly")
        combo.pack(pady=30)
        def save():
            tid = combo.get().split("ID:")[1].replace(")", ""); self.db.update_course_teacher(self.course_tree.item(sel[0])['values'][0], tid)
            top.destroy(); self.show_course_list()
        tb.Button(top, text="修改", command=save, bootstyle="success").pack()

    def show_attendance_page(self):
        self.clear_content(); tb.Label(self.content_area, text="點名系統", font=("微軟正黑體", 26, "bold")).pack(anchor=W, pady=(0, 20))
        self.att_tree = tb.Treeview(self.content_area, columns=("id", "name", "teacher"), show="headings", bootstyle="warning")
        for c, h in zip(self.att_tree["columns"], ["ID", "課程", "老師"]): self.att_tree.heading(c, text=h)
        self.att_tree.pack(fill=X, pady=10)
        for c in self.db.fetch_all_courses(): self.att_tree.insert("", END, values=(c[0], c[1], c[2]))
        tb.Button(self.content_area, text="📍 開始點名", bootstyle="warning", command=self.open_attendance_dialog).pack(pady=10)

    def open_attendance_dialog(self):
        sel = self.att_tree.selection()
        if sel: AttendanceDialog(self, *self.att_tree.item(sel[0])['values'][:2], self.db)

    def perform_search(self): self.load_student_data(self.db.search_students(self.search_var.get()))
    def open_add_student_dialog(self): StudentFormDialog(self, "新增學生", self.db.add_student)
    def open_edit_student_dialog(self, e):
        sel = self.tree.selection()
        if sel:
            full = self.db.get_student_details(self.tree.item(sel[0])['values'][0])
            if full: StudentFormDialog(self, "編輯資料", self.db.update_student, is_edit=True).load_data(full)
    def delete_selected_student(self):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("確認", "刪除學生？"): self.db.delete_student(self.tree.item(sel[0])['values'][0]); self.load_student_data()
    def export_to_excel(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if path:
            try:
                export_students(path, [self.tree.item(i)['values'] for i in self.tree.get_children()])
            except OSError as exc:
                messagebox.showerror("匯出失敗", str(exc))
                return
            messagebox.showinfo("成功", "已匯出目前顯示的學生資料")

if __name__ == "__main__":
    try:
        db = DatabaseManager()
    except (ValueError, mysql.connector.Error) as exc:
        raise SystemExit(f"無法啟動：{exc}")
    try:
        app = EduCRMApp(db)
        app.withdraw()
        LoginWindow(app, on_success=app.login_success)
        app.mainloop()
    finally:
        db.close()
