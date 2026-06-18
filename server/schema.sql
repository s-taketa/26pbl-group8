-- sql/schema.sql

-- users (ユーザー管理)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    login_id VARCHAR(255) NOT NULL UNIQUE COMMENT '電話番号またはメールアドレス',
    password_hash VARCHAR(255) NOT NULL COMMENT 'ハッシュ化されたパスワード',
    user_name VARCHAR(100) COMMENT '表示名',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '登録日時'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- recognition_logs (認識・対話ログ)
CREATE TABLE IF NOT EXISTS recognition_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '対象ユーザーID',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '発生日時',
    image_path VARCHAR(500) COMMENT 'サーバー上の画像保存先パス',
    user_query TEXT COMMENT '音声認識された質問内容',
    ai_response TEXT COMMENT 'AIが生成した回答内容',
    is_emergency TINYINT(1) DEFAULT 0 COMMENT '緊急判定 (1:緊急, 0:通常)',
    CONSTRAINT fk_recognition_logs_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- notification_history (通知・行動履歴)
CREATE TABLE IF NOT EXISTS notification_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '対象ユーザーID',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '通知日時',
    category VARCHAR(50) COMMENT '通知種別 (薬、転倒予兆、生存確認等)',
    message TEXT COMMENT '通知メッセージの内容',
    is_read TINYINT(1) DEFAULT 0 COMMENT '既読フラグ (1:既読, 0:未読)',
    CONSTRAINT fk_notification_history_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- system_settings (システム全体の設定)
CREATE TABLE IF NOT EXISTS system_settings (
    setting_key VARCHAR(100) PRIMARY KEY COMMENT '設定キー名',
    setting_value TEXT COMMENT '設定値',
    category VARCHAR(50) COMMENT '設定カテゴリ',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

