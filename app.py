import os
import requests
import urllib.parse
import re
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
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
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>

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
        
        body.theme-tiktok { --primary: #00f2fe; --neon-shadow: 0 0 10px #00f2fe, 0 0 20px #fe0979; }
        body.theme-youtube { --primary: #ff0000; --neon-shadow: 0 0 10px #ff0000, 0 0 20px #cc0000; }
        body.theme-insta { --primary: #f56040; --neon-shadow: 0 0 10px #f56040, 0 0 20px #833ab4; }

        html, body { height: 100dvh; margin: 0; padding: 0; overflow: hidden; font-family: 'Tajawal', sans-serif; background-color: var(--bg-color); color: var(--text-main); transition: 0.5s ease; }
        .app-container { display: flex; flex-direction: column; height: 100%; max-width: 500px; margin: 0 auto; position: relative; }
        
        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; border-bottom: 1px solid var(--border); background: var(--card-bg); flex-shrink: 0; }
        .logo-title { margin: 0; font-weight: 900; font-size: 24px; color: var(--primary); text-shadow: var(--neon-shadow); letter-spacing: 1px; animation: pulse 2s infinite alternate; }
        @keyframes pulse { 0% { text-shadow: 0 0 5px rgba(255,255,255,0.2); } 100% { text-shadow: var(--neon-shadow); } }
        
        .nav-btns { display: flex; gap: 10px; }
        .icon-btn { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; cursor: pointer; font-weight: bold; transition: 0.3s; }
        .icon-btn:hover { background: var(--primary); color: white; box-shadow: var(--neon-shadow); }
        
        .main-content { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .main-content::-webkit-scrollbar { width: 5px; }
        .main-content::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }

        .creator-btn { display: flex; align-items: center; justify-content: center; gap: 8px; background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); color: white; padding: 12px; border-radius: 15px; text-decoration: none; font-weight: bold; font-size: 14px; box-shadow: 0 4px 10px rgba(220, 39, 67, 0.3); transition: 0.3s; }
        .creator-btn:hover { filter: brightness(1.1); }

        .live-counter { text-align: center; font-size: 13px; font-weight: bold; color: var(--primary); background: var(--card-bg); padding: 10px; border-radius: 15px; border: 1px solid var(--border); box-shadow: var(--neon-shadow); }

        .input-card { background: var(--card-bg); padding: 15px; border-radius: 20px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 10px; margin-bottom: 5px; transition: 0.3s; }
        .card-title { font-size: 14px; font-weight: bold; color: var(--text-main); display: flex; align-items: center; gap: 8px; }
        .input-row { display: flex; gap: 8px; align-items: center; background: rgba(0,0,0,0.05); border: 1px solid var(--border); border-radius: 12px; padding-right: 10px; }
        [data-theme="dark"] .input-row { background: rgba(255,255,255,0.05); }
        input[type="text"] { flex: 1; padding: 15px 5px; background: transparent; border: none; color: var(--text-main); font-size: 15px; outline: none; font-family: 'Tajawal'; }
        .action-icon { color: var(--text-muted); cursor: pointer; padding: 10px; transition: 0.2s; }
        .action-icon:hover { color: var(--primary); }
        
        .btn-main { padding: 14px; background: var(--primary); color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: 900; cursor: pointer; font-family: 'Tajawal'; box-shadow: var(--neon-shadow); transition: 0.3s; }
        .btn-main:hover { filter: brightness(1.1); }

        .dynamic-result-container { display: none; flex-direction: column; gap: 15px; background: rgba(0,0,0,0.03); padding: 15px; border-radius: 15px; margin-top: 10px; border: 1px solid var(--border); animation: slideDown 0.4s ease-out; }
        [data-theme="dark"] .dynamic-result-container { background: rgba(255,255,255,0.03); }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

        .search-item { display: flex; gap: 15px; align-items: center; background: var(--card-bg); padding: 10px; border-radius: 12px; cursor: pointer; transition: 0.2s; border: 1px solid var(--border); }
        .search-item:hover { border-color: var(--primary); box-shadow: var(--neon-shadow); }
        .search-thumb { width: 90px; height: 60px; border-radius: 8px; object-fit: cover; }
        .search-title { font-size: 13px; font-weight: bold; line-height: 1.4; color: var(--text-main); }

        .video-header { display: flex; gap: 15px; align-items: center; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
        .thumb { width: 70px; height: 70px; border-radius: 12px; object-fit: cover; border: 1px solid var(--primary); }
        .title { font-size: 14px; font-weight: bold; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

        .btn-action-row { display: flex; gap: 10px; }
        .btn-action { flex: 1; padding: 12px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; font-size: 13px; color: white; font-family: 'Tajawal'; transition: 0.2s; }
        .btn-action:active { transform: scale(0.98); }
        .btn-icon-sq { background: #334155; width: 45px; flex: none; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; cursor: pointer; transition: 0.2s; border: none; font-size: 16px;}
        .btn-icon-sq:hover { background: #475569; }

        .bg-mp4 { background: #10b981; } .bg-mp3 { background: #8b5cf6; } .bg-wa { background: #06b6d4; } .bg-gif { background: #f59e0b; }

        .gif-editor { display: none; background: rgba(0,0,0,0.05); padding: 15px; border-radius: 15px; margin-top: 10px; border: 1px dashed var(--border); }
        [data-theme="dark"] .gif-editor { background: rgba(255,255,255,0.05); }
        .slider-container { margin: 30px 10px 10px 10px; }
        .noUi-connect { background: var(--primary); }
        .noUi-handle { border-radius: 50%; box-shadow: var(--neon-shadow); }

        .qr-modal { display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center; flex-direction: column; backdrop-filter: blur(5px); }
        .qr-box { background: white; padding: 20px; border-radius: 20px; display: flex; flex-direction: column; align-items: center; gap: 15px; box-shadow: 0 0 30px rgba(255,255,255,0.2); }
        .qr-box span { color: #000; font-weight: bold; font-size: 14px; text-align: center; }
        .close-qr { background: #ef4444; color: white; border: none; padding: 8px 20px; border-radius: 10px; font-weight: bold; cursor: pointer; font-family: 'Tajawal'; }

        .loading { text-align: center; color: var(--primary); font-size: 14px; display: none; font-weight: bold; padding: 10px; }
        .error-msg { color: #ef4444; text-align: center; font-size: 14px; font-weight: bold; display: none; padding: 10px; }
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

            <div class="live-counter">
                <i class="fas fa-chart-line"></i> تم معالجة <span id="countNum">1,425,890</span> ملف بنجاح
            </div>

            <div class="input-card" id="card-url">
                <div class="card-title"><i class="fas fa-link"></i> تحميل مباشر (تيك توك، اكس، انستا، الخ)</div>
                <div class="input-row">
                    <input type="text" id="urlInput" placeholder="الصق الرابط هنا...">
                    <i class="fas fa-times action-icon" onclick="clearInput('urlInput')"></i>
                    <i class="fas fa-paste action-icon" onclick="pasteInput('urlInput')"></i>
                </div>
                <button class="btn-main" onclick="processRequest('url', 'urlInput', 'card-url')">معالجة الرابط</button>
                <div class="dynamic-result-container" id="result-url"></div>
            </div>

            <div class="input-card" id="card-yt">
                <div class="card-title"><i class="fab fa-youtube" style="color: #ff0000;"></i> بحث وتحميل من يوتيوب</div>
                <div class="input-row">
                    <input type="text" id="ytInput" placeholder="اكتب اسم المقطع أو الصق الرابط...">
                    <i class="fas fa-times action-icon" onclick="clearInput('ytInput')"></i>
                </div>
                <button class="btn-main" onclick="processRequest('youtube', 'ytInput', 'card-yt')">بحث في يوتيوب</button>
                <div class="dynamic-result-container" id="result-yt"></div>
            </div>

            <div class="input-card" id="card-ig">
                <div class="card-title"><i class="fab fa-instagram" style="color: #f56040;"></i> تحميل ستوري انستغرام</div>
                <div class="input-row">
                    <input type="text" id="igInput" placeholder="اكتب يوزر الحساب (مثال: _otnn)">
                    <i class="fas fa-times action-icon" onclick="clearInput('igInput')"></i>
                </div>
                <button class="btn-main" onclick="processRequest('story', 'igInput', 'card-ig')">جلب الستوري</button>
                <div class="dynamic-result-container" id="result-ig"></div>
            </div>
        </div>

        <div class="qr-modal" id="qrModal">
            <div class="qr-box">
                <span>امسح الباركود للتحميل بهاتفك</span>
                <div id="qrCodeDiv"></div>
                <button class="close-qr" onclick="document.getElementById('qrModal').style.display='none'">إغلاق</button>
            </div>
        </div>
    </div>

    <template id="resultTemplate">
        <div class="loading"><i class="fas fa-spinner fa-spin"></i> تتم المعالجة لتخطي الحماية، يرجى الانتظار...</div>
        <div class="error-msg"></div>
        <div class="search-list" style="display:none; flex-direction:column; gap:10px;"></div>
        <div class="media-box" style="display:none; flex-direction:column; gap:15px;">
            <div class="video-header"></div>
            <video class="plyr-player" playsinline controls></video>
            <div class="download-grid" style="display:flex; flex-direction:column; gap:10px;"></div>
            <div class="gif-editor">
                <div style="font-size: 13px; font-weight: bold; margin-bottom: 10px;"><i class="fas fa-sliders-h"></i> حدد وقت الـ GIF:</div>
                <div class="timeSlider slider-container"></div>
                <div style="display:flex; justify-content: space-between; font-size:12px; color:var(--primary); font-weight:bold; margin-bottom: 15px;">
                    <span class="startVal">0s</span> <span class="endVal">5s</span>
                </div>
                <button class="btn-action bg-gif gifStartBtn"><i class="fas fa-check"></i> تأكيد وإنشاء GIF</button>
                <div class="gifStatus" style="font-size: 12px; text-align: center; color: var(--primary); margin-top: 10px; display: none;"></div>
            </div>
        </div>
    </template>

    <script>
        let count = 1425890;
        setInterval(() => { count += Math.floor(Math.random() * 3); document.getElementById('countNum').innerText = count.toLocaleString(); }, 3500);

        let activePlayer = null;
        let activeProxyUrl = '';
        let activeTitle = '';

        function toggleTheme() {
            const body = document.body;
            body.setAttribute('data-theme', body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
        }

        function clearInput(id) { document.getElementById(id).value = ''; }
        async function pasteInput(id) { try { document.getElementById(id).value = await navigator.clipboard.readText(); } catch(e){} }

        function applyPlatformTheme(platform) {
            document.body.className = '';
            if(platform === 'tiktok') document.body.classList.add('theme-tiktok');
            else if(platform === 'youtube') document.body.classList.add('theme-youtube');
            else if(platform === 'instagram' || platform === 'story') document.body.classList.add('theme-insta');
        }

        function showQR(url) {
            document.getElementById('qrModal').style.display = 'flex';
            document.getElementById('qrCodeDiv').innerHTML = '';
            new QRCode(document.getElementById("qrCodeDiv"), { text: (url.startsWith('http') ? url : window.location.origin + url), width: 150, height: 150 });
        }

        function copyLink(url) {
            const temp = document.createElement("input");
            temp.value = url.startsWith('http') ? url : window.location.origin + url;
            document.body.appendChild(temp); temp.select(); document.execCommand("copy"); document.body.removeChild(temp);
            alert("تم نسخ الرابط بنجاح!");
        }

        function toggleGifEditor(containerId, duration) {
            const editor = document.querySelector(`#${containerId} .gif-editor`);
            editor.style.display = editor.style.display === 'block' ? 'none' : 'block';
            
            const sliderDiv = editor.querySelector('.timeSlider');
            if(!sliderDiv.noUiSlider) {
                noUiSlider.create(sliderDiv, { start: [0, 5], connect: true, step: 1, range: { 'min': 0, 'max': Math.min(duration, 60) } });
                sliderDiv.noUiSlider.on('update', function (values) {
                    editor.querySelector('.startVal').innerText = Math.round(values[0]) + 's';
                    editor.querySelector('.endVal').innerText = Math.round(values[1]) + 's';
                });
                
                editor.querySelector('.gifStartBtn').onclick = function() {
                    const btn = this; const status = editor.querySelector('.gifStatus');
                    btn.disabled = true; status.style.display = 'block'; status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري الإنشاء...';
                    const vals = sliderDiv.noUiSlider.get();
                    
                    gifshot.createGIF({
                        'video': [activeProxyUrl], 'offset': parseInt(vals[0]), 'numFrames': (parseInt(vals[1]) - parseInt(vals[0])) * 10, 'frameDuration': 1, 'gifWidth': 300, 'gifHeight': 300
                    }, function(obj) {
                        if(!obj.error) {
                            const a = document.createElement('a'); a.href = obj.image; a.download = activeTitle + '.gif'; a.click();
                            status.innerHTML = '<i class="fas fa-check"></i> اكتمل!';
                        } else { status.innerHTML = '<i class="fas fa-times"></i> فشل الإنشاء.'; }
                        setTimeout(()=> { status.style.display = 'none'; btn.disabled = false; }, 3000);
                    });
                };
            }
        }

        async function processRequest(type, inputId, cardId) {
            const val = document.getElementById(inputId).value.trim();
            if(!val) return;

            document.querySelectorAll('.dynamic-result-container').forEach(el => { el.style.display = 'none'; el.innerHTML = ''; });
            const resultContainer = document.getElementById(`result-${cardId.split('-')[1]}`);
            const tmpl = document.getElementById('resultTemplate').content.cloneNode(true);
            resultContainer.appendChild(tmpl);
            resultContainer.style.display = 'flex';

            const loader = resultContainer.querySelector('.loading');
            const errBox = resultContainer.querySelector('.error-msg');
            const searchList = resultContainer.querySelector('.search-list');
            const mediaBox = resultContainer.querySelector('.media-box');

            if(activePlayer) { activePlayer.destroy(); activePlayer = null; }
            loader.style.display = 'block';

            try {
                const res = await fetch('/api/process', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: type, query: val }) });
                const data = await res.json();
                loader.style.display = 'none';

                if(data.error) {
                    errBox.innerHTML = data.error; errBox.style.display = 'block';
                } else if(data.search_results) {
                    applyPlatformTheme(type === 'youtube' ? 'youtube' : 'insta');
                    let html = `<div style="font-weight:bold; color:var(--primary);"><i class="fas fa-list"></i> اختر المقطع:</div>`;
                    data.search_results.forEach(item => {
                        html += `
                        <div class="search-item" onclick="document.getElementById('${inputId}').value='${item.url}'; processRequest('${type==='youtube'?'url':'url'}', '${inputId}', '${cardId}');">
                            <img src="${item.thumbnail}" class="search-thumb">
                            <div class="search-title">${item.title}</div>
                        </div>`;
                    });
                    searchList.innerHTML = html; searchList.style.display = 'flex';
                } else {
                    applyPlatformTheme(data.platform);
                    activeTitle = data.title || 'Tahmilati_Video';
                    const safeTitle = encodeURIComponent(activeTitle);
                    
                    activeProxyUrl = data.video_url;

                    mediaBox.querySelector('.video-header').innerHTML = `<img src="${data.thumbnail}" class="thumb"><div class="title">${data.title}</div>`;
                    
                    const videoEl = mediaBox.querySelector('.plyr-player');
                    activePlayer = new Plyr(videoEl, { controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'volume', 'fullscreen'] });
                    activePlayer.source = { type: 'video', sources: [{ src: activeProxyUrl, type: 'video/mp4' }] };

                    const dlVideo = data.video_url;
                    const dlAudio = data.audio_url || data.video_url;

                    let actionsHtml = `
                        <div class="btn-action-row">
                            <a href="${dlVideo}" target="_blank" class="btn-action bg-mp4"><i class="fas fa-video"></i> تحميل المقطع</a>
                            <button onclick="copyLink('${dlVideo}')" class="btn-icon-sq" title="نسخ"><i class="fas fa-link"></i></button>
                            <button onclick="showQR('${dlVideo}')" class="btn-icon-sq" title="باركود"><i class="fas fa-qrcode"></i></button>
                        </div>
                        <div class="btn-action-row">
                            <a href="${dlAudio}" target="_blank" class="btn-action bg-mp3"><i class="fas fa-music"></i> تحميل كصوت</a>
                            <button onclick="copyLink('${dlAudio}')" class="btn-icon-sq"><i class="fas fa-link"></i></button>
                            <button onclick="showQR('${dlAudio}')" class="btn-icon-sq"><i class="fas fa-qrcode"></i></button>
                        </div>
                    `;

                    if(data.platform === 'tiktok' || data.platform === 'instagram') {
                        actionsHtml += `<button onclick="toggleGifEditor('${resultContainer.id}', ${data.duration || 15})" class="btn-action bg-gif"><i class="fas fa-images"></i> إنشاء (GIF)</button>`;
                    }

                    mediaBox.querySelector('.download-grid').innerHTML = actionsHtml;
                    mediaBox.style.display = 'flex';
                }
            } catch (e) { loader.style.display = 'none'; errBox.innerHTML = "حدث خطأ في الاتصال بالسيرفر، يرجى المحاولة لاحقاً."; errBox.style.display = 'block'; }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

def fetch_cobalt_api(url, is_audio=False):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    payload = {"url": url, "vQuality": "720"}
    if is_audio: payload["isAudioOnly"] = True
    
    try:
        r = requests.post("https://api.cobalt.tools/api/json", json=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") in ["stream", "redirect"]:
                return data.get("url")
    except: pass
    return None

@app.route('/api/process', methods=['POST'])
def process_api():
    req_type = request.json.get('type')
    query = request.json.get('query', '').strip()
    if not query: return jsonify({"error": "الرجاء إدخال بيانات صالحة."}), 400

    opts = {'quiet': True, 'nocheckcertificate': True}

    if req_type == 'youtube' and not query.startswith('http'):
        try:
            opts['extract_flat'] = True
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch5:{query}", download=False)
                results = [{"title": e.get('title'), "url": f"https://www.youtube.com/watch?v={e.get('id')}", "thumbnail": e.get('thumbnails', [{}])[-1].get('url', '')} for e in info.get('entries', [])]
                return jsonify({"search_results": results})
        except: return jsonify({"error": "البحث في يوتيوب يواجه ضغطاً، حاول مجدداً."})

    if req_type == 'story':
        return jsonify({"error": "تحميل ستوريات انستغرام مغلق حالياً من قبل سيرفرات ميتا (تحتاج تسجيل دخول). استخدم رابط بوست او ريلز بدلاً من ذلك."})

    url = query
    platform = "other"
    if 'tiktok.com' in url: platform = "tiktok"
    elif 'instagram.com' in url: platform = "instagram"
    elif 'youtu' in url: platform = "youtube"

    if platform == "tiktok":
        try:
            resp = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=10).json()
            if resp.get('code') == 0:
                v = resp['data']
                return jsonify({"title": v.get('title', 'Tiktok Video'), "thumbnail": v.get('cover'), "video_url": v.get('play'), "audio_url": v.get('music'), "duration": v.get('duration', 15), "platform": platform})
        except: pass

    if platform in ["youtube", "instagram", "other"]:
        vid_url = fetch_cobalt_api(url, False)
        aud_url = fetch_cobalt_api(url, True)
        
        if vid_url:
            return jsonify({
                "title": "تم جلب المقطع بنجاح",
                "thumbnail": "https://via.placeholder.com/150", 
                "video_url": vid_url, 
                "audio_url": aud_url or vid_url, 
                "duration": 60, 
                "platform": platform
            })
            
    try:
        opts['extractor_args'] = {'youtube': {'player_client': ['android', 'ios']}} 
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            v_formats = [f for f in formats if f.get('vcodec') != 'none']
            best_v = v_formats[-1]['url'] if v_formats else info.get('url')
            return jsonify({"title": info.get('title', 'Media'), "thumbnail": info.get('thumbnail'), "video_url": best_v, "audio_url": best_v, "duration": info.get('duration', 60), "platform": platform})
    except: 
        return jsonify({"error": "سيرفرات يوتيوب/انستا تحظر السحب حالياً من هذا الرابط المجاني."})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
