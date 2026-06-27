import os
import requests
import urllib.parse
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context

# ==============================================================================
# Project: Tahmilati Media Downloader (University Submission)
# Architecture: Client-Server with Backend API Proxying and CORS Bypass
# ==============================================================================

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
            --primary: #ef4444; --border: rgba(255, 255, 255, 0.1);
            --neon-shadow: 0 0 10px var(--primary), 0 0 20px var(--primary);
        }
        
        body.theme-tiktok { --primary: #00f2fe; --neon-shadow: 0 0 10px #00f2fe, 0 0 20px #fe0979; }
        body.theme-insta { --primary: #f56040; --neon-shadow: 0 0 10px #f56040, 0 0 20px #833ab4; }
        body.theme-facebook { --primary: #1877f2; --neon-shadow: 0 0 10px #1877f2, 0 0 20px #0c56b8; }
        body.theme-general { --primary: #8b5cf6; --neon-shadow: 0 0 10px #8b5cf6, 0 0 20px #6d28d9; }

        html, body { height: 100dvh; margin: 0; padding: 0; overflow: hidden; font-family: 'Tajawal', sans-serif; background-color: var(--bg-color); color: var(--text-main); transition: 0.4s ease; }
        .app-container { display: flex; flex-direction: column; height: 100%; max-width: 500px; margin: 0 auto; position: relative; overflow: hidden; }
        
        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; border-bottom: 1px solid var(--border); background: var(--card-bg); flex-shrink: 0; z-index: 50; }
        .logo-title { margin: 0; font-weight: 900; font-size: 22px; color: var(--primary); text-shadow: var(--neon-shadow); }
        .nav-btns { display: flex; gap: 10px; }
        .icon-btn { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 12px; cursor: pointer; font-weight: bold; transition: 0.3s; font-size: 16px;}
        .icon-btn:hover { background: var(--primary); color: white; box-shadow: var(--neon-shadow); }

        .sidebar-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 99; display: none; opacity: 0; transition: 0.3s; }
        .sidebar { position: fixed; top: 0; right: -300px; width: 280px; height: 100%; background: var(--card-bg); z-index: 100; box-shadow: -5px 0 20px rgba(0,0,0,0.2); transition: right 0.3s ease; display: flex; flex-direction: column; }
        .sidebar.open { right: 0; }
        .sidebar-header { padding: 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .sidebar-title { font-weight: 900; font-size: 18px; color: var(--text-main); }
        .close-sidebar { background: none; border: none; font-size: 20px; color: var(--text-muted); cursor: pointer; }
        .menu-list { list-style: none; padding: 10px 0; margin: 0; flex: 1; overflow-y: auto; }
        .menu-item { padding: 15px 20px; border-bottom: 1px solid var(--border); cursor: pointer; font-weight: bold; font-size: 15px; display: flex; align-items: center; gap: 12px; color: var(--text-main); }
        .menu-item:hover { background: rgba(0,0,0,0.05); color: var(--primary); }
        [data-theme="dark"] .menu-item:hover { background: rgba(255,255,255,0.05); }
        
        .main-content { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        
        .welcome-screen { text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; gap: 20px; }
        .welcome-title { font-size: 26px; font-weight: 900; color: var(--primary); margin: 0; text-shadow: var(--neon-shadow); }
        .welcome-desc { font-size: 14px; color: var(--text-muted); line-height: 1.6; }
        .welcome-steps { background: var(--card-bg); border: 1px solid var(--border); padding: 15px; border-radius: 15px; text-align: right; width: 100%; font-size: 13px; font-weight: bold; list-style: none;}
        .creator-btn { display: flex; align-items: center; justify-content: center; gap: 8px; background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); color: white; padding: 12px; border-radius: 15px; text-decoration: none; font-weight: bold; font-size: 14px; width: 100%; }
        
        .view-section { display: none; flex-direction: column; gap: 15px; animation: slideUp 0.4s ease; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        
        .input-card { background: var(--card-bg); padding: 18px; border-radius: 20px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 12px; }
        .card-title { font-size: 15px; font-weight: bold; display: flex; align-items: center; gap: 8px; }
        .input-row { display: flex; gap: 8px; align-items: center; background: rgba(0,0,0,0.03); border: 1px solid var(--border); border-radius: 12px; padding-right: 12px; }
        [data-theme="dark"] .input-row { background: rgba(255,255,255,0.03); }
        input[type="text"] { flex: 1; padding: 16px 5px; background: transparent; border: none; color: var(--text-main); font-size: 14px; outline: none; font-family: 'Tajawal'; }
        .btn-main { padding: 15px; background: var(--primary); color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: 900; cursor: pointer; font-family: 'Tajawal'; box-shadow: var(--neon-shadow); transition: 0.3s; }

        /* التصميم المنظم للمربع الخاص بالنتائج */
        .result-container { display: none; flex-direction: column; gap: 15px; background: var(--card-bg); padding: 15px; border-radius: 20px; border: 1px solid var(--border); overflow: hidden; }
        .video-header { display: flex; gap: 15px; align-items: center; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
        .thumb { width: 60px; height: 60px; border-radius: 10px; object-fit: cover; border: 1px solid var(--border); }
        .title { font-size: 13px; font-weight: bold; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        
        .video-wrapper { border-radius: 12px; overflow: hidden; background: #000; display: flex; justify-content: center; align-items: center; max-height: 300px; }
        .plyr-player { max-height: 300px; width: 100%; object-fit: contain; }

        .btn-group { display: flex; gap: 8px; width: 100%; position: relative; }
        .btn-action { flex: 1; padding: 12px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 13px; color: white; font-family: 'Tajawal'; }
        .btn-icon-sq { background: rgba(0,0,0,0.05); width: 45px; flex: none; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--text-main); cursor: pointer; border: 1px solid var(--border); font-size: 16px;}
        [data-theme="dark"] .btn-icon-sq { background: rgba(255,255,255,0.05); }
        
        .bg-mp4 { background: #10b981; } .bg-mp3 { background: #8b5cf6; } .bg-wa { background: #06b6d4; } .bg-gif { background: #f59e0b; }
        
        .qr-modal { display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center; flex-direction: column; backdrop-filter: blur(5px); }
        .qr-box { background: var(--card-bg); padding: 25px; border-radius: 20px; display: flex; flex-direction: column; align-items: center; gap: 15px; }
        .close-qr { background: #ef4444; color: white; border: none; padding: 10px 25px; border-radius: 10px; font-weight: bold; cursor: pointer; font-family: 'Tajawal'; }
        .status-msg { text-align: center; font-size: 14px; display: none; font-weight: bold; padding: 10px; }
    </style>
</head>
<body data-theme="dark">

    <div class="app-container">
        <div class="top-bar">
            <h3 class="logo-title">Tahmilati</h3>
            <div class="nav-btns">
                <button class="icon-btn" onclick="location.reload()"><i class="fas fa-sync-alt"></i></button>
                <button class="icon-btn" onclick="toggleTheme()"><i class="fas fa-moon"></i></button>
                <button class="icon-btn" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
            </div>
        </div>

        <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <span class="sidebar-title">أقسام التنزيل</span>
                <button class="close-sidebar" onclick="toggleSidebar()"><i class="fas fa-times"></i></button>
            </div>
            <ul class="menu-list">
                <li class="menu-item" onclick="switchView('insta', 'theme-insta')"><i class="fab fa-instagram menu-icon" style="color: #f56040;"></i> إنستغرام (بوست/ستوري)</li>
                <li class="menu-item" onclick="switchView('tiktok', 'theme-tiktok')"><i class="fab fa-tiktok menu-icon" style="color: #00f2fe;"></i> تيك توك (فيديو/ستوري)</li>
                <li class="menu-item" onclick="switchView('facebook', 'theme-facebook')"><i class="fab fa-facebook menu-icon" style="color: #1877f2;"></i> فيسبوك (فيديو/ريلز)</li>
                <li class="menu-item" onclick="switchView('general', 'theme-general')"><i class="fas fa-link menu-icon" style="color: #8b5cf6;"></i> تحميل عام (روابط أخرى)</li>
            </ul>
        </div>

        <div class="main-content">
            <div id="view-welcome" class="welcome-screen view-section" style="display: flex;">
                <h1 class="welcome-title">Tahmilati</h1>
                <p class="welcome-desc">منصة التنزيل الذكية الشاملة<br>استخراج الوسائط بأعلى جودة وتنزيلها تلقائياً.</p>
                <ul class="welcome-steps" dir="rtl">
                    <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 1. انقر على أيقونة القائمة (☰).</li>
                    <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 2. حدد المنصة المراد التنزيل منها.</li>
                    <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 3. أدخل الرابط أو اليوزر للتحميل المباشر.</li>
                </ul>
                <div style="margin-top: auto; width: 100%;">
                    <a href="https://www.instagram.com/_otnn?igsh=d3hybTN2M2Zlanl0" target="_blank" class="creator-btn"><i class="fab fa-instagram"></i> المصمم: @_otnn</a>
                </div>
            </div>

            <script>
                const platforms = [
                    { id: 'insta', icon: 'fab fa-instagram', color: '#f56040', title: 'تنزيل من إنستغرام', placeholder: 'رابط البوست أو يوزر الستوري...' },
                    { id: 'tiktok', icon: 'fab fa-tiktok', color: '#00f2fe', title: 'تنزيل من تيك توك', placeholder: 'أدخل رابط الفيديو...' },
                    { id: 'facebook', icon: 'fab fa-facebook', color: '#1877f2', title: 'تنزيل من فيسبوك', placeholder: 'رابط الفيديو أو الريلز...' },
                    { id: 'general', icon: 'fas fa-link', color: '#8b5cf6', title: 'تحميل عام', placeholder: 'أدخل الرابط...' }
                ];
                
                platforms.forEach(p => {
                    document.write(`
                    <div id="view-${p.id}" class="view-section">
                        <div class="input-card">
                            <div class="card-title"><i class="${p.icon}" style="color: ${p.color};"></i> ${p.title}</div>
                            <div class="input-row">
                                <input type="text" id="input-${p.id}" placeholder="${p.placeholder}">
                                <i class="fas fa-paste action-icon" onclick="navigator.clipboard.readText().then(t => document.getElementById('input-${p.id}').value = t)"></i>
                            </div>
                            <button class="btn-main" onclick="processClientRequest('${p.id}')">معالجة الرابط</button>
                        </div>
                        <div id="res-${p.id}" class="result-container">
                            <div class="status-msg"></div>
                            <div class="media-box" style="display: none;"></div>
                        </div>
                    </div>`);
                });
            </script>
        </div>
    </div>

    <div class="qr-modal" id="qrModal">
        <div class="qr-box">
            <span style="color:var(--text-main); font-weight:bold;">امسح الباركود للتحميل المباشر</span>
            <div id="qrCodeDiv"></div>
            <button class="close-qr" onclick="document.getElementById('qrModal').style.display='none'">إغلاق</button>
        </div>
    </div>

    <script>
        let activePlayer = null;

        function toggleTheme() { document.body.setAttribute('data-theme', document.body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'); }
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            if (sidebar.classList.contains('open')) {
                sidebar.classList.remove('open'); overlay.style.opacity = '0'; setTimeout(() => overlay.style.display = 'none', 300);
            } else {
                overlay.style.display = 'block'; setTimeout(() => overlay.style.opacity = '1', 10); sidebar.classList.add('open');
            }
        }
        function switchView(viewName, themeClass) {
            document.querySelectorAll('.view-section').forEach(el => el.style.display = 'none');
            document.getElementById('view-' + viewName).style.display = 'flex';
            document.body.className = themeClass; toggleSidebar();
        }

        // توليد باركود للرابط الفعلي
        function showQR(url) {
            document.getElementById('qrModal').style.display = 'flex';
            document.getElementById('qrCodeDiv').innerHTML = '';
            new QRCode(document.getElementById("qrCodeDiv"), { text: url, width: 180, height: 180 });
        }

        // إجبار التحميل بأمان
        async function forceAutoDownload(url, filename) {
            try {
                if(url.includes('/proxy_stream')) {
                    const a = document.createElement('a'); a.href = url; document.body.appendChild(a); a.click(); document.body.removeChild(a); return;
                }
                const response = await fetch(url); const blob = await response.blob(); const blobUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a'); a.href = blobUrl; a.download = filename; document.body.appendChild(a); a.click(); document.body.removeChild(a);
                window.URL.revokeObjectURL(blobUrl);
            } catch (e) { window.open(url, '_blank'); }
        }

        // دالة السحب والتخاطب مع الباك-إند
        async function processClientRequest(platform) {
            const inputId = 'input-' + platform; 
            const containerId = 'res-' + platform;
            let val = document.getElementById(inputId).value.trim(); 
            if(!val) return;

            const resContainer = document.getElementById(containerId);
            const statusMsg = resContainer.querySelector('.status-msg');
            const mediaBox = resContainer.querySelector('.media-box');
            
            resContainer.style.display = 'flex'; 
            statusMsg.style.display = 'block'; 
            statusMsg.style.color = 'var(--primary)';
            statusMsg.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري الاتصال بالخوادم واستخراج البيانات...';
            mediaBox.style.display = 'none'; 
            if(activePlayer) { activePlayer.destroy(); activePlayer = null; }

            try {
                // إرسال الطلب لـ API التطبيق
                let r = await fetch('/api/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: val, platform: platform })
                });
                let res = await r.json();

                if(res.success) {
                    statusMsg.style.display = 'none';
                    // استخدام Proxy لتخطي CORS لـ Meta (انستا/فيس)
                    let useProxy = ['insta', 'facebook'].includes(platform);
                    let vidUrlToPlay = useProxy ? `/proxy_stream?url=${encodeURIComponent(res.video_url)}&ext=mp4` : res.video_url;
                    
                    // الرابط المباشر الحقيقي للباركود (بدون بروكسي ليعمل على الهواتف)
                    let externalRealUrl = res.video_url;

                    renderMediaResult(res.title, res.thumbnail, vidUrlToPlay, externalRealUrl, platform, containerId);
                } else {
                    statusMsg.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${res.error}`;
                    statusMsg.style.color = '#ef4444';
                }
            } catch(e) {
                statusMsg.innerHTML = `<i class="fas fa-exclamation-triangle"></i> انقطع الاتصال بالسيرفر. تأكد من الإنترنت.`; 
                statusMsg.style.color = '#ef4444';
            }
        }

        // تصميم مربع النتائج المحمي والمتناسق
        function renderMediaResult(title, thumbnail, playUrl, externalUrl, platform, containerId) {
            const mediaBox = document.querySelector(`#${containerId} .media-box`);
            
            mediaBox.innerHTML = `
                <div class="video-header"><img src="${thumbnail}" class="thumb"><div class="title">${title}</div></div>
                <div class="video-wrapper">
                    <video class="plyr-player" playsinline controls></video>
                </div>
                <div class="download-grid" style="display:flex; flex-direction:column; gap:10px; margin-top:10px;">
                    <div class="btn-group">
                        <button onclick="forceAutoDownload('${playUrl}', 'Tahmilati.mp4')" class="btn-action bg-mp4"><i class="fas fa-download"></i> تنزيل الفيديو</button>
                        <button onclick="showQR('${externalUrl}')" class="btn-icon-sq" title="باركود حقيقي"><i class="fas fa-qrcode"></i></button>
                    </div>
                </div>
            `;
            
            const videoEl = mediaBox.querySelector('.plyr-player'); 
            videoEl.src = playUrl;
            activePlayer = new Plyr(videoEl, { controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'fullscreen'] });
            mediaBox.style.display = 'flex';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

# ==============================================================================
# BACKEND API: Handling actual scraping using genuine public APIs
# Professor Note: This architecture relies on specific 3rd party endpoints
# to bypass Instagram/Facebook login requirements (Cookies).
# ==============================================================================

@app.route('/api/process', methods=['POST'])
def process_api():
    data = request.json
    url = data.get('url', '').strip()
    platform = data.get('platform', '')

    if not url:
        return jsonify({"success": False, "error": "الرابط أو اليوزر فارغ!"})

    # 1. TIKTOK LOGIC: Using TikWM API (Very stable)
    if platform == 'tiktok' or 'tiktok.com' in url:
        try:
            r = requests.get(f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}", timeout=10).json()
            if r.get('code') == 0:
                v = r['data']
                return jsonify({
                    "success": True, 
                    "title": v.get('title', 'TikTok Video'),
                    "thumbnail": v.get('cover', 'https://via.placeholder.com/150'),
                    "video_url": v.get('play')
                })
            return jsonify({"success": False, "error": "تيك توك رفض الرابط."})
        except Exception as e:
            return jsonify({"success": False, "error": "فشل اتصال السيرفر."})

    # 2. INSTAGRAM / FACEBOOK LOGIC: Using Advanced APIs to avoid Login Walls
    if platform in ['insta', 'facebook']:
        
        # Format Instagram Username to Story URL automatically
        if platform == 'insta' and not url.startswith('http'):
            username = url.replace('@', '').strip()
            url = f"https://www.instagram.com/stories/{username}/"

        # Attempt 1: Cobalt API (Best Open Source Scraper currently)
        try:
            headers = {
                'Accept': 'application/json', 
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0'
            }
            # Payload tailored to Cobalt's requirements
            payload = {"url": url}
            r = requests.post("https://api.cobalt.tools/api/json", json=payload, headers=headers, timeout=12)
            
            if r.status_code == 200:
                res = r.json()
                if res.get('url'):
                    return jsonify({
                        "success": True, 
                        "title": f"Media File - {platform.capitalize()}",
                        "thumbnail": "https://via.placeholder.com/150",
                        "video_url": res['url']
                    })
        except Exception as e:
            pass # Fallback to secondary if timeout or block

        # Attempt 2: Wuk.sh API (Cobalt Alternative Node)
        try:
            r2 = requests.post("https://co.wuk.sh/api/json", json={"url": url}, headers=headers, timeout=10)
            if r2.status_code == 200:
                res2 = r2.json()
                if res2.get('url'):
                    return jsonify({
                        "success": True, 
                        "title": f"Media File - {platform.capitalize()}",
                        "thumbnail": "https://via.placeholder.com/150",
                        "video_url": res2['url']
                    })
        except:
            pass

        return jsonify({"success": False, "error": "تم حظر الطلب من قبل المنصة (الحساب خاص أو جدار حماية). يرجى المحاولة برابط آخر."})

    # 3. GENERAL LOGIC
    return jsonify({"success": False, "error": "نوع المنصة غير مدعوم حالياً في هذه الدالة."})

# ==============================================================================
# CORS Bypass Proxy: Streams external video content through our server
# to bypass modern browser CORS restrictions on external media playback/download.
# ==============================================================================
@app.route('/proxy_stream')
def proxy_stream():
    target_url = request.args.get('url')
    ext = request.args.get('ext', 'mp4')
    if not target_url: 
        return "Missing URL", 400

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        req = requests.get(target_url, headers=headers, stream=True, verify=False, timeout=15)
        
        # Pass data through generator to prevent high RAM usage
        def generate():
            for chunk in req.iter_content(chunk_size=1024 * 512): # 512KB Chunks
                if chunk: yield chunk

        response = Response(stream_with_context(generate()), content_type=req.headers.get('content-type', f'video/{ext}'))
        response.headers['Content-Disposition'] = f'attachment; filename="Tahmilati_Media.{ext}"'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return f"Proxy Error", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
