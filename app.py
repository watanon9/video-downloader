from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
import yt_dlp
import requests

app = Flask(__name__)

# تصميم عصري ورسمي جداً
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>منصة تحميل الفيديوهات</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #4F46E5;
            --primary-hover: #4338CA;
            --bg: #0F172A;
            --card-bg: rgba(30, 41, 59, 0.8);
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
        }
        body {
            font-family: 'Cairo', sans-serif;
            background-color: var(--bg);
            background-image: radial-gradient(circle at 50% -20%, #312e81, var(--bg));
            margin: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: var(--text-main);
        }
        .container {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            padding: 40px;
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            width: 90%;
            max-width: 480px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        h2 { margin: 0 0 10px 0; font-weight: 800; font-size: 28px; letter-spacing: -0.5px; }
        p { color: var(--text-muted); margin-bottom: 30px; font-size: 15px; }
        .input-group { position: relative; margin-bottom: 20px; }
        input {
            width: 100%;
            padding: 16px 20px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white;
            border-radius: 16px;
            font-size: 16px;
            box-sizing: border-box;
            outline: none;
            transition: all 0.3s ease;
            font-family: 'Cairo', sans-serif;
        }
        input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.2);
        }
        button {
            width: 100%;
            padding: 16px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 16px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Cairo', sans-serif;
        }
        button:hover {
            background: var(--primary-hover);
            transform: translateY(-2px);
        }
        button:disabled {
            background: #334155;
            color: #94A3B8;
            cursor: not-allowed;
            transform: none;
        }
        #result { margin-top: 30px; }
        .download-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin: 15px 0 0 0;
            padding: 14px;
            background: #10B981;
            color: white;
            text-decoration: none;
            border-radius: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .download-btn:hover { background: #059669; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4); }
        .error { color: #F87171; background: rgba(248, 113, 113, 0.1); padding: 15px; border-radius: 14px; font-weight: 600; font-size: 14px; border: 1px solid rgba(248, 113, 113, 0.2); }
        .thumb { border-radius: 16px; width: 100%; height: 200px; object-fit: cover; margin-bottom: 15px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }
        .video-title { font-size: 16px; margin-bottom: 15px; font-weight: 600; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    </style>
</head>
<body>

    <div class="container">
        <h2>منصة التحميل</h2>
        <p>قم بتحميل مقاطع الفيديو بأعلى جودة متوفرة</p>
        
        <div class="input-group">
            <input type="text" id="videoUrl" placeholder="أدخل رابط الفيديو هنا...">
        </div>
        <button id="searchBtn" onclick="fetchVideo()">معالجة الرابط</button>

        <div id="result"></div>
    </div>

    <script>
        async function fetchVideo() {
            const url = document.getElementById('videoUrl').value;
            const resultDiv = document.getElementById('result');
            const btn = document.getElementById('searchBtn');
            
            if(!url) {
                resultDiv.innerHTML = `<div class="error">الرجاء إدخال رابط صحيح للمتابعة.</div>`;
                return;
            }

            btn.disabled = true;
            btn.innerHTML = "جاري المعالجة... ⏳";
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
                    btn.innerHTML = "معالجة الرابط";
                    return;
                }

                let html = ``;
                if(data.thumbnail) {
                    html += `<img src="${data.thumbnail}" class="thumb">`;
                }
                html += `<div class="video-title">${data.title}</div>`;
                
                data.formats.forEach(format => {
                    // هنا السحر: نرسل الرابط للسيرفر مالتنا حتى يجبره على التحميل كملف
                    const directDownloadUrl = '/download_video?url=' + encodeURIComponent(format.url);
                    html += `<a href="${directDownloadUrl}" class="download-btn">
                        <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>
                        ${format.resolution}
                    </a>`;
                });

                resultDiv.innerHTML = html;

            } catch (error) {
                resultDiv.innerHTML = `<div class="error">حدث خطأ أثناء الاتصال بالخادم. يرجى المحاولة لاحقاً.</div>`;
            } finally {
                btn.disabled = false;
                btn.innerHTML = "معالجة الرابط";
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
        return jsonify({"error": "الرجاء إدخال رابط صحيح."}), 400

    # دعم تيك توك بأداة رسمية
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
                        {"resolution": "تحميل مباشر (بدون علامة مائية)", "url": video_data.get('play')}
                    ]
                })
            else:
                return jsonify({"error": "لم يتم العثور على الفيديو. يرجى التأكد من صحة الرابط."}), 400
        except Exception as e:
            return jsonify({"error": "حدث خطأ في الخادم، يرجى المحاولة مجدداً."}), 500

    # دعم يوتيوب والمنصات الأخرى
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
                        'resolution': f"تحميل مباشر ({f.get('resolution', 'جودة عالية')})",
                        'url': f.get('url')
                    })
            
            if formats:
                formats = [formats[-1]] 

            return jsonify({
                "title": info.get('title', 'فيديو'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats
            })
            
    except Exception as e:
        return jsonify({"error": "الرابط غير مدعوم أو غير صالح."}), 500

# دالة جديدة لإجبار المتصفح على التحميل المباشر كملف
@app.route('/download_video')
def download_video():
    video_url = request.args.get('url')
    if not video_url:
        return "الرابط غير صالح", 400
    
    try:
        # نسحب الفيديو ونرسله للمستخدم على شكل ملف جاهز للتحميل
        req = requests.get(video_url, stream=True)
        return Response(
            stream_with_context(req.iter_content(chunk_size=1024*1024)),
            content_type=req.headers.get('content-type', 'video/mp4'),
            headers={'Content-Disposition': 'attachment; filename="video_download.mp4"'}
        )
    except Exception as e:
        return "حدث خطأ أثناء تحميل الفيديو", 500

if __name__ == '__main__':
    app.run(debug=True)
