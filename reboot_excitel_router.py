from flask import Flask, request, jsonify
import pytesseract
from PIL import Image
import requests
from io import BytesIO
import requests
import time


pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

#function to call the shutdown API
def shutdown(ecntToken):
    api_url = 'http://10.0.0.1/cgi-bin/mag-reset.asp'
    headers = {
        'host':'10.0.0.1',
        'proxy-connection':'keep-alive',
        'content-length':'41',
        'cache-control':'max-age=0',
        'upgrade-insecure-requests':'1',
        'origin':'http://10.0.0.1',
        'content-type':'application/x-www-form-urlencoded',
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67',
        'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'referer':'http://10.0.0.1/cgi-bin/mag-reset.asp',
        'accept-encoding':'gzip, deflate',
        'accept-language':'en-GB,en;q=0.9,en-US;q=0.8',
        'cookie':'EBOOVALUE=9b490b66; ecntToken='+ecntToken
        }
    form_data = {
    'rebootflag': '1',
    'restoreFlag': '1',
    'isCUCSupport': '0'
    }
    print("shutdown called")
    response = requests.post(api_url, headers=headers, data=form_data)
    if response.status_code == 200:
         data = response.text
         #print(data)
         return True
    else:
        print(f"Request failed with status code: {response.status_code}")

#function to fetch the encrypted token
def tokenFetch(captcha_value,i):
    api_url = 'http://10.0.0.1/cgi-bin/check_auth.json'
    headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
                   'accept':'application/json, text/javascript, */*; q=0.01',
                   'x-requested-with':'XMLHttpRequest',
                   'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67',
                   'content-type':'application/x-www-form-urlencoded; charset=UTF-8',
                   'origin':'http://10.0.0.1',
                   'cookie':'ecntToken=126e054eaa7ba777f66eafde0fd0e82dc;loginTimes=0'}
    form_data = "username=excitel&password=exc%40123&validateCode="+captcha_value+"&captcha_url="+i
    response = requests.post(api_url, headers=headers, data=form_data)
    if response.status_code == 200:
        data = response.json()
        #print(data)
        if data['ecntToken'] != "000000000000000000000000000000000":
            print("token received")
            return shutdown(data['ecntToken'])
        else:
            return False
    else:
        print(f"Request failed with status code: {response.status_code}")

#load the page to get fresh captcha
def pageLoad():

    response = requests.get("http://10.0.0.1/cgi-bin/login.asp")
    if response.status_code == 200:
        print("Page Load Called")
    else:
        print(f"Request failed with status code: {response.status_code}")

#function to read the captcha image (room for improvement)
def captcha(i):
    #image URL base on router gateway, it could be 192.168.1.1
    image_url = "http://10.0.0.1/captcha/captcha_"+i+".gif"
    pageLoad()
    try:
        response = requests.get(image_url)
        gif_image = Image.open(BytesIO(response.content))

        # Extract frames from the GIF
        frames = []
        for frame in range(0, gif_image.n_frames):
            gif_image.seek(frame)
            frame_image = gif_image.convert('RGB')
            frames.append(frame_image)

    except Exception as e:
        return jsonify({'error': 'Failed to download or process the image.', 'details': str(e)}), 500

    captcha_text = ''
    for frame_image in frames:
        # Preprocess the frame image (if required)
        # frame_image = frame_image.convert('L')  # Convert to grayscale
        # frame_image = frame_image.point(lambda x: 0 if x < 128 else 255, '1')  # Thresholding

        # Perform OCR on the frame image
        frame_text = pytesseract.image_to_string(frame_image, config='--psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz')
        captcha_text += frame_text.strip()
    #Fetch Tokem
    return tokenFetch(captcha_text,i)


app = Flask(__name__)

@app.route('/reboot_router', methods=['POST'])
def captcha_call():
    if request.json.get('secret_key') != "chan101_magicWord":
        return jsonify({'Message': "who are you ? (OwO)"}), 400
    #try captcha 0 to 29 and loop back
    i = 0
    c = 0
    while True:
        if i==29:
            i=0
            c+=1
        else:
            i+=1
        if captcha(str(i)):
            return jsonify({'Message': "reboot success"}), 200
        elif c == 2:
            time.sleep(120)
        elif c == 4:
            return jsonify({'Message': "reboot failed"}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
