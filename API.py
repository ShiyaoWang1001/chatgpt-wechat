from flask import Flask, request
import requests
import xmltodict
import time
import os
import hashlib
import logging

# 创建Flask应用实例
app = Flask(__name__)

# 从环境变量中获取钥匙和微信Token（已注释掉）
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY')
# WECHAT_TOKEN = os.getenv('WECHAT_TOKEN', 'YOUR_WECHAT_TOKEN')

# 直接在代码中定义钥匙和微信Token（不推荐，因为保密性差）
OPENAI_API_KEY = ''
WECHAT_TOKEN = 'small_beginnings'

# 设置日志记录，记录级别为INFO
logging.basicConfig(level=logging.INFO)

# 定义函数获取ChatGPT的回复
def get_chatgpt_response(prompt):
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'prompt': prompt,
        'max_tokens': 150
    }
    try:
        # 向OpenAI API发送POST请求
        response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions', headers=headers, json=data)
        response.raise_for_status()  # 如果请求失败，抛出异常
        return response.json()['choices'][0]['text']  # 返回API回复的文本
    except requests.exceptions.RequestException as e:
        # 记录请求错误日志
        logging.error(f"Error fetching response from OpenAI: {e}")
        return "Sorry, there was an error processing your request."

# 定义/wechat路由处理函数，处理GET和POST请求
@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    if request.method == 'GET':
        # 处理GET请求，主要用于微信服务器验证
        query = request.args
        signature = query.get('signature', '')
        timestamp = query.get('timestamp', '')
        nonce = query.get('nonce', '')
        echostr = query.get('echostr', '')

        # 将timestamp, nonce和WECHAT_TOKEN进行排序并连接成字符串，然后进行SHA1加密
        s = [timestamp, nonce, WECHAT_TOKEN]
        s.sort()
        s = ''.join(s).encode('utf-8')

        # 比较加密结果与微信服务器发送的signature，如果匹配则返回echostr
        if hashlib.sha1(s).hexdigest() == signature:
            return echostr
        else:
            return ""

    elif request.method == 'POST':
        # 处理POST请求，主要用于接收微信消息
        xml_data = request.data
        try:
            # 解析XML数据
            msg = xmltodict.parse(xml_data)['xml']
            user_message = msg['Content']
            # 获取ChatGPT的回复
            chatgpt_response = get_chatgpt_response(user_message)

            # 构建回复XML
            response = {
                'xml': {
                    'ToUserName': msg['FromUserName'],
                    'FromUserName': msg['ToUserName'],
                    'CreateTime': int(time.time()),
                    'MsgType': 'text',
                    'Content': chatgpt_response
                }
            }
            response_xml = xmltodict.unparse(response)  # 将字典转换回XML
            return response_xml
        except Exception as e:
            # 记录处理错误日志
            logging.error(f"Error processing request: {e}")
            return ""

# 运行Flask应用，监听所有网络接口的80端口
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)