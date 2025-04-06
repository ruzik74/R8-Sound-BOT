from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'

def run():
    port = int(os.environ.get('PORT', 5000))  # Используем порт, заданный в Render или 5000 по умолчанию
    app.run(host='0.0.0.0', port=port)
