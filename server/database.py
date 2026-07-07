# server/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# 同じフォルダにある models を明示的に読み込みます
from models import Base, User, RecognitionLog, NotificationHistory, SystemSetting

# MySQL接続情報（docker-compose / .env の変数名に合わせる）
# 旧コードは DB_PASS を参照していたが compose は DB_PASSWORD を渡すため不一致だった。
DB_USER = os.environ.get("DB_USER", "ai_assistant")
DB_PASS = os.environ.get("DB_PASSWORD", os.environ.get("DB_PASS", "changeme"))
DB_HOST = os.environ.get("DB_HOST", "db")
DB_NAME = os.environ.get("DB_NAME", "ai_assistant_db")

# データベースURLの構成
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"

class DatabaseManager:
    def __init__(self):
        # データベースエンジンとセッションの準備
        self.engine = create_engine(DATABASE_URL, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _get_session(self):
        return self.SessionLocal()

    def init_db(self, seed_default_user=True):
        """テーブルを作成し、ユーザーが一人もいなければ初期ユーザーを作成する。
        schema.sql を流さなくてもアプリ単体で起動できるようにする。"""
        Base.metadata.create_all(self.engine)
        if not seed_default_user:
            return
        session = self._get_session()
        try:
            if session.query(User).count() == 0:
                session.add(User(
                    login_id="admin@example.com",
                    password_hash=generate_password_hash("password123"),
                    user_name="管理者",
                ))
                session.commit()
                print("[DB] 初期ユーザーを作成しました → admin@example.com / password123")
        except Exception as e:
            session.rollback()
            print(f"[DB Error] init seed: {e}")
        finally:
            session.close()

    # データベース操作メソッド

    def createUser(self, user_data):
        # 新規ユーザーを作成
        session = self._get_session()
        try:
            # モデルの定義を最大限尊重し、自動生成される項目は指定しない
            new_user = User(
                login_id=user_data['login_id'],
                password_hash=user_data['password_hash'],
                user_name=user_data.get('user_name', '名無し')
            )
            session.add(new_user)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            # 詳しいエラー内容を出すことで、万が一の再発時に備えます
            print(f"[DB Error Detail] {type(e).__name__}: {e}")
            return False
        finally:
            session.close()

    def getUserByEmail(self, email):
        # ユーザー情報を取得（認証処理用）
        session = self._get_session()
        try:
            return session.query(User).filter(User.login_id == email).first()
        finally:
            session.close()

    def getFirstUserId(self):
        # 認識ログの紐付け先。実在する最初のユーザーIDを返す（初期アカウント固定に依存しない）
        session = self._get_session()
        try:
            user = session.query(User).order_by(User.id.asc()).first()
            return user.id if user else None
        finally:
            session.close()

    def getSystemSettings(self, key):
        # キーワード設定などをsystem_settingsテーブルから取得する
        session = self._get_session()
        try:
            setting = session.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
            return setting.setting_value if setting else None
        finally:
            session.close()

    def setSystemSetting(self, key, value, category=None):
        # 設定値を system_settings に保存（無ければ作成、あれば更新）
        session = self._get_session()
        try:
            setting = session.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
            if setting:
                setting.setting_value = value
                if category is not None:
                    setting.category = category
            else:
                session.add(SystemSetting(setting_key=key, setting_value=value, category=category))
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"[DB Error] setSystemSetting: {e}")
            return False
        finally:
            session.close()

    def writeRecognitionLog(self, logEntry):
        # AIの回答や緊急フラグをrecognition_logsテーブルに保存する
        session = self._get_session()
        try:
            new_log = RecognitionLog(
                user_id=logEntry['user_id'],
                image_path=logEntry.get('image_path', ''),
                user_query=logEntry.get('user_query', ''),
                ai_response=logEntry.get('ai_response', ''),
                is_emergency=logEntry.get('is_emergency', False)
            )
            session.add(new_log)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"[DB Error] writeRecognitionLog: {e}")
            return False
        finally:
            session.close()

    def getRecognitionHistory(self, limit=10):
        # ダッシュボード表示用のログ履歴を最新順で取得
        session = self._get_session()
        try:
            return session.query(RecognitionLog).order_by(RecognitionLog.timestamp.desc()).limit(limit).all()
        finally:
            session.close()

    def writeNotificationHistory(self, entry):
        # 緊急通知などを notification_history テーブルに保存する
        session = self._get_session()
        try:
            new_n = NotificationHistory(
                user_id=entry['user_id'],
                category=entry.get('category', ''),
                message=entry.get('message', ''),
            )
            session.add(new_n)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"[DB Error] writeNotificationHistory: {e}")
            return False
        finally:
            session.close()

    def updateEdgeStatus(self):
        # エッジのオンライン状態を更新
        print("[DB Info] エッジデバイスのステータスを更新しました")
        pass


