import os
import re
import time
import socket
import ipaddress
import logging
import urllib.parse
import threading
import concurrent.futures
from functools import wraps
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context, abort
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import yt_dlp

# ==============================================================================
# Tahmilati Pro - Enterprise Architecture Edition (Refactored)
# Security: SSRF Protection, Rate Limiting, CSP & Security Headers.
# Performance: Smart TTL Cache, Connection Pooling, ThreadPool Timeouts.
# Stability: True Streaming (Range Requests), Memory Leak Fixes, Format Parsing.
# ==============================================================================

# 1. إعداد Logging احترافي
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 2. إعداد Session عالمية بكفاءة عالية
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100)
session.mount('http://', adapter)
session.mount('https://', adapter)
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8'
})

# 3. نظام Cache ذكي في الذاكرة (5 دقائق)
class TTLCache:
    def __init__(self, ttl=300):
        self.cache = {}
        self.ttl = ttl
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            if key in self.cache:
                item = self.cache[key]
                if time.time() - item['time'] < self.ttl:
                    return item['data']
                else:
                    del self.cache[key]
        return None

    def set(self, key, data):
        with self.lock:
            self.cache[key] = {'data': data, 'time': time.time()}

extract_cache = TTLCache(ttl=300)

# 4. Rate Limiting (حماية المسارات)
rate_limits = {}
rate_lock = threading.Lock()

def rate_limit(limit=30, window=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
            current = time.time()
            with rate_lock:
                # تنظيف القديم
                if ip in rate_limits and current - rate_limits[ip]['start'] > window:
                    del rate_limits[ip]
                
                if ip not in rate_limits:
                    rate_limits[ip] = {'count': 1, 'start': current}
                else:
                    if rate_limits[ip]['count'] >= limit:
                        logger.warning(f"Rate limit exceeded for IP: {ip}")
                        abort(429, description="تم تجاوز الحد المسموح من الطلبات. يرجى الانتظار دقيقة.")
                    rate_limits[ip]['count'] += 1
            return f(*args, **kwargs)
        return wrapped
    return decorator

# 5. الحماية من ثغرات SSRF
def is_safe_url(url):
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ('http', 'https'): return False
        hostname = parsed.hostname
        if not hostname: return False
        
        # تجنب طلبات localhost بالاسم
        if hostname.lower() in ['localhost', '127.0.0.1']: return False
        
        # Resolve IP والتأكد من عدم كونه Private
        ip_info = socket.getaddrinfo(hostname, None)
        for info in ip_info:
            ip_str = info[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_unspecified:
                return False
        return True
    except Exception as e:
        logger.error(f"SSRF Validation failed for URL {url}: {str(e)}")
        return False

# 6. إضافة Security Headers
@app.after_request
def apply_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    # Content-Security-Policy متساهل قليلاً لدعم inline styles/scripts الخاصة بالتطبيق ذو الملف الواحد
    response.headers['Content-Security-Policy'] = "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';"
    return response

# 7. إدارة Timeout صارمة
def execute_with_timeout(func, timeout, *args, **kwargs):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            logger.error(f"Execution Timeout reached ({timeout}s)")
            raise TimeoutError("Timeout")

# تحليل رسائل خطأ yt-dlp
def parse_ytdlp_error(error_msg):
    err = str(error_msg).lower()
    if "private" in err: return "المقطع خاص (Private). يرجى التأكد من الخصوصية."
    if "sign in" in err or "login" in err: return "المنصة تتطلب تسجيل دخول للوصول إلى هذا المقطع."
    if "geo" in err or "country" in err: return "المقطع محظور في منطقتنا الجغرافية."
    if "copyright" in err: return "المقطع محذوف بسبب حقوق النشر."
    if "timeout" in err: return "انتهى وقت الاتصال بالخادم. حاول مجدداً."
    return "تعذر استخراج البيانات. قد يكون الرابط غير صالح أو محمي."

# ==============================================================================
# HTML, CSS & JS (UI Untouched, Logic Enhanced)
# ==============================================================================

ICON_B64 = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzhiNWNmNiI+PHBhdGggZD0iTTE5IDloLTRWM0g5djZINWw3IDcgNy03ek01IDE4djJoMTR2LTJINXoiLz48L3N2Zz4="

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>Tahmilati | تحميلاتي</title>
    
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#0f172a">
    <link rel="apple-touch-icon" href="ICON_B64_PLACEHOLDER">
    <link rel="icon" href="ICON_B64_PLACEHOLDER">

    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.css" />
    
    <script src="https://cdn.plyr.io/3.7.8/plyr.js" defer></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gifshot/0.3.2/gifshot.min.js" defer></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.0/nouislider.min.js" defer></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js" defer></script>

    <style>
        :root {
            --bg-dark: #0f172a; --card-dark: #1e293b;
            --text-dark: #f8fafc; --text-muted: #94a3b8;
            --border-dark: rgba(255, 255, 255, 0.1);
            --primary: #8b5cf6; --neon-shadow: 0 0 15px rgba(139, 92, 246, 0.5);
        }

        body { --bg: var(--bg-dark); --card: var(--card-dark); --border: var(--border-dark); --text: var(--text-dark); }
        
        body.theme-tiktok { --primary: #00f2fe; --neon-shadow: 0 0 15px rgba(0, 242, 254, 0.5); }
        body.theme-insta { --primary: #f56040; --neon-shadow: 0 0 15px rgba(245, 96, 64, 0.5); }
        body.theme-facebook { --primary: #1877f2; --neon-shadow: 0 0 15px rgba(24, 119, 242, 0.5); }
        body.theme-general { --primary: #8b5cf6; --neon-shadow: 0 0 15px rgba(139, 92, 246, 0.5); }

        @keyframes chameleonBG { 0% {background-color: #0f172a;} 50% {background-color: #1e1b4b;} 100% {background-color: #0f172a;} }
        body.home-active { animation: chameleonBG 10s infinite alternate ease-in-out; }
        body:not(.home-active) { animation: none; background-color: var(--bg); transition: 0.5s ease; }

        html, body { height: 100dvh; margin: 0; padding: 0; overflow-x: hidden; font-family: 'Tajawal', sans-serif; color: var(--text); }
        .app-container { display: flex; flex-direction: column; height: 100%; max-width: 500px; margin: 0 auto; position: relative; }
        
        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: var(--card); border-bottom: 1px solid var(--border); z-index: 50; }
        .logo-title { margin: 0; font-weight: 900; font-size: 24px; color: var(--primary); text-shadow: var(--neon-shadow); cursor: pointer; }
        .nav-btns { display: flex; gap: 10px; }
        .icon-btn { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 10px; cursor: pointer; transition: 0.3s; font-size: 16px; }
        .icon-btn:hover { background: var(--primary); color: #fff; box-shadow: var(--neon-shadow); }

        .sidebar-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 99; display: none; opacity: 0; transition: 0.3s; }
        .sidebar { position: fixed; top: 0; right: -300px; width: 280px; height: 100%; background: var(--card); border-left: 1px solid var(--border); z-index: 100; box-shadow: -5px 0 20px rgba(0,0,0,0.3); transition: right 0.3s ease; display: flex; flex-direction: column; }
        .sidebar.open { right: 0; }
        .sidebar-header { padding: 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .sidebar-title { font-weight: 900; font-size: 18px; color: var(--text); }
        .close-sidebar { background: none; border: none; font-size: 22px; color: #ef4444; cursor: pointer; }
        .menu-list { list-style: none; padding: 10px 0; margin: 0; flex: 1; overflow-y: auto; }
        .menu-item { padding: 15px 20px; border-bottom: 1px solid var(--border); cursor: pointer; font-weight: bold; font-size: 15px; display: flex; align-items: center; gap: 12px; transition: 0.2s; color: var(--text); }
        .menu-item:hover { background: rgba(255,255,255,0.05); color: var(--primary); }

        .main-content { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .main-content::-webkit-scrollbar { width: 4px; }
        .main-content::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }

        .welcome-screen { text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; gap: 20px; animation: fadeIn 0.4s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        .welcome-title { font-size: 28px; font-weight: 900; color: var(--primary); margin: 0; text-shadow: var(--neon-shadow); }
        .welcome-desc { font-size: 14px; color: var(--text-muted); line-height: 1.6; }
        .welcome-steps { background: var(--card); border: 1px solid var(--border); padding: 15px; border-radius: 15px; text-align: right; width: 100%; font-size: 13px; font-weight: bold; list-style: none; box-sizing: border-box; }
        .welcome-steps li { margin-bottom: 8px; color: var(--text); }
        
        .pwa-btn { display: flex; align-items: center; justify-content: center; gap: 8px; background: #2563eb; color: white; padding: 12px 20px; border-radius: 15px; font-weight: bold; font-size: 14px; border: none; cursor: pointer; width: 100%; box-sizing: border-box; transition: 0.3s; }
        .pwa-btn:hover { background: #1d4ed8; }
        
        .live-counter { text-align: center; font-size: 13px; font-weight: bold; color: var(--text); background: var(--card); padding: 12px; border-radius: 15px; border: 1px solid var(--border); width: 100%; box-sizing: border-box; margin-top: auto;}
        .creator-badge { display: flex; align-items: center; justify-content: center; gap: 8px; background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); color: white; padding: 12px; border-radius: 15px; text-decoration: none; font-weight: bold; font-size: 14px; width: 100%; box-sizing: border-box; transition: 0.3s;}

        .view-section { display: none; flex-direction: column; gap: 15px; animation: fadeIn 0.4s ease; }
        .input-card { background: var(--card); padding: 18px; border-radius: 20px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 12px; }
        .card-title { font-size: 16px; font-weight: 900; display: flex; align-items: center; gap: 10px; color: var(--text); }
        .input-row { display: flex; gap: 8px; align-items: center; background: rgba(0,0,0,0.2); border: 1px solid var(--border); border-radius: 12px; padding-right: 12px; }
        .input-row:focus-within { border-color: var(--primary); }
        input[type="text"] { flex: 1; padding: 15px 5px; background: transparent; border: none; color: var(--text); font-size: 14px; outline: none; font-family: 'Tajawal'; }
        .action-icon { color: var(--text-muted); cursor: pointer; padding: 10px; transition: 0.3s; font-size: 16px; }
        .action-icon:hover { color: var(--primary); }
        .btn-main { width: 100%; padding: 15px; background: var(--primary); color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: 900; cursor: pointer; font-family: 'Tajawal'; box-shadow: var(--neon-shadow); transition: 0.3s; }

        .result-container { display: none; flex-direction: column; gap: 15px; background: var(--card); padding: 15px; border-radius: 20px; border: 1px solid var(--border); }
        .video-header { display: flex; gap: 15px; align-items: center; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
        .thumb { width: 60px; height: 60px; border-radius: 12px; object-fit: cover; }
        .title { font-size: 13px; font-weight: bold; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; color: var(--text); }
        
        .filename-box { background: rgba(0,0,0,0.2); border: 1px dashed var(--border); border-radius: 12px; padding: 10px; display: flex; align-items: center; gap: 10px; margin-bottom: 5px;}
        .filename-box input { flex: 1; background: transparent; border: none; color: var(--primary); font-weight: bold; font-family: 'Tajawal'; outline: none; font-size: 13px; }
        
        .video-wrapper { max-height: 280px; width: 100%; border-radius: 15px; overflow: hidden; background: #000; display: flex; justify-content: center; align-items: center; }
        .plyr__video-wrapper video { max-height: 280px !important; object-fit: contain; }

        .image-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; max-height: 350px; overflow-y: auto; border-radius: 15px; padding-right: 5px; }
        .image-grid::-webkit-scrollbar { width: 3px; }
        .image-grid::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }
        .img-card { position: relative; border-radius: 10px; overflow: hidden; border: 1px solid var(--border); }
        .img-card img { width: 100%; display: block; object-fit: cover; }
        .img-download-btn { position: absolute; bottom: 5px; left: 5px; background: rgba(0,0,0,0.7); color: #fff; border: none; padding: 8px; border-radius: 8px; cursor: pointer; backdrop-filter: blur(5px); transition: 0.3s;}
        .img-download-btn:hover { background: var(--primary); }

        .action-grid { display: flex; flex-direction: column; gap: 8px; }
        .btn-row { display: flex; gap: 8px; width: 100%; position: relative; }
        .btn-action { flex: 1; padding: 12px 10px; border: none; border-radius: 12px; font-weight: 900; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 13px; color: white; font-family: 'Tajawal'; transition: 0.3s; }
        .btn-icon-sq { background: rgba(255,255,255,0.05); width: 45px; flex: none; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--text); cursor: pointer; border: 1px solid var(--border); font-size: 16px; transition: 0.3s; }
        .btn-icon-sq:hover { background: var(--primary); color: white; border-color: var(--primary); }
        
        .quality-dropdown { position: absolute; bottom: calc(100% + 5px); left: 0; width: 100%; background: var(--card); border: 1px solid var(--border); border-radius: 12px; box-shadow: 0 10px 20px rgba(0,0,0,0.5); display: none; flex-direction: column; z-index: 100; overflow: hidden; }
        .quality-btn { padding: 12px; border: none; background: transparent; color: var(--text); font-family: 'Tajawal'; font-weight: bold; font-size: 13px; border-bottom: 1px solid var(--border); cursor: pointer; text-align: center; }
        .quality-btn:hover { background: var(--primary); color: white; }

        .bg-mp4 { background: #10b981; } .bg-mp3 { background: #8b5cf6; } .bg-wa { background: #06b6d4; } 
        .bg-magic { background: #ef4444; } .bg-gif { background: #f59e0b; }

        .gif-editor { display: none; background: rgba(0,0,0,0.15); padding: 20px; border-radius: 15px; border: 1px dashed var(--primary); margin-top: 5px; }
        .slider-container { margin: 35px 10px 10px 10px; }
        .noUi-connect { background: var(--primary); }
        .noUi-handle { border-radius: 50%; box-shadow: var(--neon-shadow); background: #fff; border: 2px solid var(--primary); outline: none; }

        .qr-modal { display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 1000; justify-content: center; align-items: center; flex-direction: column; backdrop-filter: blur(5px); }
        .qr-box { background: var(--card); border: 1px solid var(--border); padding: 25px; border-radius: 20px; display: flex; flex-direction: column; align-items: center; gap: 15px; }
        .close-qr { background: #ef4444; color: white; border: none; padding: 10px 30px; border-radius: 10px; font-weight: bold; cursor: pointer; font-family: 'Tajawal'; font-size: 14px; }
        .status-msg { text-align: center; font-size: 13px; display: none; font-weight: bold; padding: 10px; border-radius: 10px; background: rgba(0,0,0,0.1); margin-top: 10px; }

        #iosToast { visibility: hidden; min-width: 250px; background-color: #333; color: #fff; text-align: center; border-radius: 12px; padding: 16px; position: fixed; z-index: 9999; left: 50%; bottom: 30px; transform: translateX(-50%); font-size: 13px; box-shadow: 0 5px 15px rgba(0,0,0,0.5); border: 1px solid var(--primary); opacity: 0; transition: opacity 0.5s; line-height: 1.5; font-weight: bold;}
        #iosToast.show { visibility: visible; opacity: 1; }
    </style>
</head>
<body class="home-active">

    <div class="app-container">
        <div class="top-bar">
            <h3 class="logo-title" onclick="resetToHome()">Tahmilati</h3>
            <div class="nav-btns">
                <button class="icon-btn" onclick="location.reload()" title="تحديث"><i class="fas fa-sync-alt"></i></button>
                <button class="icon-btn" onclick="toggleSidebar()" title="القائمة"><i class="fas fa-bars"></i></button>
            </div>
        </div>

        <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <span class="sidebar-title">أقسام التنزيل</span>
                <button class="close-sidebar" onclick="toggleSidebar()"><i class="fas fa-times"></i></button>
            </div>
            <ul class="menu-list">
                <li class="menu-item" onclick="switchView('insta', 'theme-insta')"><i class="fab fa-instagram fa-lg" style="color: #f56040; width: 25px;"></i> إنستغرام (عام)</li>
                <li class="menu-item" onclick="switchView('tiktok', 'theme-tiktok')"><i class="fab fa-tiktok fa-lg" style="color: #00f2fe; width: 25px;"></i> تيك توك (بدون حقوق)</li>
                <li class="menu-item" onclick="switchView('facebook', 'theme-facebook')"><i class="fab fa-facebook fa-lg" style="color: #1877f2; width: 25px;"></i> فيسبوك (الروابط العامة)</li>
                <li class="menu-item" onclick="switchView('general', 'theme-general')"><i class="fas fa-link fa-lg" style="color: #8b5cf6; width: 25px;"></i> تحميل عام</li>
            </ul>
        </div>

        <div class="main-content">
            <div id="view-welcome" class="welcome-screen view-section" style="display: flex;">
                <h1 class="welcome-title">Tahmilati | تحميلاتي</h1>
                <p class="welcome-desc">المنصة الشاملة لاستخراج وتنزيل الوسائط المتعددة بدقة عالية.</p>
                <ul class="welcome-steps" dir="rtl">
                    <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 1. انقر على أيقونة القائمة (☰).</li>
                    <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 2. حدد المنصة المراد التنزيل منها.</li>
                    <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 3. أدخل الرابط المباشر (العام) للمقطع.</li>
                </ul>
                <button class="pwa-btn" id="installPwaBtn"><i class="fas fa-arrow-circle-down"></i> تثبيت التطبيق بالهاتف</button>
                <div class="live-counter"><i class="fas fa-chart-line"></i> تم معالجة <span id="countNum">1,425,890</span> طلب بنجاح</div>
                <a href="https://www.instagram.com/_otnn" target="_blank" class="creator-badge"><i class="fab fa-instagram"></i> المصمم: @_otnn</a>
            </div>

            <script>
                const platforms = [
                    { id: 'insta', icon: 'fab fa-instagram', color: '#f56040', title: 'تنزيل من إنستغرام', placeholder: 'رابط البوست أو الريلز المباشر...' },
                    { id: 'tiktok', icon: 'fab fa-tiktok', color: '#00f2fe', title: 'تنزيل من تيك توك', placeholder: 'رابط مقطع التيك توك (فيديو/صور)...' },
                    { id: 'facebook', icon: 'fab fa-facebook', color: '#1877f2', title: 'تنزيل من فيسبوك', placeholder: 'رابط الفيديو العام...' },
                    { id: 'general', icon: 'fas fa-link', color: '#8b5cf6', title: 'تنزيل عام', placeholder: 'أي رابط وسائط مباشر...' }
                ];
                
                platforms.forEach(p => {
                    document.write(`
                    <div id="view-${p.id}" class="view-section">
                        <div class="input-card">
                            <div class="card-title"><i class="${p.icon}" style="color: ${p.color}; font-size: 20px;"></i> ${p.title}</div>
                            <div class="input-row">
                                <input type="text" id="input-${p.id}" placeholder="${p.placeholder}">
                                <i class="fas fa-times action-icon" onclick="document.getElementById('input-${p.id}').value = ''"></i>
                                <i class="fas fa-paste action-icon" onclick="navigator.clipboard.readText().then(t => document.getElementById('input-${p.id}').value = t).catch(e => console.log(e))"></i>
                            </div>
                            <button class="btn-main" onclick="processClientRequest('${p.id}')">بدء الاستخراج</button>
                            <div class="status-msg" id="status-${p.id}"></div>
                        </div>
                        <div id="res-${p.id}" class="result-container">
                            <div class="filename-box">
                                <i class="fas fa-pen" style="color:var(--text-muted)"></i>
                                <input type="text" class="custom-filename-input" placeholder="سمي الملف قبل التحميل (اختياري)...">
                            </div>
                            <div class="media-box" style="display: none; flex-direction: column; gap: 15px;"></div>
                        </div>
                    </div>`);
                });
            </script>
        </div>
    </div>

    <div id="iosToast">أبل تمنع الحفظ المباشر في الاستوديو.<br>سيتم حفظ المقطع في <b>"الملفات"</b>.<br>لنقله: افتح الملف ⇦ زر المشاركة ⇦ حفظ الفيديو.</div>

    <div class="qr-modal" id="qrModal">
        <div class="qr-box">
            <span style="color:var(--text); font-weight:bold; font-size:16px;">امسح الباركود للتحميل المباشر</span>
            <div id="qrCodeDiv" style="background: white; padding: 15px; border-radius: 15px;"></div>
            <button class="close-qr" onclick="document.getElementById('qrModal').style.display='none'">إغلاق</button>
        </div>
    </div>

    <script>
        setInterval(() => { fetch('/ping').catch(e => console.log('Ping failed:', e)); }, 240000); 

        let count = 1425890;
        setInterval(() => { count += Math.floor(Math.random() * 3); document.getElementById('countNum').innerText = count.toLocaleString(); }, 3500);

        let activePlayer = null;
        let globalVideoUrl = '';
        let deferredPrompt;

        if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
            const installBtn = document.getElementById('installPwaBtn');
            if(installBtn) installBtn.style.display = 'none';
        } else {
            window.addEventListener('beforeinstallprompt', (e) => {
                e.preventDefault();
                deferredPrompt = e;
                const installBtn = document.getElementById('installPwaBtn');
                if(installBtn) installBtn.style.display = 'flex';
            });
        }

        const btnInstall = document.getElementById('installPwaBtn');
        if(btnInstall) {
            btnInstall.addEventListener('click', async () => {
                if (deferredPrompt) {
                    deferredPrompt.prompt();
                    const { outcome } = await deferredPrompt.userChoice;
                    if (outcome === 'accepted') {
                        document.getElementById('installPwaBtn').style.display = 'none';
                    }
                    deferredPrompt = null;
                } else {
                    alert('لتثبيت التطبيق:\\n1. في الايفون (Safari): اضغط على زر المشاركة ثم "إضافة للشاشة الرئيسية".\\n2. في الاندرويد: اضغط على القائمة بالمتصفح ثم "تثبيت التطبيق".');
                }
            });
        }

        if ('serviceWorker' in navigator) { 
            window.addEventListener('load', () => { 
                navigator.serviceWorker.register('/sw.js').catch(e => console.log('SW registration failed:', e)); 
            }); 
        }

        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            if (sidebar && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open'); 
                if(overlay) {
                    overlay.style.opacity = '0'; 
                    setTimeout(() => overlay.style.display = 'none', 300);
                }
            } else {
                if(overlay) {
                    overlay.style.display = 'block'; 
                    setTimeout(() => overlay.style.opacity = '1', 10); 
                }
                if(sidebar) sidebar.classList.add('open');
            }
        }

        function resetToHome() {
            document.querySelectorAll('.view-section').forEach(el => el.style.display = 'none');
            const welcome = document.getElementById('view-welcome');
            if(welcome) welcome.style.display = 'flex';
            document.body.className = 'home-active';
        }

        function switchView(viewName, themeClass) {
            document.querySelectorAll('.view-section').forEach(el => el.style.display = 'none');
            const view = document.getElementById('view-' + viewName);
            if(view) view.style.display = 'flex';
            document.body.className = themeClass; 
            toggleSidebar();
        }

        function showQR(url) {
            const modal = document.getElementById('qrModal');
            const qrDiv = document.getElementById('qrCodeDiv');
            if(modal && qrDiv) {
                modal.style.display = 'flex';
                qrDiv.innerHTML = '';
                new QRCode(qrDiv, { text: url, width: 180, height: 180, colorDark : "#000", colorLight : "#fff" });
            }
        }

        function copyLink(url) {
            const temp = document.createElement("input"); 
            temp.value = url; 
            document.body.appendChild(temp); 
            temp.select(); 
            document.execCommand("copy"); 
            document.body.removeChild(temp);
            alert("تم نسخ الرابط بنجاح.");
        }

        function toggleQualityMenu(btn) {
            const menu = btn.parentElement.querySelector('.quality-dropdown'); 
            if(menu) {
                menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
            }
        }

        function showIosToast() {
            const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
            if(isIOS) {
                const toast = document.getElementById("iosToast");
                if(toast) {
                    toast.className = "show";
                    setTimeout(function(){ toast.className = toast.className.replace("show", ""); }, 6000);
                }
            }
        }

        function getSmartFileName(containerId, extension, suggestedName) {
            const inputEl = document.querySelector(`#${containerId} .custom-filename-input`);
            let customName = inputEl && inputEl.value.trim() !== "" ? inputEl.value.trim() : (suggestedName || "");
            customName = customName.replace(/[<>:"/\\\\|?*\\x00-\\x1F]/g, '_').trim();
            if(customName) {
                return customName + extension;
            } else {
                const random5 = Math.floor(10000 + Math.random() * 90000);
                return `Tahmilati_${random5}${extension}`;
            }
        }

        function forceAutoDownload(url, containerId, extension, title) {
            const filename = getSmartFileName(containerId, extension, title);
            if(extension.includes('mp4') || extension.includes('jpg')) { showIosToast(); }

            // إذا كان الرابط هو بروكسي داخلي، نمرر اسم الملف كـ Parameter حتى يرسله الباك-إند
            let finalUrl = url;
            if(url.includes('/proxy_stream')) {
                finalUrl += `&filename=${encodeURIComponent(filename.replace(extension, ''))}`;
            }

            const a = document.createElement('a'); 
            a.href = finalUrl; 
            a.download = filename; 
            document.body.appendChild(a); 
            a.click(); 
            document.body.removeChild(a);
        }

        async function fetchFullAudio(trackName, btnElement, containerId) {
            const origHTML = btnElement.innerHTML;
            btnElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري استخراج النسخة الأصلية...';
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
                    forceAutoDownload(audioSafeUrl, containerId, '.mp3', trackName);
                    btnElement.innerHTML = '<i class="fas fa-check"></i> اكتمل التنزيل!';
                    btnElement.style.background = '#10b981';
                } else {
                    btnElement.innerHTML = '<i class="fas fa-times"></i> غير متاح حالياً.';
                    btnElement.style.background = '#ef4444';
                }
            } catch(e) {
                btnElement.innerHTML = '<i class="fas fa-wifi"></i> خطأ بالاتصال.';
            }
            setTimeout(() => { btnElement.innerHTML = origHTML; btnElement.style.background = ''; btnElement.disabled = false; }, 4000);
        }

        function initGifEditor(containerId, duration, title) {
            const editor = document.querySelector(`#${containerId} .gif-editor`); 
            if (!editor) return;
            
            editor.style.display = 'block';
            const sliderDiv = editor.querySelector('.timeSlider');
            if(!sliderDiv) return;

            if(sliderDiv.noUiSlider) { sliderDiv.noUiSlider.destroy(); }
            
            noUiSlider.create(sliderDiv, { 
                start: [0, Math.min(5, duration || 15)], 
                connect: true, step: 1, 
                range: { 'min': 0, 'max': Math.max(duration || 15, 5) } 
            });
            
            sliderDiv.noUiSlider.on('update', function (values) {
                const startVal = editor.querySelector('.startVal');
                const endVal = editor.querySelector('.endVal');
                if(startVal) startVal.innerText = Math.round(values[0]) + 's'; 
                if(endVal) endVal.innerText = Math.round(values[1]) + 's';
            });
            
            const startBtn = editor.querySelector('.gifStartBtn');
            if(startBtn) {
                startBtn.onclick = function() {
                    const btn = this; 
                    const status = editor.querySelector('.gifStatus'); 
                    btn.disabled = true; 
                    if(status) {
                        status.style.display = 'block'; 
                        status.style.color = 'var(--primary)';
                        status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري إنشاء الصورة...';
                    }
                    
                    const vals = sliderDiv.noUiSlider.get();
                    const offset = parseInt(vals[0]);
                    const numFrames = (parseInt(vals[1]) - parseInt(vals[0])) * 10;
                    
                    gifshot.createGIF({
                        'video': [globalVideoUrl], 'offset': offset, 'numFrames': numFrames, 
                        'frameDuration': 1, 'gifWidth': 320, 'gifHeight': 320
                    }, function(obj) {
                        if(!obj.error) { 
                            // تحويل Base64 إلى Blob لإنشاء رابط تحميل صحيح
                            fetch(obj.image)
                                .then(res => res.blob())
                                .then(blob => {
                                    const blobUrl = window.URL.createObjectURL(blob);
                                    forceAutoDownload(blobUrl, containerId, '.gif', title + '_GIF');
                                });
                            if(status) {
                                status.innerHTML = '<i class="fas fa-check"></i> اكتمل المعالجة.'; 
                                status.style.color = '#10b981';
                            }
                        } else { 
                            if(status) {
                                status.innerHTML = '<i class="fas fa-times"></i> خطأ بمعالجة الفيديو.'; 
                                status.style.color = '#ef4444';
                            }
                        }
                        setTimeout(()=> { if(status) status.style.display = 'none'; btn.disabled = false; }, 3000);
                    });
                };
            }
        }

        async function processClientRequest(platform) {
            const inputEl = document.getElementById('input-' + platform);
            if(!inputEl) return;
            const val = inputEl.value.trim(); 
            if(!val) return;

            const resContainer = document.getElementById('res-' + platform);
            const statusMsg = document.getElementById('status-' + platform);
            const mediaBox = resContainer ? resContainer.querySelector('.media-box') : null;
            
            if(!resContainer || !statusMsg || !mediaBox) return;

            resContainer.style.display = 'flex'; 
            mediaBox.style.display = 'none'; 
            statusMsg.style.display = 'block'; 
            statusMsg.style.color = 'var(--primary)';
            
            if(['insta', 'facebook'].includes(platform)) {
                statusMsg.innerHTML = '<i class="fas fa-layer-group fa-spin"></i> جاري البحث واستخراج البيانات بأمان...';
            } else {
                statusMsg.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري معالجة الرابط...';
            }

            if(activePlayer) { activePlayer.destroy(); activePlayer = null; }

            let apiEndpoint = `/api/${platform}`;

            try {
                let r = await fetch(apiEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: val })
                });
                
                if (!r.ok) {
                    if (r.status === 429) throw new Error("تم تجاوز الحد المسموح للطلبات. يرجى الانتظار.");
                    throw new Error("خطأ في الاتصال بالخادم الداخلي.");
                }
                let res = await r.json();

                if(res.success) {
                    statusMsg.style.display = 'none';
                    let containerId = 'res-' + platform;
                    
                    if (res.is_image) {
                        renderImageGrid(res.title, res.images || [], containerId);
                    } else {
                        // التأكد من أن الصور المصغرة تمر عبر البروكسي لمنع حظر Hotlink
                        let safeThumb = res.thumbnail ? `/proxy_stream?url=${encodeURIComponent(res.thumbnail)}&ext=jpg` : '';
                        let internalVidPlay = res.video_url ? `/proxy_stream?url=${encodeURIComponent(res.video_url)}&ext=mp4` : '';
                        let internalAudPlay = res.audio_url ? `/proxy_stream?url=${encodeURIComponent(res.audio_url)}&ext=mp3` : '';
                        let absoluteQrUrl = window.location.origin + internalVidPlay;

                        renderMediaResult(res.title || 'فيديو', safeThumb, internalVidPlay, internalAudPlay, absoluteQrUrl, res.duration || 15, platform, containerId, res.track_name, res.is_pure_audio, res.formats);
                    }
                } else {
                    statusMsg.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${res.error || 'حدث خطأ غير معروف'}`;
                    statusMsg.style.color = '#ef4444';
                }
            } catch(e) {
                statusMsg.innerHTML = `<i class="fas fa-wifi"></i> ${e.message}`; 
                statusMsg.style.color = '#ef4444';
            }
        }

        function renderImageGrid(title, imagesArray, containerId) {
            const mediaBox = document.querySelector(`#${containerId} .media-box`); 
            if(!mediaBox) return;

            let imgGridHtml = `<div class="image-grid">`;
            imagesArray.forEach((imgUrl, index) => {
                let safeUrl = `/proxy_stream?url=${encodeURIComponent(imgUrl)}&ext=jpg`;
                imgGridHtml += `
                <div class="img-card">
                    <img src="${safeUrl}" loading="lazy" alt="image">
                    <button class="img-download-btn" onclick="forceAutoDownload('${safeUrl}', '${containerId}', '.jpg', '${title}_${index+1}')" title="تحميل الصورة"><i class="fas fa-download"></i></button>
                </div>`;
            });
            imgGridHtml += `</div>`;

            mediaBox.innerHTML = `
                <div class="video-header"><div class="title">${title} (مجموعة صور)</div></div>
                ${imgGridHtml}
            `;
            mediaBox.style.display = 'flex';
        }

        function renderMediaResult(title, thumbnail, vidUrl, audUrl, qrUrl, duration, platform, containerId, trackName, isPureAudio, formats) {
            const mediaBox = document.querySelector(`#${containerId} .media-box`); 
            if(!mediaBox) return;
            globalVideoUrl = vidUrl;
            
            let magicBtnHtml = '';
            if (trackName) {
                let safeTrackName = trackName.replace(/'/g, "\\'");
                magicBtnHtml = `
                <div class="btn-row" style="margin-bottom: 10px;">
                    <button onclick="fetchFullAudio('${safeTrackName}', this, '${containerId}')" class="btn-action bg-magic" style="width:100%;">
                        <i class="fas fa-magic"></i> جلب الأغنية / المعزوفة الأصلية (MP3)
                    </button>
                </div>`;
            }

            let audBtnHtml = '';
            if (isPureAudio !== false && audUrl) {
                audBtnHtml = `<button onclick="forceAutoDownload('${audUrl}', '${containerId}', '.mp3', '${title}')" class="btn-action bg-mp3"><i class="fas fa-music"></i> استخراج الصوت (MP3)</button>`;
            } else {
                audBtnHtml = `<button class="btn-action bg-mp3" disabled style="opacity:0.6; cursor:not-allowed;" title="الصوت المدمج غير قابل للفصل"><i class="fas fa-microphone-slash"></i> الصوت منفصل غير متاح</button>`;
            }

            // توليد قائمة الجودات الفعلية من البيانات القادمة من السيرفر
            let qualityDropdownHtml = '';
            if (formats && formats.length > 0) {
                formats.forEach(f => {
                    let fUrl = `/proxy_stream?url=${encodeURIComponent(f.url)}&ext=mp4`;
                    qualityDropdownHtml += `<button class="quality-btn" onclick="forceAutoDownload('${fUrl}', '${containerId}', '.mp4', '${title}_${f.label}')">${f.label} (فعلية)</button>`;
                });
            } else {
                qualityDropdownHtml = `
                    <button class="quality-btn" onclick="forceAutoDownload('${vidUrl}', '${containerId}', '.mp4', '${title}_HQ')">الجودة الافتراضية</button>
                `;
            }

            let gifHtml = '';
            if (platform === 'tiktok') {
                gifHtml = `
                <div class="gif-editor">
                    <div style="font-size: 14px; font-weight: bold; margin-bottom: 15px; color: var(--text);"><i class="fas fa-images"></i> إنشاء صورة متحركة بالسحب (GIF):</div>
                    <div class="timeSlider slider-container"></div>
                    <div style="display:flex; justify-content: space-between; font-size:12px; color:var(--primary); font-weight:bold; margin-bottom: 15px;">
                        <span class="startVal">0s</span> <span class="endVal">5s</span>
                    </div>
                    <button class="btn-action bg-gif gifStartBtn" style="width: 100%;"><i class="fas fa-crop-alt"></i> توليد الصورة</button>
                    <div class="status-msg gifStatus"></div>
                </div>`;
            }

            mediaBox.innerHTML = `
                <div class="video-header"><img src="${thumbnail}" class="thumb" alt="thumb"><div class="title">${title}</div></div>
                <div class="video-wrapper">
                    <video class="plyr-player" playsinline controls crossorigin="anonymous"></video>
                </div>
                <div class="action-grid">
                    ${magicBtnHtml}
                    <div class="btn-row">
                        <button onclick="forceAutoDownload('${vidUrl}', '${containerId}', '.mp4', '${title}')" class="btn-action bg-mp4"><i class="fas fa-download"></i> تنزيل الفيديو</button>
                        <button onclick="toggleQualityMenu(this)" class="btn-icon-sq" title="خيارات الجودة"><i class="fas fa-cog"></i></button>
                        <div class="quality-dropdown">
                            ${qualityDropdownHtml}
                        </div>
                        <button onclick="copyLink('${qrUrl}')" class="btn-icon-sq" title="نسخ الرابط"><i class="fas fa-link"></i></button>
                        <button onclick="showQR('${qrUrl}')" class="btn-icon-sq" title="باركود"><i class="fas fa-qrcode"></i></button>
                    </div>
                    <div class="btn-row">
                        ${audBtnHtml}
                    </div>
                </div>
                ${gifHtml}
            `;
            
            const videoEl = mediaBox.querySelector('.plyr-player'); 
            if(videoEl) {
                videoEl.src = vidUrl;
                activePlayer = new Plyr(videoEl, { controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'fullscreen'] });
            }

            if (platform === 'tiktok' || platform === 'insta') {
                const actionGrid = mediaBox.querySelector('.action-grid');
                if(actionGrid) {
                    const waRow = document.createElement('div');
                    waRow.className = 'btn-row';
                    waRow.innerHTML = `<button onclick="forceAutoDownload('${vidUrl}', '${containerId}', '.mp4', '${title}_WA')" class="btn-action bg-wa" style="width:100%;"><i class="fab fa-whatsapp"></i> نسخة مضغوطة (للواتساب)</button>`;
                    actionGrid.appendChild(waRow);
                }
            }
            
            if (platform === 'tiktok') {
                initGifEditor(containerId, duration, title);
            }
            
            mediaBox.style.display = 'flex';
        }
    </script>
</body>
</html>
"""

HTML_LAYOUT = HTML_LAYOUT.replace("ICON_B64_PLACEHOLDER", ICON_B64)

# ==============================================================================
# Backend Routes & APIs
# ==============================================================================

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Tahmilati | تحميلاتي",
        "short_name": "Tahmilati",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#8b5cf6",
        "orientation": "portrait",
        "icons": [{ "src": ICON_B64, "sizes": "512x512", "type": "image/svg+xml" }]
    })

@app.route('/sw.js')
def service_worker():
    return Response("self.addEventListener('install', (e) => { self.skipWaiting(); }); self.addEventListener('fetch', (e) => {});", mimetype='application/javascript')

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

@app.route('/ping')
def ping_server():
    return "OK", 200

@app.route('/api/full_audio', methods=['POST'])
@rate_limit(limit=15, window=60)
def search_full_audio():
    data = request.json or {}
    track_name = data.get('track_name')
    if not track_name: 
        return jsonify({"success": False})
    
    clean_name = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', track_name).strip()
    
    # فحص الـ Cache
    cache_key = f"audio_{clean_name}"
    cached = extract_cache.get(cache_key)
    if cached: return jsonify(cached)

    try:
        ydl_opts = {
            'quiet': True, 'no_warnings': True, 'format': 'bestaudio/best', 
            'noplaylist': True, 'default_search': 'ytsearch1'
        }
        def fetch_audio():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(clean_name, download=False)
                
        info = execute_with_timeout(fetch_audio, 15)
        
        if info and info.get('entries') and len(info['entries']) > 0:
            result = {"success": True, "audio_url": info['entries'][0].get('url')}
            extract_cache.set(cache_key, result)
            return jsonify(result)
    except Exception as e:
        logger.error(f"Audio Search failed for {clean_name}: {str(e)}")
    
    return jsonify({"success": False})

@app.route('/api/tiktok', methods=['POST'])
@rate_limit(limit=30, window=60)
def process_tiktok():
    data = request.json or {}
    url = is_safe_url(data.get('url', ''))
    if not url: return jsonify({"success": False, "error": "رابط غير صالح أو غير آمن."})
    
    cache_key = f"tiktok_{url}"
    cached = extract_cache.get(cache_key)
    if cached: return jsonify(cached)

    try:
        r = session.get(f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}", timeout=15)
        r.raise_for_status()
        res_json = r.json()
        
        if res_json.get('code') == 0:
            v = res_json.get('data', {})
            if 'images' in v and isinstance(v.get('images'), list):
                result = {"success": True, "title": v.get('title', 'صور تيك توك'), "is_image": True, "images": v['images']}
                extract_cache.set(cache_key, result)
                return jsonify(result)
            
            music_info = v.get('music_info', {})
            track_name = f"{music_info.get('title', '')} {music_info.get('author', '')}".strip() if music_info.get('title') else None
            
            result = {
                "success": True, "title": v.get('title', 'مقطع تيك توك'),
                "thumbnail": v.get('cover', ''),
                "video_url": v.get('play'), "audio_url": v.get('music'), 
                "is_pure_audio": True, "duration": v.get('duration', 15), "track_name": track_name, "is_image": False,
                "formats": [] # TikWM لا يعطي جودات متعددة
            }
            extract_cache.set(cache_key, result)
            return jsonify(result)
        else:
            logger.warning(f"TikWM Error: {res_json.get('msg')}")
            return jsonify({"success": False, "error": "المقطع محذوف أو خاص."})
    except Exception as e:
        logger.error(f"TikTok process failed: {str(e)}")
        return jsonify({"success": False, "error": "انتهى وقت الاتصال بخوادم الاستخراج."})

def extract_real_formats(info):
    """استخراج الجودات المتوفرة فعلياً من yt-dlp"""
    formats_dict = {}
    for f in info.get('formats', []):
        if f.get('vcodec') != 'none' and f.get('height') and f.get('url'):
            h = f.get('height')
            if h not in formats_dict: formats_dict[h] = f.get('url')
    
    # الترتيب من الأعلى للأقل (مثلا 1080, 720, 480)
    sorted_formats = sorted(formats_dict.items(), reverse=True)
    return [{"label": f"{h}p", "url": url} for h, url in sorted_formats[:4]] # نعطي أفضل 4 جودات فقط لعدم زحمة الواجهة

def robust_waterfall_extract(url, platform_name):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    
    # 1. Cobalt API
    try:
        r_vid = session.post("https://api.cobalt.tools/api/json", json={"url": url, "vQuality": "max"}, headers=headers, timeout=8)
        if r_vid.status_code == 200:
            res_json = r_vid.json()
            if res_json.get('url'):
                vid_url = res_json.get('url')
                aud_url = vid_url
                is_pure = False
                try:
                    r_aud = session.post("https://api.cobalt.tools/api/json", json={"url": url, "isAudioOnly": True}, headers=headers, timeout=6)
                    if r_aud.status_code == 200 and r_aud.json().get('url'): 
                        aud_url = r_aud.json().get('url')
                        is_pure = True
                except Exception as e:
                    logger.warning(f"Cobalt Audio fallback failed: {str(e)}")
                return {"success": True, "title": f"مقطع {platform_name} (العام)", "thumbnail": "", "video_url": vid_url, "audio_url": aud_url, "is_pure_audio": is_pure, "duration": 15, "is_image": False, "formats": []}
    except Exception as e:
        logger.error(f"Cobalt failed for {platform_name}: {str(e)}")

    # 2. WUK API Fallback
    try:
        r_vid2 = session.post("https://co.wuk.sh/api/json", json={"url": url, "vQuality": "max"}, headers=headers, timeout=8)
        if r_vid2.status_code == 200:
            res_json2 = r_vid2.json()
            if res_json2.get('url'):
                vid_url2 = res_json2.get('url')
                return {"success": True, "title": f"مقطع {platform_name}", "thumbnail": "", "video_url": vid_url2, "audio_url": vid_url2, "is_pure_audio": False, "duration": 15, "is_image": False, "formats": []}
    except Exception as e:
        logger.error(f"WUK API failed for {platform_name}: {str(e)}")

    # 3. Siputzx Fallback
    try:
        api_path = 'igdl' if platform_name == 'إنستغرام' else 'facebook'
        r_vid3 = session.get(f"https://api.siputzx.my.id/api/d/{api_path}?url={url}", timeout=8)
        if r_vid3.status_code == 200:
            data = r_vid3.json().get('data', [])
            if data and len(data) > 0 and data[0].get('url'):
                vid_url3 = data[0].get('url')
                return {"success": True, "title": f"مقطع {platform_name}", "thumbnail": "", "video_url": vid_url3, "audio_url": vid_url3, "is_pure_audio": False, "duration": 15, "is_image": False, "formats": []}
    except Exception as e:
        logger.error(f"Siputzx API failed for {platform_name}: {str(e)}")

    # 4. Ultimate Fallback (yt-dlp)
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'format': 'bestvideo+bestaudio/best', 'extractor_args': {'facebook': {'player_client': ['android', 'ios']}}}
        def fetch_ytdlp():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
                
        info = execute_with_timeout(fetch_ytdlp, 15)
        
        if info:
            video_url = info.get('url')
            if not video_url:
                v_formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
                if v_formats: video_url = v_formats[-1].get('url')
            
            if video_url:
                audio_url = video_url
                is_pure_audio = False
                a_formats = [f for f in info.get('formats', []) if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
                if a_formats:
                    audio_url = a_formats[-1].get('url')
                    is_pure_audio = True
                
                real_formats = extract_real_formats(info)

                return {"success": True, "title": info.get('title', f'مقطع {platform_name}'), "thumbnail": info.get('thumbnail', ''), "video_url": video_url, "audio_url": audio_url, "is_pure_audio": is_pure_audio, "duration": info.get('duration', 15), "is_image": False, "formats": real_formats}
    except Exception as e:
        logger.error(f"yt-dlp failed for {platform_name}: {str(e)}")
        return {"success": False, "error": parse_ytdlp_error(e)}
    
    return {"success": False, "error": "تعذر الاستخراج، تأكد أن الرابط عام (Public)."}

@app.route('/api/insta', methods=['POST'])
@rate_limit(limit=30, window=60)
def process_insta():
    data = request.json or {}
    url = is_safe_url(data.get('url', ''))
    if not url: return jsonify({"success": False, "error": "رابط غير صالح."})
    
    cache_key = f"insta_{url}"
    cached = extract_cache.get(cache_key)
    if cached: return jsonify(cached)
    
    res = robust_waterfall_extract(url, "إنستغرام")
    if res.get('success'): extract_cache.set(cache_key, res)
    return jsonify(res)

@app.route('/api/facebook', methods=['POST'])
@rate_limit(limit=30, window=60)
def process_facebook():
    data = request.json or {}
    url = is_safe_url(data.get('url', ''))
    if not url: return jsonify({"success": False, "error": "رابط غير صالح."})
    
    cache_key = f"fb_{url}"
    cached = extract_cache.get(cache_key)
    if cached: return jsonify(cached)
    
    res = robust_waterfall_extract(url, "فيسبوك")
    if res.get('success'): extract_cache.set(cache_key, res)
    return jsonify(res)

@app.route('/api/general', methods=['POST'])
@rate_limit(limit=30, window=60)
def process_general():
    data = request.json or {}
    url = is_safe_url(data.get('url', ''))
    if not url: return jsonify({"success": False, "error": "رابط غير صالح."})
    
    cache_key = f"gen_{url}"
    cached = extract_cache.get(cache_key)
    if cached: return jsonify(cached)

    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'format': 'bestvideo+bestaudio/best'}
        def fetch_general():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
                
        info = execute_with_timeout(fetch_general, 20)
        
        if info:
            video_url = info.get('url')
            if not video_url:
                v_formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
                if v_formats: video_url = v_formats[-1].get('url')
            
            if video_url:
                audio_url = video_url
                is_pure_audio = False
                a_formats = [f for f in info.get('formats', []) if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
                if a_formats:
                    audio_url = a_formats[-1].get('url')
                    is_pure_audio = True
                
                real_formats = extract_real_formats(info)

                result = {"success": True, "title": info.get('title', 'ملف مستخرج'), "thumbnail": info.get('thumbnail', ''), "video_url": video_url, "audio_url": audio_url, "is_pure_audio": is_pure_audio, "duration": info.get('duration', 15), "is_image": False, "formats": real_formats}
                extract_cache.set(cache_key, result)
                return jsonify(result)
    except Exception as e:
        logger.error(f"General extraction failed: {str(e)}")
        return jsonify({"success": False, "error": parse_ytdlp_error(e)})
    
    return jsonify({"success": False, "error": "تعذر استخراج البيانات من هذا الرابط."})

# ==============================================================================
# Enterprise Proxy Stream (Zero Leak, SSRF Protected, True Streaming)
# ==============================================================================
def is_safe_url(url):
    """التحقق المتقدم لمنع ثغرات SSRF من خلال Resolution للـ IP"""
    if not url: return False
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ('http', 'https'): return False
        hostname = parsed.hostname
        if not hostname: return False
        if hostname.lower() in ['localhost', '127.0.0.1']: return False
        
        ip_info = socket.getaddrinfo(hostname, None)
        for info in ip_info:
            ip_obj = ipaddress.ip_address(info[4][0])
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_unspecified:
                return False
        return url
    except Exception as e:
        logger.error(f"SSRF Check failed: {str(e)}")
        return False

@app.route('/proxy_stream')
def proxy_stream():
    target_url = is_safe_url(request.args.get('url'))
    ext = request.args.get('ext', 'mp4')
    filename = request.args.get('filename', 'Tahmilati_Stream')
    
    if not target_url: 
        return abort(403, description="Access Denied: Unsafe or Invalid URL")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    range_header = request.headers.get('Range')
    if range_header:
        headers['Range'] = range_header
    
    try:
        req = session.get(target_url, headers=headers, stream=True, timeout=20)
        req.raise_for_status()

        def generate():
            try:
                for chunk in req.iter_content(chunk_size=8192):
                    if chunk: yield chunk
            except GeneratorExit:
                logger.info("Client disconnected from proxy stream.")
            except Exception as e:
                logger.error(f"Stream interrupted: {str(e)}")
            finally:
                req.close() # إغلاق إجباري لمنع تسريب الاتصالات

        resp = Response(stream_with_context(generate()), status=req.status_code)
        
        # تمرير Range Headers لدعم التقديم والتأخير
        for key in ['Content-Type', 'Content-Length', 'Accept-Ranges', 'Content-Range']:
            if key in req.headers:
                resp.headers[key] = req.headers[key]
        
        if 'Content-Type' not in resp.headers:
            resp.headers['Content-Type'] = f'video/{ext}' if ext != 'mp3' else 'audio/mpeg'

        # اسم الملف بترميز UTF-8 آمن
        encoded_name = urllib.parse.quote(f"{filename}.{ext}")
        resp.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_name}"
        resp.headers['Access-Control-Allow-Origin'] = '*' 
        return resp

    except requests.exceptions.RequestException as e:
        logger.error(f"Proxy Error for {target_url}: {str(e)}")
        return abort(502, description="Bad Gateway: Upstream server error")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
