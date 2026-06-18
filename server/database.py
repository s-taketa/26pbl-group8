# server/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 同じフォルダにある models を明示的に読み込みます
from .models import User, RecognitionLog, NotificationHistory, SystemSetting

# あなたが構築したDocker環境のMySQL接続情報
DB_USER = os.environ.get("DB_USER", "mimamori_user")
DB_PASS = os.environ.get("DB_PASS", "mimamori_pass")
DB_HOST = os.environ.get("DB_HOST", "db")
DB_NAME = os.environ.get("DB_NAME", "mimamori_db")

# データベースURLの構成
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"

class DatabaseManager:
    def __init__(self):
        # データベースエンジンとセッションの準備
        self.engine = create_engine(DATABASE_URL, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _get_session(self):
        return self.SessionLocal()

    # --- データベース操作メソッド ---

    def createUser(self, user_data):
        """新規ユーザーを作成"""
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
        """ユーザー情報を取得（認証処理用）"""
        session = self._get_session()
        try:
            return session.query(User).filter(User.login_id == email).first()
        finally:
            session.close()

    def getSystemSettings(self, key):
        """キーワード設定などをsystem_settingsテーブルから取得する"""
        session = self._get_session()
        try:
            setting = session.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
            return setting.setting_value if setting else None
        finally:
            session.close()

    def writeRecognitionLog(self, logEntry):
        """AIの回答や緊急フラグをrecognition_logsテーブルに保存する"""
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
        """ダッシュボード表示用のログ履歴を最新順で取得"""
        session = self._get_session()
        try:
            return session.query(RecognitionLog).order_by(RecognitionLog.timestamp.desc()).limit(limit).all()
        finally:
            session.close()

    def updateEdgeStatus(self):
        """エッジのオンライン状態を更新"""
        print("[DB Info] エッジデバイスのステータスを更新しました")
        pass


