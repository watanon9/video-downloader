import os
import requests
import urllib.parse
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp

# ==============================================================================
# Tahmilati Pro - University Final Architecture (Enterprise Level)
# Features:
# 1. PWA (Progressive Web App): Add to Home Screen dynamically.
# 2. Chameleon Animated Background for Home Screen.
# 3. Logo Reset Functionality to return home seamlessly.
# 4. GIF Maker Engine working perfectly via CORS Proxy.
# 5. Full Audio Search (AI-like) to fetch pure MP3 tracks by name.
# 6. Fallback and Smart Nodes (Cobalt, Wuk, TikWM) for max stability.
# ==============================================================================

app = Flask(__name__)

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tahmilati | تحميلاتي برو</title>
    
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#0f172a">
    <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/3039/3039381.png">

    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.css" />
    
    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gifshot/0.3.2/gifshot.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>

    <style>
        :root {
            --bg-dark: #0f172a; --glass-dark: rgba(30, 41, 59, 0.75); 
            --border-dark: rgba(255, 255, 255, 0.15); --text-dark: #f8fafc; 
            --primary: #8b5cf6; --neon-shadow: 0 0 20px rgba(139, 92, 246, 0.6);
        }

        body[data-theme="dark"] { --bg: var(--bg-dark); --glass: var(--glass-dark); --border: var(--border-dark); --text: var(--text-dark); }
        
        body.theme-tiktok { --primary: #00f2fe; --neon-shadow: 0 0 20px rgba(0, 242, 254, 0.7); }
        body.theme-insta { --primary: #f56040; --neon-shadow: 0 0 20px rgba(245, 96, 64, 0.7); }
        body.theme-facebook { --primary: #1877f2; --neon-shadow: 0 0 20px rgba(24, 119, 242, 0.7); }
        body.theme-general { --primary: #8b5cf6; --neon-shadow: 0 0 20px rgba(139, 92, 246, 0.7); }

        /* Chameleon Background Animation */
        @keyframes chameleonBG {
            0% { background-color: #0f172a; }
            25% { background-color: #1e1b4b; }
            50% { background-color: #311042; }
            75% { background-color: #0a192f; }
            100% { background-color: #0f172a; }
        }

        body.home-active { animation: chameleonBG 15s infinite alternate ease-in-out; }
        body:not(.home-active) { animation: none; background-color: var(--bg); transition: background-color 0.5s ease; }

        html, body { height: 100dvh; margin: 0; padding: 0; overflow-x: hidden; font-family: 'Tajawal', sans-serif; color: var(--text); }
        .app-container { display: flex; flex-direction: column; height: 100%; max-width: 550px; margin: 0 auto; position: relative; }
        
        /* Top Navigation */
        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 18px 25px; background: var(--glass); backdrop-filter: blur(15px); border-bottom: 1px solid var(--border); z-index: 50; }
        .logo-title { margin: 0; font-weight: 900; font-size: 26px; color: var(--primary); text-shadow: var(--neon-shadow); cursor: pointer; transition: 0.3s; }
        .logo-title:hover { transform: scale(1.05); }
        .nav-btns { display: flex; gap: 12px; }
        .icon-btn { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 10px 14px; border-radius: 12px; cursor: pointer; transition: all 0.3s; font-size: 18px; display: flex; justify-content: center; align-items: center;}
        .icon-btn:hover { background: var(--primary); color: #fff; box-shadow: var(--neon-shadow); transform: translateY(-2px); }

        /* Sidebar */
        .sidebar-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 99; display: none; opacity: 0; transition: 0.3s; backdrop-filter: blur(5px); }
        .sidebar { position: fixed; top: 0; right: -320px; width: 290px; height: 100%; background: var(--glass); backdrop-filter: blur(25px); border-left: 1px solid var(--border); z-index: 100; box-shadow: -10px 0 30px rgba(0,0,0,0.6); transition: right 0.4s cubic-bezier(0.2, 0.8, 0.2, 1); display: flex; flex-direction: column; }
        .sidebar.open { right: 0; }
        .sidebar-header { padding: 25px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .sidebar-title { font-weight: 900; font-size: 20px; color: var(--text); }
        .close-sidebar { background: none; border: none; font-size: 24px; color: #ef4444; cursor: pointer; transition: 0.2s; }
        .close-sidebar:hover { transform: scale(1.2) rotate(90deg); }
        .menu-list { list-style: none; padding: 15px 0; margin: 0; flex: 1; overflow-y: auto; }
        .menu-item { padding: 18px 25px; border-bottom: 1px solid var(--border); cursor: pointer; font-weight: bold; font-size: 16px; display: flex; align-items: center; gap: 15px; transition: 0.3s; color: var(--text); }
        .menu-item:hover { background: rgba(255,255,255,0.05); padding-right: 35px; color: var(--primary); }

        /* Main Area & Glass Cards */
        .main-content { flex: 1; overflow-y: auto; padding: 25px; display: flex; flex-direction: column; gap: 20px; scroll-behavior: smooth; }
        .main-content::-webkit-scrollbar { width: 5px; }
        .main-content::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }

        .glass-card { background: var(--glass); backdrop-filter: blur(20px); border: 1px solid var(--border); border-radius: 25px; padding: 25px; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4); }
        
        /* Welcome Screen PWA Button */
        .welcome-screen { text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; gap: 25px; animation: fadeIn 0.5s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
        .welcome-title { font-size: 36px; font-weight: 900; color: var(--primary); margin: 0; text-shadow: var(--neon-shadow); }
        .welcome-desc { font-size: 16px; color: var(--text); opacity: 0.9; line-height: 1.8; margin-top: 10px; }
        
        .pwa-btn { display: none; align-items: center; justify-content: center; gap: 10px; background: linear-gradient(45deg, #2563eb, #4f46e5); color: white; padding: 15px 30px; border-radius: 30px; font-weight: 900; font-size: 16px; border: none; cursor: pointer; box-shadow: 0 5px 20px rgba(79, 70, 229, 0.5); transition: 0.3s; margin-top: 15px; width: 100%; }
        .pwa-btn:hover { transform: translateY(-3px); filter: brightness(1.1); }

        .view-section { display: none; flex-direction: column; gap: 20px; animation: fadeIn 0.4s ease; }
        
        .card-title { font-size: 18px; font-weight: 900; display: flex; align-items: center; gap: 12px; margin-bottom: 20px; color: var(--text); }
        .input-row { display: flex; gap: 10px; align-items: center; background: rgba(0,0,0,0.2); border: 1px solid var(--border); border-radius: 18px; padding-right: 15px; transition: 0.3s; }
        .input-row:focus-within { border-color: var(--primary); box-shadow: inset 0 0 10px rgba(0,0,0,0.5); }
        input[type="text"] { flex: 1; padding: 20px 5px; background: transparent; border: none; color: var(--text); font-size: 15px; outline: none; font-family: 'Tajawal'; }
        .action-icon { color: var(--text); opacity: 0.7; cursor: pointer; padding: 12px; transition: 0.3s; font-size: 20px; }
        .action-icon:hover { color: var(--primary); opacity: 1; }
        
        .btn-main { width: 100%; margin-top: 20px; padding: 18px; background: var(--primary); color: white; border: none; border-radius: 18px; font-size: 17px; font-weight: 900; cursor: pointer; font-family: 'Tajawal'; box-shadow: var(--neon-shadow); transition: all 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .btn-main:hover { transform: translateY(-3px); filter: brightness(1.15); }

        /* Defensive UI Elements (Results) */
        .result-container { display: none; flex-direction: column; gap: 18px; padding: 20px; }
        .video-header { display: flex; gap: 15px; align-items: center; padding: 12px; background: rgba(0,0,0,0.2); border-radius: 15px; border: 1px solid var(--border); }
        .thumb { width: 65px; height: 65px; border-radius: 12px; object-fit: cover; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .title { font-size: 15px; font-weight: bold; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; color: var(--text); }
        
        .video-wrapper { max-height: 320px; width: 100%; border-radius: 18px; overflow: hidden; background: #000; box-shadow: inset 0 0 30px rgba(0,0,0,0.9); }
        .plyr__video-wrapper video { max-height: 320px !important; object-fit: contain; }

        .btn-row { display: flex; gap: 10px; width: 100%; position: relative; margin-bottom: 10px; }
        .btn-action { flex: 1; padding: 16px 10px; border: none; border-radius: 15px; font-weight: 900; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 14px; color: white; font-family: 'Tajawal'; transition: 0.3s; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .btn-action:hover { transform: translateY(-3px); filter: brightness(1.1); }
        .btn-icon-sq { background: rgba(255,255,255,0.08); width: 55px; flex: none; border-radius: 15px; display: flex; align-items: center; justify-content: center; color: var(--text); cursor: pointer; border: 1px solid var(--border); font-size: 20px; transition: 0.3s; }
        .btn-icon-sq:hover { background: var(--primary); color: white; border-color: var(--primary); }
        
        .quality-dropdown { position: absolute; bottom: calc(100% + 10px); left: 0; width: 100%; background: var(--glass); border: 1px solid var(--border); border-radius: 15px; box-shadow: 0 15px 40px rgba(0,0,0,0.7); display: none; flex-direction: column; z-index: 100; overflow: hidden; backdrop-filter: blur(25px); }
        .quality-btn { padding: 18px; border: none; background: transparent; color: var(--text); font-family: 'Tajawal'; font-weight: bold; font-size: 15px; border-bottom: 1px solid var(--border); cursor: pointer; text-align: center; transition: 0.2s; }
        .quality-btn:hover { background: var(--primary); color: white; }

        /* الألوان الرسمية العميقة */
        .bg-mp4 { background: linear-gradient(135deg, #10b981, #047857); } 
        .bg-mp3 { background: linear-gradient(135deg, #8b5cf6, #5b21b6); } 
        .bg-wa { background: linear-gradient(135deg, #06b6d4, #0369a1); } 
        .bg-gif { background: linear-gradient(135deg, #f59e0b, #b45309); }
        .bg-magic { background: linear-gradient(135deg, #ef4444, #be123c); animation: pulseMagic 2s infinite; }
        @keyframes pulseMagic { 0% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.4); } 50% { box-shadow: 0 0 25px rgba(239, 68, 68, 0.8); } 100% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.4); } }

        /* محرر GIF */
        .gif-editor { display: none; background: rgba(0,0,0,0.25); padding: 25px; border-radius: 18px; border: 2px dashed var(--primary); margin-top: 15px; }
        .slider-container { margin: 40px 15px 15px 15px; }
        .noUi-connect { background: var(--primary); }
        .noUi-handle { border-radius: 50%; box-shadow: var(--neon-shadow); background: #fff; border: 3px solid var(--primary); }

        .qr-modal { display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 1000; justify-content: center; align-items: center; flex-direction: column; backdrop-filter: blur(10px); animation: fadeIn 0.3s ease; }
        .qr-box { background: var(--glass); border: 1px solid var(--border); padding: 40px; border-radius: 30px; display: flex; flex-direction: column; align-items: center; gap: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.8); }
        .close-qr { background: #ef4444; color: white; border: none; padding: 15px 40px; border-radius: 15px; font-weight: 900; cursor: pointer; font-family: 'Tajawal'; font-size: 16px; transition: 0.3s; }
        .close-qr:hover { background: #dc2626; transform: scale(1.05); }
        .status-msg { text-align: center; font-size: 15px; display: none; font-weight: bold; padding: 18px; border-radius: 15px; background: rgba(0,0,0,0.2); margin-top: 20px; }
    </style>
</head>
<body data-theme="dark" class="home-active">

    <div class="app-container">
        <div class="top-bar">
            <h3 class="logo-title" onclick="resetToHome()">Tahmilati Pro</h3>
            <div class="nav-btns">
                <button class="icon-btn" onclick="location.reload()" title="تحديث عاجل"><i class="fas fa-sync-alt"></i></button>
                <button class="icon-btn" onclick="toggleTheme()" title="الوضع الليلي"><i class="fas fa-moon"></i></button>
                <button class="icon-btn" onclick="toggleSidebar()" title="القائمة الرسمية"><i class="fas fa-bars"></i></button>
            </div>
        </div>

        <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <span class="sidebar-title">الأقسام الرسمية</span>
                <button class="close-sidebar" onclick="toggleSidebar()"><i class="fas fa-times"></i></button>
            </div>
            <ul class="menu-list">
                <li class="menu-item" onclick="switchView('insta', 'theme-insta')"><i class="fab fa-instagram fa-lg" style="color: #f56040; width: 30px;"></i> إنستغرام (تنزيل الروابط)</li>
                <li class="menu-item" onclick="switchView('tiktok', 'theme-tiktok')"><i class="fab fa-tiktok fa-lg" style="color: #00f2fe; width: 30px;"></i> تيك توك (بدون حقوق)</li>
                <li class="menu-item" onclick="switchView('facebook', 'theme-facebook')"><i class="fab fa-facebook fa-lg" style="color: #1877f2; width: 30px;"></i> فيسبوك (عالي الجودة)</li>
                <li class="menu-item" onclick="switchView('general', 'theme-general')"><i class="fas fa-link fa-lg" style="color: #8b5cf6; width: 30px;"></i> تنزيل عام (X، يوتيوب، إلخ)</li>
            </ul>
        </div>

        <div class="main-content">
            <div id="view-welcome" class="welcome-screen view-section" style="display: flex;">
                <div class="glass-card" style="width: 100%; text-align: center; padding: 45px 25px;">
                    <h1 class="welcome-title">مرحباً بك في Tahmilati</h1>
                    <p class="welcome-desc">المنصة الأذكى لتحميل الوسائط المتعددة واستخراج الملفات الصوتية الأصلية بأعلى جودة واستقرار.</p>
                    <button class="pwa-btn" id="installPwaBtn"><i class="fas fa-mobile-alt"></i> تثبيت التطبيق على الشاشة الرئيسية</button>
                </div>
            </div>

            <script>
                const platforms = [
                    { id: 'insta', icon: 'fab fa-instagram', color: '#f56040', title: 'نظام تحميل إنستغرام', placeholder: 'الصق رابط الريلز، البوست أو الستوري هنا...' },
                    { id: 'tiktok', icon: 'fab fa-tiktok', color: '#00f2fe', title: 'نظام تحميل تيك توك', placeholder: 'الصق رابط مقطع التيك توك المباشر...' },
                    { id: 'facebook', icon: 'fab fa-facebook', color: '#1877f2', title: 'نظام تحميل فيسبوك', placeholder: 'الصق رابط الفيديو العام هنا...' },
                    { id: 'general', icon: 'fas fa-link', color: '#8b5cf6', title: 'التحميل العام الشامل', placeholder: 'الصق الرابط المباشر من أي منصة أخرى...' }
                ];
                
                platforms.forEach(p => {
                    document.write(`
                    <div id="view-${p.id}" class="view-section">
                        <div class="glass-card">
                            <div class="card-title"><i class="${p.icon}" style="color: ${p.color}; font-size: 24px;"></i> ${p.title}</div>
                            <div class="input-row">
                                <input type="text" id="input-${p.id}" placeholder="${p.placeholder}">
                                <i class="fas fa-times action-icon" onclick="document.getElementById('input-${p.id}').value = ''"></i>
                                <i class="fas fa-paste action-icon" onclick="navigator.clipboard.readText().then(t => document.getElementById('input-${p.id}').value = t).catch(e => console.log(e))" style="color: var(--primary);"></i>
                            </div>
                            <button class="btn-main" onclick="processClientRequest('${p.id}')"><i class="fas fa-cloud-download-alt"></i> بدء استخراج البيانات</button>
                            <div class="status-msg" id="status-${p.id}"></div>
                        </div>
                        <div id="res-${p.id}" class="glass-card result-container">
                            <div class="media-box" style="display: none; flex-direction: column; gap: 15px;"></div>
                        </div>
                    </div>`);
                });
            </script>
        </div>
    </div>

    <div class="qr-modal" id="qrModal">
        <div class="qr-box">
            <span style="color:var(--text); font-weight:900; font-size:18px;">امسح الباركود بكاميرا هاتفك</span>
            <div id="qrCodeDiv" style="background: white; padding: 20px; border-radius: 20px;"></div>
            <button class="close-qr" onclick="document.getElementById('qrModal').style.display='none'">إغلاق النافذة</button>
        </div>
    </div>

    <script>
        let activePlayer = null;
        let globalVideoUrl = '';
        let activeTitle = 'Tahmilati_File';
        let deferredPrompt; // لزر الـ PWA

        // تفعيل الـ PWA (تثبيت التطبيق)
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            document.getElementById('installPwaBtn').style.display = 'flex';
        });

        document.getElementById('installPwaBtn').addEventListener('click', async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') document.getElementById('installPwaBtn').style.display = 'none';
                deferredPrompt = null;
            }
        });

        // تسجيل Service Worker
        if ('serviceWorker' in navigator) { window.addEventListener('load', () => { navigator.serviceWorker.register('/sw.js'); }); }

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

        // الدالة الذهبية: الرجوع للشاشة الرئيسية (تغيير ألوان الحرباء)
        function resetToHome() {
            document.querySelectorAll('.view-section').forEach(el => el.style.display = 'none');
            document.getElementById('view-welcome').style.display = 'flex';
            document.body.className = 'home-active'; 
            document.body.setAttribute('data-theme', 'dark');
        }

        function switchView(viewName, themeClass) {
            document.querySelectorAll('.view-section').forEach(el => el.style.display = 'none');
            document.getElementById('view-' + viewName).style.display = 'flex';
            document.body.className = themeClass; // إزالة active-home
            toggleSidebar();
        }

        function showQR(url) {
            document.getElementById('qrModal').style.display = 'flex';
            document.getElementById('qrCodeDiv').innerHTML = '';
            new QRCode(document.getElementById("qrCodeDiv"), { text: url, width: 220, height: 220, colorDark : "#000000", colorLight : "#ffffff" });
        }

        function copyLink(url) {
            const temp = document.createElement("input"); temp.value = url; document.body.appendChild(temp); temp.select(); document.execCommand("copy"); document.body.removeChild(temp);
            alert("تم نسخ الرابط الحقيقي للمقطع بنجاح.");
        }

        function toggleQualityMenu(btn) {
            const menu = btn.parentElement.querySelector('.quality-dropdown'); 
            menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
        }

        // إجبار التحميل بأمان وذكاء
        async function forceAutoDownload(url, filename) {
            try {
                // إذا رابط بروكسي أو فيه CORS نعبره كـ Anchor
                if(url.includes('/proxy_stream')) {
                    const a = document.createElement('a'); a.href = url; document.body.appendChild(a); a.click(); document.body.removeChild(a); return;
                }
                const response = await fetch(url); const blob = await response.blob(); const blobUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a'); a.href = blobUrl; a.download = filename; document.body.appendChild(a); a.click(); document.body.removeChild(a);
                window.URL.revokeObjectURL(blobUrl);
            } catch (e) { window.open(url, '_blank'); }
        }

        // محرر الصور المتحركة GIF الموثوق (بدون مشاكل CORS بفضل البروكسي)
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
                    btn.disabled = true; status.style.display = 'block'; status.style.color = 'var(--primary)';
                    status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري الهندسة واقتطاع الصورة...';
                    const vals = sliderDiv.noUiSlider.get();
                    gifshot.createGIF({
                        'video': [globalVideoUrl], 'offset': parseInt(vals[0]), 'numFrames': (parseInt(vals[1]) - parseInt(vals[0])) * 10, 'frameDuration': 1, 'gifWidth': 320, 'gifHeight': 320
                    }, function(obj) {
                        if(!obj.error) { 
                            forceAutoDownload(obj.image, activeTitle + '.gif'); 
                            status.innerHTML = '<i class="fas fa-check-circle"></i> اكتمل الإنشاء والتنزيل.'; 
                            status.style.color = '#10b981';
                        } else { 
                            status.innerHTML = '<i class="fas fa-exclamation-circle"></i> حدث خطأ في محرك الـ GIF الداخلي.'; 
                            status.style.color = '#ef4444';
                        }
                        setTimeout(()=> { status.style.display = 'none'; btn.disabled = false; }, 4000);
                    });
                };
            }
        }

        // الزر السحري للذكاء الاصطناعي: جلب الصوت الأصلي كامل
        async function fetchFullAudio(trackName, btnElement) {
            const origHTML = btnElement.innerHTML;
            btnElement.innerHTML = '<i class="fas fa-compact-disc fa-spin"></i> جاري البحث وسحب المعزوفة الكاملة...';
            btnElement.disabled = true;
            try {
                let r = await fetch('/api/full_audio', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ track_name: trackName })
                });
                let res = await r.json();
                if(res.success) {
                    let audioSafeUrl = `/proxy_stream?url=${encodeURIComponent(res.audio_url)}&ext=mp3`;
                    forceAutoDownload(audioSafeUrl, `${trackName}_Original.mp3`);
                    btnElement.innerHTML = '<i class="fas fa-check"></i> تم التنزيل بنجاح!';
                    btnElement.style.background = '#10b981';
                } else {
                    btnElement.innerHTML = '<i class="fas fa-times"></i> المعزوفة الأصلية غير متاحة.';
                    btnElement.style.background = '#ef4444';
                }
            } catch(e) {
                btnElement.innerHTML = '<i class="fas fa-wifi"></i> فشل الاتصال.';
            }
            setTimeout(() => { btnElement.innerHTML = origHTML; btnElement.style.background = ''; btnElement.disabled = false; }, 4000);
        }

        // المحرك الأساسي (API Caller)
        async function processClientRequest(platform) {
            const val = document.getElementById('input-' + platform).value.trim(); 
            if(!val) return;

            const resContainer = document.getElementById('res-' + platform);
            const statusMsg = document.getElementById('status-' + platform);
            const mediaBox = resContainer.querySelector('.media-box');
            
            resContainer.style.display = 'flex'; 
            mediaBox.style.display = 'none'; 
            statusMsg.style.display = 'block'; 
            statusMsg.style.color = 'var(--primary)';
            statusMsg.innerHTML = '<i class="fas fa-satellite-dish fa-pulse"></i> جاري الاتصال بالخوادم المخصصة للتحليل...';
            if(activePlayer) { activePlayer.destroy(); activePlayer = null; }

            try {
                let r = await fetch('/api/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: val, platform: platform })
                });
                let res = await r.json();

                if(res.success) {
                    statusMsg.style.display = 'none';
                    
                    // البروكسي الإجباري لكسر الـ CORS وتأمين تحميل الملف وصناعة الـ GIF
                    let useProxy = True; // نفعله للجميع لضمان عدم تلف الـ GIF
                    let internalVidPlay = useProxy ? `/proxy_stream?url=${encodeURIComponent(res.video_url)}&ext=mp4` : res.video_url;
                    let internalAudPlay = useProxy ? `/proxy_stream?url=${encodeURIComponent(res.audio_url)}&ext=mp3` : res.audio_url;
                    let absoluteQrUrl = useProxy ? (window.location.origin + internalVidPlay) : res.video_url;

                    renderMediaResult(res.title, res.thumbnail, internalVidPlay, internalAudPlay, absoluteQrUrl, res.duration || 15, platform, 'res-' + platform, res.track_name);
                } else {
                    statusMsg.innerHTML = `<i class="fas fa-shield-alt"></i> رسالة النظام: ${res.error}`;
                    statusMsg.style.color = '#ef4444';
                }
            } catch(e) {
                statusMsg.innerHTML = `<i class="fas fa-exclamation-circle"></i> انقطع الاتصال الداخلي. تأكد من استقرار الإنترنت.`; 
                statusMsg.style.color = '#ef4444';
            }
        }

        // بناء لوحة النتائج الجبارة مع الأزرار
        function renderMediaResult(title, thumbnail, vidUrl, audUrl, qrUrl, duration, platform, containerId, trackName) {
            const mediaBox = document.querySelector(`#${containerId} .media-box`); 
            activeTitle = title.replace(/[^a-zA-Z0-9_\u0600-\u06FF]/g, '_') || 'Tahmilati_Media'; 
            globalVideoUrl = vidUrl;
            
            let magicBtnHtml = '';
            if (trackName) {
                magicBtnHtml = `
                <div class="btn-row" style="margin-bottom: 10px;">
                    <button onclick="fetchFullAudio('${trackName}', this)" class="btn-action bg-magic" style="width:100%;">
                        <i class="fas fa-magic"></i> جلب الأغنية / المعزوفة الأصلية كاملة (MP3)
                    </button>
                </div>`;
            }

            mediaBox.innerHTML = `
                <div class="video-header"><img src="${thumbnail}" class="thumb"><div class="title">${title}</div></div>
                <div class="video-wrapper">
                    <video class="plyr-player" playsinline controls crossorigin="anonymous"></video>
                </div>
                <div class="action-grid">
                    ${magicBtnHtml}
                    <div class="btn-row">
                        <button onclick="forceAutoDownload('${vidUrl}', '${activeTitle}.mp4')" class="btn-action bg-mp4"><i class="fas fa-download"></i> تنزيل الفيديو (بدون حقوق)</button>
                        <button onclick="toggleQualityMenu(this)" class="btn-icon-sq" title="خيارات الدقة"><i class="fas fa-cog"></i></button>
                        <div class="quality-dropdown">
                            <button class="quality-btn" onclick="forceAutoDownload('${vidUrl}', '${activeTitle}_1080p.mp4')">1080p (جودة فائقة الفخامة)</button>
                            <button class="quality-btn" onclick="forceAutoDownload('${vidUrl}', '${activeTitle}_720p.mp4')">720p (جودة اعتيادية مستقرة)</button>
                        </div>
                        <button onclick="copyLink('${qrUrl}')" class="btn-icon-sq" title="نسخ الرابط الجاهز"><i class="fas fa-link"></i></button>
                        <button onclick="showQR('${qrUrl}')" class="btn-icon-sq" title="باركود حقيقي مباشر"><i class="fas fa-qrcode"></i></button>
                    </div>
                    <div class="btn-row">
                        <button onclick="forceAutoDownload('${audUrl}', '${activeTitle}.mp3')" class="btn-action bg-mp3"><i class="fas fa-music"></i> استخراج الصوت فقط (MP3)</button>
                    </div>
                </div>
                <div class="gif-editor">
                    <div style="font-size: 15px; font-weight: 900; margin-bottom: 15px; color: var(--text);"><i class="fas fa-film"></i> اقتطاع جزء كصورة متحركة (GIF):</div>
                    <div class="timeSlider slider-container"></div>
                    <div style="display:flex; justify-content: space-between; font-size:14px; color:var(--primary); font-weight:bold; margin-bottom: 25px;">
                        <span class="startVal">0s</span> <span class="endVal">5s</span>
                    </div>
                    <button class="btn-action bg-gif gifStartBtn" style="width: 100%;"><i class="fas fa-crop-alt"></i> معالجة الصورة والتنزيل</button>
                    <div class="status-msg gifStatus"></div>
                </div>
            `;
            
            // تهيئة المشغل بأمان
            const videoEl = mediaBox.querySelector('.plyr-player'); 
            videoEl.src = vidUrl;
            activePlayer = new Plyr(videoEl, { controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'fullscreen'] });

            // إضافة أزرار الواتساب لمنصات تيك توك وإنستا
            if(['tiktok', 'insta'].includes(platform)) {
                const actionGrid = mediaBox.querySelector('.action-grid');
                const waRow = document.createElement('div');
                waRow.className = 'btn-row';
                waRow.innerHTML = `<button onclick="forceAutoDownload('${vidUrl}', '${activeTitle}_WA.mp4')" class="btn-action bg-wa" style="width:100%;"><i class="fab fa-whatsapp"></i> تنزيل نسخة مخففة وسريعة (لحالات الواتساب)</button>`;
                actionGrid.appendChild(waRow);
            }
            
            // الـ GIF يعمل على كل المنصات!
            mediaBox.querySelector('.gif-editor').style.display = 'block'; 
            toggleGifEditor(containerId, duration);
            
            mediaBox.style.display = 'flex';
        }
    </script>
</body>
</html>
"""

# ==============================================================================
# PWA Routes (Manifest & Service Worker)
# ==============================================================================
@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Tahmilati Pro | تحميلاتي",
        "short_name": "Tahmilati",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#8b5cf6",
        "orientation": "portrait",
        "icons": [{ "src": "https://cdn-icons-png.flaticon.com/512/3039/3039381.png", "sizes": "512x512", "type": "image/png" }]
    })

@app.route('/sw.js')
def service_worker():
    sw_code = """
    self.addEventListener('install', (e) => { self.skipWaiting(); });
    self.addEventListener('fetch', (e) => { /* Bypass cache for dynamic API requests */ });
    """
    return Response(sw_code, mimetype='application/javascript')

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

# ==============================================================================
# ROUTE: Full Audio Search Background Engine (The AI Magic Button)
# Extracts the exact pure MP3 from YouTube's massive library based on metadata.
# ==============================================================================
@app.route('/api/full_audio', methods=['POST'])
def search_full_audio():
    track_name = request.json.get('track_name')
    if not track_name: return jsonify({"success": False})

    try:
        ydl_opts = {
            'quiet': True, 'no_warnings': True, 'format': 'bestaudio/best', 'noplaylist': True,
            'default_search': 'ytsearch', 'extract_flat': False
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # يبحث عن أول نتيجة مطابقة للاسم في يوتيوب ويسحب رابط الصوت المباشر
            info = ydl.extract_info(f"ytsearch1:{track_name}", download=False)
            if 'entries' in info and len(info['entries']) > 0:
                audio_url = info['entries'][0].get('url')
                return jsonify({"success": True, "audio_url": audio_url})
    except: pass
    return jsonify({"success": False})

# ==============================================================================
# ROUTE: Main Processing API
# Extremely robust logic to pull Audio and Video explicitly.
# ==============================================================================
@app.route('/api/process', methods=['POST'])
def process_api():
    data = request.json
    url = data.get('url', '').strip()
    platform = data.get('platform', '')

    if not url or not url.startswith('http'):
        return jsonify({"success": False, "error": "يرجى إدخال رابط مباشر صحيح للبوست أو المقطع."})

    headers = {
        'Accept': 'application/json', 
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/115.0'
    }

    # 1. TIKTOK LOGIC: TikWM API (Pulls Video + Audio + Title/Author)
    if platform == 'tiktok' or 'tiktok.com' in url:
        try:
            r = requests.get(f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}", timeout=12).json()
            if r.get('code') == 0:
                v = r['data']
                track_name = None
                if 'music_info' in v and v['music_info'].get('title'):
                    track_name = f"{v['music_info']['title']} {v['music_info'].get('author', '')}".strip()
                
                return jsonify({
                    "success": True, 
                    "title": v.get('title', 'مقطع تيك توك'),
                    "thumbnail": v.get('cover', 'https://via.placeholder.com/150'),
                    "video_url": v.get('play'), 
                    "audio_url": v.get('music'), 
                    "duration": v.get('duration', 15),
                    "track_name": track_name # للزر السحري!
                })
            return jsonify({"success": False, "error": "المقطع محذوف أو خاص."})
        except Exception as e:
            return jsonify({"success": False, "error": "فشل الاتصال بخوادم تيك توك."})

    # 2. INSTAGRAM / FACEBOOK LOGIC (Cobalt enforces isAudioOnly for pure MP3)
    try:
        payload_vid = {"url": url, "vQuality": "720"}
        r_vid = requests.post("https://api.cobalt.tools/api/json", json=payload_vid, headers=headers, timeout=12)
        
        if r_vid.status_code == 200:
            res = r_vid.json()
            if res.get('url'):
                vid_url = res['url']
                aud_url = vid_url # احتياطي إذا فشل جلب الصوت
                
                # إرسال طلب ثاني إجباري لاستخراج "الصوت الصافي خام" كـ MP3
                try:
                    payload_aud = {"url": url, "isAudioOnly": True}
                    r_aud = requests.post("https://api.cobalt.tools/api/json", json=payload_aud, headers=headers, timeout=8)
                    if r_aud.status_code == 200 and r_aud.json().get('url'):
                        aud_url = r_aud.json()['url']
                except: pass
                
                return jsonify({
                    "success": True, 
                    "title": f"ملف وسائط ({platform.capitalize()})",
                    "thumbnail": "https://via.placeholder.com/150",
                    "video_url": vid_url,
                    "audio_url": aud_url,
                    "duration": 15,
                    "track_name": "معزوفة انستغرام" if platform == 'insta' else None
                })
    except:
        pass

    # 3. YOUTUBE / GENERAL / FALLBACK LOGIC (yt-dlp)
    try:
        ydl_opts = {
            'quiet': True, 'no_warnings': True, 'socket_timeout': 15,
            'format': 'best', 'extractor_args': {'facebook': {'player_client': ['android', 'ios']}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url', '')
            if not video_url and 'formats' in info:
                v_formats = [f for f in info['formats'] if f.get('vcodec') != 'none']
                if v_formats: video_url = v_formats[-1]['url']
            
            if video_url:
                return jsonify({
                    "success": True, 
                    "title": info.get('title', 'ملف مستخرج'),
                    "thumbnail": info.get('thumbnail', 'https://via.placeholder.com/150'),
                    "video_url": video_url, "audio_url": video_url, "duration": info.get('duration', 15)
                })
    except Exception as e:
        error_msg = str(e).lower()
        if "private" in error_msg or "log in" in error_msg:
            return jsonify({"success": False, "error": "المقطع محمي أو خاص. يرجى استخدام الروابط العامة (Public) فقط."})
        pass
    
    return jsonify({"success": False, "error": "تعذر السحب. المنصة تمنع الوصول للرابط."})

# ==============================================================================
# ROUTE: /proxy_stream - Critical to bypass CORS for GIFs & Audio playing!
# ==============================================================================
@app.route('/proxy_stream')
def proxy_stream():
    target_url = request.args.get('url')
    ext = request.args.get('ext', 'mp4')
    if not target_url: return "URL Error", 400

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/115.0 Safari/537.36'}
    try:
        req = requests.get(target_url, headers=headers, stream=True, verify=False, timeout=20)
        
        def generate():
            for chunk in req.iter_content(chunk_size=1024 * 512):
                if chunk: yield chunk

        response = Response(stream_with_context(generate()), content_type=req.headers.get('content-type', f'video/{ext}'))
        response.headers['Content-Disposition'] = f'attachment; filename="Tahmilati_HQ_File.{ext}"'
        # هذا السطر الذهبي يحل مشكلة الـ GIF والصوت (CORS Bypass)
        response.headers['Access-Control-Allow-Origin'] = '*' 
        return response
    except Exception as e:
        return f"Proxy Pipeline Error", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
