# エッジデバイス統合システム README

Raspberry Pi 5 上で動作する「目（カメラ）」「耳（音声認識）」「口（音声合成）」を統括する
エッジ側メインシステムのセットアップ・運用ガイドです。

---

## 0. クイックスタート（毎回の起動手順）

セットアップが完了している前提で、普段の起動はこれだけです。

```bash
cd edge/
source env/bin/activate
python3 app.py
```

| コマンド | 内容 |
|---------|------|
| `cd edge/` | エッジプロジェクトのディレクトリへ移動 |
| `source env/bin/activate` | Python仮想環境を有効化（プロンプトが `(env)` になる） |
| `python3 app.py` | メインプログラム起動（耳・目・口・サーバー通信が全て立ち上がる） |

起動が成功すると、以下のようなログが表示されます。

```
[SYSTEM] エッジデバイスを起動します...
[SYSTEM] 音声モジュール（耳）を初期化中...
[SYSTEM] カメラモジュール（目）を初期化中...
[CAMERA] ===== 起動時カメラ情報 =====
[SYSTEM] ハートビート監視開始（30秒間隔）
[SYSTEM] ウェイクワード待機ループ開始
[SYSTEM] Flaskサーバー起動 → ポート 5002
```

この状態になれば、マイクに向かって「チャピー」または「起動して」と
話しかけることでシステムが反応します。

終了する場合は `Ctrl + C` を押してください。

初回セットアップがまだの場合は「4. インストール手順」から進めてください。

---

## 1. システム概要

```
┌─────────────────────────────────────────────┐
│           Raspberry Pi 5（エッジ側）           │
│                                                │
│  ウェイクワード検知（耳）                       │
│       ↓ 「チャピー」「起動して」                │
│  コマンド音声取得                               │
│       ↓                                       │
│  カメラ撮影（目）                               │
│       ↓                                       │
│  Ubuntuサーバーへ送信 ───────────► AI解析       │
│       ↓ 回答テキスト受信  ◄───────────         │
│  VOICEVOXで音声再生（口）                       │
│                                                │
│  ※ /video エンドポイントでブラウザから          │
│     リアルタイム映像確認も可能                  │
└─────────────────────────────────────────────┘
```

| モジュール | 役割 | 主な技術 |
|-----------|------|---------|
| `keyword_listener.py` | 耳：ウェイクワード検知・コマンド音声認識 | Vosk, PyAudio |
| `image_processor.py` | 目：カメラ撮影・画像補正 | Picamera2, OpenCV |
| `app.py` | 司令塔：全体制御・サーバー通信・音声再生・映像配信 | Flask, requests, VOICEVOX |

---

## 2. ファイル構成

```
edge/
├── app.py                 # メインプログラム（司令塔）
├── keyword_listener.py    # 耳：ウェイクワード検知
├── image_processor.py     # 目：カメラ撮影・補正
├── test_edge.py           # 結合テストスクリプト
├── start.sh               # 一括起動スクリプト
├── model/                 # Voskの音声認識モデル
└── env/                   # Python仮想環境
```

---

## 3. 必要な環境

- Raspberry Pi 5（Raspberry Pi OS）
- Pythonカメラモジュール（NoIR対応、色補正済み）
- USBマイク
- スピーカー（VOICEVOX音声出力用）
- Ubuntuサーバー（AI解析サーバー、別デバイス）

---

## 4. インストール手順

### 4-1. システムパッケージ

```bash
sudo apt update
sudo apt install -y \
    python3-picamera2 \
    libcap-dev \
    libcamera-dev \
    python3-libcamera \
    portaudio19-dev \
    alsa-utils \
    unzip
```

### 4-2. Python仮想環境の作成

picamera2 はシステム側のパッケージに依存するため、
`--system-site-packages` 付きで仮想環境を作成します。

```bash
cd /home/pbl8/edge
python3 -m venv --system-site-packages env
source env/bin/activate
```

### 4-3. pipパッケージのインストール

```bash
pip install \
    vosk \
    SpeechRecognition \
    pyaudio \
    flask \
    requests \
    opencv-python \
    pillow \
    numpy
```

### 4-4. VOICEVOXエンジンの導入

ARM64版は新しいバージョン（0.25.2）を使用します。

```bash
cd ~
wget https://github.com/VOICEVOX/voicevox_engine/releases/download/0.25.2/voicevox_engine-linux-cpu-arm64-0.25.2.vvpp
mkdir ~/voicevox_engine
unzip voicevox_engine-linux-cpu-arm64-0.25.2.vvpp -d ~/voicevox_engine
```

動作確認：

```bash
~/voicevox_engine/run --host 0.0.0.0 --port 50021 &
curl http://localhost:50021/version
```

---

## 5. マイクの設定

USBマイクが `card 0` 以外（例：`card 2`）に割り当てられている場合、
ALSAのデフォルトデバイスを固定します。

```bash
nano ~/.asoundrc
```

```
defaults.pcm.card 2
defaults.ctl.card 2
```

確認：

```bash
arecord -l                                   # マイクのカード番号確認
arecord -d 3 -D hw:2,0 -f cd /tmp/test.wav   # 録音テスト
aplay /tmp/test.wav                          # 再生確認
```

---

## 6. カメラの色補正について

NoIRカメラは赤外線カットフィルターがないため、肌や髪が青みがかって映ります。
`image_processor.py` 内でBGR888取得後にRGBへスワップする補正を行っています。

```python
config = self.picam.create_video_configuration(
    main={"format": "BGR888", "size": (640, 480)}
)
...
frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
```

色味が気になる場合は、カメラ前面に **IRカットフィルター** を取り付けると
ハード的に解決できます。

---

## 7. 起動方法

### 7-1. 個別に手動起動する場合

```bash
# VOICEVOXエンジン起動
~/voicevox_engine/run --host 0.0.0.0 --port 50021 &

# エッジアプリ起動
cd /home/pbl8/edge
source env/bin/activate
python3 app.py
```

### 7-2. 起動スクリプトを使う場合

```bash
nano /home/pbl8/edge/start.sh
```

```bash
#!/bin/bash
~/voicevox_engine/run --host 0.0.0.0 --port 50021 &
echo "[VOICEVOX] 起動中... 5秒待機"
sleep 5

source /home/pbl8/edge/env/bin/activate
python3 /home/pbl8/edge/app.py
```

```bash
chmod +x /home/pbl8/edge/start.sh
./start.sh
```

起動後、以下のエンドポイントが利用可能になります。

| エンドポイント | 用途 |
|---------------|------|
| `POST http://<RasPiIP>:5002/command` | サーバーからの命令受付（認識開始・停止） |
| `GET  http://<RasPiIP>:5002/video` | ブラウザでリアルタイム映像を確認 |

---

## 8. 設定値の変更箇所

`app.py` の先頭にある設定値は環境に応じて変更してください。

```python
SERVER_URL    = "http://192.168.100.103:5000"  # ← UbuntuサーバーのIPアドレス
VOICEVOX_URL  = "http://localhost:50021"        # ラズパイローカルのVOICEVOX
FLASK_PORT    = 5002                             # ラズパイ側Flaskのポート
HEARTBEAT_INTERVAL = 30                          # サーバー死活確認間隔（秒）
```

UbuntuサーバーのIPアドレスは、サーバー側で以下を実行して確認します。

```bash
hostname -I
```

---

## 9. テスト方法

`app.py` を起動した状態で **別ターミナル**から実行します。
（マイク・カメラはどちらか一方しか同時に専有できないため、
 app.py を一度止めてからテストすることを推奨します）

```bash
cd /home/pbl8/edge
source env/bin/activate
python3 test_edge.py
```

テスト内容：

| # | テスト内容 | 確認できること |
|---|-----------|--------------|
| 1 | ウェイクワード＋コマンド取得 | 音声が正しく認識されているか |
| 2 | カメラ撮影 | 画像が撮れているか・色味（`test_outputs/`に保存） |
| 3 | サーバー送信 | データが届いてAI回答が返ってくるか |
| 4 | VOICEVOX再生 | スピーカーから音声が出るか |
| 5 | ハートビート | サーバーと常時通信できているか |
| 6 | Flask `/command` | サーバーからの命令を受け取れるか |

---

## 10. 主要メソッド一覧（app.py）

| メソッド名 | 役割 | 戻り値 |
|-----------|------|--------|
| `listen_to_server_request()` | サーバーからの実行命令を待ち受ける（`/command`） | JSON形式の命令データ |
| `play_voice(text)` | VOICEVOXでキャラクターボイスを再生する | なし |
| `send_data_to_server(image_bytes, command)` | 画像・コマンドをサーバーへ送信し回答を受け取る | 回答テキスト（失敗時はNone） |
| `heartbeat_check()` | サーバーとの接続状態を定期確認する | なし |
| `generate_video_stream()` | カメラ映像をMJPEGストリームとして配信する | フレームのジェネレータ |

---

## 11. トラブルシューティング

| 症状 | 原因・対処 |
|------|-----------|
| `ModuleNotFoundError: videodev2` | Raspberry Pi OS以外、または非対応Pythonバージョンで実行している。`--system-site-packages`でvenvを作り直す |
| `ModuleNotFoundError: pykms` | システム側にしかないモジュール。venvを`--system-site-packages`で再作成 |
| カメラ初期化で `Camera frontend has timed out` | フレックスケーブルの接触不良。電源を切ってケーブルを挿し直す |
| マイクが `Device or resource busy` | 他のプロセス（app.pyなど）がすでにマイクを掴んでいる。該当プロセスを停止してから実行 |
| マイクの初期化に失敗し続ける | ALSAのデフォルトカード番号が違う。`~/.asoundrc` でカード番号を固定する |
| カメラ映像が青っぽい | NoIRカメラの特性。`image_processor.py` のBGR/RGBスワップ処理で補正、根本解決はIRカットフィルター |
| サーバー送信が `接続できません` になる | `SERVER_URL` のIPが間違っている、またはサーバー側が未起動 |

---

## 12. 終了方法

```
Ctrl + C
```

終了時にカメラ・マイクのリソースが自動的に解放されます。