from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from dotenv import load_dotenv
from openai import OpenAI

# .envファイル読み込み
load_dotenv()

# OpenAIクライアント
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# LINE Botの設定
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

app = Flask(__name__)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
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
あなたはプロの料理人です。
以下の食材を使って美味しいレシピを1つ考えてください。
食材: {user_input}
出力形式：
レシピ名:
材料:
作り方:
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        reply_text = response.choices[0].message.content

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        print(f"処理中にエラー: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ごめんね、レシピを作れなかった💦 また送ってみて！")
        )

if __name__ == "__main__":
    app.run(port=8000)


