from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import os
from dotenv import load_dotenv
from openai import OpenAI

# .envファイルの読み込み
load_dotenv()

# OpenAIクライアント（v1対応）
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

    # GPTに送るプロンプト
    prompt = f"""
    あなたはプロの料理人です。
    以下の食材を使って家庭でも作れる美味しいレシピを1つ考えてください。
    食材: {user_input}
    出力形式：
    レシピ名:
    材料:
    作り方:
    """

    try:
        # ChatGPTからレシピを取得
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        reply_text = response.choices[0].message.content

        # タイトル部分を切り出す（画像生成用プロンプトに使う）
        recipe_title = reply_text.split("材料:")[0].replace("レシピ名:", "").strip()

        # DALL·Eで料理画像生成（1024x1024）
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=f"{recipe_title}の料理写真風イラスト",
            size="1024x1024",
            quality="standard",
            n=1
        )
        image_url = image_response.data[0].url

        # LINEへテキスト＋画像メッセージを送信
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text=reply_text),
                ImageSendMessage(
                    original_content_url=image_url,
                    preview_image_url=image_url
                )
            ]
        )
    except Exception as e:
        print(f"処理中にエラー: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ごめんなさい！レシピを生成できませんでした。もう一度試してね🙏")
        )

if __name__ == "__main__":
    app.run(port=8000)

