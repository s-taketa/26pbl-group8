class MainController:
    # 管理・認証を扱うサーバーサイドのメインクラス

    def authenticateUser(self, id, password):
        # 補助者のログイン情報を検証する。
        pass

    def sendAuthCode(self):
        # 認証用4桁コードを生成・送信する。
        pass

    def validateAuthCode(self, code):
        # 送信した認証コードを検証する。
        pass

    def resetPassword(self):
        # 認証後にパスワードを更新する。
        pass

    def getDashboardData(self):
        # 画面表示用にログや接続状態を一括取得する。
        pass

    def syncSettingsToEdge(self):
        # 画面での設定変更を即座にラズパイへ反映させる命令を送る。
        pass
