from flask import Flask, request, jsonify, render_template_string
import yt_dlp
import requests

app = Flask(__name__)

# تصميم عصري وحديث
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محمل الفيديوهات الذكي</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Cairo', sans-serif;
            background: linear-gradient(135deg, #111 0%, #333 100%);
            margin: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #fff;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 15px 30px rgba(0,0,0,0.5);
            width: 90%;
            max-width: 450px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
        }
        h2 { margin-bottom: 5px; font-weight: 700; font-size: 28px; color: #00ffcc; }
        p { color: #ccc; margin-bottom: 30px; font-size: 15px; }
        input {
            width: 100%;
            padding: 15px;
            border: 2px solid #555;
            background: rgba(0,0,0,0.5);
            color: white;
            border-radius: 12px;
            font-size: 16px;
            box-sizing: border-box;
            outline: none;
            transition: 0.3s;
            font-family: 'Cairo', sans-serif;
            margin-bottom: 15px;
        }
        input:focus { border-color: #00ffcc; }
        button {
            width: 100%;
            padding: 15px;
            background: #00ffcc;
            color: #111;
            border: none;
            border-radius: 12px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
            font-family: 'Cairo', sans-serif;
        }
        button:hover { background: #00ccaa; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 255, 204, 0.4); }
        button:disabled { background: #555; color: #888; cursor: not-allowed; transform: none; box-shadow: none; }
        #result { margin-top: 25px; }
        .download-btn {
            display: block;
            margin: 10px 0;
            padding: 12px;
            background: #ff0055;
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: bold;
            transition: 0.3s;
            box-shadow: 0 4px 6px rgba(255, 0, 85, 0.3);
        }
        .download-btn:hover { background: #cc0044; transform: translateY(-2px); }
        .error { color: #ff4444; background: rgba(255,0,0,0.1); padding: 12px; border-radius: 10px; font-weight: bold; font-size: 14px; border: 1px solid #ff4444; }
        .thumb { border-radius: 15px; max-width: 100%; height: auto; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .video-title { font-size: 16px; margin-bottom: 15px; font-weight: bold; color: #eee;}
    </style>
</head>
<body>

    <div class="container">
        <h2>تحميل الفيديوهات 🔥</h2>
        <p>تيك توك (بدون حقوق)، يوتيوب، وغيرها</p>
        
        <input type="text" id="videoUrl" placeholder="الصق الرابط هنا...">
        <button id="searchBtn" onclick="fetchVideo()">بحث وتحميل</button>

        <div id="result"></div>
    </div>

    <script>
        async function fetchVideo() {
            const url = document.getElementById('videoUrl').value;
            const resultDiv = document.getElementById('result');
            const btn = document.getElementById('searchBtn');
            
            if(!url) {
                resultDiv.innerHTML = `<div class="error">يا طيب غير تخلي الرابط أول؟ 😅</div>`;
                return;
            }

            btn.disabled = true;
            btn.innerHTML = "جاري الاختراق والسحب... ⏳";
            resultDiv.innerHTML = "";

            try {
                const response = await fetch('/get_video', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                if (data.error) {
                    resultDiv.innerHTML = `<div class="error">${data.error}</div>`;
                    btn.disabled = false;
                    btn.innerHTML = "بحث وتحميل";
                    return;
                }

                let html = ``;
                if(data.thumbnail) {
                    html += `<img src="${data.thumbnail}" class="thumb">`;
                }
                html += `<div class="video-title">${data.title}</div>`;
                
                data.formats.forEach(format => {
                    html += `<a href="${format.url}" target="_blank" class="download-btn">📥 ${format.resolution}</a>`;
                });

                resultDiv.innerHTML = html;

            } catch (error) {
                resultDiv.innerHTML = `<div class="error">صار خطأ بالاتصال، تأكد من الرابط.</div>`;
            } finally {
                btn.disabled = false;
                btn.innerHTML = "بحث وتحميل";
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

@app.route('/get_video', methods=['POST'])
def get_video():
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({"error": "الرجاء إدخال رابط صحيح"}), 400

    # 1. السلاح السري: إذا الرابط تيك توك، نستخدم API خارجي حتى نتجاوز الحظر
    if 'tiktok.com' in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            response = requests.get(api_url).json()
            
            if response.get('code') == 0:
                video_data = response['data']
                return jsonify({
                    "title": video_data.get('title', 'فيديو تيك توك'),
                    "thumbnail": video_data.get('cover'),
                    "formats": [
                        {"resolution": "تحميل بدون علامة مائية", "url": video_data.get('play')}
                    ]
                })
            else:
                return jsonify({"error": "رابط تيك توك غلط أو الفيديو محذوف."}), 400
        except Exception as e:
            return jsonify({"error": "سيرفر تيك توك ديقاوم، جرب مرة ثانية."}), 500

    # 2. إذا مو تيك توك (مثل يوتيوب)، نستخدم الأداة العادية
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    formats.append({
                        'resolution': f"تحميل بدقة {f.get('resolution', 'Unknown')}",
                        'url': f.get('url')
                    })
            
            if formats:
                formats = [formats[-1]] # ناخذ أعلى دقة بس حتى لا تصير هوسة

            return jsonify({
                "title": info.get('title', 'فيديو'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats
            })
            
    except Exception as e:
        return jsonify({"error": "الموقع حظرنا أو الرابط مو مدعوم حالياً."}), 500

if __name__ == '__main__':
    app.run(debug=True)
