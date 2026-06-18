# server/models.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# SQLAlchemyのベースクラス
Base = declarative_base()

class User(Base):
    """users テーブルのモデル"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    login_id = Column(String(255), unique=True, nullable=False, comment='電話番号またはメールアドレス')
    password_hash = Column(String(255), nullable=False, comment='ハッシュ化されたパスワード')
    user_name = Column(String(100), comment='表示名')
    created_at = Column(DateTime, default=datetime.utcnow, comment='登録日時')

    # リレーションシップ（ユーザーが削除されたら関連ログも削除される設定）
    recognition_logs = relationship("RecognitionLog", back_populates="user", cascade="all, delete-orphan")
    notification_history = relationship("NotificationHistory", back_populates="user", cascade="all, delete-orphan")


class RecognitionLog(Base):
    """recognition_logs テーブルのモデル"""
    __tablename__ = 'recognition_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, comment='発生日時')
    image_path = Column(String(500), comment='サーバー上の画像保存先パス')
    user_query = Column(Text, comment='音声認識された質問内容')
    ai_response = Column(Text, comment='AIが生成した回答内容')
    is_emergency = Column(Boolean, default=False, comment='緊急判定 (1:緊急, 0:通常)')

    # リレーションシップ
    user = relationship("User", back_populates="recognition_logs")


class NotificationHistory(Base):
    """notification_history テーブルのモデル"""
    __tablename__ = 'notification_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, comment='通知日時')
    category = Column(String(50), comment='通知種別')
    message = Column(Text, comment='通知メッセージの内容')
    is_read = Column(Boolean, default=False, comment='既読フラグ')

    # リレーションシップ
    user = relationship("User", back_populates="notification_history")


class SystemSetting(Base):
    """system_settings テーブルのモデル"""
    __tablename__ = 'system_settings'

    setting_key = Column(String(100), primary_key=True, comment='設定キー名')
    setting_value = Column(Text, comment='設定値')
    category = Column(String(50), comment='設定カテゴリ')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新日時')

