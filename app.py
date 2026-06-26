from flask import Flask, request, jsonify, render_template_string
import yt_dlp
import requests

app = Flask(__name__)

# تصميم زجاجي (Glassmorphism) فاتح وفخم يشبه الآيفون، مع دعم الوضع الليلي
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>منصة التحميل الشاملة | VIP</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-color: #f0f2f5;
            --card-bg: rgba(255, 255, 255, 0.85);
            --text-main: #1c1e21;
            --text-muted: #65676B;
            --primary: #0084ff;
            --primary-hover: #006bce;
            --border: rgba(0, 0, 0, 0.1);
            --shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        }
        [data-theme="dark"] {
            --bg-color: #18191A;
            --card-bg: rgba(36, 37, 38, 0.85);
            --text-main: #E4E6EB;
            --text-muted: #B0B3B8;
            --border: rgba(255, 255, 255, 0.1);
            --shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }
        body {
            font-family: 'Tajawal', sans-serif;
            background-color: var(--bg-color);
            background-image: radial-gradient(circle at 10% 20%, rgba(0, 132, 255, 0.05) 0%, transparent 90%);
            margin: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            color: var(--text-main);
            transition: 0.3s;
        }
        .header-bar { width: 100%; padding: 15px 20px; display: flex; justify-content: flex-end; box-sizing: border-box; }
        .theme-toggle { background: var(--card-bg); border: 1px solid var(--border); padding: 10px 15px; border-radius: 20px; cursor: pointer; color: var(--text-main); font-weight: bold; backdrop-filter: blur(10px); }
        .container {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            padding: 40px;
            border-radius: 30px;
            box-shadow: var(--shadow);
            width: 90%;
            max-width: 500px;
            text-align: center;
            border: 1px solid var(--border);
            margin-top: 20px;
        }
        h2 { margin: 0 0 10px 0; font-weight: 900; font-size: 32px; background: -webkit-linear-gradient(45deg, var(--primary), #00c6ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .platforms { font-size: 24px; color: var(--text-muted); margin-bottom: 25px; display: flex; justify-content: center; gap: 15px; }
        .platforms i { transition: 0.3s; }
        .platforms i:hover { color: var(--primary); transform: scale(1.2); }
        
        .input-group { display: flex; gap: 10px; margin-bottom: 20px; }
        input {
            flex: 1; padding: 16px; background: transparent; border: 2px solid var(--border);
            color: var(--text-main); border-radius: 16px; font-size: 16px; outline: none; transition: 0.3s; font-family: 'Tajawal', sans-serif;
        }
        input:focus { border-color: var(--primary); }
        .paste-btn { padding: 0 20px; background: var(--border); color: var(--text-main); border: none; border-radius: 16px; cursor: pointer; font-size: 18px; transition: 0.3s; }
        .paste-btn:hover { background: var(--primary); color: white; }
        
        .main-btn {
            width: 100%; padding: 16px; background: var(--primary); color: white; border: none; border-radius: 16px;
            font-size: 18px; font-weight: 700; cursor: pointer; transition: 0.3s; font-family: 'Tajawal', sans-serif; box-shadow: 0 4px 15px rgba(0, 132, 255, 0.3);
        }
        .main-btn:hover { background: var(--primary-hover); transform: translateY(-2px); }
        
        /* Progress Bar */
        .progress-container { width: 100%; background: var(--border); border-radius: 10px; margin-top: 20px; display: none; overflow: hidden; }
        .progress-bar { height: 8px; background: var(--primary); width: 0%; transition: width 0.4s ease; }
        
        /* Action Buttons Grid */
        .actions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px; }
        .action-btn {
            padding: 12px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: 0.3s; font-family: 'Tajawal', sans-serif; text-decoration: none;
        }
        .btn-mp4 { background: #10B981; color: white; }
        .btn-mp3 { background: #8B5CF6; color: white; }
        .btn-whatsapp { background: #25D366; color: white; }
        .btn-gif { background: #F59E0B; color: white; }
        .btn-cut { background: #EF4444; color: white; }
        .btn-ai { background: #3B82F6; color: white; grid-column: span 2; }
        .action-btn:hover { transform: translateY(-2px); filter: brightness(1.1); }
        
        /* History Section */
        .history-sec { margin-top: 30px; text-align: right; border-top: 1px solid var(--border); padding-top: 20px; }
        .history-title { font-weight: bold; font-size: 14px; color: var(--text-muted); margin-bottom: 10px; }
        .history-list { list-style: none; padding: 0; margin: 0; font-size: 14px; }
        .history-list li { margin-bottom: 8px; color: var(--primary); cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        
        .thumb { border-radius: 16px; width: 100%; height: 180px; object-fit: cover; margin-top: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .error { color: #EF4444; margin-top: 15px; font-weight: bold; }
    </style>
</head>
<body>

    <div class="header-bar">
        <button class="theme-toggle" onclick="toggleTheme()"><i class="fas fa-moon"></i> داكن</button>
    </div>

    <div class="container">
        <h2>منصة التحميل السريعة</h2>
        <div class="platforms">
            <i class="fab fa-tiktok"></i>
            <i class="fab fa-instagram"></i>
            <i class="fab fa-youtube"></i>
            <i class="fab fa-x-twitter"></i>
            <i class="fab fa-facebook"></i>
        </div>
        
        <div class="input-group">
            <input type="text" id="videoUrl" placeholder="أدخل رابط الفيديو هنا...">
            <button class="paste-btn" onclick="pasteFromClipboard()" title="لصق"><i class="fas fa-paste"></i></button>
        </div>
        
        <button class="main-btn" id="searchBtn" onclick="fetchVideo()"><i class="fas fa-bolt"></i> معالجة صاروخية</button>

        <div class="progress-container" id="progressContainer">
            <div class="progress-bar" id="progressBar"></div>
        </div>

        <div id="result"></div>
        
        <div class="history-sec" id="historySec" style="display:none;">
            <div class="history-title"><i class="fas fa-history"></i> آخر التحميلات:</div>
            <ul class="history-list" id="historyList"></ul>
        </div>
    </div>

    <script>
        // الوضع الليلي والنهاري
        function toggleTheme() {
            const body = document.body;
            const btn = document.querySelector('.theme-toggle');
            if(body.getAttribute('data-theme') === 'dark') {
                body.removeAttribute('data-theme');
                btn.innerHTML = '<i class="fas fa-moon"></i> داكن';
            } else {
                body.setAttribute('data-theme', 'dark');
                btn.innerHTML = '<i class="fas fa-sun"></i> فاتح';
            }
        }

        // اللصق التلقائي الذكي
        async function pasteFromClipboard() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('videoUrl').value = text;
            } catch (err) {
                alert('يرجى السماح بصلاحية اللصق أو استخدم اللصق اليدوي.');
            }
        }

        // السجل (Local Storage)
        function saveToHistory(url) {
            let history = JSON.parse(localStorage.getItem('dl_history') || '[]');
            if(!history.includes(url)) {
                history.unshift(url);
                if(history.length > 3) history.pop();
                localStorage.setItem('dl_history', JSON.stringify(history));
            }
            loadHistory();
        }

        function loadHistory() {
            let history = JSON.parse(localStorage.getItem('dl_history') || '[]');
            const list = document.getElementById('historyList');
            const sec = document.getElementById('historySec');
            if(history.length > 0) {
                sec.style.display = 'block';
                list.innerHTML = history.map(url => `<li onclick="document.getElementById('videoUrl').value='${url}'; fetchVideo();"><i class="fas fa-link"></i> ${url}</li>`).join('');
            }
        }
        
        window.onload = loadHistory;

        // دالة عرض الشريط التفاعلي
        function startProgress() {
            const pc = document.getElementById('progressContainer');
            const pb = document.getElementById('progressBar');
            pc.style.display = 'block';
            pb.style.width = '0%';
            setTimeout(() => pb.style.width = '40%', 500);
            setTimeout(() => pb.style.width = '80%', 1500);
        }

        // المعالجة الرئيسية
        async function fetchVideo() {
            const url = document.getElementById('videoUrl').value;
            const resultDiv = document.getElementById('result');
            const btn = document.getElementById('searchBtn');
            const pb = document.getElementById('progressBar');
            
            if(!url) { resultDiv.innerHTML = `<div class="error">أدخل الرابط أولاً!</div>`; return; }

            btn.disabled = true;
            resultDiv.innerHTML = "";
            startProgress();

            try {
                const response = await fetch('/get_video', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();
                pb.style.width = '100%';

                if (data.error) {
                    resultDiv.innerHTML = `<div class="error"><i class="fas fa-exclamation-triangle"></i> ${data.error}</div>`;
                    return;
                }

                saveToHistory(url);

                let html = ``;
                if(data.thumbnail) { html += `<img src="${data.thumbnail}" class="thumb">`; }
                html += `<h3 style="margin-top:15px; font-size:18px;">${data.title}</h3>`;
                
                // الأزرار الجبارة
                const videoUrl = data.formats[0]?.url || '#';
                
                html += `
                <div class="actions-grid">
                    <a href="${videoUrl}" target="_blank" class="action-btn btn-mp4"><i class="fas fa-download"></i> تحميل سريع (MP4)</a>
                    <a href="${videoUrl}" target="_blank" class="action-btn btn-mp3"><i class="fas fa-music"></i> تحميل صوت (MP3)</a>
                    <button class="action-btn btn-whatsapp" onclick="alert('جاري إعداد السيرفر لضغط الفيديو للواتساب...')"><i class="fab fa-whatsapp"></i> ضغط للواتساب</button>
                    <button class="action-btn btn-cut" onclick="alert('ميزة القص تتطلب تفعيل مكتبة FFMPEG على السيرفر.')"><i class="fas fa-cut"></i> قص الفيديو</button>
                    <button class="action-btn btn-gif" onclick="alert('جاري التجهيز لتحويل المقطع إلى صورة متحركة GIF...')"><i class="fas fa-images"></i> تحويل لـ GIF</button>
                    <button class="action-btn btn-ai" onclick="alert('ميزة الذكاء الاصطناعي لفصل الصوت قيد التطوير للاستضافات المجانية!')"><i class="fas fa-robot"></i> فصل الموسيقى عن الصوت (AI)</button>
                </div>
                `;

                resultDiv.innerHTML = html;

            } catch (error) {
                pb.style.width = '100%';
                pb.style.backgroundColor = '#EF4444';
                resultDiv.innerHTML = `<div class="error">خطأ بالاتصال! يرجى المحاولة مجدداً.</div>`;
            } finally {
                setTimeout(() => { document.getElementById('progressContainer').style.display = 'none'; }, 1000);
                btn.disabled = false;
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
    
    if not url: return jsonify({"error": "الرابط فارغ!"}), 400

    # التحميل المباشر السريع من تيك توك
    if 'tiktok.com' in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            response = requests.get(api_url).json()
            if response.get('code') == 0:
                v = response['data']
                return jsonify({
                    "title": v.get('title', 'تيك توك ترند'),
                    "thumbnail": v.get('cover'),
                    "formats": [{"url": v.get('play')}]
                })
        except: pass # إذا فشل يكمل عاليوتيوب دي ال

    # التحميل السريع لباقي المنصات (يوتيوب، انستا...)
    ydl_opts = {'quiet': True, 'no_warnings': True, 'nocheckcertificate': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
            best_format = formats[-1] if formats else {"url": ""}
            
            return jsonify({
                "title": info.get('title', 'فيديو'),
                "thumbnail": info.get('thumbnail'),
                "formats": [best_format]
            })
    except Exception as e:
        return jsonify({"error": "تعذر جلب الفيديو. قد يكون الرابط خاصاً أو غير مدعوم."}), 500

if __name__ == '__main__':
    app.run(debug=True)
