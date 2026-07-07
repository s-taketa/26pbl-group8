# server/main_controller.py
import os
import time
import random

from werkzeug.security import check_password_hash

try:
    import mailer
except Exception as e:
    print(f"[WARN] mailer 読み込み失敗（メール送信なしで継続）: {e}")
    mailer = None

# 認証コードの有効期限（秒）
AUTH_CODE_TTL = 300

# 設定項目のデフォルト値（system_settings に未保存のときに使う）
SETTING_DEFAULTS = {
    "notify_conversation_log": "1",   # 会話ログ送信
    "notify_periodic": "0",           # 定期的な通知
    "keyword": "チャピー,起動して",   # ウェイクワード（カンマ区切りで複数可）
    "user_name": "管理者",            # 表示名
}


class MainController:
    """管理・認証を扱うサーバーサイドのメインクラス。
    DatabaseManager を受け取り、認証やダッシュボード用データ取得を担う。"""

    def __init__(self, db=None):
        self.db = db
        # 認証コードの一時保管（連絡先 → コード）。デモ用にメモリ上で管理する。
        self._auth_codes = {}

    # ---------- 認証 ----------
    def authenticateUser(self, login_id, password):
        """補助者のログイン情報を検証する（ハッシュ照合）。"""
        if not self.db or not login_id or not password:
            return False
        try:
            user = self.db.getUserByEmail(login_id)
        except Exception as e:
            print(f"[AUTH] DB照会失敗: {e}")
            return False
        if user and check_password_hash(user.password_hash, password):
            return True
        return False

    def registerUser(self, login_id, password, user_name=None):
        """新規アカウントを登録する。戻り値は (成功フラグ, メッセージ)。"""
        if not (self.db and login_id and password):
            return (False, "必須項目を入力してください")
        if len(password) < 8:
            return (False, "パスワードは8文字以上で入力してください")
        try:
            if self.db.getUserByEmail(login_id):
                return (False, "このIDは既に登録されています")
            from werkzeug.security import generate_password_hash
            ok = self.db.createUser({
                "login_id": login_id,
                "password_hash": generate_password_hash(password),
                "user_name": user_name or "名無し",
            })
            return (True, "登録が完了しました") if ok else (False, "登録に失敗しました")
        except Exception as e:
            print(f"[AUTH] 登録失敗: {e}")
            return (False, "登録に失敗しました")

    def sendAuthCode(self, contact=None):
        """認証用4桁コードを生成・保管し、可能ならメール送信する。
        宛先がメール形式かつSMTP設定済みなら実送信、それ以外はログ出力にフォールバック。"""
        code = f"{random.randint(0, 9999):04d}"
        key = contact or "_last"
        self._auth_codes[key] = {"code": code, "expires_at": time.time() + AUTH_CODE_TTL}

        # メール宛 & SMTP設定済みなら実送信
        if mailer and contact and mailer.is_email(contact) and mailer.is_configured():
            try:
                mailer.send_email_code(contact, code)
                print(f"[AUTH] 認証コードをメール送信しました → {contact}")
                return code
            except Exception as e:
                print(f"[AUTH] メール送信失敗（ログ出力に代替）: {e}")

        # フォールバック：ログ出力（SMS基盤やSMTP未設定時）
        print(f"[AUTH] 認証コードを発行しました（{contact or '宛先未指定'}）: {code}")
        return code

    def validateAuthCode(self, code, contact=None):
        """送信した認証コードを検証する（有効期限つき）。"""
        if not code:
            return False
        entry = self._auth_codes.get(contact or "_last")
        if not entry:
            return False
        if time.time() > entry["expires_at"]:
            print("[AUTH] 認証コードの有効期限切れ")
            return False
        return code == entry["code"]

    def resetPassword(self, login_id=None, new_password=None):
        """認証後にパスワードを更新する。"""
        if not (self.db and login_id and new_password):
            return False
        try:
            from werkzeug.security import generate_password_hash
            session = self.db._get_session()
            from models import User
            user = session.query(User).filter(User.login_id == login_id).first()
            if not user:
                return False
            user.password_hash = generate_password_hash(new_password)
            session.commit()
            return True
        except Exception as e:
            print(f"[AUTH] パスワード更新失敗: {e}")
            return False
        finally:
            try:
                session.close()
            except Exception:
                pass

    # ---------- ダッシュボード ----------
    def getDashboardData(self):
        """画面表示用にログ履歴を取得する。"""
        if not self.db:
            return []
        try:
            logs = self.db.getRecognitionHistory(limit=20)
        except Exception as e:
            print(f"[DASH] ログ取得失敗: {e}")
            return []
        result = []
        for log in logs:
            image_url = ""
            if log.image_path:
                image_url = "/images/" + os.path.basename(log.image_path)
            result.append({
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M") if getattr(log, "timestamp", None) else "",
                "query": log.user_query,
                "response": log.ai_response,
                "is_emergency": int(bool(log.is_emergency)),
                "image_url": image_url,
            })
        return result

    # ---------- 設定 ----------
    def getSettings(self):
        """通知設定などを取得する（未保存項目はデフォルト値）。"""
        settings = dict(SETTING_DEFAULTS)
        if not self.db:
            return settings
        for key in SETTING_DEFAULTS:
            try:
                value = self.db.getSystemSettings(key)
                if value is not None:
                    settings[key] = value
            except Exception as e:
                print(f"[SET] 設定取得失敗 {key}: {e}")
        return settings

    def updateSettings(self, data):
        """設定を保存する。boolは "1"/"0" に正規化して保存。"""
        if not self.db:
            return False
        ok = True
        for key in SETTING_DEFAULTS:
            if key in data and data[key] is not None:
                value = data[key]
                if isinstance(value, bool):
                    value = "1" if value else "0"
                ok = self.db.setSystemSetting(key, str(value), "notification") and ok
        return ok

    def syncSettingsToEdge(self):
        """画面での設定変更をラズパイへ反映させる命令を送る（将来実装）。"""
        edge_url = os.getenv("EDGE_URL")
        if not edge_url:
            print("[SYNC] EDGE_URL 未設定のためスキップ")
            return False
        try:
            import requests
            requests.post(f"{edge_url}/command", json={"action": "sync_settings"}, timeout=5)
            return True
        except Exception as e:
            print(f"[SYNC] エッジ反映失敗: {e}")
            return False
