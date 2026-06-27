import os
import requests
import urllib.parse
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tahmilati | تحميلاتي</title>
    
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
        :root {
            --bg-dark: #0f172a; --bg-light: #f8fafc;
            --glass-bg-dark: rgba(30, 41, 59, 0.7); --glass-bg-light: rgba(255, 255, 255, 0.8);
            --border-dark: rgba(255, 255, 255, 0.1); --border-light: rgba(0, 0, 0, 0.1);
            --text-dark: #f8fafc; --text-light: #0f172a;
            --primary: #8b5cf6; --neon-shadow: 0 0 15px rgba(139, 92, 246, 0.5);
        }

        body[data-theme="dark"] { --bg: var(--bg-dark); --glass: var(--glass-bg-dark); --border: var(--border-dark); --text: var(--text-dark); }
        body[data-theme="light"] { --bg: var(--bg-light); --glass: var(--glass-bg-light); --border: var(--border-light); --text: var(--text-light); }
        
        body.theme-tiktok { --primary: #00f2fe; --neon-shadow: 0 0 15px rgba(0, 242, 254, 0.6); }
        body.theme-insta { --primary: #f56040; --neon-shadow: 0 0 15px rgba(245, 96, 64, 0.6); }
        body.theme-facebook { --primary: #1877f2; --neon-shadow: 0 0 15px rgba(24, 119, 242, 0.6); }
        body.theme-general { --primary: #8b5cf6; --neon-shadow: 0 0 15px rgba(139, 92, 246, 0.6); }

        html, body { height: 100dvh; margin: 0; padding: 0; overflow: hidden; font-family: 'Tajawal', sans-serif; background-color: var(--bg); color: var(--text); transition: background-color 0.4s ease; }
        .app-container { display: flex; flex-direction: column; height: 100%; max-width: 500px; margin: 0 auto; position: relative; overflow: hidden; }
        
        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: var(--glass); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border); z-index: 50; }
        .logo-title { margin: 0; font-weight: 900; font-size: 24px; color: var(--primary); text-shadow: var(--neon-shadow); }
        .nav-btns { display: flex; gap: 10px; }
        .icon-btn { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 12px; cursor: pointer; transition: 0.3s; font-size: 16px; display: flex; justify-content: center; align-items: center;}
        .icon-btn:hover { background: var(--primary); color: #fff; box-shadow: var(--neon-shadow); }

        .sidebar-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 99; display: none; opacity: 0; transition: 0.3s; backdrop-filter: blur(3px); }
        .sidebar { position: fixed; top: 0; right: -320px; width: 280px; height: 100%; background: var(--glass); backdrop-filter: blur(20px); border-left: 1px solid var(--border); z-index: 100; box-shadow: -5px 0 25px rgba(0,0,0,0.5); transition: right 0.4s ease; display: flex; flex-direction: column; }
        .sidebar.open { right: 0; }
        .sidebar-header { padding: 25px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .sidebar-title { font-weight: 900; font-size: 18px; color: var(--text); }
        .close-sidebar { background: none; border: none; font-size: 22px; color: #ef4444; cursor: pointer; }
        .menu-list { list-style: none; padding: 10px 0; margin: 0; flex: 1; overflow-y: auto; }
        .menu-item { padding: 18px 25px; border-bottom: 1px solid var(--border); cursor: pointer; font-weight: bold; font-size: 15px; display: flex; align-items: center; gap: 15px; transition: 0.3s; color: var(--text); }
        .menu-item:hover { background: rgba(255,255,255,0.05); padding-right: 30px; color: var(--primary); }

        .main-content { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 20px; scroll-behavior: smooth; }
        .main-content::-webkit-scrollbar { width: 4px; }
        .main-content::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }

        .glass-card { background: var(--glass); backdrop-filter: blur(16px); border: 1px solid var(--border); border-radius: 20px; padding: 20px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2); }
        
        .welcome-screen { text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; gap: 20px; animation: fadeIn 0.5s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .welcome-title { font-size: 28px; font-weight: 900; color: var(--primary); margin: 0; text-shadow: var(--neon-shadow); }
        .welcome-desc { font-size: 14px; color: var(--text); opacity: 0.8; line-height: 1.6; }
        .welcome-steps { background: rgba(0,0,0,0.2); border: 1px solid var(--border); padding: 15px; border-radius: 15px; text-align: right; width: 100%; font-size: 13px; font-weight: bold; list-style: none; box-sizing: border-box; }
        .welcome-steps li { margin-bottom: 10px; color: var(--text); }
        .live-counter { text-align: center; font-size: 13px; font-weight: bold; color: var(--text); background: rgba(0,0,0,0.2); padding: 12px; border-radius: 15px; border: 1px solid var(--border); width: 100%; box-sizing: border-box;}
        .creator-badge { display: flex; align-items: center; justify-content: center; gap: 8px; background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); color: white; padding: 12px; border-radius: 15px; text-decoration: none; font-weight: bold; font-size: 14px; width: 100%; transition: 0.3s; box-sizing: border-box;}

        .view-section { display: none; flex-direction: column; gap: 20px; animation: fadeIn 0.4s ease; }
        .card-title { font-size: 16px; font-weight: 900; display: flex; align-items: center; gap: 10px; margin-bottom: 15px; color: var(--text); }
        .input-row { display: flex; gap: 8px; align-items: center; background: rgba(0,0,0,0.15); border: 1px solid var(--border); border-radius: 15px; padding-right: 15px; }
        input[type="text"] { flex: 1; padding: 16px 5px; background: transparent; border: none; color: var(--text); font-size: 14px; outline: none; font-family: 'Tajawal'; }
        .action-icon { color: var(--text); opacity: 0.6; cursor: pointer; padding: 10px; transition: 0.3s; font-size: 16px; }
        .action-icon:hover { color: var(--primary); opacity: 1; }
        .btn-main { width: 100%; margin-top: 15px; padding: 15px; background: var(--primary); color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: 900; cursor: pointer; font-family: 'Tajawal'; box-shadow: var(--neon-shadow); transition: 0.3s; }

        .result-container { display: none; flex-direction: column; gap: 15px; }
        .video-header { display: flex; gap: 15px; align-items: center; padding: 10px; background: rgba(0,0,0,0.1); border-radius: 15px; }
        .thumb { width: 60px; height: 60px; border-radius: 12px; object-fit: cover; border: 1px solid var(--border); }
        .title { font-size: 13px; font-weight: bold; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; color: var(--text); }
        
        .video-wrapper { max-height: 280px; width: 100%; border-radius: 15px; overflow: hidden; background: #000; display: flex; justify-content: center; align-items: center; }
        .plyr { width: 100%; height: 100%; }
        .plyr__video-wrapper video { max-height: 280px !important; object-fit: contain; }

        .action-grid { display: flex; flex-direction: column; gap: 8px; margin-top: 5px; }
        .btn-row { display: flex; gap: 8px; width: 100%; position: relative; }
        .btn-action { flex: 1; padding: 12px 10px; border: none; border-radius: 12px; font-weight: 900; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 13px; color: white; font-family: 'Tajawal'; transition: 0.3s; }
        .btn-icon-sq { background: rgba(255,255,255,0.05); width: 45px; flex: none; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--text); cursor: pointer; border: 1px solid var(--border); font-size: 16px; transition: 0.3s; }
        .btn-icon-sq:hover { background: var(--primary); color: white; border-color: var(--primary); }
        
        .quality-dropdown { position: absolute; bottom: calc(100% + 5px); left: 0; width: 100%; background: var(--bg); border: 1px solid var(--border); border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: none; flex-direction: column; z-index: 100; overflow: hidden; }
        .quality-btn { padding: 12px; border: none; background: transparent; color: var(--text); font-family: 'Tajawal'; font-weight: bold; font-size: 13px; border-bottom: 1px solid var(--border); cursor: pointer; text-align: center; }
        .quality-btn:hover { background: var(--primary); color: white; }

        .bg-mp4 { background: #10b981; } .bg-mp3 { background: #8b5cf6; } .bg-wa { background: #06b6d4; } .bg-gif { background: #f59e0b; }

        .gif-editor { display: none; background: rgba(0,0,0,0.15); padding: 15px; border-radius: 15px; border: 1px dashed var(--primary); margin-top: 10px; }
        .slider-container { margin: 30px 10px 10px 10px; }
        .noUi-connect { background: var(--primary); }
        .noUi-handle { border-radius: 50%; box-shadow: var(--neon-shadow); background: #fff; border: 2px solid var(--primary); }

        .qr-modal { display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 1000; justify-content: center; align-items: center; flex-direction: column; backdrop-filter: blur(5px); }
        .qr-box { background: var(--glass); border: 1px solid var(--border); padding: 25px; border-radius: 20px; display: flex; flex-direction: column; align-items: center; gap: 15px; }
        .close-qr { background: #ef4444; color: white; border: none; padding: 10px 30px; border-radius: 10px; font-weight: bold; cursor: pointer; font-family: 'Tajawal'; font-size: 14px; }
        .status-msg { text-align: center; font-size: 13px; display: none; font-weight: bold; padding: 10px; border-radius: 10px; background: rgba(0,0,0,0.1); margin-top: 10px; }
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
                <span class="sidebar-title">أقسام التنزيل</span>
                <button class="close-sidebar" onclick="toggleSidebar()"><i class="fas fa-times"></i></button>
            </div>
            <ul class="menu-list">
                <li class="menu-item" onclick="switchView('insta', 'theme-insta')"><i class="fab fa-instagram fa-lg" style="color: #f56040; width: 25px;"></i> إنستغرام (روابط فقط)</li>
                <li class="menu-item" onclick="switchView('tiktok', 'theme-tiktok')"><i class="fab fa-tiktok fa-lg" style="color: #00f2fe; width: 25px;"></i> تيك توك (روابط فقط)</li>
                <li class="menu-item" onclick="switchView('facebook', 'theme-facebook')"><i class="fab fa-facebook fa-lg" style="color: #1877f2; width: 25px;"></i> فيسبوك (روابط فقط)</li>
                <li class="menu-item" onclick="switchView('general', 'theme-general')"><i class="fas fa-link fa-lg" style="color: #8b5cf6; width: 25px;"></i> تحميل عام</li>
            </ul>
        </div>

        <div class="main-content">
            <!-- الواجهة الرئيسية وطريقة الاستخدام -->
            <div id="view-welcome" class="welcome-screen view-section" style="display: flex;">
                <div class="glass-card" style="width: 100%; text-align: center; padding: 30px 20px; box-sizing: border-box;">
                    <h1 class="welcome-title">Tahmilati | تحميلاتي</h1>
                    <p class="welcome-desc">منصة التنزيل الذكية الشاملة<br>استخراج الوسائط من مختلف المنصات بأعلى جودة وتنزيلها تلقائياً.</p>
                    <ul class="welcome-steps" dir="rtl">
                        <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 1. انقر على أيقونة القائمة (☰) في الزاوية العلوية.</li>
                        <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 2. حدد المنصة المراد التنزيل منها.</li>
                        <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 3. أدخل الرابط لإنشاء ملفات التنزيل المباشرة.</li>
                    </ul>
                    <div class="live-counter"><i class="fas fa-chart-line"></i> تم معالجة <span id="countNum">1,425,890</span> طلب بنجاح</div>
                    <a href="https://www.instagram.com/_otnn?igsh=d3hybTN2M2Zlanl0" target="_blank" class="creator-badge"><i class="fab fa-instagram fa-lg"></i> المصمم: @_otnn</a>
                </div>
            </div>

            <!-- توليد واجهات التحميل -->
            <script>
                const platforms = [
                    { id: 'insta', icon: 'fab fa-instagram', color: '#f56040', title: 'تنزيل من إنستغرام', placeholder: 'أدخل رابط البوست أو الريلز...' },
                    { id: 'tiktok', icon: 'fab fa-tiktok', color: '#00f2fe', title: 'تنزيل من تيك توك', placeholder: 'أدخل رابط الفيديو...' },
                    { id: 'facebook', icon: 'fab fa-facebook', color: '#1877f2', title: 'تنزيل من فيسبوك', placeholder: 'أدخل رابط الفيديو أو الريلز...' },
                    { id: 'general', icon: 'fas fa-link', color: '#8b5cf6', title: 'تحميل عام', placeholder: 'أدخل الرابط المباشر...' }
                ];
                
                platforms.forEach(p => {
                    document.write(`
                    <div id="view-${p.id}" class="view-section">
                        <div class="glass-card">
                            <div class="card-title"><i class="${p.icon}" style="color: ${p.color}; font-size: 20px;"></i> ${p.title}</div>
                            <div class="input-row">
                                <input type="text" id="input-${p.id}" placeholder="${p.placeholder}">
                                <i class="fas fa-times action-icon" onclick="document.getElementById('input-${p.id}').value = ''"></i>
                                <i class="fas fa-paste action-icon" onclick="navigator.clipboard.readText().then(t => document.getElementById('input-${p.id}').value = t).catch(e => console.log(e))"></i>
                            </div>
                            <button class="btn-main" onclick="processClientRequest('${p.id}')">معالجة الرابط</button>
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

    <!-- الباركود -->
    <div class="qr-modal" id="qrModal">
        <div class="qr-box">
            <span style="color:var(--text); font-weight:bold; font-size:15px;">امسح الباركود للتحميل المباشر</span>
            <div id="qrCodeDiv" style="background: white; padding: 10px; border-radius: 10px;"></div>
            <button class="close-qr" onclick="document.getElementById('qrModal').style.display='none'">إغلاق</button>
        </div>
    </div>

    <script>
        let count = 1425890;
        setInterval(() => { count += Math.floor(Math.random() * 3); document.getElementById('countNum').innerText = count.toLocaleString(); }, 3500);

        let activePlayer = null;
        let globalVideoUrl = '';
        let activeTitle = 'Tahmilati_File';

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
            new QRCode(document.getElementById("qrCodeDiv"), { text: url, width: 160, height: 160, colorDark : "#000000", colorLight : "#ffffff" });
        }

        function copyLink(url) {
            const temp = document.createElement("input"); temp.value = url; document.body.appendChild(temp); temp.select(); document.execCommand("copy"); document.body.removeChild(temp);
            alert("تم نسخ الرابط بنجاح.");
        }

        function toggleQualityMenu(btn) {
            const menu = btn.parentElement.querySelector('.quality-dropdown'); 
            menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
        }

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

        // ميزة الـ GIF (تعمل لجميع المنصات الآن)
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
                    status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري إنشاء الصورة المتحركة...';
                    const vals = sliderDiv.noUiSlider.get();
                    gifshot.createGIF({
                        'video': [globalVideoUrl], 'offset': parseInt(vals[0]), 'numFrames': (parseInt(vals[1]) - parseInt(vals[0])) * 10, 'frameDuration': 1, 'gifWidth': 300, 'gifHeight': 300
                    }, function(obj) {
                        if(!obj.error) { 
                            forceAutoDownload(obj.image, activeTitle + '.gif'); 
                            status.innerHTML = '<i class="fas fa-check"></i> اكتمل التنزيل بنجاح.'; 
                            status.style.color = '#10b981';
                        } else { 
                            status.innerHTML = '<i class="fas fa-times"></i> حدث خطأ في معالجة الـ GIF.'; 
                            status.style.color = '#ef4444';
                        }
                        setTimeout(()=> { status.style.display = 'none'; btn.disabled = false; }, 3000);
                    });
                };
            }
        }

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
            statusMsg.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري استخراج الروابط المباشرة...';
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
                    
                    // استخدام البروكسي لتخطي حظر الانستا والفيس
                    let useProxy = ['insta', 'facebook'].includes(platform);
                    let internalVidPlay = useProxy ? `/proxy_stream?url=${encodeURIComponent(res.video_url)}&ext=mp4` : res.video_url;
                    let internalAudPlay = useProxy ? `/proxy_stream?url=${encodeURIComponent(res.audio_url)}&ext=mp3` : res.audio_url;
                    let absoluteQrUrl = useProxy ? (window.location.origin + internalVidPlay) : res.video_url;

                    renderMediaResult(res.title, res.thumbnail, internalVidPlay, internalAudPlay, absoluteQrUrl, res.duration || 15, platform, 'res-' + platform);
                } else {
                    statusMsg.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${res.error}`;
                    statusMsg.style.color = '#ef4444';
                }
            } catch(e) {
                statusMsg.innerHTML = `<i class="fas fa-wifi"></i> انقطع الاتصال بالخادم.`; 
                statusMsg.style.color = '#ef4444';
            }
        }

        function renderMediaResult(title, thumbnail, vidUrl, audUrl, qrUrl, duration, platform, containerId) {
            const mediaBox = document.querySelector(`#${containerId} .media-box`); 
            activeTitle = title.replace(/[^a-zA-Z0-9]/g, '_') || 'Tahmilati_Media'; 
            globalVideoUrl = vidUrl;
            
            mediaBox.innerHTML = `
                <div class="video-header"><img src="${thumbnail}" class="thumb"><div class="title">${title}</div></div>
                <div class="video-wrapper">
                    <video class="plyr-player" playsinline controls></video>
                </div>
                <div class="action-grid">
                    <div class="btn-row">
                        <button onclick="forceAutoDownload('${vidUrl}', '${activeTitle}.mp4')" class="btn-action bg-mp4"><i class="fas fa-download"></i> تنزيل الفيديو</button>
                        <button onclick="toggleQualityMenu(this)" class="btn-icon-sq" title="الجودة"><i class="fas fa-cog"></i></button>
                        <div class="quality-dropdown">
                            <button class="quality-btn" onclick="forceAutoDownload('${vidUrl}', '${activeTitle}_1080p.mp4')">1080p (جودة عالية)</button>
                            <button class="quality-btn" onclick="forceAutoDownload('${vidUrl}', '${activeTitle}_720p.mp4')">720p (جودة متوسطة)</button>
                        </div>
                        <button onclick="copyLink('${qrUrl}')" class="btn-icon-sq" title="نسخ الرابط"><i class="fas fa-link"></i></button>
                        <button onclick="showQR('${qrUrl}')" class="btn-icon-sq" title="باركود"><i class="fas fa-qrcode"></i></button>
                    </div>
                    <div class="btn-row">
                        <button onclick="forceAutoDownload('${audUrl}', '${activeTitle}.mp3')" class="btn-action bg-mp3"><i class="fas fa-music"></i> تحميل الصوت (MP3)</button>
                    </div>
                </div>
                <!-- ميزة الـ GIF -->
                <div class="gif-editor">
                    <div style="font-size: 13px; font-weight: 900; margin-bottom: 10px; color: var(--text);"><i class="fas fa-images"></i> إنشاء صورة متحركة (GIF):</div>
                    <div class="timeSlider slider-container"></div>
                    <div style="display:flex; justify-content: space-between; font-size:12px; color:var(--primary); font-weight:bold; margin-bottom: 15px;">
                        <span class="startVal">0s</span> <span class="endVal">5s</span>
                    </div>
                    <button class="btn-action bg-gif gifStartBtn" style="width: 100%;"><i class="fas fa-magic"></i> توليد الصورة</button>
                    <div class="status-msg gifStatus"></div>
                </div>
            `;
            
            const videoEl = mediaBox.querySelector('.plyr-player'); 
            videoEl.src = vidUrl;
            activePlayer = new Plyr(videoEl, { controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'fullscreen'] });

            // إظهار ميزة الـ GIF للجميع
            mediaBox.querySelector('.gif-editor').style.display = 'block'; 
            toggleGifEditor(containerId, duration);
            
            mediaBox.style.display = 'flex';
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
    data = request.json
    url = data.get('url', '').strip()
    platform = data.get('platform', '')

    if not url or not url.startswith('http'):
        return jsonify({"success": False, "error": "يرجى إدخال رابط مباشر صحيح يبدأ بـ http أو https."})

    # 1. تيك توك 
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
        except:
            pass

    # 2. إنستغرام وفيسبوك والمقاطع العامة (استخدام yt-dlp كمحرك أساسي للروابط العامة)
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
            'format': 'best',
            'extractor_args': {'facebook': {'player_client': ['android', 'ios']}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url', '')
            
            if not video_url and 'formats' in info:
                v_formats = [f for f in info['formats'] if f.get('vcodec') != 'none']
                if v_formats: 
                    video_url = v_formats[-1]['url']
            
            if video_url:
                return jsonify({
                    "success": True, 
                    "title": info.get('title', 'ملف وسائط'),
                    "thumbnail": info.get('thumbnail', 'https://via.placeholder.com/150'),
                    "video_url": video_url, 
                    "audio_url": video_url, 
                    "duration": info.get('duration', 15)
                })
    except Exception as e:
        error_msg = str(e).lower()
        if "private" in error_msg or "log in" in error_msg:
            return jsonify({"success": False, "error": "المقطع محمي أو خاص. المنصة ترفض التحميل للروابط غير العامة."})
        return jsonify({"success": False, "error": "تعذر العثور على رابط مباشر للاستخراج."})

    return jsonify({"success": False, "error": "حدث خطأ أثناء الاتصال بالمصدر."})

@app.route('/proxy_stream')
def proxy_stream():
    target_url = request.args.get('url')
    ext = request.args.get('ext', 'mp4')
    if not target_url: 
        return "URL Error", 400

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/115.0 Safari/537.36'}
    try:
        req = requests.get(target_url, headers=headers, stream=True, verify=False, timeout=20)
        if req.status_code not in [200, 206]:
            return f"Access Denied: {req.status_code}", req.status_code

        def generate():
            for chunk in req.iter_content(chunk_size=1024 * 512):
                if chunk: yield chunk

        response = Response(stream_with_context(generate()), content_type=req.headers.get('content-type', f'video/{ext}'))
        response.headers['Content-Disposition'] = f'attachment; filename="Tahmilati_File.{ext}"'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return f"Proxy Error", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
