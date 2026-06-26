import os
import requests
import urllib.parse
import re
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context

# استخدام yt_dlp للسحب
import yt_dlp

app = Flask(__name__)

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tahmilati | تحميلاتي</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.css" />
    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gifshot/0.3.2/gifshot.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.js"></script>

    <style>
        :root {
            --bg-color: #f8fafc; --card-bg: #ffffff;
            --text-main: #0f172a; --text-muted: #64748b;
            --primary: #dc2626; --primary-hover: #b91c1c; 
            --border: rgba(0, 0, 0, 0.1); --neon-shadow: none;
        }
        [data-theme="dark"] {
            --bg-color: #0f172a; --card-bg: #1e293b;
            --text-main: #f8fafc; --text-muted: #94a3b8;
            --primary: #ef4444; --primary-hover: #dc2626; 
            --border: rgba(255, 255, 255, 0.1);
            --neon-shadow: 0 0 10px var(--primary), 0 0 20px var(--primary);
        }
        
        /* تأثيرات الثيم الديناميكي */
        body.theme-tiktok { --primary: #00f2fe; --neon-shadow: 0 0 10px #00f2fe, 0 0 20px #fe0979; }
        body.theme-youtube { --primary: #ff0000; --neon-shadow: 0 0 10px #ff0000, 0 0 20px #cc0000; }
        body.theme-insta { --primary: #f56040; --neon-shadow: 0 0 10px #f56040, 0 0 20px #833ab4; }

        html, body { height: 100dvh; margin: 0; padding: 0; overflow: hidden; font-family: 'Tajawal', sans-serif; background-color: var(--bg-color); color: var(--text-main); transition: 0.5s ease; }
        .app-container { display: flex; flex-direction: column; height: 100%; max-width: 500px; margin: 0 auto; position: relative; }
        
        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; border-bottom: 1px solid var(--border); background: var(--card-bg); flex-shrink: 0; }
        .logo-title { margin: 0; font-weight: 900; font-size: 24px; color: var(--primary); text-shadow: var(--neon-shadow); letter-spacing: 1px; animation: pulse 2s infinite alternate; }
        @keyframes pulse { 0% { text-shadow: 0 0 5px rgba(255,255,255,0.2); } 100% { text-shadow: var(--neon-shadow); } }
        
        .nav-btns { display: flex; gap: 10px; }
        .icon-btn { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; cursor: pointer; font-weight: bold; transition: 0.3s; display: flex; align-items: center; justify-content: center; }
        .icon-btn:hover { background: var(--primary); color: white; box-shadow: var(--neon-shadow); }
        
        .main-content { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .main-content::-webkit-scrollbar { width: 5px; }
        .main-content::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }

        .creator-btn { display: flex; align-items: center; justify-content: center; gap: 8px; background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); color: white; padding: 12px; border-radius: 15px; text-decoration: none; font-weight: bold; font-size: 14px; box-shadow: 0 4px 10px rgba(220, 39, 67, 0.3); transition: 0.3s; }
        .creator-btn:hover { transform: scale(0.98); }

        .live-counter { text-align: center; font-size: 13px; font-weight: bold; color: var(--primary); background: var(--card-bg); padding: 10px; border-radius: 15px; border: 1px solid var(--border); box-shadow: var(--neon-shadow); }

        .input-card { background: var(--card-bg); padding: 15px; border-radius: 20px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px; }
        .card-title { font-size: 14px; font-weight: bold; color: var(--text-main); display: flex; align-items: center; gap: 8px; }
        .input-row { display: flex; gap: 8px; align-items: center; background: rgba(0,0,0,0.05); border: 1px solid var(--border); border-radius: 12px; padding-right: 10px; }
        [data-theme="dark"] .input-row { background: rgba(255,255,255,0.05); }
        input[type="text"] { flex: 1; padding: 15px 5px; background: transparent; border: none; color: var(--text-main); font-size: 15px; outline: none; font-family: 'Tajawal'; }
        .action-icon { color: var(--text-muted); cursor: pointer; padding: 10px; transition: 0.2s; }
        .action-icon:hover { color: var(--primary); }
        
        .btn-main { padding: 14px; background: var(--primary); color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: 900; cursor: pointer; font-family: 'Tajawal'; box-shadow: var(--neon-shadow); transition: 0.3s; }
        .btn-main:hover { filter: brightness(1.1); transform: translateY(-1px); }

        .search-results-box { display: none; flex-direction: column; gap: 10px; background: var(--card-bg); padding: 15px; border-radius: 20px; border: 1px solid var(--border); }
        .search-item { display: flex; gap: 15px; align-items: center; background: rgba(0,0,0,0.05); padding: 10px; border-radius: 15px; cursor: pointer; transition: 0.2s; border: 1px solid var(--border); }
        [data-theme="dark"] .search-item { background: rgba(255,255,255,0.05); }
        .search-item:hover { border-color: var(--primary); }
        .search-thumb { width: 90px; height: 60px; border-radius: 8px; object-fit: cover; }
        .search-title { font-size: 13px; font-weight: bold; line-height: 1.4; color: var(--text-main); }

        .result-box { display: none; background: var(--card-bg); padding: 15px; border-radius: 20px; border: 1px solid var(--border); flex-direction: column; gap: 15px; }
        .video-header { display: flex; gap: 15px; align-items: center; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
        .thumb { width: 70px; height: 70px; border-radius: 12px; object-fit: cover; border: 1px solid var(--primary); }
        .title { font-size: 14px; font-weight: bold; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

        .btn-action-row { display: flex; gap: 10px; }
        .btn-action { flex: 1; padding: 12px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; font-size: 13px; color: white; font-family: 'Tajawal'; transition: 0.2s; }
        .btn-action:active { transform: scale(0.98); }
        .btn-copy { background: #334155; width: 45px; flex: none; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; cursor: pointer; transition: 0.2s; border: none;}
        .btn-copy:hover { background: #475569; }

        .bg-mp4 { background: #10b981; } .bg-mp3 { background: #8b5cf6; } .bg-wa { background: #06b6d4; } .bg-gif { background: #f59e0b; }

        /* منطقة الـ GIF الذكية */
        .gif-editor { display: none; background: rgba(0,0,0,0.05); padding: 15px; border-radius: 15px; margin-top: 10px; border: 1px dashed var(--border); }
        [data-theme="dark"] .gif-editor { background: rgba(255,255,255,0.05); }
        .slider-container { margin: 30px 10px 10px 10px; }
        .noUi-connect { background: var(--primary); }
        .noUi-handle { border-radius: 50%; box-shadow: var(--neon-shadow); }

        .loading { text-align: center; color: var(--primary); font-size: 14px; display: none; font-weight: bold; }
        .error-msg { color: #ef4444; text-align: center; font-size: 14px; font-weight: bold; display: none; }
    </style>
</head>
<body data-theme="dark">

    <div class="app-container">
        <div class="top-bar">
            <h3 class="logo-title">Tahmilati | تحميلاتي</h3>
            <div class="nav-btns">
                <button class="icon-btn" onclick="location.reload()" title="تحديث"><i class="fas fa-sync-alt"></i></button>
                <button class="icon-btn" onclick="toggleTheme()" title="تغيير المظهر"><i class="fas fa-moon"></i></button>
            </div>
        </div>

        <div class="main-content">
            <a href="https://www.instagram.com/_otnn?igsh=d3hybTN2M2Zlanl0" target="_blank" class="creator-btn">
                <i class="fab fa-instagram"></i> المصمم: @_otnn
            </a>

            <div class="live-counter" id="liveCounter">
                <i class="fas fa-chart-line"></i> تم معالجة <span id="countNum">1,425,890</span> ملف بنجاح
            </div>

            <div class="input-card">
                <div class="card-title"><i class="fas fa-link"></i> تحميل مباشر (تيك توك، انستا، X)</div>
                <div class="input-row">
                    <input type="text" id="urlInput" placeholder="الصق الرابط هنا...">
                    <i class="fas fa-times action-icon" onclick="clearInput('urlInput')"></i>
                    <i class="fas fa-paste action-icon" onclick="pasteInput('urlInput')"></i>
                </div>
                <button class="btn-main" onclick="processRequest('url', 'urlInput')">معالجة الرابط</button>
            </div>

            <div class="input-card">
                <div class="card-title"><i class="fab fa-youtube" style="color: #ff0000;"></i> بحث وتحميل من يوتيوب</div>
                <div class="input-row">
                    <input type="text" id="ytInput" placeholder="اكتب اسم المقطع أو الأغنية...">
                    <i class="fas fa-times action-icon" onclick="clearInput('ytInput')"></i>
                </div>
                <button class="btn-main" onclick="processRequest('search', 'ytInput')">بحث في يوتيوب</button>
            </div>

            <div class="input-card">
                <div class="card-title"><i class="fab fa-instagram" style="color: #f56040;"></i> تحميل ستوري انستغرام</div>
                <div class="input-row">
                    <input type="text" id="igInput" placeholder="اكتب يوزر الحساب (مثال: _otnn)">
                    <i class="fas fa-times action-icon" onclick="clearInput('igInput')"></i>
                </div>
                <button class="btn-main" onclick="processRequest('story', 'igInput')">جلب الستوري</button>
            </div>

            <div class="loading" id="globalLoader"><i class="fas fa-spinner fa-spin"></i> جاري المعالجة، يرجى الانتظار...</div>
            <div id="errorBox" class="error-msg"></div>

            <div class="search-results-box" id="searchResultsBox"></div>

            <div class="result-box" id="resultArea">
                <div class="video-header" id="videoInfo"></div>
                
                <video id="player" playsinline controls data-poster=""></video>
                
                <div id="downloadGrid" style="display: flex; flex-direction: column; gap: 10px; margin-top: 10px;"></div>

                <div class="gif-editor" id="gifEditor">
                    <div style="font-size: 13px; font-weight: bold; color: var(--text-main); margin-bottom: 10px;">
                        <i class="fas fa-sliders-h"></i> حدد وقت البداية والنهاية للـ GIF:
                    </div>
                    <div id="timeSlider" class="slider-container"></div>
                    <div style="display:flex; justify-content: space-between; font-size:12px; color:var(--primary); font-weight:bold; margin-bottom: 15px;">
                        <span id="startVal">0s</span> <span id="endVal">5s</span>
                    </div>
                    <button id="gifStartBtn" onclick="generateGif()" class="btn-action bg-gif"><i class="fas fa-check"></i> تأكيد وإنشاء GIF</button>
                    <div id="gifStatus" style="font-size: 12px; text-align: center; color: var(--primary); margin-top: 10px; display: none;"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // إعداد المشغل الاحترافي
        const player = new Plyr('#player', { controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'volume', 'fullscreen'] });
        let currentProxyUrl = '';
        let currentVideoTitle = '';
        let videoDuration = 15; // افتراضي للـ GIF
        let gifSlider;

        // العداد الوهمي المباشر
        let count = 1425890;
        setInterval(() => { count += Math.floor(Math.random() * 3); document.getElementById('countNum').innerText = count.toLocaleString(); }, 3500);

        function toggleTheme() {
            const body = document.body;
            body.setAttribute('data-theme', body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
        }

        function clearInput(id) { document.getElementById(id).value = ''; }
        async function pasteInput(id) { try { document.getElementById(id).value = await navigator.clipboard.readText(); } catch(e){} }

        function copyLink(url) {
            const tempInput = document.createElement("input");
            tempInput.value = window.location.origin + url;
            document.body.appendChild(tempInput);
            tempInput.select();
            document.execCommand("copy");
            document.body.removeChild(tempInput);
            alert("تم نسخ رابط التحميل المباشر بنجاح!");
        }

        // تغيير الثيم حسب المنصة
        function applyPlatformTheme(platform) {
            document.body.className = '';
            if(platform === 'tiktok') document.body.classList.add('theme-tiktok');
            else if(platform === 'youtube') document.body.classList.add('theme-youtube');
            else if(platform === 'instagram') document.body.classList.add('theme-insta');
        }

        function showGifEditor() {
            const editor = document.getElementById('gifEditor');
            editor.style.display = editor.style.display === 'block' ? 'none' : 'block';
            
            if(!gifSlider) {
                gifSlider = document.getElementById('timeSlider');
                noUiSlider.create(gifSlider, {
                    start: [0, 5], connect: true, step: 1, range: { 'min': 0, 'max': Math.min(videoDuration, 60) }
                });
                gifSlider.noUiSlider.on('update', function (values) {
                    document.getElementById('startVal').innerText = Math.round(values[0]) + 's';
                    document.getElementById('endVal').innerText = Math.round(values[1]) + 's';
                });
            } else {
                gifSlider.noUiSlider.updateOptions({ range: { 'min': 0, 'max': Math.min(videoDuration, 60) } });
            }
        }

        function generateGif() {
            const btn = document.getElementById('gifStartBtn');
            const status = document.getElementById('gifStatus');
            btn.disabled = true; status.style.display = 'block';
            status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري إنشاء الصورة المتحركة...';
            
            const values = gifSlider.noUiSlider.get();
            const startSec = parseInt(values[0]);
            const endSec = parseInt(values[1]);
            const duration = endSec - startSec;

            gifshot.createGIF({
                'video': [currentProxyUrl], 'offset': startSec, 'numFrames': duration * 10, 'frameDuration': 1, 'gifWidth': 300, 'gifHeight': 300
            }, function(obj) {
                if(!obj.error) {
                    const a = document.createElement('a');
                    a.href = obj.image; a.download = currentVideoTitle + '.gif'; a.click();
                    status.innerHTML = '<i class="fas fa-check"></i> اكتمل التحميل!';
                } else { status.innerHTML = '<i class="fas fa-times"></i> فشلت العملية.'; }
                setTimeout(()=> { status.style.display = 'none'; btn.disabled = false; }, 3000);
            });
        }

        async function processRequest(type, inputId) {
            const val = document.getElementById(inputId).value.trim();
            const loader = document.getElementById('globalLoader');
            const resultArea = document.getElementById('resultArea');
            const searchResultsBox = document.getElementById('searchResultsBox');
            const errBox = document.getElementById('errorBox');
            
            if(!val) return;

            loader.style.display = 'block'; resultArea.style.display = 'none'; searchResultsBox.style.display = 'none'; errBox.style.display = 'none';
            player.stop();

            try {
                const res = await fetch('/api/process', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: type, query: val }) });
                const data = await res.json();
                
                if(data.error) {
                    errBox.innerHTML = data.error; errBox.style.display = 'block';
                } else if(data.search_results) {
                    applyPlatformTheme(type === 'search' ? 'youtube' : 'instagram');
                    let html = `<div style="font-weight:bold; color:var(--primary); margin-bottom:10px;"><i class="fas fa-list"></i> نتائج البحث:</div>`;
                    data.search_results.forEach(item => {
                        html += `
                        <div class="search-item" onclick="document.getElementById('urlInput').value='${item.url}'; processRequest('url', 'urlInput');">
                            <img src="${item.thumbnail}" class="search-thumb">
                            <div class="search-title">${item.title}</div>
                        </div>`;
                    });
                    searchResultsBox.innerHTML = html; searchResultsBox.style.display = 'flex';
                } else {
                    applyPlatformTheme(data.platform);
                    currentVideoTitle = data.title || 'Tahmilati_Video';
                    videoDuration = data.duration || 15;
                    
                    const safeTitle = encodeURIComponent(currentVideoTitle);
                    currentProxyUrl = `/proxy?url=${encodeURIComponent(data.video_url)}&title=${safeTitle}&ext=mp4`;
                    
                    player.source = { type: 'video', sources: [{ src: currentProxyUrl, type: 'video/mp4' }] };
                    
                    document.getElementById('videoInfo').innerHTML = `
                        <img src="${data.thumbnail}" class="thumb">
                        <div class="title">${data.title}</div>
                    `;
                    
                    const safeVideoUrl = encodeURIComponent(data.video_url);
                    const safeAudioUrl = encodeURIComponent(data.audio_url || data.video_url);
                    const safeWaUrl = encodeURIComponent(data.whatsapp_url || data.video_url);

                    const dlVideo = `/proxy?url=${safeVideoUrl}&title=${safeTitle}&ext=mp4`;
                    const dlAudio = `/proxy?url=${safeAudioUrl}&title=${safeTitle}&ext=mp3`;
                    const dlWa = `/proxy?url=${safeWaUrl}&title=${safeTitle}_WA&ext=mp4`;

                    let actionsHtml = `
                        <div class="btn-action-row">
                            <a href="${dlVideo}" class="btn-action bg-mp4"><i class="fas fa-download"></i> تحميل (MP4)</a>
                            <button onclick="copyLink('${dlVideo}')" class="btn-copy" title="نسخ الرابط"><i class="fas fa-link"></i></button>
                        </div>
                        <div class="btn-action-row">
                            <a href="${dlAudio}" class="btn-action bg-mp3"><i class="fas fa-headphones"></i> تحميل (MP3)</a>
                            <button onclick="copyLink('${dlAudio}')" class="btn-copy" title="نسخ الرابط"><i class="fas fa-link"></i></button>
                        </div>
                        <div class="btn-action-row">
                            <a href="${dlWa}" class="btn-action bg-wa"><i class="fab fa-whatsapp"></i> نسخة للواتساب</a>
                            <button onclick="copyLink('${dlWa}')" class="btn-copy" title="نسخ الرابط"><i class="fas fa-link"></i></button>
                        </div>
                    `;

                    if(data.platform === 'tiktok' || data.platform === 'instagram') {
                        actionsHtml += `<button onclick="showGifEditor()" class="btn-action bg-gif"><i class="fas fa-images"></i> إنشاء (GIF)</button>`;
                    }

                    document.getElementById('downloadGrid').innerHTML = actionsHtml;
                    document.getElementById('gifEditor').style.display = 'none';
                    resultArea.style.display = 'flex';
                }
            } catch (e) { errBox.innerHTML = "خطأ في الاتصال بالخادم الرئيسي."; errBox.style.display = 'block'; } 
            finally { loader.style.display = 'none'; }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

@app.route('/api/process', methods=['POST'])
def process_api():
    req_type = request.json.get('type')
    query = request.json.get('query', '').strip()
    if not query: return jsonify({"error": "الحقل فارغ."}), 400

    opts = {'quiet': True, 'nocheckcertificate': True}

    # 1. بحث يوتيوب
    if req_type == 'search':
        try:
            opts['extract_flat'] = True
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch5:{query}", download=False)
                results = []
                for entry in info.get('entries', []):
                    results.append({
                        "title": entry.get('title', 'فيديو'),
                        "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "thumbnail": entry.get('thumbnails', [{}])[-1].get('url', '')
                    })
                return jsonify({"search_results": results})
        except: return jsonify({"error": "تعذر البحث في يوتيوب حالياً."})

    # 2. ستوري انستغرام (تعتمد على الروابط العامة أو جلب عبر yt-dlp)
    if req_type == 'story':
        try:
            # محاولة استخراج ستوري الانستا باليوزر
            user_url = f"https://instagram.com/stories/{query.replace('@','')}/"
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(user_url, download=False)
                results = []
                entries = info.get('entries', [info])
                for entry in entries:
                    results.append({
                        "title": entry.get('title', f"ستوري {query}"),
                        "url": entry.get('webpage_url', user_url),
                        "thumbnail": entry.get('thumbnail', '')
                    })
                if results: return jsonify({"search_results": results})
                return jsonify({"error": "لا توجد ستوريات متاحة أو الحساب خاص."})
        except: return jsonify({"error": "يتطلب انستغرام حساباً عاماً لعرض الستوري."})

    # 3. معالجة الروابط المباشرة (تيك توك، انستا، يوتيوب)
    url = query
    platform = "other"
    if 'tiktok.com' in url: platform = "tiktok"
    elif 'instagram.com' in url: platform = "instagram"
    elif 'youtube.com' in url or 'youtu.be' in url: platform = "youtube"

    if platform == "tiktok":
        try:
            resp = requests.get(f"https://www.tikwm.com/api/?url={url}").json()
            if resp.get('code') == 0:
                v = resp['data']
                return jsonify({
                    "title": v.get('title', 'Tiktok Video'),
                    "thumbnail": v.get('cover'),
                    "video_url": v.get('play'), "audio_url": v.get('music'), 
                    "whatsapp_url": v.get('wmplay') or v.get('play'),
                    "duration": v.get('duration', 15), "platform": platform
                })
        except: pass

    # الاستخراج العام
    try:
        opts['extractor_args'] = {'youtube': {'player_client': ['android', 'web']}}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            v_formats = [f for f in formats if f.get('vcodec') != 'none']
            a_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
            
            best_video = v_formats[-1]['url'] if v_formats else info.get('url')
            best_audio = a_formats[-1]['url'] if a_formats else best_video
            worst_video = v_formats[0]['url'] if v_formats else best_video 

            return jsonify({
                "title": info.get('title', 'Video'), "thumbnail": info.get('thumbnail'),
                "video_url": best_video, "audio_url": best_audio, "whatsapp_url": worst_video,
                "duration": info.get('duration', 60), "platform": platform
            })
    except: return jsonify({"error": "الرابط غير صالح أو المحتوى خاص."})

# دعم الـ Range Requests للتقديم والتأخير في المشغل
@app.route('/proxy')
def proxy_download():
    file_url = request.args.get('url')
    title = request.args.get('title', 'Tahmilati')
    ext = request.args.get('ext', 'mp4')
    if not file_url: return "الرابط مفقود", 400

    safe_title = re.sub(r'[^\w\s-]', '', urllib.parse.unquote(title)).strip().replace(' ', '_') or "Tahmilati"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    range_header = request.headers.get('Range', None)
    if range_header: headers['Range'] = range_header

    try:
        req = requests.get(file_url, headers=headers, stream=True, verify=False)
        content_type = 'audio/mp3' if ext == 'mp3' else req.headers.get('content-type', 'video/mp4')
        
        resp = Response(stream_with_context(req.iter_content(chunk_size=1024*512)), status=req.status_code, content_type=content_type)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Accept-Ranges'] = 'bytes'
        
        if 'Content-Range' in req.headers: resp.headers['Content-Range'] = req.headers['Content-Range']
        if 'Content-Length' in req.headers: resp.headers['Content-Length'] = req.headers['Content-Length']
        
        # إذا لم يكن طلب Range (يعني طلب تحميل مباشر)، نفرض التحميل كملف
        if not range_header: resp.headers['Content-Disposition'] = f'attachment; filename="{safe_title}.{ext}"'
            
        return resp
    except Exception as e: return "فشلت العملية", 500

if __name__ == '__main__':
    app.run(debug=True)
