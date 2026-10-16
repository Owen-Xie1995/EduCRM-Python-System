# EduCRM 補習班學生管理系統

使用 Python、Tkinter 和 MySQL 的桌面練習專案。將學生、選課、點名和收款放在同一個介面，資料保存在本機資料庫。

目前可管理學生資料、課程指派、選課、成績及員工打卡；管理員可按月產生學費帳單。學生清單支援搜尋，並可將當前顯示的資料匯出為 Excel。

`student_db.sql` 的學生與員工種子資料為虛構示範資料；學號使用 `DEMO-S001` 等代號，學生聯絡電話與地址均留空。

## 安裝與啟動

需要 Python 3.12、Tk，以及 MySQL／MariaDB。以下使用本機資料庫示範；Windows 可用 `.venv\Scripts\activate` 啟用環境。

```sh
git clone https://github.com/Owen-Xie1995/EduCRM-Python-System.git
cd EduCRM-Python-System
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Ubuntu 若缺少 Tk，可安裝 `python3-tk`。先執行 `python -m tkinter` 確認測試視窗能開啟。

**全新資料庫**：使用具有建庫權限的帳號建立 `student_db`，再匯入附帶的資料表與示範資料。以下的 root 僅用於資料庫初始化。

```sh
mysql -u root -p -e "CREATE DATABASE student_db CHARACTER SET utf8mb4;"
mysql -u root -p student_db < student_db.sql
```

再以資料庫維護帳號執行下列 SQL，將範例密碼替換成自己的密碼。桌面程式只需要讀寫資料，不需要建表或管理其他資料庫的權限。

```sql
CREATE USER 'educrm_app'@'127.0.0.1' IDENTIFIED BY 'replace-with-a-long-local-password';
GRANT SELECT, INSERT, UPDATE, DELETE ON student_db.* TO 'educrm_app'@'127.0.0.1';
```

編輯 `.env`，填入相同的帳號與密碼。環境變數會優先於 `.env`；程式不會使用預設 root 或空密碼連線。

附帶的 `admin`、`teacher01`、`teacher02`、`teacher03` 帳號都沒有可用的預設登入密碼。先設定需要使用的帳號：

```sh
python manage_database.py set-password admin
python mydbsystemfinal.py
```

密碼透過終端機輸入，不會出現在命令列參數中。新密碼至少 8 個字元，資料庫儲存 PBKDF2-SHA256 雜湊。

## 更新既有資料庫

不要把 `student_db.sql` 再次匯入已有資料的資料庫。請先停止程式並備份，例如：

```sh
mkdir -p backups
mysqldump --single-transaction -u root -p student_db > backups/student_db-before-migration.sql
python manage_database.py migrate
```

檢查模式不會寫入。若有重複的學生／課程組合，程式會列出並停止；請依實際選課紀錄核對，備份後自行處理。遷移不會自動刪除任何選課資料，也不會調整既有欠款。

確認備份可以還原，且沒有其他程式正在寫入後，再使用具有 `ALTER`、`CREATE` 與資料讀寫權限的維護帳號套用：

```sh
python manage_database.py --db-user root migrate --apply --backup-confirmed
```

這會補上選課唯一約束、建立 `billing_runs`，並將既有明文密碼轉為雜湊。登入不接受舊的明文格式；舊短密碼在明確執行遷移後仍可使用，請再用 `set-password` 更換。空密碼帳號仍須設定新密碼才能登入。

MySQL 的建表與索引變更會自動提交，因此整份遷移不是單一交易；密碼更新另用交易處理。若中斷，確認錯誤原因後可重跑。請保管備份和 `.env`，兩者都不應提交到 Git。

## 計費與點名規則

- 點名只列出該課程中仍在學的學生。每次提交保留一批紀錄，目前沒有點名歷史修改介面。
- 同一學生不能重複加選同一課程，限制同時存在於應用程式及資料庫。
- 帳期使用 `YYYY-MM`。每期依**執行當下**的在學狀態、選課及課程費用增加欠款；同一期再次執行不會加收。產單紀錄與欠款更新在同一交易內。
- 目前沒有按天比例計費、歷史選課快照或產單撤回功能。當期產單後新增的選課，不會在重跑時補收。更新舊資料庫時，請先核對已收取的帳期，避免把過去已計入的費用再產生一次。
- 繳費只接受正整數，且不可超過欠款。扣款和收款紀錄一起提交或回滾。
- Excel 匯出目前畫面上的清單；員工帳號畫面中隱藏的欠款，也會維持隱藏。

## 測試

```sh
python -m unittest discover -s tests -v
```

一般執行會測試輸入驗證、密碼、搜尋畫面更新及 Excel，並略過資料庫整合測試。整合測試會**清空指定資料庫的所有資料表**，只接受名稱以 `_test` 結尾的獨立測試庫。

先建立例如 `educrm_test` 的空資料庫，透過環境變數指定連線，再設定 `EDUCRM_TEST_MYSQL=1` 執行相同命令。測試帳號需具有該測試庫的建表、刪表與讀寫權限，請勿使用實際學生資料庫。

GitHub Actions 配有獨立的 MariaDB 服務，執行資料表匯入、點名篩選、重複選課、帳期防重、收款回滾及遷移測試。CI 使用的 root 是可丟棄測試容器的帳號，桌面程式仍使用上述受限帳號。

## 專案檔案

- `mydbsystemfinal.py`：桌面介面。
- `database.py`：資料查詢與交易。
- `security.py`、`validation.py`、`exports.py`：密碼、輸入規則及 Excel 匯出。
- `manage_database.py`：既有資料遷移及密碼設定。
- `student_db.sql`：全新資料庫的資料表與示範資料。

這仍是單機練習專案。權限主要由桌面介面控制，尚未提供多人部署、完整操作稽核、備份排程或復原介面；不宜直接拿來保存實際學生與收款資料。
