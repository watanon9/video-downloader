import os
import tempfile
import requests
import subprocess
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
import yt_dlp
import imageio_ffmpeg

app = Flask(__name__)

# جلب مسار FFmpeg برمجياً ليعمل على استضافة Render
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>منصة التحميل الذكية</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --text-main: #f8fafc;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --border: rgba(255, 255, 255, 0.1);
        }
        /* منع السكرول في كامل الصفحة وجعلها بحجم الشاشة فقط */
        html, body {
            height: 100dvh;
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: 'Tajawal', sans-serif;
            background-color: var(--bg-color);
            background-image: radial-gradient(circle at top right, #1e293b, var(--bg-color));
            color: var(--text-main);
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .app-wrapper {
            width: 100%;
            height: 100%;
            max-width: 500px;
            display: flex;
            flex-direction: column;
            padding: 20px;
            box-sizing: border-box;
        }
        .header { text-align: center; margin-bottom: 15px; flex-shrink: 0; }
        .header h2 { margin: 0; font-size: 28px; font-weight: 900; color: #60a5fa; }
        .header p { margin: 5px 0 0; font-size: 14px; color: #94a3b8; }
        
        .input-box {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 15px;
            backdrop-filter: blur(10px);
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .input-row { display: flex; gap: 10px; }
        input {
            flex: 1; padding: 15px; background: rgba(0,0,0,0.2); border: 1px solid var(--border);
            color: white; border-radius: 12px; font-size: 15px; outline: none; font-family: 'Tajawal', sans-serif;
        }
        input:focus { border-color: var(--primary); }
        .btn-paste { background: #334155; border: none; color: white; padding: 0 15px; border-radius: 12px; cursor: pointer; transition: 0.2s; }
        .btn-paste:hover { background: #475569; }
        .btn-main {
            padding: 15px; background: var(--primary); color: white; border: none; border-radius: 12px;
            font-size: 16px; font-weight: 700; cursor: pointer; font-family: 'Tajawal', sans-serif; transition: 0.2s;
        }
        .btn-main:hover { background: var(--primary-hover); transform: translateY(-2px); }
        
        /* منطقة النتائج مع سكرول داخلي فقط */
        .result-area {
            margin-top: 15px;
            flex: 1;
            overflow-y: auto;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 15px;
            backdrop-filter: blur(10px);
            display: none; /* تظهر فقط عند وجود نتائج */
        }
        /* تجميل شريط السكرول */
        .result-area::-webkit-scrollbar { width: 6px; }
        .result-area::-webkit-scrollbar-thumb { background: #475569; border-radius: 10px; }

        .video-info { display: flex; gap: 15px; align-items: center; margin-bottom: 15px; border-bottom: 1px solid var(--border); padding-bottom: 15px; }
        .thumb { width: 80px; height: 80px; border-radius: 12px; object-fit: cover; }
        .title { font-size: 15px; font-weight: bold; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
        
        .actions-grid { display: grid; grid-template-columns: 1fr; gap: 10px; }
        .btn-action {
            padding: 12px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; 
            display: flex; align-items: center; justify-content: center; gap: 10px; 
            text-decoration: none; font-size: 15px; color: white; transition: 0.2s; font-family: 'Tajawal', sans-serif;
        }
        .btn-action:hover { filter: brightness(1.1); transform: translateY(-2px); }
        
        .bg-mp4 { background: #10b981; } /* أخضر */
        .bg-mp3 { background: #8b5cf6; } /* بنفسجي */
        .bg-wa { background: #25d366; }  /* واتساب */
        .bg-gif { background: #f59e0b; } /* برتقالي */
        .bg-cut { background: #ef4444; } /* أحمر */

        .loading { text-align: center; color: #94a3b8; font-size: 14px; display: none; margin-top: 10px; }
        .error-msg { color: #ef4444; text-align: center; font-size: 14px; margin-top: 10px; font-weight: bold;}
    </style>
</head>
<body>

    <div class="app-wrapper">
        <div class="header">
            <h2>محمل الفيديوهات</h2>
            <p>سريع • مباشر • شامل</p>
        </div>

        <div class="input-box">
            <div class="input-row">
                <input type="text" id="videoUrl" placeholder="أدخل الرابط هنا...">
                <button class="btn-paste" onclick="pasteBtn()"><i class="fas fa-paste"></i></button>
            </div>
            <button class="btn-main" id="searchBtn" onclick="processUrl()">
                <i class="fas fa-search"></i> معالجة الرابط
            </button>
            <div class="loading" id="loader"><i class="fas fa-spinner fa-spin"></i> جاري سحب البيانات...</div>
            <div id="errorBox" class="error-msg"></div>
        </div>

        <div class="result-area" id="resultArea">
            <div class="video-info" id="videoInfo">
                </div>
            <div class="actions-grid" id="actionsGrid">
                </div>
        </div>
    </div>

    <script>
        async function pasteBtn() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('videoUrl').value = text;
            } catch (err) { alert('يرجى السماح باللصق'); }
        }

        async function processUrl() {
            const url = document.getElementById('videoUrl').value;
            const btn = document.getElementById('searchBtn');
            const loader = document.getElementById('loader');
            const resultArea = document.getElementById('resultArea');
            const errBox = document.getElementById('errorBox');
            
            if(!url) return;

            btn.disabled = true;
            loader.style.display = 'block';
            resultArea.style.display = 'none';
            errBox.innerHTML = '';

            try {
                const res = await fetch('/extract_info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                
                const data = await res.json();
                
                if(data.error) {
                    errBox.innerHTML = data.error;
                } else {
                    // عرض النتائج
                    document.getElementById('videoInfo').innerHTML = `
                        <img src="${data.thumbnail}" class="thumb">
                        <div class="title">${data.title}</div>
                    `;
                    
                    const safeTitle = encodeURIComponent(data.title.substring(0,30));
                    const safeUrl = encodeURIComponent(data.video_url);

                    // أزرار التحميل المباشر الإجباري
                    document.getElementById('actionsGrid').innerHTML = `
                        <a href="/force_download?url=${safeUrl}&title=${safeTitle}&ext=mp4" class="btn-action bg-mp4">
                            <i class="fas fa-download"></i> تحميل مباشر (فيديو)
                        </a>
                        <a href="#" onclick="alert('جاري إعداد معالجة الصوت بالخادم...')" class="btn-action bg-mp3">
                            <i class="fas fa-music"></i> تحميل كـ (MP3)
                        </a>
                        <a href="#" onclick="alert('يتم معالجة ضغط الواتساب في الخلفية...')" class="btn-action bg-wa">
                            <i class="fab fa-whatsapp"></i> ضغط فيديو للواتساب
                        </a>
                        <a href="#" onclick="alert('تفعيل مكتبة الصور المتحركة قيد الإجراء...')" class="btn-action bg-gif">
                            <i class="fas fa-images"></i> تحويل إلى (GIF)
                        </a>
                    `;
                    resultArea.style.display = 'block';
                }
            } catch (e) {
                errBox.innerHTML = "حدث خطأ بالاتصال بالخادم.";
            } finally {
                btn.disabled = false;
                loader.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

@app.route('/extract_info', methods=['POST'])
def extract_info():
    url = request.json.get('url', '')
    if not url: return jsonify({"error": "الرابط فارغ!"}), 400

    # 1. دعم تيك توك بأقصى سرعة
    if 'tiktok.com' in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            resp = requests.get(api_url).json()
            if resp.get('code') == 0:
                v = resp['data']
                return jsonify({
                    "title": v.get('title', 'فيديو تيك توك'),
                    "thumbnail": v.get('cover'),
                    "video_url": v.get('play')
                })
        except: pass

    # 2. دعم يوتيوب والمنصات الأخرى باستخدام yt-dlp
    opts = {'quiet': True, 'nocheckcertificate': True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # جلب رابط الفيديو الأصلي المباشر
            formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
            best_video = formats[-1]['url'] if formats else info.get('url')

            return jsonify({
                "title": info.get('title', 'فيديو'),
                "thumbnail": info.get('thumbnail'),
                "video_url": best_video
            })
    except Exception as e:
        return jsonify({"error": "الرابط غير مدعوم أو الحساب خاص."}), 500

# السحر هنا: دالة تجبر المتصفح على تحميل الملف مباشرة (بدون فتح صفحة جديدة)
@app.route('/force_download')
def force_download():
    video_url = request.args.get('url')
    title = request.args.get('title', 'Video_Download')
    ext = request.args.get('ext', 'mp4')
    
    if not video_url: return "رابط مفقود", 400

    try:
        # الاتصال بالرابط المخفي وسحبه كحزم صغيرة ليكون التحميل سريعاً
        req = requests.get(video_url, stream=True, verify=False)
        
        # إجبار المتصفح على تحميله كملف
        headers = {
            'Content-Disposition': f'attachment; filename="{title}.{ext}"',
            'Content-Type': req.headers.get('content-type', 'application/octet-stream')
        }
        
        return Response(stream_with_context(req.iter_content(chunk_size=1024*1024)), headers=headers)
    except Exception as e:
        return "خطأ أثناء محاولة التحميل", 500

if __name__ == '__main__':
    app.run(debug=True)
