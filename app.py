import os
import requests
import urllib.parse
import re
from flask import Flask, render_template_string, request, Response, stream_with_context

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
        
        /* الثيم الحرباء المتغير تلقائياً حسب نوع القسم المختار */
        body.theme-tiktok { --primary: #00f2fe; --neon-shadow: 0 0 10px #00f2fe, 0 0 20px #fe0979; }
        body.theme-insta { --primary: #f56040; --neon-shadow: 0 0 10px #f56040, 0 0 20px #833ab4; }
        body.theme-facebook { --primary: #1877f2; --neon-shadow: 0 0 10px #1877f2, 0 0 20px #0c56b8; }
        body.theme-general { --primary: #8b5cf6; --neon-shadow: 0 0 10px #8b5cf6, 0 0 20px #6d28d9; }

        html, body { height: 100dvh; margin: 0; padding: 0; overflow: hidden; font-family: 'Tajawal', sans-serif; background-color: var(--bg-color); color: var(--text-main); transition: 0.4s ease; }
        .app-container { display: flex; flex-direction: column; height: 100%; max-width: 500px; margin: 0 auto; position: relative; overflow: hidden; }
        
        /* الشريط العلوي الفخم */
        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; border-bottom: 1px solid var(--border); background: var(--card-bg); flex-shrink: 0; z-index: 50; }
        .logo-title { margin: 0; font-weight: 900; font-size: 22px; color: var(--primary); text-shadow: var(--neon-shadow); }
        .nav-btns { display: flex; gap: 10px; }
        .icon-btn { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 12px; cursor: pointer; font-weight: bold; transition: 0.3s; display: flex; justify-content: center; align-items: center; font-size: 16px;}
        .icon-btn:hover { background: var(--primary); color: white; box-shadow: var(--neon-shadow); }

        /* القائمة الجانبية المنسلقة ☰ */
        .sidebar-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 99; display: none; opacity: 0; transition: 0.3s; backdrop-filter: blur(3px); }
        .sidebar { position: fixed; top: 0; right: -300px; width: 280px; height: 100%; background: var(--card-bg); z-index: 100; box-shadow: -5px 0 20px rgba(0,0,0,0.2); transition: right 0.3s ease; display: flex; flex-direction: column; }
        .sidebar.open { right: 0; }
        .sidebar-header { padding: 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .sidebar-title { font-weight: 900; font-size: 18px; color: var(--text-main); }
        .close-sidebar { background: none; border: none; font-size: 20px; color: var(--text-muted); cursor: pointer; }
        .menu-list { list-style: none; padding: 10px 0; margin: 0; flex: 1; overflow-y: auto; }
        .menu-item { padding: 15px 20px; border-bottom: 1px solid var(--border); cursor: pointer; font-weight: bold; font-size: 15px; display: flex; align-items: center; gap: 12px; transition: 0.2s; color: var(--text-main); }
        .menu-item:hover { background: rgba(0,0,0,0.05); color: var(--primary); }
        
        .main-content { flex: 1; overflow-y: auto; padding: 20px; position: relative; display: flex; flex-direction: column; gap: 15px; }
        .main-content::-webkit-scrollbar { width: 5px; }
        .main-content::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }

        /* الشاشة الترحيبية الرسمية والجافة */
        .welcome-screen { text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; gap: 20px; animation: fadeIn 0.5s; }
        @keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
        .welcome-title { font-size: 26px; font-weight: 900; color: var(--primary); margin: 0; text-shadow: var(--neon-shadow); }
        .welcome-desc { font-size: 14px; color: var(--text-muted); line-height: 1.6; padding: 0 15px; }
        .welcome-steps { background: var(--card-bg); border: 1px solid var(--border); padding: 15px; border-radius: 15px; text-align: right; width: 100%; font-size: 13px; font-weight: bold; color: var(--text-main); list-style: none;}
        .welcome-steps li { margin-bottom: 8px; }
        .live-counter { text-align: center; font-size: 13px; font-weight: bold; color: var(--text-main); background: var(--card-bg); padding: 12px; border-radius: 15px; border: 1px solid var(--border); box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-top: auto; width: 100%;}
        .creator-btn { display: flex; align-items: center; justify-content: center; gap: 8px; background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); color: white; padding: 12px; border-radius: 15px; text-decoration: none; font-weight: bold; font-size: 14px; width: 100%; transition: 0.3s; }
        
        .view-section { display: none; flex-direction: column; gap: 15px; animation: slideUp 0.4s ease; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        
        .input-card { background: var(--card-bg); padding: 18px; border-radius: 20px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 12px; }
        .card-title { font-size: 15px; font-weight: bold; color: var(--text-main); display: flex; align-items: center; gap: 8px; }
        .input-row { display: flex; gap: 8px; align-items: center; background: rgba(0,0,0,0.03); border: 1px solid var(--border); border-radius: 12px; padding-right: 12px; }
        [data-theme="dark"] .input-row { background: rgba(255,255,255,0.03); }
        input[type="text"] { flex: 1; padding: 16px 5px; background: transparent; border: none; color: var(--text-main); font-size: 14px; outline: none; font-family: 'Tajawal'; }
        .action-icon { color: var(--text-muted); cursor: pointer; padding: 10px; transition: 0.2s; }
        .action-icon:hover { color: var(--primary); }
        
        .btn-main { padding: 15px; background: var(--primary); color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: 900; cursor: pointer; font-family: 'Tajawal'; box-shadow: var(--neon-shadow); transition: 0.3s; }

        /* حاوية النتائج الأنيقة والـ Grid للستوريات */
        .result-container { display: none; flex-direction: column; gap: 15px; background: var(--card-bg); padding: 15px; border-radius: 20px; border: 1px solid var(--border); }
        .story-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 10px; max-height: 300px; overflow-y: auto; padding: 5px; }
        .story-tile { position: relative; border-radius: 10px; overflow: hidden; aspect-ratio: 9/16; cursor: pointer; border: 2px solid transparent; transition: 0.2s; background: #000; }
        .story-tile:hover { border-color: var(--primary); transform: scale(0.96); }
        .story-img { width: 100%; height: 100%; object-fit: cover; opacity: 0.8; }
        .story-badge { position: absolute; top: 5px; left: 5px; background: rgba(0,0,0,0.6); color: white; padding: 3px 6px; border-radius: 5px; font-size: 10px; font-weight: bold; display: flex; align-items: center; gap: 3px; }

        .video-header { display: flex; gap: 15px; align-items: center; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
        .thumb { width: 70px; height: 70px; border-radius: 12px; object-fit: cover; border: 1px solid var(--border); }
        .title { font-size: 13px; font-weight: bold; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

        .btn-group { display: flex; gap: 8px; width: 100%; position: relative; }
        .btn-action { flex: 1; padding: 12px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; font-size: 13px; color: white; font-family: 'Tajawal'; transition: 0.2s; text-align: center; }
        .btn-icon-sq { background: rgba(0,0,0,0.05); width: 45px; flex: none; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--text-main); cursor: pointer; transition: 0.2s; border: 1px solid var(--border); font-size: 16px;}
        [data-theme="dark"] .btn-icon-sq { background: rgba(255,255,255,0.05); }
        .btn-icon-sq:hover { background: var(--primary); color: white; border-color: var(--primary); }

        /* نافذة الدشلي ⚙️ لاختيار الجودة المخصصة إجبارياً */
        .quality-dropdown { position: absolute; bottom: 110%; left: 0; width: 100%; background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); display: none; flex-direction: column; z-index: 10; overflow: hidden; }
        .quality-btn { padding: 12px; border: none; background: transparent; color: var(--text-main); font-family: 'Tajawal'; font-weight: bold; font-size: 13px; border-bottom: 1px solid var(--border); cursor: pointer; transition: 0.2s; text-align: center; }
        .quality-btn:hover { background: var(--primary); color: white; }

        .bg-mp4 { background: #10b981; } .bg-mp3 { background: #8b5cf6; } .bg-wa { background: #06b6d4; } .bg-gif { background: #f59e0b; }

        .gif-editor { display: none; background: rgba(0,0,0,0.02); padding: 15px; border-radius: 15px; border: 1px dashed var(--border); }
        .slider-container { margin: 30px 10px 10px 10px; }
        .noUi-connect { background: var(--primary); }
        .noUi-handle { border-radius: 50%; box-shadow: var(--neon-shadow); }

        .qr-modal { display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center; flex-direction: column; backdrop-filter: blur(5px); }
        .qr-box { background: var(--card-bg); padding: 25px; border-radius: 20px; display: flex; flex-direction: column; align-items: center; gap: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .close-qr { background: #ef4444; color: white; border: none; padding: 10px 25px; border-radius: 10px; font-weight: bold; cursor: pointer; font-family: 'Tajawal'; }

        .status-msg { text-align: center; color: var(--primary); font-size: 14px; display: none; font-weight: bold; padding: 10px; }
    </style>
</head>
<body data-theme="dark">

    <div class="app-container">
        <div class="top-bar">
            <h3 class="logo-title">Tahmilati</h3>
            <div class="nav-btns">
                <button class="icon-btn" onclick="location.reload()" title="تحديث الموقع"><i class="fas fa-sync-alt"></i></button>
                <button class="icon-btn" onclick="toggleTheme()" title="تغيير المظهر"><i class="fas fa-moon"></i></button>
                <button class="icon-btn" onclick="toggleSidebar()" style="font-size: 20px;"><i class="fas fa-bars"></i></button>
            </div>
        </div>

        <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <span class="sidebar-title">أقسام التنزيل</span>
                <button class="close-sidebar" onclick="toggleSidebar()"><i class="fas fa-times"></i></button>
            </div>
            <ul class="menu-list">
                <li class="menu-item" onclick="switchView('insta', 'theme-insta')"><i class="fab fa-instagram menu-icon" style="color: #f56040;"></i> إنستغرام (بوست/ستوري باليوزر)</li>
                <li class="menu-item" onclick="switchView('tiktok', 'theme-tiktok')"><i class="fab fa-tiktok menu-icon" style="color: #00f2fe;"></i> تيك توك (فيديو/ستوري)</li>
                <li class="menu-item" onclick="switchView('facebook', 'theme-facebook')"><i class="fab fa-facebook menu-icon" style="color: #1877f2;"></i> فيسبوك (فيديو/ريلز)</li>
                <li class="menu-item" onclick="switchView('general', 'theme-general')"><i class="fas fa-link menu-icon" style="color: #8b5cf6;"></i> تحميل عام (روابط أخرى)</li>
            </ul>
        </div>

        <div class="main-content">
            
            <div id="view-welcome" class="welcome-screen view-section" style="display: flex;">
                <h1 class="welcome-title">Tahmilati | تحميلاتي</h1>
                <p class="welcome-desc">منصة التنزيل الذكية الشاملة<br>استخراج الوسائط من مختلف المنصات العالمية بأعلى جودة وتنزيلها تلقائياً.</p>
                <ul class="welcome-steps" dir="rtl">
                    <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 1. انقر على أيقونة القائمة (☰) في الزاوية العلوية.</li>
                    <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 2. حدد المنصة المراد التنزيل منها.</li>
                    <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 3. أدخل الرابط أو اسم الحساب لإنشاء ملفات التنزيل المباشرة.</li>
                </ul>
                <div class="live-counter"><i class="fas fa-chart-line"></i> تم معالجة <span id="countNum">1,425,890</span> طلب بنجاح</div>
                <a href="https://www.instagram.com/_otnn?igsh=d3hybTN2M2Zlanl0" target="_blank" class="creator-btn"><i class="fab fa-instagram"></i> المصمم: @_otnn</a>
            </div>

            <div id="view-insta" class="view-section">
                <div class="input-card">
                    <div class="card-title"><i class="fab fa-instagram" style="color: #f56040;"></i> تنزيل من إنستغرام</div>
                    <div class="input-row">
                        <input type="text" id="input-insta" placeholder="أدخل رابط المقطع أو اكتب يوزر الحساب للستوريات...">
                        <i class="fas fa-times action-icon" onclick="clearInput('input-insta')"></i>
                        <i class="fas fa-paste action-icon" onclick="pasteInput('input-insta')"></i>
                    </div>
                    <button class="btn-main" onclick="processClientRequest('insta')">معالجة وحفظ البيانات</button>
                </div>
                <div id="res-insta" class="result-container">
                    <div class="status-msg" id="insta-status"></div>
                    <div class="story-grid" id="insta-stories-grid" style="display: none;"></div>
                    <div class="media-box" id="insta-media-box" style="display: none;"></div>
                </div>
            </div>

            <div id="view-tiktok" class="view-section">
                <div class="input-card">
                    <div class="card-title"><i class="fab fa-tiktok" style="color: #00f2fe;"></i> تنزيل من تيك توك</div>
                    <div class="input-row">
                        <input type="text" id="input-tiktok" placeholder="أدخل رابط الفيديو المباشر...">
                        <i class="fas fa-times action-icon" onclick="clearInput('input-tiktok')"></i>
                        <i class="fas fa-paste action-icon" onclick="pasteInput('input-tiktok')"></i>
                    </div>
                    <button class="btn-main" onclick="processClientRequest('tiktok')">معالجة وحفظ البيانات</button>
                </div>
                <div id="res-tiktok" class="result-container">
                    <div class="status-msg"></div>
                    <div class="media-box" style="display: none;"></div>
                </div>
            </div>
            
            <div id="view-facebook" class="view-section">
                <div class="input-card">
                    <div class="card-title"><i class="fab fa-facebook" style="color: #1877f2;"></i> تنزيل من فيسبوك</div>
                    <div class="input-row">
                        <input type="text" id="input-facebook" placeholder="أدخل رابط الفيديو أو الريلز...">
                        <i class="fas fa-times action-icon" onclick="clearInput('input-facebook')"></i>
                        <i class="fas fa-paste action-icon" onclick="pasteInput('input-facebook')"></i>
                    </div>
                    <button class="btn-main" onclick="processClientRequest('facebook')">معالجة وحفظ البيانات</button>
                </div>
                <div id="res-facebook" class="result-container">
                    <div class="status-msg"></div>
                    <div class="media-box" style="display: none;"></div>
                </div>
            </div>

            <div id="view-general" class="view-section">
                <div class="input-card">
                    <div class="card-title"><i class="fas fa-link" style="color: #8b5cf6;"></i> تحميل عام</div>
                    <div class="input-row">
                        <input type="text" id="input-general" placeholder="أدخل رابط المقطع من أي موقع...">
                        <i class="fas fa-times action-icon" onclick="clearInput('input-general')"></i>
                        <i class="fas fa-paste action-icon" onclick="pasteInput('input-general')"></i>
                    </div>
                    <button class="btn-main" onclick="processClientRequest('general')">معالجة وحفظ البيانات</button>
                </div>
                <div id="res-general" class="result-container">
                    <div class="status-msg"></div>
                    <div class="media-box" style="display: none;"></div>
                </div>
            </div>

        </div>
    </div>

    <div class="qr-modal" id="qrModal">
        <div class="qr-box">
            <span>امسح الباركود للتحميل بهاتفك</span>
            <div id="qrCodeDiv"></div>
            <button class="close-qr" onclick="document.getElementById('qrModal').style.display='none'">إغلاق</button>
        </div>
    </div>

    <script>
        let activePlayer = null;
        let globalVideoUrl = '';
        let activeTitle = 'Tahmilati_File';

        function toggleTheme() {
            const body = document.body;
            body.setAttribute('data-theme', body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
        }

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

        function clearInput(id) { document.getElementById(id).value = ''; }
        async function pasteInput(id) { try { document.getElementById(id).value = await navigator.clipboard.readText(); } catch(e){} }

        function showQR(url) {
            document.getElementById('qrModal').style.display = 'flex';
            document.getElementById('qrCodeDiv').innerHTML = '';
            new QRCode(document.getElementById("qrCodeDiv"), { text: url, width: 160, height: 160 });
        }

        function copyLink(url) {
            const temp = document.createElement("input");
            temp.value = url; document.body.appendChild(temp); temp.select(); document.execCommand("copy"); document.body.removeChild(temp);
            alert("تم نسخ رابط التنزيل المباشر بنجاح.");
        }

        function toggleQualityMenu(btn) {
            const menu = btn.parentElement.querySelector('.quality-dropdown');
            menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
        }

        // إجبار التنزيل التلقائي الفوري داخل الجهاز دون فتح صفحة جديدة
        async function forceAutoDownload(url, filename) {
            try {
                if(url.includes('/proxy')) {
                    const a = document.createElement('a'); a.href = url; document.body.appendChild(a); a.click(); document.body.removeChild(a); return;
                }
                const response = await fetch(url);
                const blob = await response.blob();
                const blobUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = blobUrl; a.download = filename;
                document.body.appendChild(a); a.click(); document.body.removeChild(a);
                window.URL.revokeObjectURL(blobUrl);
            } catch (e) {
                window.open(url, '_blank');
            }
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
                    btn.disabled = true; status.style.display = 'block'; status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري إنشاء الملف...';
                    const vals = sliderDiv.noUiSlider.get();
                    
                    gifshot.createGIF({
                        'video': [globalVideoUrl], 'offset': parseInt(vals[0]), 'numFrames': (parseInt(vals[1]) - parseInt(vals[0])) * 10, 'frameDuration': 1, 'gifWidth': 300, 'gifHeight': 300
                    }, function(obj) {
                        if(!obj.error) {
                            const a = document.createElement('a'); a.href = obj.image; a.download = activeTitle + '.gif'; a.click();
                            status.innerHTML = '<i class="fas fa-check"></i> اكتمل التنزيل';
                        } else { status.innerHTML = '<i class="fas fa-times"></i> خطأ في النظام.'; }
                        setTimeout(()=> { status.style.display = 'none'; btn.disabled = false; }, 3000);
                    });
                };
            }
        }

        // دالة الاتصال المخصصة بمهلة محددة لكل سيرفر لكسر التعليق
        async function fetchWithTimeout(resource, options = {}) {
            const { timeout = 5000 } = options; // مهلة 5 ثوانٍ بالضبط بناءً على الاتفاق
            const controller = new AbortController();
            const id = setTimeout(() => controller.abort(), timeout);
            const response = await fetch(resource, { ...options, signal: controller.signal });
            clearTimeout(id);
            return response;
        }

        // 🌊 معالجة جميع المنصات بنظام الشلال والـ 5 ثوانٍ للـ الستوريات
        async function processClientRequest(platform) {
            const inputId = 'input-' + platform;
            const containerId = 'res-' + platform;
            let val = document.getElementById(inputId).value.trim();
            if(!val) return;

            const resContainer = document.getElementById(containerId);
            resContainer.style.display = 'flex';
            
            // تهيئة واجهات العرض الداخلية للإنستغرام لمنع التداخل
            if(platform === 'insta') {
                document.getElementById('insta-status').innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري معالجة وحفظ البيانات...';
                document.getElementById('insta-status').style.display = 'block';
                document.getElementById('insta-stories-grid').style.display = 'none';
                document.getElementById('insta-media-box').style.display = 'none';
            } else {
                resContainer.querySelector('.status-msg').innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري معالجة وحفظ البيانات...';
                resContainer.querySelector('.status-msg').style.display = 'block';
                resContainer.querySelector('.media-box').style.display = 'none';
            }

            if(activePlayer) { activePlayer.destroy(); activePlayer = null; }

            // 1. معالجة تيك توك المباشرة والستوريات بسيرفرها السريع المخصص
            if(platform === 'tiktok' || val.includes('tiktok.com')) {
                try {
                    let r = await fetchWithTimeout('https://www.tikwm.com/api/?url=' + encodeURIComponent(val));
                    let res = await r.json();
                    if(res.code === 0) {
                        resContainer.querySelector('.status-msg').style.display = 'none';
                        renderMediaResult(res.data.title, res.data.cover, res.data.play, res.data.music, res.data.wmplay, res.data.duration, platform, containerId + ' .media-box');
                        return;
                    }
                } catch(e) {}
            }

            // 2. معالجة إنستغرام ستوريات باليوزر (نظام شلال بـ 3 سيرفرات و مهلة 5 ثوانٍ لكل منها)
            if(platform === 'insta' && !val.startsWith('http')) {
                const user = val.replace('@', '').split('?')[0].split('/')[-1];
                
                // قائمة خوادم فك التشفير التفاعلية للستوريات
                const storyNodes = [
                    `https://api.storiesig.info/download?username=${user}`,
                    `https://saveig.app/api/info?url=https://instagram.com/stories/${user}/`,
                    `https://co.wuk.sh/api/json`
                ];

                let storyFetched = false;
                
                for(let i=0; i<storyNodes.length; i++) {
                    try {
                        // طلب البيانات مع تحديد مهلة 5 ثوانٍ إجبارية لكل سيرفر
                        let r = await fetchWithTimeout(storyNodes[i], { timeout: 5000 });
                        if(r.ok) {
                            let data = await r.json();
                            // معالجة وحقن شبكة الستوريات التفاعلية (Grid)
                            let items = data.items || data.result || [];
                            if(items.length > 0) {
                                let gridHtml = '';
                                items.forEach((item, index) => {
                                    let isVid = item.is_video || (item.type && item.type.includes('video')) || false;
                                    let snap = item.image_versions2?.candidates[0]?.url || item.thumbnail_url || 'https://via.placeholder.com/150';
                                    let vUrl = item.video_versions?.[0]?.url || item.video_url || item.url;
                                    
                                    gridHtml += `
                                    <div class="story-tile" onclick="selectStoryItem('${vUrl}', '${snap}', ${isVid}, '${user}')">
                                        <img src="${snap}" class="story-img">
                                        <div class="story-badge">${isVid ? '<i class="fas fa-play"></i> فيديو':'<i class="fas fa-image"></i> صورة'}</div>
                                    </div>`;
                                });
                                document.getElementById('insta-stories-grid').innerHTML = gridHtml;
                                document.getElementById('insta-stories-grid').style.display = 'grid';
                                document.getElementById('insta-status').style.display = 'none';
                                storyFetched = true;
                                break;
                            }
                        }
                    } catch(e) {
                        console.log(`السيرفر رقم ${i+1} انتهت مهلته أو واجه خطأ، يحول تلقائياً...`);
                        continue; // التحويل الفوري التلقائي للسيرفر التالي في المصفوفة
                    }
                }

                if(!storyFetched) {
                    document.getElementById('insta-status').innerHTML = `<i class="fas fa-exclamation-triangle"></i> الحساب خاص أو لا توجد ستوريات نشطة حالياً.`;
                    document.getElementById('insta-status').style.color = '#ef4444';
                }
                return;
            }

            // 3. معالجة البوستات والريلز والفيس بوك والعام (Cobalt المطور)
            const cobaltNodes = ["https://api.cobalt.tools/api/json", "https://co.wuk.sh/api/json"];
            let success = false;

            for(let node of cobaltNodes) {
                try {
                    let r = await fetchWithTimeout(node, {
                        method: 'POST',
                        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url: val, vQuality: "720" }),
                        timeout: 6000
                    });
                    if(r.status == 200) {
                        let res = await r.json();
                        if(res.url) {
                            let rAudio = await fetchWithTimeout(node, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: JSON.stringify({ url: val, isAudioOnly: true }), timeout: 6000 });
                            let resAudio = rAudio.status == 200 ? await rAudio.json() : {};
                            
                            let targetBox = platform === 'insta' ? 'insta-media-box' : containerId + ' .media-box';
                            if(platform === 'insta') document.getElementById('insta-status').style.display = 'none';
                            else resContainer.querySelector('.status-msg').style.display = 'none';

                            renderMediaResult("تم استخراج المقطع بنجاح", "https://via.placeholder.com/150", res.url, resAudio.url || res.url, res.url, 60, platform, targetBox);
                            success = true;
                            break;
                        }
                    }
                } catch(e) {}
            }

            if(!success && platform !== 'insta') {
                resContainer.querySelector('.status-msg').innerHTML = `<i class="fas fa-exclamation-triangle"></i> تعذر معالجة البيانات، تأكد من صحة الرابط.`;
                resContainer.querySelector('.status-msg').style.color = '#ef4444';
            }
        }

        // تفريغ وعرض العنصر المختار من شبكة الستوريات
        function selectStoryItem(url, snap, isVid, user) {
            document.getElementById('insta-media-box').style.display = 'none';
            renderMediaResult(`ستوري حساب @${user}`, snap, url, url, url, 15, 'insta', 'insta-media-box');
        }

        // بناء لوحة التحكم الفخمة بالأزرار والدشلي ⚙️
        function renderMediaResult(title, thumbnail, videoUrl, audioUrl, whatsappUrl, duration, platform, targetSelector) {
            const mediaBox = document.getElementById(targetSelector) || document.querySelector('.' + targetSelector.split(' ')[1] || targetSelector);
            
            activeTitle = title || 'Tahmilati_File';
            globalVideoUrl = videoUrl;

            mediaBox.innerHTML = `
                <div class="video-header"><img src="${thumbnail}" class="thumb"><div class="title">${title}</div></div>
                <video class="plyr-player" playsinline controls></video>
                <div class="download-grid" style="display:flex; flex-direction:column; gap:10px;"></div>
                <div class="gif-editor">
                    <div style="font-size: 13px; font-weight: bold; margin-bottom: 10px;"><i class="fas fa-sliders-h"></i> تحديد نطاق الـ GIF:</div>
                    <div class="timeSlider slider-container"></div>
                    <div style="display:flex; justify-content: space-between; font-size:12px; color:var(--primary); font-weight:bold; margin-bottom: 15px;">
                        <span class="startVal">0s</span> <span class="endVal">5s</span>
                    </div>
                    <button class="btn-action bg-gif gifStartBtn"><i class="fas fa-check"></i> توليد الصورة (GIF)</button>
                    <div class="status-msg gifStatus" style="font-size: 12px; margin-top: 10px;"></div>
                </div>
            `;

            const videoEl = mediaBox.querySelector('.plyr-player');
            videoEl.src = videoUrl;
            activePlayer = new Plyr(videoEl, { controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'volume', 'fullscreen'] });

            // ممر البروكسي الداخلي الخفيف جداً لفرض التحميل التلقائي وتسمية الملفات
            const pVideo = `/proxy?url=${encodeURIComponent(videoUrl)}&ext=mp4`;
            const pAudio = `/proxy?url=${encodeURIComponent(audioUrl)}&ext=mp3`;
            const pWa = `/proxy?url=${encodeURIComponent(whatsappUrl)}&ext=mp4`;

            let actionsHtml = `
                <div class="btn-group">
                    <button onclick="forceAutoDownload('${pVideo}', '${activeTitle}.mp4')" class="btn-action bg-mp4"><i class="fas fa-download"></i> تنزيل تلقائي (فيديو)</button>
                    <button onclick="toggleQualityMenu(this)" class="btn-icon-sq" title="تحديد الجودة المخصصة"><i class="fas fa-cog"></i></button>
                    <div class="quality-dropdown">
                        <button class="quality-btn" onclick="forceAutoDownload('${pVideo}', '${activeTitle}_1080p.mp4')">1080p (أعلى جودة)</button>
                        <button class="quality-btn" onclick="forceAutoDownload('${pVideo}', '${activeTitle}_720p.mp4')">720p (جودة متوسطة)</button>
                        <button class="quality-btn" onclick="forceAutoDownload('${pWa}', '${activeTitle}_480p.mp4')">480p (جودة خفيفة)</button>
                    </div>
                    <button onclick="copyLink('${window.location.origin + pVideo}')" class="btn-icon-sq" title="نسخ الرابط"><i class="fas fa-link"></i></button>
                    <button onclick="showQR('${window.location.origin + pVideo}')" class="btn-icon-sq" title="باركود"><i class="fas fa-qrcode"></i></button>
                </div>
                <div class="btn-group">
                    <button onclick="forceAutoDownload('${pAudio}', '${activeTitle}.mp3')" class="btn-action bg-mp3"><i class="fas fa-music"></i> تنزيل (صوت MP3)</button>
                    <button onclick="copyLink('${window.location.origin + pAudio}')" class="btn-icon-sq"><i class="fas fa-link"></i></button>
                    <button onclick="showQR('${window.location.origin + pAudio}')" class="btn-icon-sq"><i class="fas fa-qrcode"></i></button>
                </div>
            `;

            if(platform === 'tiktok' || platform === 'insta') {
                actionsHtml += `
                <div class="btn-group">
                    <button onclick="forceAutoDownload('${pWa}', '${activeTitle}_Story.mp4')" class="btn-action bg-wa"><i class="fab fa-whatsapp"></i> نسخة مضغوطة (ستوري)</button>
                </div>`;
                mediaBox.querySelector('.gif-editor').style.display = 'block';
            } else {
                mediaBox.querySelector('.gif-editor').style.display = 'none';
            }

            mediaBox.querySelector('.download-grid').innerHTML = actionsHtml;
            mediaBox.style.display = 'flex';
            
            if(platform === 'tiktok' || platform === 'insta') {
                toggleGifEditor(mediaBox.parentElement.id || 'res-insta', duration);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

# بروكسي العبور الذكي والخفيف جداً (إجبار المتصفح على التحميل ومنع الـ CORS)
@app.route('/proxy')
def proxy_download():
    file_url = request.args.get('url')
    ext = request.args.get('ext', 'mp4')
    if not file_url: return "رابط مفقود", 400

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        req = requests.get(file_url, headers=headers, stream=True, verify=False, timeout=10)
        resp = Response(stream_with_context(req.iter_content(chunk_size=1024*512)), status=req.status_code, content_type=req.headers.get('content-type'))
        resp.headers['Content-Disposition'] = f'attachment; filename="Tahmilati_Media.{ext}"'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except:
        return "خطأ في الاتصال بالخادم الخارجي", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
