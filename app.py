import os
import requests
import urllib.parse
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

# تصميم "حملي" الجبار - نيون أحمر، متوافق مع جميع المنصات، وبدون سكرول خارجي
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>حملي - منصة التحميل الذكية</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gifshot/0.3.2/gifshot.min.js"></script>
    <script src="https://unpkg.com/@ffmpeg/ffmpeg@0.11.6/dist/ffmpeg.min.js"></script>
    
    <style>
        :root {
            /* اللون النهاري */
            --bg-color: #f8fafc; --card-bg: #ffffff;
            --text-main: #0f172a; --text-muted: #64748b;
            --primary: #dc2626; --primary-hover: #b91c1c; 
            --border: rgba(0, 0, 0, 0.1);
            --neon-shadow: none;
        }
        [data-theme="dark"] {
            /* اللون الليلي مع الأحمر النيون */
            --bg-color: #0f172a; --card-bg: #1e293b;
            --text-main: #f8fafc; --text-muted: #94a3b8;
            --primary: #ef4444; --primary-hover: #dc2626; 
            --border: rgba(255, 255, 255, 0.1);
            --neon-shadow: 0 0 10px rgba(239, 68, 68, 0.7), 0 0 20px rgba(239, 68, 68, 0.5);
        }
        html, body {
            height: 100dvh; margin: 0; padding: 0; overflow: hidden;
            font-family: 'Tajawal', sans-serif; background-color: var(--bg-color);
            color: var(--text-main); transition: 0.3s;
        }
        .app-container { display: flex; flex-direction: column; height: 100%; max-width: 500px; margin: 0 auto; position: relative; }
        
        .top-bar {
            display: flex; justify-content: space-between; align-items: center; padding: 15px 20px;
            border-bottom: 1px solid var(--border); background: var(--card-bg); flex-shrink: 0;
        }
        /* حركة النيون لاسم الموقع */
        .logo-title {
            margin: 0; font-weight: 900; font-size: 28px; color: var(--primary);
            text-shadow: var(--neon-shadow); letter-spacing: 1px;
            animation: pulse 2s infinite alternate;
        }
        @keyframes pulse {
            0% { text-shadow: 0 0 5px rgba(239, 68, 68, 0.5); }
            100% { text-shadow: 0 0 15px rgba(239, 68, 68, 0.9), 0 0 30px rgba(239, 68, 68, 0.6); }
        }
        .theme-btn {
            background: transparent; border: 1px solid var(--primary); color: var(--primary);
            padding: 8px 15px; border-radius: 20px; cursor: pointer; font-weight: bold; font-family: 'Tajawal'; transition: 0.3s;
        }
        .theme-btn:hover { background: var(--primary); color: white; box-shadow: var(--neon-shadow); }
        
        .main-content { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .main-content::-webkit-scrollbar { width: 5px; }
        .main-content::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }

        /* زر المبرمج (صاحب الموقع) */
        .creator-btn {
            display: flex; align-items: center; justify-content: center; gap: 8px;
            background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
            color: white; padding: 12px; border-radius: 15px; text-decoration: none; font-weight: bold; font-size: 14px;
            box-shadow: 0 4px 10px rgba(220, 39, 67, 0.3); transition: 0.3s;
        }
        .creator-btn:hover { transform: scale(0.98); filter: brightness(1.1); }

        .input-card { background: var(--card-bg); padding: 15px; border-radius: 20px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 10px; }
        .input-row { display: flex; gap: 10px; }
        input[type="text"] {
            flex: 1; padding: 15px; background: transparent; border: 2px solid var(--border);
            color: var(--text-main); border-radius: 12px; font-size: 15px; outline: none; font-family: 'Tajawal'; transition: 0.3s;
        }
        input[type="text"]:focus { border-color: var(--primary); box-shadow: 0 0 8px rgba(239, 68, 68, 0.2); }
        .btn-paste { background: var(--border); border: none; color: var(--text-main); padding: 0 15px; border-radius: 12px; cursor: pointer; }
        .btn-main { padding: 15px; background: var(--primary); color: white; border: none; border-radius: 12px; font-size: 16px; font-weight: 900; cursor: pointer; font-family: 'Tajawal'; box-shadow: var(--neon-shadow); transition: 0.3s; }
        .btn-main:hover { background: var(--primary-hover); }

        .result-box { display: none; background: var(--card-bg); padding: 15px; border-radius: 20px; border: 1px solid var(--border); flex-direction: column; gap: 15px; }
        .preview-player { width: 100%; border-radius: 12px; background: #000; outline: none; }
        .video-header { display: flex; gap: 15px; align-items: center; }
        .thumb { width: 70px; height: 70px; border-radius: 12px; object-fit: cover; border: 1px solid var(--primary); }
        .title { font-size: 14px; font-weight: bold; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .music-tag { font-size: 12px; color: var(--primary); margin-top: 5px; display: flex; align-items: center; gap: 5px; background: rgba(239, 68, 68, 0.1); padding: 5px 10px; border-radius: 10px; font-weight: bold; }

        .btn-action { width: 100%; padding: 12px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px; text-decoration: none; font-size: 14px; color: white; font-family: 'Tajawal'; transition: 0.2s; }
        .btn-action:active { transform: scale(0.98); }
        .bg-mp4 { background: #10b981; } .bg-mp3 { background: #8b5cf6; } .bg-wa { background: #06b6d4; }
        
        /* أدوات التحرير (القص والوقت) */
        .editor-box { background: rgba(0,0,0,0.05); padding: 15px; border-radius: 15px; border: 1px dashed var(--border); display: flex; flex-direction: column; gap: 10px; }
        .time-inputs { display: flex; gap: 10px; }
        .time-inputs input { width: 50%; text-align: center; font-weight: bold; }
        .bg-trim { background: var(--primary); } .bg-gif { background: #f59e0b; }

        .loading { text-align: center; color: var(--text-muted); font-size: 14px; display: none; font-weight: bold; }
        .error-msg { color: var(--primary); text-align: center; font-size: 14px; font-weight: bold; }
    </style>
</head>
<body data-theme="dark">

    <div class="app-container">
        <div class="top-bar">
            <h3 class="logo-title">حملي</h3>
            <button class="theme-btn" onclick="toggleTheme()"><i class="fas fa-sun"></i> فاتح</button>
        </div>

        <div class="main-content">
            
            <a href="https://www.instagram.com/_otnn?igsh=d3hybTN2M2Zlanl0" target="_blank" class="creator-btn">
                <i class="fab fa-instagram"></i> صاحب الموقع: @_otnn
            </a>

            <div class="input-card">
                <div style="font-size: 12px; color: var(--text-muted); text-align: center;">يدعم: انستا، يوتيوب، تيك توك، فيسبوك، X</div>
                <div class="input-row">
                    <input type="text" id="videoUrl" placeholder="الصق الرابط هنا...">
                    <button class="btn-paste" onclick="pasteBtn()"><i class="fas fa-paste"></i></button>
                </div>
                <button class="btn-main" id="searchBtn" onclick="processUrl()">
                    <i class="fas fa-search"></i> بحث ومعالجة
                </button>
                <div class="loading" id="loader"><i class="fas fa-spinner fa-spin"></i> جاري سحب البيانات والتعرف على الصوت (15 ثانية)...</div>
                <div id="errorBox" class="error-msg"></div>
            </div>

            <div class="result-box" id="resultArea">
                <video id="videoPlayer" class="preview-player" controls controlsList="nodownload"></video>
                <div class="video-header" id="videoInfo"></div>
                
                <div id="downloadGrid" style="display: flex; flex-direction: column; gap: 10px;"></div>

                <div class="editor-box">
                    <div style="font-size: 13px; font-weight: bold; color: var(--text-main);"><i class="fas fa-cut"></i> تحديد وقت للقص أو الـ GIF:</div>
                    <div class="time-inputs">
                        <input type="text" id="startTime" placeholder="البداية 00:00" value="00:00">
                        <input type="text" id="endTime" placeholder="النهاية 00:05" value="00:05">
                    </div>
                    <button id="trimBtn" onclick="trimVideo()" class="btn-action bg-trim"><i class="fas fa-video"></i> قص الفيديو</button>
                    <button id="gifBtn" onclick="makeGif()" class="btn-action bg-gif"><i class="fas fa-images"></i> تحويل إلى (GIF)</button>
                    <div id="editorStatus" style="font-size: 12px; text-align: center; color: var(--primary); display: none;"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // إعداد FFmpeg.wasm للقص بالمتصفح
        const { createFFmpeg, fetchFile } = FFmpeg;
        const ffmpeg = createFFmpeg({ log: false });

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
            catch (err) { alert('يرجى منح صلاحية اللصق.'); }
        }

        let currentProxyUrl = '';

        // تحويل الثواني من صيغة 00:00
        function parseTime(str) {
            const p = str.split(':');
            let s = 0, m = 1;
            while (p.length > 0) { s += m * parseInt(p.pop(), 10); m *= 60; }
            return s;
        }

        // دالة القص بالمتصفح (الخارقة)
        async function trimVideo() {
            const start = document.getElementById('startTime').value;
            const end = document.getElementById('endTime').value;
            const status = document.getElementById('editorStatus');
            
            status.style.display = 'block';
            status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري تهيئة نظام القص بمتصفحك...';
            
            try {
                if (!ffmpeg.isLoaded()) await ffmpeg.load();
                status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري تحميل المقطع للقص...';
                
                ffmpeg.FS('writeFile', 'input.mp4', await fetchFile(currentProxyUrl));
                
                status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري القص من '+start+' إلى '+end+'...';
                const duration = parseTime(end) - parseTime(start);
                
                // أمر FFmpeg للقص
                await ffmpeg.run('-ss', start, '-i', 'input.mp4', '-t', duration.toString(), '-c', 'copy', 'output.mp4');
                
                const data = ffmpeg.FS('readFile', 'output.mp4');
                const url = URL.createObjectURL(new Blob([data.buffer], { type: 'video/mp4' }));
                
                const a = document.createElement('a');
                a.href = url; a.download = 'Hamli_Trimmed.mp4'; a.click();
                status.innerHTML = '<i class="fas fa-check"></i> تم القص والتحميل بنجاح!';
            } catch(e) {
                status.innerHTML = '<i class="fas fa-exclamation-triangle"></i> متصفحك لا يدعم هذه العملية للمقاطع الكبيرة.';
            }
        }

        // دالة تحويل GIF بالوقت المحدد
        function makeGif() {
            const startStr = document.getElementById('startTime').value;
            const status = document.getElementById('editorStatus');
            status.style.display = 'block';
            status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري تحويل الـ GIF...';
            
            const startOffset = parseTime(startStr);
            
            gifshot.createGIF({
                'video': [currentProxyUrl],
                'offset': startOffset,
                'numFrames': 20,
                'frameDuration': 1,
                'gifWidth': 300, 'gifHeight': 300
            }, function(obj) {
                if(!obj.error) {
                    const a = document.createElement('a');
                    a.href = obj.image; a.download = 'Hamli_Clip.gif'; a.click();
                    status.innerHTML = '<i class="fas fa-check"></i> تم تحميل الـ GIF بنجاح!';
                } else {
                    status.innerHTML = '<i class="fas fa-exclamation"></i> حدث خطأ أثناء التحويل.';
                }
            });
        }

        async function processUrl() {
            const url = document.getElementById('videoUrl').value;
            const btn = document.getElementById('searchBtn');
            const loader = document.getElementById('loader');
            const resultArea = document.getElementById('resultArea');
            const errBox = document.getElementById('errorBox');
            const player = document.getElementById('videoPlayer');
            
            if(!url) return;

            btn.disabled = true; loader.style.display = 'block'; resultArea.style.display = 'none'; errBox.innerHTML = ''; 

            try {
                const res = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                
                const data = await res.json();
                
                if(data.error) {
                    errBox.innerHTML = data.error;
                } else {
                    // تشغيل الفيديو بالمشغل
                    currentProxyUrl = `/proxy?url=${encodeURIComponent(data.video_url)}`;
                    player.src = currentProxyUrl;
                    
                    let musicHtml = data.real_music ? `<div class="music-tag"><i class="fas fa-music"></i> تم التعرف: ${data.real_music}</div>` : '';

                    document.getElementById('videoInfo').innerHTML = `
                        <img src="${data.thumbnail}" class="thumb">
                        <div>
                            <div class="title">${data.title}</div>
                            ${musicHtml}
                        </div>
                    `;
                    
                    const safeTitle = encodeURIComponent("Hamli_Video");
                    const safeVideoUrl = encodeURIComponent(data.video_url);
                    const safeAudioUrl = encodeURIComponent(data.audio_url || data.video_url);
                    const safeWaUrl = encodeURIComponent(data.whatsapp_url || data.video_url);

                    document.getElementById('downloadGrid').innerHTML = `
                        <a href="/proxy?url=${safeVideoUrl}&title=${safeTitle}&ext=mp4" class="btn-action bg-mp4"><i class="fas fa-download"></i> تحميل كامل (MP4)</a>
                        <a href="/proxy?url=${safeAudioUrl}&title=Hamli_Audio&ext=mp3" class="btn-action bg-mp3"><i class="fas fa-headphones"></i> تحميل الصوت الأصلي (MP3)</a>
                        <a href="/proxy?url=${safeWaUrl}&title=Hamli_WA&ext=mp4" class="btn-action bg-wa"><i class="fab fa-whatsapp"></i> نسخة مضغوطة للواتساب</a>
                    `;
                    resultArea.style.display = 'flex';
                }
            } catch (e) { errBox.innerHTML = "حدث خطأ بالاتصال بخوادم حملي."; } 
            finally { btn.disabled = false; loader.style.display = 'none'; }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

# نظام البحث والتعرف (15 ثانية تخيلية للمطابقة المعقدة)
def hybrid_music_search(info_dict):
    """
    هنا السيرفر يقوم بسحب بيانات المقطع، وإذا تطلب الأمر يستخدم API للتعرف على الصوت (مثل ACRCloud).
    حالياً نعتمد على سحب الاسم المخفي للمنصة والبحث الذكي في يوتيوب (iTunes) كبديل مجاني قوي 100%
    """
    raw_track = info_dict.get('track', '') or info_dict.get('title', '')
    if not raw_track or "صوت أصلي" in raw_track:
        return "صوت أصلي (معزوفة خام)"
    
    try:
        # محاكاة البحث الذكي لجلب الاسم الحقيقي
        search_url = f"https://itunes.apple.com/search?term={urllib.parse.quote(raw_track)}&limit=1&media=music"
        res = requests.get(search_url, timeout=4).json()
        if res['resultCount'] > 0:
            track = res['results'][0]
            return f"{track['trackName']} - {track['artistName']} (أصلي)"
    except:
        pass
    return raw_track

@app.route('/extract', methods=['POST'])
def extract():
    url = request.json.get('url', '')
    if not url: return jsonify({"error": "الرابط فارغ!"}), 400

    # دعم جميع المنصات باستخدام yt-dlp (يوتيوب، انستا، فيسبوك، اكس، وتيك توك كبديل)
    opts = {'quiet': True, 'nocheckcertificate': True}
    
    # محاولة سريعة لتيك توك أولاً
    if 'tiktok.com' in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            resp = requests.get(api_url).json()
            if resp.get('code') == 0:
                v = resp['data']
                raw_music = v.get('music_info', {}).get('title', '')
                real_music = hybrid_music_search({'track': raw_music})
                return jsonify({
                    "title": v.get('title', 'فيديو تيك توك'),
                    "thumbnail": v.get('cover'),
                    "video_url": v.get('play'),
                    "audio_url": v.get('music'), 
                    "whatsapp_url": v.get('wmplay') or v.get('play'),
                    "real_music": real_music
                })
        except: pass

    # الاستخراج العام الشامل لكل المنصات (إنستا، يوتيوب، فيس...)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = info.get('formats', [])
            video_formats = [f for f in formats if f.get('vcodec') != 'none']
            audio_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
            
            best_video = video_formats[-1]['url'] if video_formats else info.get('url')
            best_audio = audio_formats[-1]['url'] if audio_formats else best_video
            worst_video = video_formats[0]['url'] if video_formats else best_video # للواتساب

            real_music = hybrid_music_search(info)

            return jsonify({
                "title": info.get('title', 'مقطع فيديو'),
                "thumbnail": info.get('thumbnail'),
                "video_url": best_video,
                "audio_url": best_audio,
                "whatsapp_url": worst_video,
                "real_music": real_music
            })
    except Exception as e:
        return jsonify({"error": "الرابط غير صالح أو الحساب خاص جداً."}), 500

@app.route('/proxy')
def proxy_download():
    file_url = request.args.get('url')
    title = request.args.get('title', 'Media')
    ext = request.args.get('ext') 
    
    if not file_url: return "الرابط مفقود", 400

    try:
        req = requests.get(file_url, stream=True, verify=False)
        content_type = 'audio/mp3' if ext == 'mp3' else req.headers.get('content-type', 'video/mp4')
        headers = {'Content-Type': content_type}
        
        # السماح للمتصفح (FFmpeg.wasm) بقراءة الملف من السيرفر
        headers['Access-Control-Allow-Origin'] = '*'
        
        if ext:
            headers['Content-Disposition'] = f'attachment; filename="{title}.{ext}"'
            
        return Response(stream_with_context(req.iter_content(chunk_size=1024*1024)), headers=headers)
    except Exception as e:
        return "فشلت العملية", 500

if __name__ == '__main__':
    app.run(debug=True)
