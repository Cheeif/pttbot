import sqlite3
import os
import shutil
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path="data/users.db"):
        """Инициализация базы данных"""
        self.db_path = db_path
        self.backup_dir = "data/backups"
        self.init_database()
    
    def init_database(self):
        """Создание базы данных и таблиц при первом запуске"""
        # Создаем папки если их нет
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Создаем таблицу пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    status TEXT DEFAULT 'none',
                    plan TEXT DEFAULT 'none',
                    start_date TEXT,
                    end_date TEXT,
                    joined_at TEXT NOT NULL,
                    last_seen TEXT
                )
            ''')
            
            # Создаем таблицу платежей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    txid TEXT,
                    screenshot_file_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
                )
            ''')
            
            # Добавляем отсутствующие колонки (для совместимости)
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN user_state TEXT")
            except sqlite3.OperationalError:
                pass  # Колонка уже существует
            
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'none'")
            except sqlite3.OperationalError:
                pass  # Колонка уже существует
                
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN last_seen TEXT")
            except sqlite3.OperationalError:
                pass  # Колонка уже существует
            
            conn.commit()
    
    def create_backup(self):
        """Создание резервной копии базы данных"""
        try:
            if not os.path.exists(self.db_path):
                return False
            
            timestamp = datetime.now().strftime("%Y%m%d")
            backup_filename = f"users_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Копируем файл базы данных
            shutil.copy2(self.db_path, backup_path)
            
            # Удаляем старые бэкапы (старше 30 дней)
            self.cleanup_old_backups()
            
            return True
        except Exception as e:
            print(f"Ошибка создания резервной копии: {e}")
            return False
    
    def cleanup_old_backups(self, days=30):
        """Удаление старых резервных копий"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("users_") and filename.endswith(".db"):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        print(f"Удален старый бэкап: {filename}")
        except Exception as e:
            print(f"Ошибка очистки старых бэкапов: {e}")
    
    def add_user(self, telegram_id, username=None):
        """Добавление нового пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO users (telegram_id, username, joined_at, last_seen)
                    VALUES (?, ?, ?, ?)
                ''', (telegram_id, username, datetime.now().isoformat(), datetime.now().isoformat()))
                
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Пользователь уже существует, обновляем last_seen
                cursor.execute('''
                    UPDATE users SET last_seen = ?, username = ?
                    WHERE telegram_id = ?
                ''', (datetime.now().isoformat(), username, telegram_id))
                conn.commit()
                return False
    
    def get_user(self, telegram_id):
        """Получение информации о пользователе"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT telegram_id, username, status, plan, start_date, end_date, joined_at, last_seen
                FROM users WHERE telegram_id = ?
            ''', (telegram_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'telegram_id': result[0],
                    'username': result[1],
                    'status': result[2],
                    'plan': result[3],
                    'start_date': result[4],
                    'end_date': result[5],
                    'joined_at': result[6],
                    'last_seen': result[7]
                }
            return None
    
    def update_user_status(self, telegram_id, status, plan=None, start_date=None, end_date=None):
        """Обновление статуса пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if start_date and plan:
                cursor.execute('''
                    UPDATE users 
                    SET status = ?, plan = ?, start_date = ?, end_date = ?
                    WHERE telegram_id = ?
                ''', (status, plan, start_date, end_date, telegram_id))
            elif plan:
                cursor.execute('''
                    UPDATE users 
                    SET status = ?, plan = ?
                    WHERE telegram_id = ?
                ''', (status, plan, telegram_id))
            else:
                cursor.execute('''
                    UPDATE users 
                    SET status = ?
                    WHERE telegram_id = ?
                ''', (status, telegram_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_active_users(self):
        """Получение списка активных пользователей с неистёкшей подпиской"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT telegram_id FROM users 
                WHERE status = 'active' AND (end_date > ? OR end_date IS NULL OR plan = 'lifetime')
            ''', (datetime.now().isoformat(),))
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_all_users(self):
        """Получение списка всех пользователей"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT telegram_id, username, status, plan, start_date, end_date, joined_at, last_seen
                FROM users ORDER BY joined_at DESC
            ''')
            
            return cursor.fetchall()
    
    def user_exists(self, telegram_id):
        """Проверка существования пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT 1 FROM users WHERE telegram_id = ?', (telegram_id,))
            return cursor.fetchone() is not None
    
    def set_user_state(self, telegram_id, state):
        """Установка состояния пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET user_state = ? WHERE telegram_id = ?
            ''', (state, telegram_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_user_state(self, telegram_id):
        """Получение состояния пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_state FROM users WHERE telegram_id = ?
            ''', (telegram_id,))
            
            result = cursor.fetchone()
            return result[0] if result else None
    
    def add_payment(self, user_id, txid=None, screenshot_file_id=None, status="pending"):
        """Добавление платежа"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO payments (user_id, txid, screenshot_file_id, status, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, txid, screenshot_file_id, status, datetime.now().isoformat()))
                
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"Ошибка добавления платежа: {e}")
                return None
    
    def update_payment(self, user_id, txid=None, screenshot_file_id=None, status=None):
        """Обновление платежа"""
        try:
            fields = []
            params = []

            if txid:
                fields.append("txid = ?")
                params.append(txid)
            if screenshot_file_id:
                fields.append("screenshot_file_id = ?")
                params.append(screenshot_file_id)
            if status:
                fields.append("status = ?")
                params.append(status)

            if not fields:
                return False

            params.append(user_id)

            query = f"""
                UPDATE payments
                SET {', '.join(fields)}
                WHERE user_id = ?
            """
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"[DB ERROR] update_payment: {e}")
            return False

    
    def get_user_payment(self, user_id):
        """Получение информации о последнем платеже пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT txid, screenshot_file_id, status, created_at
                FROM payments 
                WHERE user_id = ? AND status IN ('pending', 'sent_screenshot', 'sent_txid')
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'txid': result[0],
                    'screenshot_file_id': result[1],
                    'status': result[2],
                    'created_at': result[3]
                }
            return None
    
    def get_latest_payments(self, limit=10):
        """Получение последних платежей для отчета"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT p.id, u.username, p.txid, p.status, p.created_at
                FROM payments p
                JOIN users u ON p.user_id = u.telegram_id
                ORDER BY p.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            return cursor.fetchall()
    
    def get_expiring_users(self, date):
        """Получение пользователей, у которых подписка истекает в указанную дату"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT telegram_id, username, end_date 
                FROM users 
                WHERE status = 'active' AND DATE(end_date) = DATE(?)
            ''', (date.isoformat(),))
            
            results = cursor.fetchall()
            return [
                {
                    'telegram_id': row[0],
                    'username': row[1],
                    'end_date': row[2]
                }
                for row in results
            ]
    
    def get_expired_users(self):
        """Получение пользователей с просроченной подпиской"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT telegram_id, username 
                FROM users 
                WHERE status = 'active' AND end_date < ?
            ''', (datetime.now().isoformat(),))
            
            results = cursor.fetchall()
            return [
                {
                    'telegram_id': row[0],
                    'username': row[1]
                }
                for row in results
            ]
    
    def get_database_stats(self):
        """Получение общей статистики базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Статистика пользователей
            cursor.execute('SELECT status, COUNT(*) FROM users GROUP BY status')
            user_stats = dict(cursor.fetchall())
            
            # Статистика планов
            cursor.execute('SELECT plan, COUNT(*) FROM users GROUP BY plan')
            plan_stats = dict(cursor.fetchall())
            
            # Статистика платежей
            cursor.execute('SELECT status, COUNT(*) FROM payments GROUP BY status')
            payment_stats = dict(cursor.fetchall())
            
            # Общее количество
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM payments')
            total_payments = cursor.fetchone()[0]
            
            # Активные подписки
            cursor.execute('SELECT COUNT(*) FROM users WHERE status = "active"')
            active_users = cursor.fetchone()[0]
            
            return {
                'users': user_stats,
                'plans': plan_stats,
                'payments': payment_stats,
                'total_users': total_users,
                'total_payments': total_payments,
                'active_users': active_users
            }
    
    def get_users_for_admin(self, limit=20):
        """Получение пользователей для админ-панели"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT telegram_id, username, status, plan, start_date, end_date
                FROM users ORDER BY joined_at DESC LIMIT ?
            ''', (limit,))
            
            return cursor.fetchall()
    
    def get_daily_stats(self):
        """Получение статистики за сегодня"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Новые пользователи за сегодня
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(joined_at) = DATE(?)
            ''', (today,))
            new_users = cursor.fetchone()[0]
            
            # Новые платежи за сегодня
            cursor.execute('''
                SELECT COUNT(*) FROM payments 
                WHERE DATE(created_at) = DATE(?)
            ''', (today,))
            new_payments = cursor.fetchone()[0]
            
            # Истекшие подписки за сегодня
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE status = "expired" AND DATE(end_date) = DATE(?)
            ''', (today,))
            expired_users = cursor.fetchone()[0]
            
            # Активные подписки
            cursor.execute('SELECT COUNT(*) FROM users WHERE status = "active"')
            active_users = cursor.fetchone()[0]
            
            return {
                'new_users': new_users,
                'new_payments': new_payments,
                'expired_users': expired_users,
                'active_users': active_users
            }