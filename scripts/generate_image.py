#!/usr/bin/env python3
import os
import sys
import httpx
from PIL import Image
from io import BytesIO

# 从环境变量获取配置
API_KEY = os.getenv('IMAGE_GEN_API_KEY', 'sk-1111')
BASE_URL = os.getenv('IMAGE_GEN_BASE_URL', 'https://api.example.com')
MODEL = os.getenv('IMAGE_GEN_MODEL', 'gemini-2.0-flash-exp-image-generation')
TIMEOUT = int(os.getenv('IMAGE_GEN_TIMEOUT', '120'))

# 解析命令行参数
prompt = None
output = 'output.png'

i = 1
while i < len(sys.argv):
    if sys.argv[i] == '--prompt' and i+1 < len(sys.argv):
        prompt = sys.argv[i+1]
        i += 1
    elif sys.argv[i] == '--output' and i+1 < len(sys.argv):
        output = sys.argv[i+1]
        i += 1
    i += 1

if not prompt:
    print('Error: --prompt is required')
    sys.exit(1)

# 生成请求
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}

data = {
    'model': MODEL,
    'prompt': prompt,
    'n': 1,
    'size': '1024x1024',
    'response_format': 'b64_json'
}

try:
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
        response = client.post('/v1/images/generations', json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # 保存图片
        if 'data' in result and len(result['data']) > 0:
            img_data = result['data'][0]['b64_json']
            img = Image.open(BytesIO(base64.b64decode(img_data)))
            img.save(output)
            print(f'Image saved to {output}')
        else:
            print('Error: No image data in response')
            sys.exit(1)

except Exception as e:
    print(f'Error: {str(e)}')
    sys.exit(1)