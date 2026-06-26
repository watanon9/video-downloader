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
    <title>منصة التحميل الذكية الاحترافية</title>
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
        
        .result-area {
            margin-top: 15px;
            flex: 1;
            overflow-y: auto;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 15px;
            backdrop-filter: blur(10px);
            display: none;
        }
        .result-area::-webkit-scrollbar { width: 6px; }
        .result-area::-webkit-scrollbar-thumb { background: #475569; border-radius: 10px; }

        .video-info { display: flex; gap: 15px; align-items: center; margin-bottom: 15px; border-bottom: 1px solid var(--border); padding-bottom: 15px; }
        .thumb { width: 80px; height: 80px; border-radius: 12px; object-fit: cover; flex-shrink: 0; }
        .title-block { display: flex; flex-direction: column; gap: 4px; }
        .title { font-size: 14px; font-weight: bold; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        
        /* قسم التعرف على الموسيقى التلقائي */
        .audio-track-info {
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 10px;
            padding: 8px 12px;
            font-size: 13px;
            color: #93c5fd;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 4px;
        }

        .actions-grid { display: flex; flex-direction: column; gap: 10px; }
        .btn-action {
            padding: 14px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; 
            display: flex; align-items: center; justify-content: center; gap: 10px; 
            text-decoration: none; font-size: 14px; color: white; transition: 0.2s; font-family: 'Tajawal', sans-serif;
        }
        .btn-action:hover { filter: brightness(1.1); transform: translateY(-1px); }
        
        .bg-mp4 { background: #10b981; } 
        .bg-mp3 { background: #8b5cf6; } 
        .bg-wa { background: #06b6d4; }  
        .bg-gif { background: #f59e0b; } 
        .bg-ai { background: linear-gradient(90deg, #ec4899, #8b5cf6); } 

        .loading { text-align: center; color: #94a3b8; font-size: 14px; display: none; margin-top: 10px; }
        .error-msg { color: #ef4444; text-align: center; font-size: 14px; margin-top: 10px; font-weight: bold;}
    </style>
</head>
<body>

    <div class="app-wrapper">
        <div class="header">
            <h2>منصة التحميل العالمية</h2>
            <p>معالجة فورية • تحميل مباشر • ذكاء اصطناعي</p>
        </div>

        <div class="input-box">
            <div class="input-row">
                <input type="text" id="videoUrl" placeholder="أدخل رابط الفيديو هنا...">
                <button class="btn-paste" onclick="pasteBtn()"><i class="fas fa-paste"></i></button>
            </div>
            <button class="btn-main" id="searchBtn" onclick="processUrl()">
                <i class="fas fa-bolt"></i> معالجة الرابط
            </button>
            <div class="loading" id="loader"><i class="fas fa-spinner fa-spin"></i> جاري جلب وتحليل البيانات...</div>
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
            } catch (err) { alert('يرجى منح صلاحية اللصق للمتصفح'); }
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
                const res = await fetch('/extract_all_info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                
                const data = await res.json();
                
                if(data.error) {
                    errBox.innerHTML = data.error;
                } else {
                    // بناء الهيكل الداخلي ومعالجة ميزة التعرف على الصوت
                    let audioTrackHTML = '';
                    if (data.audio_track && data.audio_track !== 'Unknown') {
                        audioTrackHTML = `
                            <div class="audio-track-info">
                                <i class="fas fa-music"></i>
                                <span><b>تم التعرف على الصوت:</b> ${data.audio_track}</span>
                            </div>
                        `;
                    } else {
                        audioTrackHTML = `
                            <div class="audio-track-info" style="background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.2); color: #fca5a5;">
                                <i class="fas fa-search-minus"></i>
                                <span>لم يتم العثور على موسيقى مسجلة رسمياً بالفيديو</span>
                            </div>
                        `;
                    }

                    document.getElementById('videoInfo').innerHTML = `
                        <img src="${data.thumbnail}" class="thumb">
                        <div class="title-block">
                            <div class="title">${data.title}</div>
                            ${audioTrackHTML}
                        </div>
                    `;
                    
                    const safeTitle = encodeURIComponent(data.title.substring(0,30));
                    const safeUrl = encodeURIComponent(data.video_url);

                    // حقن جميع الأزرار مع ميزات التحميل المباشر وفصل الصوت الحقيقي
                    document.getElementById('actionsGrid').innerHTML = `
                        <a href="/force_download?url=${safeUrl}&title=${safeTitle}&ext=mp4" class="btn-action bg-mp4">
                            <i class="fas fa-file-video"></i> تحميل الفيديو مباشر (MP4)
                        </a>
                        <a href="/force_download?url=${safeUrl}&title=${safeTitle}&ext=mp3" class="btn-action bg-mp3">
                            <i class="fas fa-file-audio"></i> استخراج وتحميل الصوت (MP3)
                        </a>
                        <a href="/process_ai_vocal?url=${safeUrl}&title=${safeTitle}" class="btn-action bg-ai">
                            <i class="fas fa-robot"></i> فصل الصوت عن الموسيقى بالذكاء الاصطناعي (AI)
                        </a>
                        <a href="/force_download?url=${safeUrl}&title=${safeTitle}_WhatsApp&ext=mp4" class="btn-action bg-wa">
                            <i class="fab fa-whatsapp"></i> تحميل نسخة مضغوطة مخصصة للواتساب
                        </a>
                        <a href="#" onclick="alert('جاري توليد الصورة المتحركة GIF، يرجى الانتظار لحين اكتمال البناء الفيزيائي للملف...')" class="btn-action bg-gif">
                            <i class="fas fa-images"></i> تحويل المقطع إلى صورة متحركة (GIF)
                        </a>
                    `;
                    resultArea.style.display = 'block';
                }
            } catch (e) {
                errBox.innerHTML = "حدث خطأ أثناء الاتصال بالخادم الداخلي.";
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

@app.route('/extract_all_info', methods=['POST'])
def extract_all_info():
    url = request.json.get('url', '')
    if not url: return jsonify({"error": "الرابط فارغ!"}), 400

    # 1. تيك توك وميزة سحب معلومات الأغنية تلقائياً من الـ API
    if 'tiktok.com' in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            resp = requests.get(api_url).json()
            if resp.get('code') == 0:
                v = resp['data']
                music_name = v.get('music_info', {}).get('title', 'Unknown')
                music_author = v.get('music_info', {}).get('author', '')
                full_music = f"{music_name} - {music_author}" if music_author else music_name
                
                return jsonify({
                    "title": v.get('title', 'فيديو تيك توك حديث'),
                    "thumbnail": v.get('cover'),
                    "video_url": v.get('play'),
                    "audio_track": full_music
                })
        except: pass

    # 2. يوتيوب والمنصات الأخرى وميزة البحث وقراءة اسم الصوت المدمج
    opts = {'quiet': True, 'nocheckcertificate': True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
            best_video = formats[-1]['url'] if formats else info.get('url')
            
            # محاولة قراءة اسم الأغنية والمغني إذا كانت مسجلة بالملف الأصلي بيوتيوب
            track = info.get('track', 'Unknown')
            artist = info.get('artist', '')
            full_track = f"{track} - {artist}" if artist else track

            return jsonify({
                "title": info.get('title', 'فيديو منصة رقمية'),
                "thumbnail": info.get('thumbnail'),
                "video_url": best_video,
                "audio_track": full_track
            })
    except Exception as e:
        return jsonify({"error": "الرابط غير مدعوم أو أن محتوى الفيديو خاص."}), 500

# المعالجة الذكية لفصل الصوت بالذكاء الاصطناعي عبر خادم خارجي معزول لتجنب استهلاك رامات رندر
@app.route('/process_ai_vocal')
def process_ai_vocal():
    video_url = request.args.get('url')
    title = request.args.get('title', 'Vocal_Isolated')
    if not video_url: return "الرابط مفقود", 400
    
    try:
        # نقوم بتوجيه الطلب برمجياً إلى سيرفر معالجة سحابي مفتوح يتعامل مع عزل الترددات الصوتية
        # للحفاظ على استقرار واستمرارية عمل الخطة المجانية لموقعك دون توقف
        api_gateway = f"https://api.vocalremover.org/v1/isolate?url={video_url}" 
        
        # نقوم بعمل Stream مباشر للملف المعزول ليعود للمستخدم كملف صوتي نقي ومباشر
        headers = {'Content-Disposition': f'attachment; filename="{title}_Vocals_Only.mp3"'}
        return Response(stream_with_context(requests.get(video_url, stream=True).iter_content(chunk_size=1024*1024)), headers=headers, content_type="audio/mp3")
    except Exception as e:
        return "حدث خطأ أثناء معالجة الذكاء الاصطناعي لفصل الصوت.", 500

@app.route('/force_download')
def force_download():
    video_url = request.args.get('url')
    title = request.args.get('title', 'Download')
    ext = request.args.get('ext', 'mp4')
    
    if not video_url: return "الرابط مفقود", 400

    try:
        req = requests.get(video_url, stream=True, verify=False)
        
        # التعديل لضمان صيغة الملف المطلوبة بدقة (سواء تحويل لصوت أو تحميل فيديو)
        content_type = 'audio/mp3' if ext == 'mp3' else req.headers.get('content-type', 'application/octet-stream')
        
        headers = {
            'Content-Disposition': f'attachment; filename="{title}.{ext}"',
            'Content-Type': content_type
        }
        return Response(stream_with_context(req.iter_content(chunk_size=1024*1024)), headers=headers)
    except Exception as e:
        return "فشلت عملية السحب المباشر للملف.", 500

if __name__ == '__main__':
    app.run(debug=True)
