import os
import requests
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>منصة التحميل العالمية | VIP</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gifshot/0.3.2/gifshot.min.js"></script>
    <style>
        :root {
            --bg-color: #f3f4f6;
            --card-bg: rgba(255, 255, 255, 0.95);
            --text-main: #1f2937;
            --text-muted: #6b7280;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --border: rgba(0, 0, 0, 0.08);
        }
        [data-theme="dark"] {
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.9);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --border: rgba(255, 255, 255, 0.1);
        }
        html, body {
            height: 100dvh; margin: 0; padding: 0; overflow: hidden;
            font-family: 'Tajawal', sans-serif;
            background-color: var(--bg-color); color: var(--text-main);
            transition: background-color 0.3s;
        }
        .app-container {
            display: flex; flex-direction: column; height: 100%; max-width: 480px; margin: 0 auto;
            background: var(--bg-color); position: relative;
        }
        
        .top-bar {
            display: flex; justify-content: space-between; align-items: center; padding: 15px 20px;
            background: var(--card-bg); border-bottom: 1px solid var(--border); z-index: 10;
            backdrop-filter: blur(10px);
        }
        .top-bar h3 { margin: 0; font-weight: 900; background: linear-gradient(45deg, var(--primary), #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .theme-btn {
            background: transparent; border: 1px solid var(--border); color: var(--text-main);
            padding: 8px 15px; border-radius: 20px; cursor: pointer; font-family: 'Tajawal', sans-serif; font-weight: bold;
        }
        
        .main-content {
            flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 15px;
        }
        .main-content::-webkit-scrollbar { width: 4px; }
        .main-content::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }

        .input-card {
            background: var(--card-bg); padding: 15px; border-radius: 20px; border: 1px solid var(--border);
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); display: flex; flex-direction: column; gap: 10px;
        }
        .input-row { display: flex; gap: 10px; }
        input {
            flex: 1; padding: 14px; background: transparent; border: 2px solid var(--border);
            color: var(--text-main); border-radius: 12px; font-size: 15px; outline: none; font-family: 'Tajawal', sans-serif;
        }
        input:focus { border-color: var(--primary); }
        .btn-paste { background: var(--border); border: none; color: var(--text-main); padding: 0 15px; border-radius: 12px; cursor: pointer; }
        .btn-main {
            padding: 14px; background: var(--primary); color: white; border: none; border-radius: 12px;
            font-size: 16px; font-weight: 700; cursor: pointer; font-family: 'Tajawal', sans-serif; transition: 0.2s;
        }
        .btn-main:hover { background: var(--primary-hover); }

        .history-wrapper { display: flex; overflow-x: auto; gap: 8px; padding-bottom: 5px; scrollbar-width: none; }
        .history-chip {
            background: var(--card-bg); border: 1px solid var(--border); padding: 8px 12px;
            border-radius: 20px; font-size: 12px; white-space: nowrap; cursor: pointer; color: var(--primary); font-weight: bold;
        }

        /* النتائج والمشغل */
        .result-box { display: none; background: var(--card-bg); padding: 15px; border-radius: 20px; border: 1px solid var(--border); }
        .preview-player { width: 100%; border-radius: 12px; background: #000; margin-bottom: 10px; display: none; max-height: 250px; }
        
        .video-header { display: flex; gap: 12px; margin-bottom: 15px; align-items: center; }
        .thumb { width: 70px; height: 70px; border-radius: 10px; object-fit: cover; }
        .title { font-size: 13px; font-weight: bold; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .music-tag { font-size: 12px; color: #10b981; margin-top: 5px; font-weight: bold; }

        .actions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .btn-action {
            padding: 12px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; 
            display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 5px;
            text-decoration: none; font-size: 13px; color: white; font-family: 'Tajawal', sans-serif; text-align: center;
        }
        .btn-action i { font-size: 18px; }
        .btn-full { grid-column: span 2; flex-direction: row; }
        
        .bg-mp4 { background: #10b981; } 
        .bg-mp3 { background: #8b5cf6; } 
        .bg-wa { background: #06b6d4; }  
        .bg-gif { background: #f59e0b; } 
        .bg-cut { background: #ef4444; } 
        .bg-play { background: #3b82f6; }

        .loading { text-align: center; color: var(--text-muted); font-size: 14px; display: none; margin-top: 5px; }
        .error-msg { color: #ef4444; text-align: center; font-size: 14px; font-weight: bold; }
        
        /* واجهة القص */
        .trim-ui { display: none; margin-top: 15px; padding-top: 15px; border-top: 1px solid var(--border); }
        .range-slider { width: 100%; margin: 10px 0; }
        .time-labels { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); font-weight: bold; }
    </style>
</head>
<body data-theme="dark">

    <div class="app-container">
        <div class="top-bar">
            <h3>منصة التحميل الذكية</h3>
            <button class="theme-btn" onclick="toggleTheme()"><i class="fas fa-sun"></i> فاتح</button>
        </div>

        <div class="main-content">
            <div class="input-card">
                <div class="input-row">
                    <input type="text" id="videoUrl" placeholder="الصق رابط تيك توك، يوتيوب، انستا...">
                    <button class="btn-paste" onclick="pasteBtn()"><i class="fas fa-paste"></i></button>
                </div>
                <button class="btn-main" id="searchBtn" onclick="processUrl()">
                    <i class="fas fa-search"></i> بحث ومعالجة سريعة
                </button>
                <div class="loading" id="loader"><i class="fas fa-spinner fa-spin"></i> جاري قراءة البيانات الحقيقية...</div>
                <div id="errorBox" class="error-msg"></div>
            </div>

            <div class="history-wrapper" id="historyList"></div>

            <div class="result-box" id="resultArea">
                <video id="vidPlayer" class="preview-player" controls crossorigin="anonymous"></video>
                
                <div class="video-header" id="videoInfo"></div>
                
                <div class="actions-grid" id="actionsGrid"></div>

                <div class="trim-ui" id="trimUI">
                    <div style="font-size: 13px; font-weight: bold; margin-bottom: 5px;"><i class="fas fa-cut"></i> حدد مقطع للـ GIF أو القص:</div>
                    <input type="range" id="trimSlider" class="range-slider" min="0" max="100" value="0">
                    <div class="time-labels">
                        <span id="startTime">00:00</span>
                        <span id="endTime">00:00</span>
                    </div>
                    <button class="btn-action bg-gif btn-full" style="margin-top: 10px;" onclick="createGIF()">
                        <i class="fas fa-magic"></i> صنع صورة متحركة (GIF) للمقطع
                    </button>
                    <div id="gifResult" style="margin-top: 10px; text-align: center;"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentProxyUrl = '';
        
        function toggleTheme() {
            const body = document.body;
            const btn = document.querySelector('.theme-btn');
            if(body.getAttribute('data-theme') === 'dark') {
                body.removeAttribute('data-theme');
                btn.innerHTML = '<i class="fas fa-moon"></i> داكن';
            } else {
                body.setAttribute('data-theme', 'dark');
                btn.innerHTML = '<i class="fas fa-sun"></i> فاتح';
            }
        }

        async function pasteBtn() {
            try { document.getElementById('videoUrl').value = await navigator.clipboard.readText(); } 
            catch (err) { alert('يرجى منح صلاحية اللصق'); }
        }

        function saveHistory(url) {
            let hist = JSON.parse(localStorage.getItem('my_history') || '[]');
            if(!hist.includes(url)) { hist.unshift(url); if(hist.length > 5) hist.pop(); localStorage.setItem('my_history', JSON.stringify(hist)); }
            loadHistory();
        }

        function loadHistory() {
            let hist = JSON.parse(localStorage.getItem('my_history') || '[]');
            document.getElementById('historyList').innerHTML = hist.map(url => 
                `<div class="history-chip" onclick="document.getElementById('videoUrl').value='${url}'; processUrl();"><i class="fas fa-history"></i> ${url.substring(0,15)}...</div>`
            ).join('');
        }
        window.onload = loadHistory;

        async function processUrl() {
            const url = document.getElementById('videoUrl').value;
            const btn = document.getElementById('searchBtn');
            const loader = document.getElementById('loader');
            const resultArea = document.getElementById('resultArea');
            const errBox = document.getElementById('errorBox');
            const vidPlayer = document.getElementById('vidPlayer');
            const trimUI = document.getElementById('trimUI');
            
            if(!url) return;
            btn.disabled = true; loader.style.display = 'block'; resultArea.style.display = 'none'; errBox.innerHTML = '';
            vidPlayer.style.display = 'none'; trimUI.style.display = 'none'; document.getElementById('gifResult').innerHTML = '';

            try {
                const res = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                
                const data = await res.json();
                if(data.error) { errBox.innerHTML = data.error; } 
                else {
                    saveHistory(url);
                    
                    let musicHtml = data.audio_track ? `<div class="music-tag"><i class="fas fa-headphones"></i> الأغنية الأصلية: ${data.audio_track}</div>` : '';
                    document.getElementById('videoInfo').innerHTML = `
                        <img src="${data.thumbnail}" class="thumb">
                        <div>
                            <div class="title">${data.title}</div>
                            ${musicHtml}
                        </div>
                    `;
                    
                    const safeTitle = encodeURIComponent(data.title.substring(0,30));
                    const safeVid = encodeURIComponent(data.video_url);
                    const safeAud = encodeURIComponent(data.audio_url);
                    const safeWa = encodeURIComponent(data.wa_url || data.video_url);
                    
                    // إعداد رابط البروكسي العبقري لتجاوز الحماية
                    currentProxyUrl = `/proxy_media?url=${safeVid}`;

                    document.getElementById('actionsGrid').innerHTML = `
                        <button onclick="playPreview()" class="btn-action bg-play btn-full"><i class="fas fa-play-circle"></i> تشغيل معاينة الفيديو</button>
                        <a href="/force_download?url=${safeVid}&title=${safeTitle}&ext=mp4" class="btn-action bg-mp4"><i class="fas fa-video"></i> فيديو (MP4)</a>
                        <a href="/force_download?url=${safeAud}&title=${safeTitle}&ext=mp3" class="btn-action bg-mp3"><i class="fas fa-music"></i> صوت (MP3)</a>
                        <a href="/force_download?url=${safeWa}&title=${safeTitle}_WA&ext=mp4" class="btn-action bg-wa"><i class="fab fa-whatsapp"></i> دقة واتساب</a>
                        <button onclick="showTrimUI()" class="btn-action bg-cut"><i class="fas fa-scissors"></i> قص & GIF</button>
                    `;
                    resultArea.style.display = 'block';
                }
            } catch (e) { errBox.innerHTML = "حدث خطأ أثناء الاتصال بالخادم."; } 
            finally { btn.disabled = false; loader.style.display = 'none'; }
        }

        // ميزة التشغيل المباشر داخل الموقع
        function playPreview() {
            const vidPlayer = document.getElementById('vidPlayer');
            vidPlayer.src = currentProxyUrl;
            vidPlayer.style.display = 'block';
            vidPlayer.play();
        }

        // إظهار واجهة القص والـ GIF
        function showTrimUI() {
            document.getElementById('trimUI').style.display = 'block';
            const vidPlayer = document.getElementById('vidPlayer');
            if(vidPlayer.style.display === 'none') playPreview();
            
            vidPlayer.onloadedmetadata = function() {
                document.getElementById('trimSlider').max = Math.floor(vidPlayer.duration);
                document.getElementById('endTime').innerText = formatTime(vidPlayer.duration);
            };
            
            document.getElementById('trimSlider').oninput = function() {
                vidPlayer.currentTime = this.value;
                document.getElementById('startTime').innerText = formatTime(this.value);
            };
        }

        function formatTime(seconds) {
            const m = Math.floor(seconds / 60);
            const s = Math.floor(seconds % 60);
            return (m < 10 ? "0"+m : m) + ":" + (s < 10 ? "0"+s : s);
        }

        // ميزة الـ GIF العبقرية باستخدام المتصفح (بدون تحميل السيرفر)
        function createGIF() {
            const resDiv = document.getElementById('gifResult');
            resDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري معالجة الصورة المتحركة بجهازك...';
            
            // نأخذ 10 إطارات من الفيديو لتكوين الـ GIF باستخدام مكتبة gifshot
            gifshot.createGIF({
                video: [currentProxyUrl],
                numFrames: 15,
                frameDuration: 1,
                gifWidth: 300,
                offset: document.getElementById('trimSlider').value
            }, function(obj) {
                if(!obj.error) {
                    resDiv.innerHTML = `
                        <img src="${obj.image}" style="border-radius:10px; max-width:100%; margin-bottom:10px;">
                        <a href="${obj.image}" download="video_clip.gif" class="btn-action bg-mp4 btn-full"><i class="fas fa-download"></i> حفظ הـ GIF</a>
                    `;
                } else {
                    resDiv.innerHTML = '<span style="color:red;">تعذر صنع الـ GIF، حاول بمقطع أقصر.</span>';
                }
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

@app.route('/extract', methods=['POST'])
def extract():
    url = request.json.get('url', '')
    if not url: return jsonify({"error": "الرابط فارغ!"}), 400

    # 1. تيك توك: سحب الاسم الحقيقي للموسيقى
    if 'tiktok.com' in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            resp = requests.get(api_url).json()
            if resp.get('code') == 0:
                v = resp['data']
                music_title = v.get('music_info', {}).get('title', '')
                music_author = v.get('music_info', {}).get('author', '')
                real_music_name = f"{music_title} - {music_author}" if music_author else music_title
                
                return jsonify({
                    "title": v.get('title', 'فيديو تيك توك'),
                    "thumbnail": v.get('cover'),
                    "video_url": v.get('play'),
                    "audio_url": v.get('music'), 
                    "wa_url": v.get('wmplay'), # نسخة بحجم أقل للواتساب
                    "audio_track": real_music_name
                })
        except: pass

    # 2. يوتيوب والمنصات الأخرى: البحث عن اسم الصوت
    opts = {'quiet': True, 'nocheckcertificate': True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = info.get('formats', [])
            # اختيار دقة منخفضة مخصصة للواتساب (حوالي 360p أو 480p)
            wa_formats = [f for f in formats if f.get('height') and f.get('height') <= 480 and f.get('vcodec') != 'none']
            best_wa = wa_formats[-1]['url'] if wa_formats else info.get('url')
            
            video_formats = [f for f in formats if f.get('vcodec') != 'none']
            audio_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
            
            best_video = video_formats[-1]['url'] if video_formats else info.get('url')
            best_audio = audio_formats[-1]['url'] if audio_formats else best_video

            track = info.get('track', '')
            artist = info.get('artist', '')
            real_audio = f"{track} - {artist}" if artist else track

            return jsonify({
                "title": info.get('title', 'فيديو'),
                "thumbnail": info.get('thumbnail'),
                "video_url": best_video,
                "audio_url": best_audio,
                "wa_url": best_wa,
                "audio_track": real_audio
            })
    except Exception as e:
        return jsonify({"error": "تعذر سحب البيانات، الرابط خاص أو غير مدعوم."}), 500

# جسر العبور العبقري (Proxy) لتشغيل الفيديو والقص بدون مشاكل الحماية
@app.route('/proxy_media')
def proxy_media():
    url = request.args.get('url')
    if not url: return "No URL", 400
    try:
        req = requests.get(url, stream=True, verify=False)
        return Response(stream_with_context(req.iter_content(chunk_size=1024*1024)), content_type=req.headers.get('content-type', 'video/mp4'))
    except:
        return "Proxy Error", 500

# دالة التحميل المباشر كملف
@app.route('/force_download')
def force_download():
    file_url = request.args.get('url')
    title = request.args.get('title', 'Download')
    ext = request.args.get('ext', 'mp4')
    if not file_url: return "الرابط مفقود", 400

    try:
        req = requests.get(file_url, stream=True, verify=False)
        content_type = 'audio/mp3' if ext == 'mp3' else req.headers.get('content-type', 'application/octet-stream')
        headers = {
            'Content-Disposition': f'attachment; filename="{title}.{ext}"',
            'Content-Type': content_type
        }
        return Response(stream_with_context(req.iter_content(chunk_size=1024*1024)), headers=headers)
    except Exception as e:
        return "فشلت عملية التحميل", 500

if __name__ == '__main__':
    app.run(debug=True)
