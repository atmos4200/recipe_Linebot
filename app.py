from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from dotenv import load_dotenv
from openai import OpenAI

# .envファイルの読み込み
load_dotenv()

# OpenAIクライアント（gpt-3.5-turbo 使用）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# LINE Botの設定
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Flaskアプリ
app = Flask(__name__)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"エラー: {e}")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text

    prompt = f"""
以下の食材を使った、簡単で美味しい1品料理を考えてください。
ステップは3つ以内。出力形式は以下でお願いします。

レシピ名:
材料:
作り方:

食材: {user_input}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300  # 出力制限（省メモリ）
        )

        reply_text = response.choices[0].message.content.strip()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )

    except Exception as e:
        print(f"処理中にエラー: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="レシピを作れなかったよ💦 また送ってみてね！")
        )

if __name__ == "__main__":
    app.run(port=8000)
