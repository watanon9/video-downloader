import os
import requests
import re
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context

app = Flask(__name__)

# ==========================================
# 1. FRONTEND: واجهة المستخدم (HTML/CSS/JS)
# ==========================================
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tahmilati | تحميلاتي - System Architecture</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- مكتبات مساعدة -->
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.css" />
    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gifshot/0.3.2/gifshot.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>

    <style>
        /* التنسيقات الأساسية والمتغيرات */
        :root { --bg-color: #f8fafc; --card-bg: #ffffff; --text-main: #0f172a; --text-muted: #64748b; --primary: #dc2626; --border: rgba(0,0,0,0.1); --neon-shadow: none; }
        [data-theme="dark"] { --bg-color: #0f172a; --card-bg: #1e293b; --text-main: #f8fafc; --text-muted: #94a3b8; --primary: #ef4444; --border: rgba(255,255,255,0.1); --neon-shadow: 0 0 10px var(--primary); }
        
        body.theme-tiktok { --primary: #00f2fe; --neon-shadow: 0 0 10px #00f2fe; }
        body.theme-insta { --primary: #f56040; --neon-shadow: 0 0 10px #f56040; }
        body.theme-facebook { --primary: #1877f2; --neon-shadow: 0 0 10px #1877f2; }
        body.theme-general { --primary: #8b5cf6; --neon-shadow: 0 0 10px #8b5cf6; }

        html, body { height: 100dvh; margin: 0; padding: 0; overflow: hidden; font-family: 'Tajawal', sans-serif; background-color: var(--bg-color); color: var(--text-main); transition: 0.4s ease; }
        .app-container { display: flex; flex-direction: column; height: 100%; max-width: 500px; margin: 0 auto; position: relative; overflow: hidden; }
        
        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; border-bottom: 1px solid var(--border); background: var(--card-bg); z-index: 50; }
        .logo-title { margin: 0; font-weight: 900; font-size: 22px; color: var(--primary); text-shadow: var(--neon-shadow); }
        .nav-btns { display: flex; gap: 10px; }
        .icon-btn { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 12px; cursor: pointer; transition: 0.3s; font-size: 16px;}
        .icon-btn:hover { background: var(--primary); color: white; box-shadow: var(--neon-shadow); }

        .sidebar-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 99; display: none; opacity: 0; transition: 0.3s; backdrop-filter: blur(3px); }
        .sidebar { position: fixed; top: 0; right: -300px; width: 280px; height: 100%; background: var(--card-bg); z-index: 100; box-shadow: -5px 0 20px rgba(0,0,0,0.2); transition: right 0.3s ease; display: flex; flex-direction: column; }
        .sidebar.open { right: 0; }
        .sidebar-header { padding: 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .sidebar-title { font-weight: 900; font-size: 18px; color: var(--text-main); }
        .close-sidebar { background: none; border: none; font-size: 20px; color: var(--text-muted); cursor: pointer; }
        .menu-list { list-style: none; padding: 10px 0; margin: 0; flex: 1; overflow-y: auto; }
        .menu-item { padding: 15px 20px; border-bottom: 1px solid var(--border); cursor: pointer; font-weight: bold; font-size: 15px; display: flex; align-items: center; gap: 12px; transition: 0.2s; color: var(--text-main); }
        .menu-item:hover { background: rgba(0,0,0,0.05); color: var(--primary); }
        
        .main-content { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .main-content::-webkit-scrollbar { width: 5px; }
        .main-content::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }

        .welcome-screen { text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; gap: 20px; animation: fadeIn 0.5s; }
        @keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
        .welcome-title { font-size: 26px; font-weight: 900; color: var(--primary); margin: 0; text-shadow: var(--neon-shadow); }
        
        .view-section { display: none; flex-direction: column; gap: 15px; animation: slideUp 0.4s ease; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        
        .input-card { background: var(--card-bg); padding: 18px; border-radius: 20px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 12px; }
        .card-title { font-size: 15px; font-weight: bold; color: var(--text-main); display: flex; align-items: center; gap: 8px; }
        .input-row { display: flex; gap: 8px; align-items: center; background: rgba(0,0,0,0.03); border: 1px solid var(--border); border-radius: 12px; padding-right: 12px; }
        [data-theme="dark"] .input-row { background: rgba(255,255,255,0.03); }
        input[type="text"] { flex: 1; padding: 16px 5px; background: transparent; border: none; color: var(--text-main); font-size: 14px; outline: none; font-family: 'Tajawal'; }
        .action-icon { color: var(--text-muted); cursor: pointer; padding: 10px; transition: 0.2s; }
        .btn-main { padding: 15px; background: var(--primary); color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: 900; cursor: pointer; font-family: 'Tajawal'; box-shadow: var(--neon-shadow); transition: 0.3s; }

        .result-container { display: none; flex-direction: column; gap: 15px; background: var(--card-bg); padding: 15px; border-radius: 20px; border: 1px solid var(--border); }
        .video-header { display: flex; gap: 15px; align-items: center; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
        .thumb { width: 70px; height: 70px; border-radius: 12px; object-fit: cover; border: 1px solid var(--border); }
        .title { font-size: 13px; font-weight: bold; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

        .btn-group { display: flex; gap: 8px; width: 100%; position: relative; }
        .btn-action { flex: 1; padding: 12px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 13px; color: white; font-family: 'Tajawal'; transition: 0.2s; text-align: center; }
        .btn-icon-sq { background: rgba(0,0,0,0.05); width: 45px; flex: none; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--text-main); cursor: pointer; transition: 0.2s; border: 1px solid var(--border); font-size: 16px;}
        [data-theme="dark"] .btn-icon-sq { background: rgba(255,255,255,0.05); }
        
        .quality-dropdown { position: absolute; bottom: 110%; left: 0; width: 100%; background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); display: none; flex-direction: column; z-index: 10; overflow: hidden; }
        .quality-btn { padding: 12px; border: none; background: transparent; color: var(--text-main); font-family: 'Tajawal'; font-weight: bold; font-size: 13px; border-bottom: 1px solid var(--border); cursor: pointer; transition: 0.2s; }
        .quality-btn:hover { background: var(--primary); color: white; }

        .bg-mp4 { background: #10b981; } .bg-mp3 { background: #8b5cf6; } .bg-wa { background: #06b6d4; } .bg-gif { background: #f59e0b; }
        .status-msg { text-align: center; color: var(--primary); font-size: 14px; display: none; font-weight: bold; padding: 10px; }
        
        /* محرر GIF */
        .gif-editor { display: none; background: rgba(0,0,0,0.02); padding: 15px; border-radius: 15px; border: 1px dashed var(--border); }
        .slider-container { margin: 30px 10px 10px 10px; }
        .noUi-connect { background: var(--primary); }
        .noUi-handle { border-radius: 50%; box-shadow: var(--neon-shadow); }

        /* QR Code Modal */
        .qr-modal { display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center; flex-direction: column; backdrop-filter: blur(5px); }
        .qr-box { background: var(--card-bg); padding: 25px; border-radius: 20px; display: flex; flex-direction: column; align-items: center; gap: 15px; }
        .close-qr { background: #ef4444; color: white; border: none; padding: 10px 25px; border-radius: 10px; font-weight: bold; cursor: pointer; font-family: 'Tajawal'; }
    </style>
</head>
<body data-theme="dark">

    <div class="app-container">
        <!-- الشريط العلوي -->
        <div class="top-bar">
            <h3 class="logo-title">Tahmilati</h3>
            <div class="nav-btns">
                <button class="icon-btn" onclick="location.reload()"><i class="fas fa-sync-alt"></i></button>
                <button class="icon-btn" onclick="toggleTheme()"><i class="fas fa-moon"></i></button>
                <button class="icon-btn" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
            </div>
        </div>

        <!-- القائمة الجانبية -->
        <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <span class="sidebar-title">الأقسام المعزولة</span>
                <button class="close-sidebar" onclick="toggleSidebar()"><i class="fas fa-times"></i></button>
            </div>
            <ul class="menu-list">
                <li class="menu-item" onclick="switchView('tiktok', 'theme-tiktok')"><i class="fab fa-tiktok menu-icon" style="color: #00f2fe;"></i> تيك توك (سيرفر مستقل)</li>
                <li class="menu-item" onclick="switchView('insta', 'theme-insta')"><i class="fab fa-instagram menu-icon" style="color: #f56040;"></i> إنستغرام (بروكسي محمي)</li>
                <li class="menu-item" onclick="switchView('facebook', 'theme-facebook')"><i class="fab fa-facebook menu-icon" style="color: #1877f2;"></i> فيسبوك (بروكسي محمي)</li>
                <li class="menu-item" onclick="switchView('general', 'theme-general')"><i class="fas fa-link menu-icon" style="color: #8b5cf6;"></i> تحميل عام</li>
            </ul>
        </div>

        <div class="main-content">
            <!-- الشاشة الترحيبية -->
            <div id="view-welcome" class="welcome-screen view-section" style="display: flex;">
                <h1 class="welcome-title">Tahmilati</h1>
                <p class="welcome-desc">نظام معزول لتجاوز قيود التحميل (CORS By-pass)</p>
                <ul class="welcome-steps" dir="rtl">
                    <li><i class="fas fa-server" style="color:var(--primary)"></i> 1. يتم فصل الطلبات برمجياً.</li>
                    <li><i class="fas fa-shield-alt" style="color:var(--primary)"></i> 2. استخدام بروكسي البث لمنع حظر الإنستا.</li>
                </ul>
            </div>

            <!-- واجهة تيك توك -->
            <div id="view-tiktok" class="view-section">
                <div class="input-card">
                    <div class="card-title"><i class="fab fa-tiktok" style="color: #00f2fe;"></i> نظام تيك توك المعزول</div>
                    <div class="input-row">
                        <input type="text" id="input-tiktok" placeholder="أدخل رابط تيك توك...">
                        <i class="fas fa-paste action-icon" onclick="pasteInput('input-tiktok')"></i>
                    </div>
                    <button class="btn-main" onclick="handleTikTok()">سحب البيانات</button>
                </div>
                <div id="res-tiktok" class="result-container"><div class="status-msg"></div><div class="media-box"></div></div>
            </div>

            <!-- واجهة إنستغرام -->
            <div id="view-insta" class="view-section">
                <div class="input-card">
                    <div class="card-title"><i class="fab fa-instagram" style="color: #f56040;"></i> نظام إنستغرام المحمي (بروكسي)</div>
                    <div class="input-row">
                        <input type="text" id="input-insta" placeholder="رابط بوست أو ريلز أو يوزر الستوري...">
                        <i class="fas fa-paste action-icon" onclick="pasteInput('input-insta')"></i>
                    </div>
                    <button class="btn-main" onclick="handleInstagram()">اتصال عبر البروكسي</button>
                </div>
                <div id="res-insta" class="result-container"><div class="status-msg"></div><div class="media-box"></div></div>
            </div>

            <!-- واجهة فيسبوك -->
            <div id="view-facebook" class="view-section">
                <div class="input-card">
                    <div class="card-title"><i class="fab fa-facebook" style="color: #1877f2;"></i> نظام فيسبوك المحمي</div>
                    <div class="input-row">
                        <input type="text" id="input-facebook" placeholder="أدخل رابط فيسبوك...">
                        <i class="fas fa-paste action-icon" onclick="pasteInput('input-facebook')"></i>
                    </div>
                    <button class="btn-main" onclick="handleFacebook()">اتصال عبر البروكسي</button>
                </div>
                <div id="res-facebook" class="result-container"><div class="status-msg"></div><div class="media-box"></div></div>
            </div>

            <!-- واجهة عامة -->
            <div id="view-general" class="view-section">
                <div class="input-card">
                    <div class="card-title"><i class="fas fa-link" style="color: #8b5cf6;"></i> تحميل عام</div>
                    <div class="input-row">
                        <input type="text" id="input-general" placeholder="أي رابط آخر...">
                        <i class="fas fa-paste action-icon" onclick="pasteInput('input-general')"></i>
                    </div>
                    <button class="btn-main" onclick="handleGeneral()">سحب البيانات</button>
                </div>
                <div id="res-general" class="result-container"><div class="status-msg"></div><div class="media-box"></div></div>
            </div>
        </div>
    </div>

    <div class="qr-modal" id="qrModal">
        <div class="qr-box">
            <span>باركود التحميل</span>
            <div id="qrCodeDiv"></div>
            <button class="close-qr" onclick="document.getElementById('qrModal').style.display='none'">إغلاق</button>
        </div>
    </div>

    <script>
        let activePlayer = null;
        let globalVideoUrl = ''; // للـ GIF

        function toggleTheme() { document.body.setAttribute('data-theme', document.body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'); }
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            if (sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
                overlay.style.opacity = '0';
                setTimeout(() => overlay.style.display = 'none', 300);
            } else {
                overlay.style.display = 'block';
                setTimeout(() => overlay.style.opacity = '1', 10);
                sidebar.classList.add('open');
            }
        }
        function switchView(viewName, themeClass) {
            document.querySelectorAll('.view-section').forEach(el => el.style.display = 'none');
            document.getElementById('view-' + viewName).style.display = 'flex';
            document.body.className = themeClass;
            toggleSidebar();
        }
        async function pasteInput(id) { try { document.getElementById(id).value = await navigator.clipboard.readText(); } catch(e){} }
        function showQR(url) {
            document.getElementById('qrModal').style.display = 'flex';
            document.getElementById('qrCodeDiv').innerHTML = '';
            new QRCode(document.getElementById("qrCodeDiv"), { text: url, width: 160, height: 160 });
        }
        function copyLink(url) {
            const temp = document.createElement("input");
            temp.value = url; document.body.appendChild(temp); temp.select(); document.execCommand("copy"); document.body.removeChild(temp);
            alert("تم نسخ الرابط.");
        }
        function toggleQualityMenu(btn) {
            const menu = btn.parentElement.querySelector('.quality-dropdown');
            menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
        }

        // دالة إجبار التحميل (Trigger Download)
        function forceAutoDownload(url, filename) {
            const a = document.createElement('a'); 
            a.href = url; 
            a.download = filename; 
            document.body.appendChild(a); 
            a.click(); 
            document.body.removeChild(a);
        }

        // دالة الـ GIF
        function toggleGifEditor(containerId, duration) {
            const editor = document.querySelector(`#${containerId} .gif-editor`);
            editor.style.display = editor.style.display === 'block' ? 'none' : 'block';
            const sliderDiv = editor.querySelector('.timeSlider');
            if(!sliderDiv.noUiSlider) {
                noUiSlider.create(sliderDiv, { start: [0, 5], connect: true, step: 1, range: { 'min': 0, 'max': Math.min(duration || 15, 60) } });
                sliderDiv.noUiSlider.on('update', function (values) {
                    editor.querySelector('.startVal').innerText = Math.round(values[0]) + 's';
                    editor.querySelector('.endVal').innerText = Math.round(values[1]) + 's';
                });
                editor.querySelector('.gifStartBtn').onclick = function() {
                    const btn = this; const status = editor.querySelector('.gifStatus');
                    btn.disabled = true; status.style.display = 'block'; status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري الإنشاء...';
                    const vals = sliderDiv.noUiSlider.get();
                    gifshot.createGIF({
                        'video': [globalVideoUrl], 'offset': parseInt(vals[0]), 'numFrames': (parseInt(vals[1]) - parseInt(vals[0])) * 10, 'frameDuration': 1, 'gifWidth': 300, 'gifHeight': 300
                    }, function(obj) {
                        if(!obj.error) { forceAutoDownload(obj.image, 'Tahmilati.gif'); status.innerHTML = 'اكتمل!'; } 
                        else { status.innerHTML = 'خطأ.'; }
                        setTimeout(()=> { status.style.display = 'none'; btn.disabled = false; }, 3000);
                    });
                };
            }
        }

        // ==========================================
        // الدوال المنفصلة (Separation of Concerns)
        // ==========================================

        // 1. TikTok Controller
        async function handleTikTok() {
            const val = document.getElementById('input-tiktok').value.trim();
            if(!val) return;
            const container = document.getElementById('res-tiktok');
            const status = container.querySelector('.status-msg');
            container.style.display = 'flex'; status.style.display = 'block'; status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري الاتصال بخادم تيك توك...';
            container.querySelector('.media-box').innerHTML = '';

            try {
                // الاتصال بمسار الباك إند المعزول
                let r = await fetch('/api/tiktok', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: val}) });
                let res = await r.json();
                if(res.success) {
                    status.style.display = 'none';
                    // تيك توك لا يحتاج بروكسي، روابطه تعمل مباشرة
                    renderMediaResult('tiktok', res.data.title, res.data.thumbnail, res.data.video_url, res.data.audio_url, res.data.video_url, res.data.duration);
                } else throw new Error();
            } catch(e) {
                status.innerHTML = '<i class="fas fa-times"></i> فشل الاتصال، تأكد من الرابط.'; status.style.color = 'red';
            }
        }

        // 2. Instagram Controller
        async function handleInstagram() {
            let val = document.getElementById('input-insta').value.trim();
            if(!val) return;
            if(!val.startsWith('http')) val = 'https://instagram.com/stories/' + val.replace('@', '') + '/'; // معالجة اليوزر للستوري
            
            const container = document.getElementById('res-insta');
            const status = container.querySelector('.status-msg');
            container.style.display = 'flex'; status.style.display = 'block'; status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري فك التشفير وتهيئة البروكسي...';
            container.querySelector('.media-box').innerHTML = '';

            try {
                let r = await fetch('/api/instagram', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: val}) });
                let res = await r.json();
                if(res.success) {
                    status.style.display = 'none';
                    // إنستغرام يحتاج بروكسي لكسر الـ CORS
                    let proxyVid = `/proxy_stream?url=${encodeURIComponent(res.data.video_url)}&ext=mp4`;
                    let proxyAud = `/proxy_stream?url=${encodeURIComponent(res.data.audio_url)}&ext=mp3`;
                    renderMediaResult('insta', 'فيديو إنستغرام', res.data.thumbnail, proxyVid, proxyAud, proxyVid, 15);
                } else throw new Error();
            } catch(e) {
                status.innerHTML = '<i class="fas fa-times"></i> الحساب خاص أو الرابط غير صحيح.'; status.style.color = 'red';
            }
        }

        // 3. Facebook Controller
        async function handleFacebook() {
            const val = document.getElementById('input-facebook').value.trim();
            if(!val) return;
            const container = document.getElementById('res-facebook');
            const status = container.querySelector('.status-msg');
            container.style.display = 'flex'; status.style.display = 'block'; status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري سحب بيانات فيسبوك...';
            container.querySelector('.media-box').innerHTML = '';

            try {
                let r = await fetch('/api/facebook', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: val}) });
                let res = await r.json();
                if(res.success) {
                    status.style.display = 'none';
                    // فيسبوك يحتاج بروكسي لكسر الـ CORS
                    let proxyVid = `/proxy_stream?url=${encodeURIComponent(res.data.video_url)}&ext=mp4`;
                    let proxyAud = `/proxy_stream?url=${encodeURIComponent(res.data.audio_url)}&ext=mp3`;
                    renderMediaResult('facebook', 'فيديو فيسبوك', res.data.thumbnail, proxyVid, proxyAud, proxyVid, 60);
                } else throw new Error();
            } catch(e) {
                status.innerHTML = '<i class="fas fa-times"></i> فشل جلب فيديو فيسبوك.'; status.style.color = 'red';
            }
        }

        // 4. General Controller
        async function handleGeneral() {
            const val = document.getElementById('input-general').value.trim();
            if(!val) return;
            const container = document.getElementById('res-general');
            const status = container.querySelector('.status-msg');
            container.style.display = 'flex'; status.style.display = 'block'; status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> معالجة عامة...';
            container.querySelector('.media-box').innerHTML = '';

            try {
                let r = await fetch('/api/general', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: val}) });
                let res = await r.json();
                if(res.success) {
                    status.style.display = 'none';
                    let proxyVid = `/proxy_stream?url=${encodeURIComponent(res.data.video_url)}&ext=mp4`;
                    renderMediaResult('general', 'مقطع عام', res.data.thumbnail, proxyVid, proxyVid, proxyVid, 60);
                } else throw new Error();
            } catch(e) {
                status.innerHTML = '<i class="fas fa-times"></i> فشل السحب.'; status.style.color = 'red';
            }
        }

        // ==========================================
        // دالة بناء واجهة النتيجة والأزرار
        // ==========================================
        function renderMediaResult(platform, title, thumbnail, videoUrl, audioUrl, whatsappUrl, duration) {
            const containerId = 'res-' + platform;
            const mediaBox = document.querySelector(`#${containerId} .media-box`);
            globalVideoUrl = videoUrl;

            mediaBox.innerHTML = `
                <div class="video-header"><img src="${thumbnail}" class="thumb"><div class="title">${title}</div></div>
                <video class="plyr-player" playsinline controls></video>
                <div class="download-grid" style="display:flex; flex-direction:column; gap:10px;"></div>
                <div class="gif-editor">
                    <div style="font-size: 13px; font-weight: bold; margin-bottom: 10px;"><i class="fas fa-sliders-h"></i> محرر GIF:</div>
                    <div class="timeSlider slider-container"></div>
                    <div style="display:flex; justify-content: space-between; font-size:12px; color:var(--primary); font-weight:bold; margin-bottom: 15px;">
                        <span class="startVal">0s</span> <span class="endVal">5s</span>
                    </div>
                    <button class="btn-action bg-gif gifStartBtn"><i class="fas fa-check"></i> توليد GIF</button>
                    <div class="status-msg gifStatus" style="font-size: 12px; margin-top: 10px;"></div>
                </div>
            `;

            const videoEl = mediaBox.querySelector('.plyr-player');
            videoEl.src = videoUrl;
            if(activePlayer) activePlayer.destroy();
            activePlayer = new Plyr(videoEl, { controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'volume', 'fullscreen'] });

            let actionsHtml = `
                <div class="btn-group">
                    <button onclick="forceAutoDownload('${videoUrl}', 'Tahmilati_Vid.mp4')" class="btn-action bg-mp4"><i class="fas fa-download"></i> تنزيل مباشر</button>
                    <button onclick="toggleQualityMenu(this)" class="btn-icon-sq"><i class="fas fa-cog"></i></button>
                    <div class="quality-dropdown">
                        <button class="quality-btn" onclick="forceAutoDownload('${videoUrl}', 'Tahmilati_1080p.mp4')">1080p (جودة عالية)</button>
                        <button class="quality-btn" onclick="forceAutoDownload('${whatsappUrl}', 'Tahmilati_480p.mp4')">480p (واتساب)</button>
                    </div>
                    <button onclick="copyLink('${window.location.origin + videoUrl}')" class="btn-icon-sq"><i class="fas fa-link"></i></button>
                    <button onclick="showQR('${window.location.origin + videoUrl}')" class="btn-icon-sq"><i class="fas fa-qrcode"></i></button>
                </div>
                <div class="btn-group">
                    <button onclick="forceAutoDownload('${audioUrl}', 'Tahmilati_Aud.mp3')" class="btn-action bg-mp3"><i class="fas fa-music"></i> صوت MP3</button>
                </div>
            `;

            mediaBox.querySelector('.download-grid').innerHTML = actionsHtml;
            if(['tiktok', 'insta'].includes(platform)) {
                mediaBox.querySelector('.gif-editor').style.display = 'block';
                toggleGifEditor(containerId, duration);
            }
            mediaBox.style.display = 'flex';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

# ==========================================
# 2. BACKEND API ROUTES: البنية التحتية المفصولة
# ==========================================

# [1] دالة تيك توك المستقلة
@app.route('/api/tiktok', methods=['POST'])
def api_tiktok():
    url = request.json.get('url', '')
    try:
        r = requests.get(f'https://www.tikwm.com/api/?url={urllib.parse.quote(url)}', timeout=8).json()
        if r.get('code') == 0:
            d = r['data']
            return jsonify({"success": True, "data": {
                "title": d.get('title', 'TikTok Video'),
                "thumbnail": d.get('cover', 'https://via.placeholder.com/150'),
                "video_url": d.get('play'),
                "audio_url": d.get('music'),
                "duration": d.get('duration', 15)
            }})
    except Exception as e:
        pass
    return jsonify({"success": False})

# [2] دالة إنستغرام المستقلة
@app.route('/api/instagram', methods=['POST'])
def api_instagram():
    url = request.json.get('url', '')
    # نستخدم Cobalt لروابط الإنستا المباشرة، أو واجهة عامة للستوريات
    try:
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        payload = {"url": url, "vQuality": "720"}
        r = requests.post("https://api.cobalt.tools/api/json", json=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            res = r.json()
            if res.get('url'):
                r_audio = requests.post("https://api.cobalt.tools/api/json", json={"url": url, "isAudioOnly": True}, headers=headers).json()
                return jsonify({"success": True, "data": {
                    "title": "Instagram Media",
                    "thumbnail": "https://via.placeholder.com/150",
                    "video_url": res['url'],
                    "audio_url": r_audio.get('url', res['url'])
                }})
    except:
        pass
    return jsonify({"success": False})

# [3] دالة فيسبوك والعام
@app.route('/api/facebook', methods=['POST'])
@app.route('/api/general', methods=['POST'])
def api_facebook():
    url = request.json.get('url', '')
    try:
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        payload = {"url": url}
        r = requests.post("https://co.wuk.sh/api/json", json=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            res = r.json()
            if res.get('url'):
                return jsonify({"success": True, "data": {
                    "title": "Media File",
                    "thumbnail": "https://via.placeholder.com/150",
                    "video_url": res['url'],
                    "audio_url": res['url']
                }})
    except:
        pass
    return jsonify({"success": False})

# ==========================================
# 3. STREAMING PROXY: سر كسر الحماية (CORS Bypasser)
# ==========================================
# هذه الدالة تقوم بسحب الفيديو من سيرفرات إنستا/فيس بوك وتمريره كـ Stream (قطرات) 
# مباشرة لجهاز المستخدم لكي لا يصاب السيرفر بانهيار 502، ويمنع رفض التحميل.
@app.route('/proxy_stream')
def proxy_stream():
    target_url = request.args.get('url')
    ext = request.args.get('ext', 'mp4')
    if not target_url:
        return "No URL provided", 400

    # التخفي كمتصفح طبيعي
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': '*/*'
    }

    try:
        req = requests.get(target_url, headers=headers, stream=True, verify=False, timeout=15)
        
        # إذا كان الرابط يرفض الوصول
        if req.status_code != 200 and req.status_code != 206:
            return f"Access Denied by Source. Status: {req.status_code}", req.status_code

        # تمرير الملف كتدفق (Streaming)
        def generate():
            for chunk in req.iter_content(chunk_size=1024 * 512): # 512KB chunks
                if chunk:
                    yield chunk

        response = Response(stream_with_context(generate()), content_type=req.headers.get('content-type', f'video/{ext}'))
        response.headers['Content-Disposition'] = f'attachment; filename="Tahmilati_Download.{ext}"'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except requests.exceptions.RequestException as e:
        return f"Proxy Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
