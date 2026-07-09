# 各種図（Mermaid） — コエミマ

フローチャート・ユースケース図・全体構成図・クラス図・シーケンス図・ER図を Mermaid で記述する。Markdown対応ビューア（GitHub, VS Code等）でそのまま図として表示できる。

---

## 1. 全体構成図

```mermaid
flowchart LR
    subgraph Edge["エッジ: Raspberry Pi 5"]
        MIC[USBマイク] --> KL[keyword_listener<br/>Vosk STT]
        BTN[物理ボタン GPIO18] --> KL
        CAM[カメラ NoIR] --> IP[image_processor]
        KL --> APP[app.py Flask]
        IP --> APP
        SPK[スピーカー] 
        APP --> SPK
    end
    subgraph Server["サーバー: Ubuntu / Docker"]
        MAIN[main.py Flask]
        AI[ai_logic<br/>Gemini]
        VH[voice_handler<br/>VOICEVOX]
        DB[(MySQL)]
        MAIN --> AI
        MAIN --> VH
        MAIN --> DB
    end
    subgraph Ext["外部サービス"]
        GEM[Gemini API]
        VVX[VOICEVOX Engine]
        LINE[LINE Messaging API]
        SMTP[Gmail SMTP]
    end
    subgraph Family["家族"]
        WEB[ブラウザ<br/>ダッシュボード]
        LN[LINEアプリ]
    end

    APP -->|画像+コマンド| MAIN
    MAIN -->|音声ストリーム| APP
    AI --> GEM
    VH --> VVX
    MAIN --> LINE --> LN
    MAIN --> SMTP
    WEB -->|HTTP| MAIN
    WEB -.->|/video| APP
```

---

## 2. ユースケース図

```mermaid
flowchart TB
    User((利用者<br/>視覚に不安のある方))
    Family((家族/補助者))

    subgraph コエミマ
        UC1[声/ボタンで起動する]
        UC2[周囲の状況を尋ねる]
        UC3[AIの回答を音声で聞く]
        UC4[ダッシュボードで見守る]
        UC5[履歴ログを確認する]
        UC6[通知設定を変更する]
        UC7[緊急通知を受け取る]
        UC8[ログイン/登録/再設定]
    end

    User --- UC1
    User --- UC2
    User --- UC3
    Family --- UC4
    Family --- UC5
    Family --- UC6
    Family --- UC7
    Family --- UC8
```

---

## 3. フローチャート（エッジの認識フロー）

```mermaid
flowchart TD
    A[待機: ウェイクワード監視] --> B{合言葉 or ボタン?}
    B -- いいえ --> A
    B -- はい --> C[合図音 ピッ]
    C --> D[コマンド聞き取り Vosk]
    D --> E{聞き取れた?}
    E -- いいえ --> A
    E -- はい --> F[カメラ撮影 JPEG]
    F --> G[サーバーへ送信<br/>POST /api/recognition]
    G --> H{応答あり?}
    H -- いいえ(エラー) --> A
    H -- はい --> I[文ごとにWAV受信・再生]
    I --> A
```

---

## 4. クラス図・シーケンス図・ER図
- クラス図・シーケンス図 → 「詳細設計/詳細設計書.md」
- 認識フローのシーケンス → 「基本設計/基本設計書.md 6章」
- ER図 → 「基本設計/SQL設計書.md」

> 画像（PNG）が必要な場合は、Mermaid を `mmdc`（mermaid-cli）や各種オンラインエディタでPNG/SVGに書き出せる。
