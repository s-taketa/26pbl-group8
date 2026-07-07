import requests

# ここに実際の値を直接コピペする（" " で囲むのを忘れずに！）
TEST_TOKEN = "ojAa+93cWqpSwYrmeMiwA7vJ1MuZ7o+vcpmrMIcw0wvGtbDevSMt3qyNe9CIvJ5jsHAfD33CfGHWVPKULLddLcScTf6OcWR/XHWwQkbTILH8HTkPBiLshXpEvlyPLd5RgFAug7zxUb1haakBxxp2iwdB04t89/1O/w1cDnyilFU="
TEST_USER_ID = "U4d8d82ab35e42a3dcf29471cd48d970a"

url = "https://api.line.me/v2/bot/message/push"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TEST_TOKEN}"
}
data = {
    "to": TEST_USER_ID,
    "messages": [
        {
            "type": "text",
            "text": "テスト通知だよ！無事に届いたかな？"
        }
    ]
}

print("送信テストを開始するよ...")
response = requests.post(url, headers=headers, json=data)

print(f"ステータスコード: {response.status_code}")
print(f"レスポンス詳細: {response.text}")