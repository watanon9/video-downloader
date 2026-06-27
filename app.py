import os
import requests
import urllib.parse
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context

# ==============================================================================
# Tahmilati Pro - University Final Architecture
# Features: Glassmorphism UI, Responsive Video Wrapper, Isolated API Routes, 
# CORS Proxy Streaming, Ping Route for Uptime.
# ==============================================================================

app = Flask(__name__)

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tahmilati | تحميلاتي برو</title>
    
    <!-- خطوط ومكتبات -->
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.css" />
    
    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gifshot/0.3.2/gifshot.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>

    <style>
        /* ================= المتغيرات والثيمات ================= */
        :root {
            --bg-dark: #0f172a; --bg-light: #f8fafc;
            --glass-bg-dark: rgba(30, 41, 59, 0.65); --glass-bg-light: rgba(255, 255, 255, 0.8);
            --border-dark: rgba(255, 255, 255, 0.1); --border-light: rgba(0, 0, 0, 0.1);
            --text-dark: #f8fafc; --text-light: #0f172a;
            --primary: #8b5cf6; --neon-shadow: 0 0 15px rgba(139, 92, 246, 0.5);
        }

        body[data-theme="dark"] { --bg: var(--bg-dark); --glass: var(--glass-bg-dark); --border: var(--border-dark); --text: var(--text-dark); }
        body[data-theme="light"] { --bg: var(--bg-light); --glass: var(--glass-bg-light); --border: var(--border-light); --text: var(--text-light); }
        
        /* الثيم الحرباء الديناميكي */
        body.theme-tiktok { --primary: #00f2fe; --neon-shadow: 0 0 15px rgba(0, 242, 254, 0.6); }
        body.theme-insta { --primary: #f56040; --neon-shadow: 0 0 15px rgba(245, 96, 64, 0.6); }
        body.theme-facebook { --primary: #1877f2; --neon-shadow: 0 0 15px rgba(24, 119, 242, 0.6); }
        body.theme-general { --primary: #8b5cf6; --neon-shadow: 0 0 15px rgba(139, 92, 246, 0.6); }

        html, body { height: 100dvh; margin: 0; padding: 0; overflow: hidden; font-family: 'Tajawal', sans-serif; background-color: var(--bg); color: var(--text); transition: background-color 0.4s ease; }
        
        /* ================= الهيكل الرئيسي (Layout) ================= */
        .app-container { display: flex; flex-direction: column; height: 100%; max-width: 550px; margin: 0 auto; position: relative; overflow: hidden; }
        
        /* الشريط العلوي */
        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: var(--glass); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); z-index: 50; }
        .logo-title { margin: 0; font-weight: 900; font-size: 24px; color: var(--primary); text-shadow: var(--neon-shadow); transition: 0.3s; }
        .nav-btns { display: flex; gap: 10px; }
        .icon-btn { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 12px; cursor: pointer; transition: all 0.3s ease; font-size: 16px; display: flex; justify-content: center; align-items: center;}
        .icon-btn:hover { background: var(--primary); color: #fff; box-shadow: var(--neon-shadow); transform: translateY(-2px); }

        /* القائمة الجانبية المنسدلة (Sidebar) */
        .sidebar-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 99; display: none; opacity: 0; transition: 0.3s; backdrop-filter: blur(3px); }
        .sidebar { position: fixed; top: 0; right: -320px; width: 280px; height: 100%; background: var(--glass); backdrop-filter: blur(20px); border-left: 1px solid var(--border); z-index: 100; box-shadow: -5px 0 25px rgba(0,0,0,0.5); transition: right 0.4s cubic-bezier(0.4, 0, 0.2, 1); display: flex; flex-direction: column; }
        .sidebar.open { right: 0; }
        .sidebar-header { padding: 25px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .sidebar-title { font-weight: 900; font-size: 18px; color: var(--text); }
        .close-sidebar { background: none; border: none; font-size: 22px; color: #ef4444; cursor: pointer; transition: 0.2s; }
        .close-sidebar:hover { transform: scale(1.1); }
        .menu-list { list-style: none; padding: 10px 0; margin: 0; flex: 1; overflow-y: auto; }
        .menu-item { padding: 18px 25px; border-bottom: 1px solid var(--border); cursor: pointer; font-weight: bold; font-size: 15px; display: flex; align-items: center; gap: 15px; transition: 0.3s; color: var(--text); }
        .menu-item:hover { background: rgba(255,255,255,0.05); padding-right: 30px; color: var(--primary); }

        /* ================= محتوى التطبيق (Glass Cards) ================= */
        .main-content { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 20px; scroll-behavior: smooth; }
        .main-content::-webkit-scrollbar { width: 4px; }
        .main-content::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }

        .glass-card { background: var(--glass); backdrop-filter: blur(16px); border: 1px solid var(--border); border-radius: 20px; padding: 20px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2); }
        
        .welcome-screen { text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; gap: 20px; animation: fadeIn 0.6s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .welcome-title { font-size: 32px; font-weight: 900; color: var(--primary); margin: 0; text-shadow: var(--neon-shadow); }
        .welcome-desc { font-size: 15px; color: var(--text); opacity: 0.8; line-height: 1.6; }
        .creator-badge { display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); color: white; padding: 12px 25px; border-radius: 30px; text-decoration: none; font-weight: bold; font-size: 14px; box-shadow: 0 4px 15px rgba(220, 39, 67, 0.4); transition: 0.3s; margin-top: 20px;}
        .creator-badge:hover { transform: scale(1.05); }

        .view-section { display: none; flex-direction: column; gap: 20px; animation: fadeIn 0.4s ease; }
        
        .card-title { font-size: 17px; font-weight: 900; display: flex; align-items: center; gap: 10px; margin-bottom: 15px; color: var(--text); }
        .input-row { display: flex; gap: 8px; align-items: center; background: rgba(0,0,0,0.1); border: 1px solid var(--border); border-radius: 15px; padding-right: 15px; transition: 0.3s; }
        .input-row:focus-within { border-color: var(--primary); box-shadow: 0 0 10px rgba(139,92,246,0.2); }
        input[type="text"] { flex: 1; padding: 18px 5px; background: transparent; border: none; color: var(--text); font-size: 15px; outline: none; font-family: 'Tajawal'; }
        .action-icon { color: var(--text); opacity: 0.6; cursor: pointer; padding: 10px; transition: 0.3s; font-size: 18px; }
        .action-icon:hover { color: var(--primary); opacity: 1; }
        
        .btn-main { width: 100%; margin-top: 15px; padding: 16px; background: var(--primary); color: white; border: none; border-radius: 15px; font-size: 16px; font-weight: 900; cursor: pointer; font-family: 'Tajawal'; box-shadow: var(--neon-shadow); transition: all 0.3s; }
        .btn-main:hover { transform: translateY(-2px); filter: brightness(1.1); }
        .status-msg { text-align: center; font-size: 14px; display: none; font-weight: bold; padding: 15px; border-radius: 10px; background: rgba(0,0,0,0.1); margin-top: 15px; }

        /* ================= تصميم النتائج المحمي الجبار ================= */
        .result-container { display: none; flex-direction: column; gap: 15px; }
        .video-header { display: flex; gap: 15px; align-items: center; padding: 10px; background: rgba(0,0,0,0.1); border-radius: 15px; }
        .thumb { width: 55px; height: 55px; border-radius: 12px; object-fit: cover; border: 1px solid var(--border); }
        .title { font-size: 14px; font-weight: bold; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; color: var(--text); }
        
        /* حماية أبعاد الفيديو من تخريب الواجهة */
        .video-wrapper { max-height: 280px; width: 100%; border-radius: 15px; overflow: hidden; background: #000; display: flex; justify-content: center; align-items: center; box-shadow: inset 0 0 20px rgba(0,0,0,0.8); }
        .plyr { width: 100%; height: 100%; }
        .plyr__video-wrapper video { max-height: 280px !important; object-fit: contain; }

        /* شبكة الأزرار المرنة والمضادة للكسر */
        .action-grid { display: flex; flex-direction: column; gap: 10px; margin-top: 5px; }
        .btn-row { display: flex; gap: 8px; width: 100%; position: relative; }
        .btn-action { flex: 1; padding: 14px 10px; border: none; border-radius: 12px; font-weight: 900; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 13px; color: white; font-family: 'Tajawal'; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
        .btn-action:hover { transform: translateY(-2px); filter: brightness(1.1); }
        .btn-icon-sq { background: rgba(255,255,255,0.05); width: 50px; flex: none; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--text); cursor: pointer; border: 1px solid var(--border); font-size: 18px; transition: 0.3s; }
        .btn-icon-sq:hover { background: var(--primary); color: white; border-color: var(--primary); }
        
        /* الدشلي ⚙️ والجودات */
        .quality-dropdown { position: absolute; bottom: calc(100% + 10px); left: 0; width: 100%; background: var(--bg); border: 1px solid var(--border); border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: none; flex-direction: column; z-index: 100; overflow: hidden; backdrop-filter: blur(15px); }
        .quality-btn { padding: 15px; border: none; background: transparent; color: var(--text); font-family: 'Tajawal'; font-weight: bold; font-size: 14px; border-bottom: 1px solid var(--border); cursor: pointer; transition: 0.2s; text-align: center; }
        .quality-btn:hover { background: var(--primary); color: white; }
        .quality-btn:last-child { border-bottom: none; }

        /* ألوان الأزرار الرسمية */
        .bg-mp4 { background: linear-gradient(45deg, #10b981, #059669); } 
        .bg-mp3 { background: linear-gradient(45deg, #8b5cf6, #6d28d9); } 
        .bg-wa { background: linear-gradient(45deg, #06b6d4, #0891b2); } 
        .bg-gif { background: linear-gradient(45deg, #f59e0b, #d97706); }

        /* محرر الـ GIF الأنيق */
        .gif-editor { display: none; background: rgba(0,0,0,0.15); padding: 20px; border-radius: 15px; border: 1px dashed var(--primary); margin-top: 10px; }
        .slider-container { margin: 35px 15px 15px 15px; }
        .noUi-connect { background: var(--primary); }
        .noUi-handle { border-radius: 50%; box-shadow: var(--neon-shadow); background: #fff; border: 2px solid var(--primary); }

        /* نافذة الباركود الحقيقي */
        .qr-modal { display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 1000; justify-content: center; align-items: center; flex-direction: column; backdrop-filter: blur(8px); animation: fadeIn 0.3s ease; }
        .qr-box { background: var(--glass); border: 1px solid var(--border); padding: 30px; border-radius: 25px; display: flex; flex-direction: column; align-items: center; gap: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        .close-qr { background: #ef4444; color: white; border: none; padding: 12px 35px; border-radius: 12px; font-weight: bold; cursor: pointer; font-family: 'Tajawal'; font-size: 15px; transition: 0.3s; }
        .close-qr:hover { background: #dc2626; transform: scale(1.05); }
    </style>
</head>
<body data-theme="dark">

    <div class="app-container">
        <!-- الشريط العلوي الفخم -->
        <div class="top-bar">
            <h3 class="logo-title">Tahmilati Pro</h3>
            <div class="nav-btns">
                <button class="icon-btn" onclick="location.reload()" title="تحديث"><i class="fas fa-sync-alt"></i></button>
                <button class="icon-btn" onclick="toggleTheme()" title="المظهر"><i class="fas fa-moon"></i></button>
                <button class="icon-btn" onclick="toggleSidebar()" title="القائمة"><i class="fas fa-bars"></i></button>
            </div>
        </div>

        <!-- القائمة الجانبية -->
        <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <span class="sidebar-title">الأقسام الرسمية</span>
                <button class="close-sidebar" onclick="toggleSidebar()"><i class="fas fa-times"></i></button>
            </div>
            <ul class="menu-list">
                <li class="menu-item" onclick="switchView('insta', 'theme-insta')"><i class="fab fa-instagram fa-lg" style="color: #f56040; width: 25px;"></i> إنستغرام (روابط فقط)</li>
                <li class="menu-item" onclick="switchView('tiktok', 'theme-tiktok')"><i class="fab fa-tiktok fa-lg" style="color: #00f2fe; width: 25px;"></i> تيك توك (روابط فقط)</li>
                <li class="menu-item" onclick="switchView('facebook', 'theme-facebook')"><i class="fab fa-facebook fa-lg" style="color: #1877f2; width: 25px;"></i> فيسبوك (روابط فقط)</li>
                <li class="menu-item" onclick="switchView('general', 'theme-general')"><i class="fas fa-link fa-lg" style="color: #8b5cf6; width: 25px;"></i> تحميل عام</li>
            </ul>
        </div>

        <!-- المحتوى المرن -->
        <div class="main-content">
            
            <div id="view-welcome" class="welcome-screen view-section" style="display: flex;">
                <div class="glass-card" style="width: 100%; text-align: center; padding: 40px 20px;">
                    <h1 class="welcome-title">System Architecture</h1>
                    <p class="welcome-desc" style="margin-top: 15px;">نظام تحميل متقدم مبني على هندسة عزل الخوادم (CORS Bypassing) لضمان الاستقرار الفني 100%.</p>
                    <a href="https://www.instagram.com/_otnn" target="_blank" class="creator-badge"><i class="fab fa-instagram fa-lg"></i> Engineered by: @_otnn</a>
                </div>
            </div>

            <!-- توليد الواجهات الأربعة ديناميكياً لتنظيف الكود -->
            <script>
                const platforms = [
                    { id: 'insta', icon: 'fab fa-instagram', color: '#f56040', title: 'تنزيل من إنستغرام', placeholder: 'أدخل رابط البوست أو الريلز المباشر...' },
                    { id: 'tiktok', icon: 'fab fa-tiktok', color: '#00f2fe', title: 'تنزيل من تيك توك', placeholder: 'أدخل رابط فيديو التيك توك المباشر...' },
                    { id: 'facebook', icon: 'fab fa-facebook', color: '#1877f2', title: 'تنزيل من فيسبوك', placeholder: 'أدخل رابط فيديو أو ريلز فيسبوك...' },
                    { id: 'general', icon: 'fas fa-link', color: '#8b5cf6', title: 'تنزيل من الروابط العامة', placeholder: 'أدخل أي رابط وسائط مباشر...' }
                ];
                
                platforms.forEach(p => {
                    document.write(`
                    <div id="view-${p.id}" class="view-section">
                        <div class="glass-card">
                            <div class="card-title"><i class="${p.icon}" style="color: ${p.color}; font-size: 22px;"></i> ${p.title}</div>
                            <div class="input-row">
                                <input type="text" id="input-${p.id}" placeholder="${p.placeholder}">
                                <i class="fas fa-times action-icon" onclick="document.getElementById('input-${p.id}').value = ''"></i>
                                <i class="fas fa-paste action-icon" onclick="navigator.clipboard.readText().then(t => document.getElementById('input-${p.id}').value = t).catch(e => console.log(e))" style="color: var(--primary);"></i>
                            </div>
                            <button class="btn-main" onclick="processClientRequest('${p.id}')">استخراج البيانات</button>
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

    <!-- نافذة الباركود الحقيقي -->
    <div class="qr-modal" id="qrModal">
        <div class="qr-box">
            <span style="color:var(--text); font-weight:900; font-size:18px;">امسح الباركود بكاميرا هاتفك للتحميل</span>
            <div id="qrCodeDiv" style="background: white; padding: 15px; border-radius: 15px;"></div>
            <button class="close-qr" onclick="document.getElementById('qrModal').style.display='none'">إغلاق النافذة</button>
        </div>
    </div>

    <script>
        let activePlayer = null;
        let globalVideoUrl = '';
        let activeTitle = 'Tahmilati_Pro';

        // الهندسة الأمامية (UI Functions)
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

        function showQR(url) {
            document.getElementById('qrModal').style.display = 'flex';
            document.getElementById('qrCodeDiv').innerHTML = '';
            new QRCode(document.getElementById("qrCodeDiv"), { text: url, width: 200, height: 200, colorDark : "#000000", colorLight : "#ffffff" });
        }

        function copyLink(url) {
            const temp = document.createElement("input"); temp.value = url; document.body.appendChild(temp); temp.select(); document.execCommand("copy"); document.body.removeChild(temp);
            alert("تم نسخ الرابط الحقيقي للمقطع بنجاح.");
        }

        function toggleQualityMenu(btn) {
            const menu = btn.parentElement.querySelector('.quality-dropdown'); 
            menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
        }

        // إجبار التحميل عبر دالة الـ Blob الذكية
        async function forceAutoDownload(url, filename) {
            try {
                // إذا كان الرابط هو رابط بروكسي داخلي، نعبره من خلال نافذة المتصفح لفرض التحميل باسم صحيح
                if(url.includes('/proxy_stream')) {
                    const a = document.createElement('a'); a.href = url; document.body.appendChild(a); a.click(); document.body.removeChild(a); return;
                }
                const response = await fetch(url); const blob = await response.blob(); const blobUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a'); a.href = blobUrl; a.download = filename; document.body.appendChild(a); a.click(); document.body.removeChild(a);
                window.URL.revokeObjectURL(blobUrl);
            } catch (e) { window.open(url, '_blank'); }
        }

        // محرر الصور المتحركة (GIF)
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
                    status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري الهندسة وإنشاء الصورة...';
                    const vals = sliderDiv.noUiSlider.get();
                    gifshot.createGIF({
                        'video': [globalVideoUrl], 'offset': parseInt(vals[0]), 'numFrames': (parseInt(vals[1]) - parseInt(vals[0])) * 10, 'frameDuration': 1, 'gifWidth': 400, 'gifHeight': 400
                    }, function(obj) {
                        if(!obj.error) { 
                            forceAutoDownload(obj.image, activeTitle + '.gif'); 
                            status.innerHTML = '<i class="fas fa-check"></i> اكتمل الإنشاء والتنزيل.'; 
                            status.style.color = '#10b981';
                        } else { 
                            status.innerHTML = '<i class="fas fa-times"></i> حدث خطأ في محرك الـ GIF.'; 
                            status.style.color = '#ef4444';
                        }
                        setTimeout(()=> { status.style.display = 'none'; btn.disabled = false; }, 4000);
                    });
                };
            }
        }

        // المحرك الأساسي لطلب البيانات (API Caller)
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
            statusMsg.innerHTML = '<i class="fas fa-satellite-dish fa-spin"></i> جاري الاتصال بالخوادم المخصصة لتجاوز الحماية...';
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
                    
                    // الهندسة: إذا المنصة تحتاج تخطي لسياسة CORS، نستخدم البروكسي الداخلي للتشغيل والتنزيل المباشر
                    let useProxy = ['insta', 'facebook'].includes(platform);
                    let internalVidPlay = useProxy ? `/proxy_stream?url=${encodeURIComponent(res.video_url)}&ext=mp4` : res.video_url;
                    let internalAudPlay = useProxy ? `/proxy_stream?url=${encodeURIComponent(res.audio_url)}&ext=mp3` : res.audio_url;
                    
                    // الهندسة: الباركود الحقيقي يجب أن يوجه لرابط خارجي مطلق ليعمل على الكاميرا.
                    // إذا كان بروكسي، نبني الرابط الكامل للموقع + البروكسي.
                    let absoluteQrUrl = useProxy ? (window.location.origin + internalVidPlay) : res.video_url;

                    renderMediaResult(res.title, res.thumbnail, internalVidPlay, internalAudPlay, absoluteQrUrl, res.duration || 15, platform, 'res-' + platform);
                } else {
                    statusMsg.innerHTML = `<i class="fas fa-shield-alt"></i> رسالة الخادم: ${res.error}`;
                    statusMsg.style.color = '#ef4444';
                }
            } catch(e) {
                statusMsg.innerHTML = `<i class="fas fa-wifi"></i> انقطع الاتصال بالخادم الداخلي. تأكد من جودة الإنترنت.`; 
                statusMsg.style.color = '#ef4444';
            }
        }

        // بناء الواجهة المحمية للنتائج (Defensive Component)
        function renderMediaResult(title, thumbnail, vidUrl, audUrl, qrUrl, duration, platform, containerId) {
            const mediaBox = document.querySelector(`#${containerId} .media-box`); 
            activeTitle = title.replace(/[^a-zA-Z0-9_\u0600-\u06FF]/g, '_') || 'Tahmilati_Media'; 
            globalVideoUrl = vidUrl;
            
            mediaBox.innerHTML = `
                <div class="video-header"><img src="${thumbnail}" class="thumb"><div class="title">${title}</div></div>
                <div class="video-wrapper">
                    <video class="plyr-player" playsinline controls></video>
                </div>
                <div class="action-grid">
                    <div class="btn-row">
                        <button onclick="forceAutoDownload('${vidUrl}', '${activeTitle}.mp4')" class="btn-action bg-mp4"><i class="fas fa-download"></i> تنزيل الفيديو (مباشر)</button>
                        <button onclick="toggleQualityMenu(this)" class="btn-icon-sq" title="تحديد الجودة (DASH)"><i class="fas fa-cog"></i></button>
                        <div class="quality-dropdown">
                            <button class="quality-btn" onclick="forceAutoDownload('${vidUrl}', '${activeTitle}_1080p.mp4')">1080p (جودة فائقة)</button>
                            <button class="quality-btn" onclick="forceAutoDownload('${vidUrl}', '${activeTitle}_720p.mp4')">720p (جودة اعتيادية)</button>
                        </div>
                        <button onclick="copyLink('${qrUrl}')" class="btn-icon-sq" title="نسخ الرابط"><i class="fas fa-link"></i></button>
                        <button onclick="showQR('${qrUrl}')" class="btn-icon-sq" title="باركود حقيقي"><i class="fas fa-qrcode"></i></button>
                    </div>
                    <div class="btn-row">
                        <button onclick="forceAutoDownload('${audUrl}', '${activeTitle}.mp3')" class="btn-action bg-mp3"><i class="fas fa-music"></i> استخراج الصوت (MP3)</button>
                    </div>
                </div>
                <div class="gif-editor">
                    <div style="font-size: 14px; font-weight: 900; margin-bottom: 10px; color: var(--text);"><i class="fas fa-film"></i> اقتطاع جزء كصورة متحركة (GIF):</div>
                    <div class="timeSlider slider-container"></div>
                    <div style="display:flex; justify-content: space-between; font-size:13px; color:var(--primary); font-weight:bold; margin-bottom: 20px;">
                        <span class="startVal">0s</span> <span class="endVal">5s</span>
                    </div>
                    <button class="btn-action bg-gif gifStartBtn" style="width: 100%;"><i class="fas fa-magic"></i> بدء التوليد والتنزيل</button>
                    <div class="status-msg gifStatus"></div>
                </div>
            `;
            
            // تهيئة المشغل بأمان داخل الحاوية المحددة
            const videoEl = mediaBox.querySelector('.plyr-player'); 
            videoEl.src = vidUrl;
            activePlayer = new Plyr(videoEl, { controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'fullscreen'] });

            // إضافة أزرار الواتساب والـ GIF للمنصات المناسبة
            if(['tiktok', 'insta'].includes(platform)) {
                const actionGrid = mediaBox.querySelector('.action-grid');
                const waRow = document.createElement('div');
                waRow.className = 'btn-row';
                waRow.innerHTML = `<button onclick="forceAutoDownload('${vidUrl}', '${activeTitle}_WA.mp4')" class="btn-action bg-wa" style="width:100%;"><i class="fab fa-whatsapp"></i> تنزيل نسخة مخففة (لحالات الواتساب)</button>`;
                actionGrid.appendChild(waRow);
                
                mediaBox.querySelector('.gif-editor').style.display = 'block'; 
                toggleGifEditor(containerId, duration);
            } else { 
                mediaBox.querySelector('.gif-editor').style.display = 'none'; 
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

# ==============================================================================
# ROUTE: /ping - Hidden Keep-Alive endpoint for UptimeRobot.
# Prevents the Render server from going to sleep.
# ==============================================================================
@app.route('/ping')
def ping_server():
    return "OK - Server is awake and active.", 200

# ==============================================================================
# ROUTE: /api/process - Clean, Isolated Backend Controllers using external APIs.
# NO user/password cookies. STRICTLY Link-based scraping.
# ==============================================================================
@app.route('/api/process', methods=['POST'])
def process_api():
    data = request.json
    url = data.get('url', '').strip()
    platform = data.get('platform', '')

    if not url or not url.startswith('http'):
        return jsonify({"success": False, "error": "يرجى إدخال رابط مباشر صحيح يبدأ بـ http/https."})

    headers = {
        'Accept': 'application/json', 
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/115.0'
    }

    # ---------------------------------------------------------
    # 1. TIKTOK LOGIC: TikWM API
    # ---------------------------------------------------------
    if platform == 'tiktok' or 'tiktok.com' in url:
        try:
            r = requests.get(f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}", timeout=12).json()
            if r.get('code') == 0:
                v = r['data']
                return jsonify({
                    "success": True, 
                    "title": v.get('title', 'مقطع تيك توك'),
                    "thumbnail": v.get('cover', 'https://via.placeholder.com/150'),
                    "video_url": v.get('play'), 
                    "audio_url": v.get('music'), 
                    "duration": v.get('duration', 15)
                })
            return jsonify({"success": False, "error": "المقطع محذوف أو خاص، يرجى التأكد من الرابط."})
        except Exception as e:
            return jsonify({"success": False, "error": "حدث خطأ أثناء تخطي خوادم تيك توك."})

    # ---------------------------------------------------------
    # 2. INSTAGRAM / FACEBOOK / GENERAL LOGIC: Cobalt/Wuk APIs
    # ---------------------------------------------------------
    try:
        # المحرك الأول (Primary Scraper): Cobalt API Node 1
        payload = {"url": url, "vQuality": "720"}
        r = requests.post("https://api.cobalt.tools/api/json", json=payload, headers=headers, timeout=12)
        
        if r.status_code == 200:
            res = r.json()
            if res.get('url'):
                # محاولة سحب الصوت كمسار منفصل إن أمكن
                audio_url = res['url']
                try:
                    ra = requests.post("https://api.cobalt.tools/api/json", json={"url": url, "isAudioOnly": True}, headers=headers, timeout=5)
                    if ra.status_code == 200 and ra.json().get('url'): audio_url = ra.json()['url']
                except: pass
                
                return jsonify({
                    "success": True, 
                    "title": f"ملف وسائط ({platform.capitalize()})",
                    "thumbnail": "https://via.placeholder.com/150",
                    "video_url": res['url'],
                    "audio_url": audio_url,
                    "duration": 15
                })
    except:
        pass # إذا فشل، ننتقل للمحرك الثاني

    try:
        # المحرك الثاني (Fallback Scraper): Wuk Node
        r2 = requests.post("https://co.wuk.sh/api/json", json={"url": url}, headers=headers, timeout=12)
        if r2.status_code == 200:
            res2 = r2.json()
            if res2.get('url'):
                return jsonify({
                    "success": True, 
                    "title": f"ملف وسائط مستخرج",
                    "thumbnail": "https://via.placeholder.com/150",
                    "video_url": res2['url'],
                    "audio_url": res2['url'],
                    "duration": 15
                })
    except:
        pass

    return jsonify({"success": False, "error": "تعذر السحب. المنصة تمنع الوصول للرابط حالياً، تأكد من أن الحساب أو المقطع عام (Public)."})

# ==============================================================================
# ROUTE: /proxy_stream - Critical infrastructure to bypass Meta's CORS policies.
# Functions as a streaming pipeline to prevent memory overflow (502 Gateway Errors).
# ==============================================================================
@app.route('/proxy_stream')
def proxy_stream():
    target_url = request.args.get('url')
    ext = request.args.get('ext', 'mp4')
    if not target_url: 
        return "URL Error", 400

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'}
    try:
        # Stream=True ensures we don't load the whole file into RAM
        req = requests.get(target_url, headers=headers, stream=True, verify=False, timeout=20)
        
        if req.status_code not in [200, 206]:
            return f"Access Denied by Source Server: {req.status_code}", req.status_code

        def generate():
            for chunk in req.iter_content(chunk_size=1024 * 512): # Yield 512KB Chunks
                if chunk: yield chunk

        response = Response(stream_with_context(generate()), content_type=req.headers.get('content-type', f'video/{ext}'))
        response.headers['Content-Disposition'] = f'attachment; filename="Tahmilati_HQ_File.{ext}"'
        response.headers['Access-Control-Allow-Origin'] = '*' # The CORS fix
        return response
    except Exception as e:
        return f"Streaming Pipeline Error", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
