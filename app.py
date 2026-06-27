import os
import requests
import urllib.parse
import urllib3
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context

# Suppress SSL warnings from verify=False in proxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==============================================================================
# Project: Tahmilati Media Downloader (University Submission)
# Architecture: Client-Server with Backend API Proxying and CORS Bypass
# ==============================================================================

app = Flask(__name__)

# NOTE: Jinja2 processes {{ }} and {% %} inside render_template_string.
# All JS template literals that use {{ }} must be escaped as {{ '{{' }} / {{ '}}' }},
# OR â€” the cleaner fix used here â€” we serve HTML from a raw string with
# render_template_string(...) replaced by Response(..., mimetype='text/html')
# so Jinja2 never touches the JS at all.

HTML_LAYOUT = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tahmilati | ØªØ­Ù…ÙŠÙ„Ø§ØªÙŠ</title>
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
        body.theme-tiktok  { --primary: #00f2fe; --neon-shadow: 0 0 10px #00f2fe, 0 0 20px #fe0979; }
        body.theme-insta   { --primary: #f56040; --neon-shadow: 0 0 10px #f56040, 0 0 20px #833ab4; }
        body.theme-facebook{ --primary: #1877f2; --neon-shadow: 0 0 10px #1877f2, 0 0 20px #0c56b8; }
        body.theme-general { --primary: #8b5cf6; --neon-shadow: 0 0 10px #8b5cf6, 0 0 20px #6d28d9; }

        html, body { height: 100dvh; margin: 0; padding: 0; overflow: hidden; font-family: 'Tajawal', sans-serif; background-color: var(--bg-color); color: var(--text-main); transition: 0.4s ease; }
        .app-container { display: flex; flex-direction: column; height: 100%; max-width: 500px; margin: 0 auto; position: relative; overflow: hidden; }

        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; border-bottom: 1px solid var(--border); background: var(--card-bg); flex-shrink: 0; z-index: 50; }
        .logo-title { margin: 0; font-weight: 900; font-size: 22px; color: var(--primary); text-shadow: var(--neon-shadow); }
        .nav-btns { display: flex; gap: 10px; }
        .icon-btn { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 12px; cursor: pointer; font-weight: bold; transition: 0.3s; font-size: 16px; }
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
        .welcome-steps { background: var(--card-bg); border: 1px solid var(--border); padding: 15px; border-radius: 15px; text-align: right; width: 100%; font-size: 13px; font-weight: bold; list-style: none; }
        .creator-btn { display: flex; align-items: center; justify-content: center; gap: 8px; background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); color: white; padding: 12px; border-radius: 15px; text-decoration: none; font-weight: bold; font-size: 14px; width: 100%; box-sizing: border-box; }

        /* FIX: all view sections hidden by default; JS shows the active one */
        .view-section { display: none; flex-direction: column; gap: 15px; animation: slideUp 0.4s ease; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

        .input-card { background: var(--card-bg); padding: 18px; border-radius: 20px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 12px; }
        .card-title { font-size: 15px; font-weight: bold; display: flex; align-items: center; gap: 8px; }
        .input-row { display: flex; gap: 8px; align-items: center; background: rgba(0,0,0,0.03); border: 1px solid var(--border); border-radius: 12px; padding-right: 12px; }
        [data-theme="dark"] .input-row { background: rgba(255,255,255,0.03); }
        input[type="text"] { flex: 1; padding: 16px 5px; background: transparent; border: none; color: var(--text-main); font-size: 14px; outline: none; font-family: 'Tajawal'; }
        /* FIX: defined .paste-icon (was .action-icon â€” undefined in CSS) */
        .paste-icon { padding: 10px; color: var(--text-muted); cursor: pointer; font-size: 16px; }
        .paste-icon:hover { color: var(--primary); }
        .btn-main { padding: 15px; background: var(--primary); color: white; border: none; border-radius: 12px; font-size: 15px; font-weight: 900; cursor: pointer; font-family: 'Tajawal'; box-shadow: var(--neon-shadow); transition: 0.3s; }
        .btn-main:disabled { opacity: 0.6; cursor: not-allowed; }

        .result-container { display: none; flex-direction: column; gap: 15px; background: var(--card-bg); padding: 15px; border-radius: 20px; border: 1px solid var(--border); overflow: hidden; }
        .video-header { display: flex; gap: 15px; align-items: center; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
        .thumb { width: 60px; height: 60px; border-radius: 10px; object-fit: cover; border: 1px solid var(--border); }
        .vid-title { font-size: 13px; font-weight: bold; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

        .video-wrapper { border-radius: 12px; overflow: hidden; background: #000; display: flex; justify-content: center; align-items: center; max-height: 300px; }
        .plyr-player { max-height: 300px; width: 100%; object-fit: contain; }

        .btn-group { display: flex; gap: 8px; width: 100%; }
        .btn-action { flex: 1; padding: 12px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 13px; color: white; font-family: 'Tajawal'; }
        .btn-icon-sq { background: rgba(0,0,0,0.05); width: 45px; flex: none; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--text-main); cursor: pointer; border: 1px solid var(--border); font-size: 16px; }
        [data-theme="dark"] .btn-icon-sq { background: rgba(255,255,255,0.05); }
        .bg-mp4 { background: #10b981; }

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
            <span class="sidebar-title">Ø£Ù‚Ø³Ø§Ù… Ø§Ù„ØªÙ†Ø²ÙŠÙ„</span>
            <button class="close-sidebar" onclick="toggleSidebar()"><i class="fas fa-times"></i></button>
        </div>
        <ul class="menu-list">
            <li class="menu-item" onclick="switchView('insta','theme-insta')"><i class="fab fa-instagram" style="color:#f56040;"></i> Ø¥Ù†Ø³ØªØºØ±Ø§Ù… (Ø¨ÙˆØ³Øª/Ø³ØªÙˆØ±ÙŠ)</li>
            <li class="menu-item" onclick="switchView('tiktok','theme-tiktok')"><i class="fab fa-tiktok" style="color:#00f2fe;"></i> ØªÙŠÙƒ ØªÙˆÙƒ (ÙÙŠØ¯ÙŠÙˆ/Ø³ØªÙˆØ±ÙŠ)</li>
            <li class="menu-item" onclick="switchView('facebook','theme-facebook')"><i class="fab fa-facebook" style="color:#1877f2;"></i> ÙÙŠØ³Ø¨ÙˆÙƒ (ÙÙŠØ¯ÙŠÙˆ/Ø±ÙŠÙ„Ø²)</li>
            <li class="menu-item" onclick="switchView('general','theme-general')"><i class="fas fa-link" style="color:#8b5cf6;"></i> ØªØ­Ù…ÙŠÙ„ Ø¹Ø§Ù… (Ø±ÙˆØ§Ø¨Ø· Ø£Ø®Ø±Ù‰)</li>
        </ul>
    </div>

    <div class="main-content">

        <!-- Welcome screen (shown on load) -->
        <div id="view-welcome" class="view-section welcome-screen">
            <h1 class="welcome-title">Tahmilati</h1>
            <p class="welcome-desc">Ù…Ù†ØµØ© Ø§Ù„ØªÙ†Ø²ÙŠÙ„ Ø§Ù„Ø°ÙƒÙŠØ© Ø§Ù„Ø´Ø§Ù…Ù„Ø©<br>Ø§Ø³ØªØ®Ø±Ø§Ø¬ Ø§Ù„ÙˆØ³Ø§Ø¦Ø· Ø¨Ø£Ø¹Ù„Ù‰ Ø¬ÙˆØ¯Ø© ÙˆØªÙ†Ø²ÙŠÙ„Ù‡Ø§ ØªÙ„Ù‚Ø§Ø¦ÙŠØ§Ù‹.</p>
            <ul class="welcome-steps" dir="rtl">
                <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 1. Ø§Ù†Ù‚Ø± Ø¹Ù„Ù‰ Ø£ÙŠÙ‚ÙˆÙ†Ø© Ø§Ù„Ù‚Ø§Ø¦Ù…Ø© (â˜°).</li>
                <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 2. Ø­Ø¯Ø¯ Ø§Ù„Ù…Ù†ØµØ© Ø§Ù„Ù…Ø±Ø§Ø¯ Ø§Ù„ØªÙ†Ø²ÙŠÙ„ Ù…Ù†Ù‡Ø§.</li>
                <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 3. Ø£Ø¯Ø®Ù„ Ø§Ù„Ø±Ø§Ø¨Ø· Ø£Ùˆ Ø§Ù„ÙŠÙˆØ²Ø± Ù„Ù„ØªØ­Ù…ÙŠÙ„ Ø§Ù„Ù…Ø¨Ø§Ø´Ø±.</li>
            </ul>
            <div style="margin-top:auto; width:100%;">
                <a href="https://www.instagram.com/_otnn?igsh=d3hybTN2M2Zlanl0" target="_blank" class="creator-btn">
                    <i class="fab fa-instagram"></i> Ø§Ù„Ù…ØµÙ…Ù…: @_otnn
                </a>
            </div>
        </div>

        <!-- Instagram -->
        <div id="view-insta" class="view-section">
            <div class="input-card">
                <div class="card-title"><i class="fab fa-instagram" style="color:#f56040;"></i> ØªÙ†Ø²ÙŠÙ„ Ù…Ù† Ø¥Ù†Ø³ØªØºØ±Ø§Ù…</div>
                <div class="input-row">
                    <input type="text" id="input-insta" placeholder="Ø±Ø§Ø¨Ø· Ø§Ù„Ø¨ÙˆØ³Øª Ø£Ùˆ ÙŠÙˆØ²Ø± Ø§Ù„Ø³ØªÙˆØ±ÙŠ...">
                    <i class="fas fa-paste paste-icon" onclick="pasteText('input-insta')"></i>
                </div>
                <button class="btn-main" onclick="processClientRequest('insta')">Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„Ø±Ø§Ø¨Ø·</button>
            </div>
            <div id="res-insta" class="result-container">
                <div class="status-msg"></div>
                <div class="media-box" style="display:none;"></div>
            </div>
        </div>

        <!-- TikTok -->
        <div id="view-tiktok" class="view-section">
            <div class="input-card">
                <div class="card-title"><i class="fab fa-tiktok" style="color:#00f2fe;"></i> ØªÙ†Ø²ÙŠÙ„ Ù…Ù† ØªÙŠÙƒ ØªÙˆÙƒ</div>
                <div class="input-row">
                    <input type="text" id="input-tiktok" placeholder="Ø£Ø¯Ø®Ù„ Ø±Ø§Ø¨Ø· Ø§Ù„ÙÙŠØ¯ÙŠÙˆ...">
                    <i class="fas fa-paste paste-icon" onclick="pasteText('input-tiktok')"></i>
                </div>
                <button class="btn-main" onclick="processClientRequest('tiktok')">Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„Ø±Ø§Ø¨Ø·</button>
            </div>
            <div id="res-tiktok" class="result-container">
                <div class="status-msg"></div>
                <div class="media-box" style="display:none;"></div>
            </div>
        </div>

        <!-- Facebook -->
        <div id="view-facebook" class="view-section">
            <div class="input-card">
                <div class="card-title"><i class="fab fa-facebook" style="color:#1877f2;"></i> ØªÙ†Ø²ÙŠÙ„ Ù…Ù† ÙÙŠØ³Ø¨ÙˆÙƒ</div>
                <div class="input-row">
                    <input type="text" id="input-facebook" placeholder="Ø±Ø§Ø¨Ø· Ø§Ù„ÙÙŠØ¯ÙŠÙˆ Ø£Ùˆ Ø§Ù„Ø±ÙŠÙ„Ø²...">
                    <i class="fas fa-paste paste-icon" onclick="pasteText('input-facebook')"></i>
                </div>
                <button class="btn-main" onclick="processClientRequest('facebook')">Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„Ø±Ø§Ø¨Ø·</button>
            </div>
            <div id="res-facebook" class="result-container">
                <div class="status-msg"></div>
                <div class="media-box" style="display:none;"></div>
            </div>
        </div>

        <!-- General -->
        <div id="view-general" class="view-section">
            <div class="input-card">
                <div class="card-title"><i class="fas fa-link" style="color:#8b5cf6;"></i> ØªØ­Ù…ÙŠÙ„ Ø¹Ø§Ù…</div>
                <div class="input-row">
                    <input type="text" id="input-general" placeholder="Ø£Ø¯Ø®Ù„ Ø§Ù„Ø±Ø§Ø¨Ø·...">
                    <i class="fas fa-paste paste-icon" onclick="pasteText('input-general')"></i>
                </div>
                <button class="btn-main" onclick="processClientRequest('general')">Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„Ø±Ø§Ø¨Ø·</button>
            </div>
            <div id="res-general" class="result-container">
                <div class="status-msg"></div>
                <div class="media-box" style="display:none;"></div>
            </div>
        </div>

    </div><!-- /main-content -->
</div><!-- /app-container -->

<div class="qr-modal" id="qrModal">
    <div class="qr-box">
        <span style="color:var(--text-main); font-weight:bold;">Ø§Ù…Ø³Ø­ Ø§Ù„Ø¨Ø§Ø±ÙƒÙˆØ¯ Ù„Ù„ØªØ­Ù…ÙŠÙ„ Ø§Ù„Ù…Ø¨Ø§Ø´Ø±</span>
        <div id="qrCodeDiv"></div>
        <button class="close-qr" onclick="document.getElementById('qrModal').style.display='none'">Ø¥ØºÙ„Ø§Ù‚</button>
    </div>
</div>

<script>
    // -----------------------------------------------------------------------
    // Show welcome on load
    // -----------------------------------------------------------------------
    document.getElementById('view-welcome').style.display = 'flex';

    let activePlayer = null;

    // -----------------------------------------------------------------------
    // UI helpers
    // -----------------------------------------------------------------------
    function toggleTheme() {
        const t = document.body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.body.setAttribute('data-theme', t);
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
        const view = document.getElementById('view-' + viewName);
        if (view) view.style.display = 'flex';
        // Preserve dark/light data-theme while changing accent class
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        document.body.className = themeClass;
        if (isDark) document.body.setAttribute('data-theme', 'dark');
        toggleSidebar();
    }

    // FIX: replaced inline onclick with a named function so the clipboard API
    // error (if denied) is caught cleanly instead of failing silently.
    async function pasteText(inputId) {
        try {
            const text = await navigator.clipboard.readText();
            document.getElementById(inputId).value = text;
        } catch (e) {
            alert('Ù„Ù… ÙŠØªÙ… Ù…Ù†Ø­ Ø¥Ø°Ù† Ø§Ù„Ù„ØµÙ‚. Ø§Ù„ØµÙ‚ Ø§Ù„Ø±Ø§Ø¨Ø· ÙŠØ¯ÙˆÙŠØ§Ù‹.');
        }
    }

    // -----------------------------------------------------------------------
    // QR Code
    // -----------------------------------------------------------------------
    function showQR(url) {
        document.getElementById('qrModal').style.display = 'flex';
        document.getElementById('qrCodeDiv').innerHTML = '';
        new QRCode(document.getElementById('qrCodeDiv'), { text: url, width: 180, height: 180 });
    }

    // -----------------------------------------------------------------------
    // Download helper
    // -----------------------------------------------------------------------
    async function forceAutoDownload(url, filename) {
        try {
            // Proxied URLs: direct anchor click (server sends Content-Disposition)
            if (url.includes('/proxy_stream')) {
                const a = document.createElement('a');
                a.href = url; a.download = filename;
                document.body.appendChild(a); a.click(); document.body.removeChild(a);
                return;
            }
            // External URLs: fetch â†’ blob â†’ object URL
            const response = await fetch(url);
            if (!response.ok) throw new Error('fetch failed');
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

    // -----------------------------------------------------------------------
    // Main request handler
    // -----------------------------------------------------------------------
    async function processClientRequest(platform) {
        const inputEl    = document.getElementById('input-' + platform);
        const val        = inputEl.value.trim();
        if (!val) { inputEl.focus(); return; }

        const resContainer = document.getElementById('res-' + platform);
        const statusMsg    = resContainer.querySelector('.status-msg');
        const mediaBox     = resContainer.querySelector('.media-box');

        // Reset UI
        resContainer.style.display = 'flex';
        statusMsg.style.display    = 'block';
        statusMsg.style.color      = 'var(--primary)';
        statusMsg.innerHTML        = '<i class="fas fa-spinner fa-spin"></i> Ø¬Ø§Ø±ÙŠ Ø§Ù„Ø§ØªØµØ§Ù„ Ø¨Ø§Ù„Ø®ÙˆØ§Ø¯Ù… ÙˆØ§Ø³ØªØ®Ø±Ø§Ø¬ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª...';
        mediaBox.style.display     = 'none';
        mediaBox.innerHTML         = '';

        // FIX: destroy previous Plyr instance before overwriting the element
        if (activePlayer) {
            try { activePlayer.destroy(); } catch (_) {}
            activePlayer = null;
        }

        // Disable button to prevent double submission
        const btn = resContainer.closest('.view-section').querySelector('.btn-main');
        btn.disabled = true;

        try {
            const r   = await fetch('/api/process', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ url: val, platform: platform })
            });
            const res = await r.json();

            if (res.success) {
                statusMsg.style.display = 'none';

                // Use proxy for Meta platforms to avoid CORS on playback/download
                const useProxy    = ['insta', 'facebook'].includes(platform);
                const vidUrlToPlay = useProxy
                    ? '/proxy_stream?url=' + encodeURIComponent(res.video_url) + '&ext=mp4'
                    : res.video_url;

                renderMediaResult(res.title, res.thumbnail, vidUrlToPlay, res.video_url, containerId(platform));
            } else {
                statusMsg.innerHTML   = '<i class="fas fa-exclamation-triangle"></i> ' + res.error;
                statusMsg.style.color = '#ef4444';
            }
        } catch (e) {
            statusMsg.innerHTML   = '<i class="fas fa-exclamation-triangle"></i> Ø§Ù†Ù‚Ø·Ø¹ Ø§Ù„Ø§ØªØµØ§Ù„ Ø¨Ø§Ù„Ø³ÙŠØ±ÙØ±. ØªØ£ÙƒØ¯ Ù…Ù† Ø§Ù„Ø¥Ù†ØªØ±Ù†Øª.';
            statusMsg.style.color = '#ef4444';
        } finally {
            btn.disabled = false;
        }
    }

    function containerId(platform) {
        return 'res-' + platform;
    }

    // -----------------------------------------------------------------------
    // Render result card
    // -----------------------------------------------------------------------
    function renderMediaResult(title, thumbnail, playUrl, externalUrl, cid) {
        const mediaBox = document.querySelector('#' + cid + ' .media-box');

        // Escape values for safe inline attribute injection
        const safePlay     = playUrl.replace(/'/g, '%27');
        const safeExternal = externalUrl.replace(/'/g, '%27');
        const safeTitle    = title.replace(/</g, '&lt;').replace(/>/g, '&gt;');

        mediaBox.innerHTML = `
            <div class="video-header">
                <img src="${thumbnail}" class="thumb" onerror="this.src='https://via.placeholder.com/60'">
                <div class="vid-title">${safeTitle}</div>
            </div>
            <div class="video-wrapper">
                <video class="plyr-player" playsinline controls></video>
            </div>
            <div style="display:flex; flex-direction:column; gap:10px; margin-top:10px;">
                <div class="btn-group">
                    <button onclick="forceAutoDownload('${safePlay}', 'Tahmilati.mp4')" class="btn-action bg-mp4">
                        <i class="fas fa-download"></i> ØªÙ†Ø²ÙŠÙ„ Ø§Ù„ÙÙŠØ¯ÙŠÙˆ
                    </button>
                    <button onclick="showQR('${safeExternal}')" class="btn-icon-sq" title="Ø¨Ø§Ø±ÙƒÙˆØ¯">
                        <i class="fas fa-qrcode"></i>
                    </button>
                </div>
            </div>
        `;

        const videoEl = mediaBox.querySelector('.plyr-player');
        videoEl.src   = playUrl;
        activePlayer  = new Plyr(videoEl, {
            controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'fullscreen']
        });
        mediaBox.style.display = 'flex';
    }
</script>
</body>
</html>
"""

# ==============================================================================
# Routes
# ==============================================================================

@app.route('/')
def home():
    # FIX: return raw HTML â€” bypasses Jinja2 entirely so {{ }} in JS is safe.
    return Response(HTML_LAYOUT, mimetype='text/html')


@app.route('/api/process', methods=['POST'])
def process_api():
    data     = request.json or {}
    url      = data.get('url', '').strip()
    platform = data.get('platform', '').strip()

    if not url:
        return jsonify({"success": False, "error": "Ø§Ù„Ø±Ø§Ø¨Ø· Ø£Ùˆ Ø§Ù„ÙŠÙˆØ²Ø± ÙØ§Ø±Øº!"})

    # ------------------------------------------------------------------
    # 1. TIKTOK â€” TikWM public API (stable)
    # ------------------------------------------------------------------
    if platform == 'tiktok' or 'tiktok.com' in url:
        try:
            r = requests.get(
                f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}",
                timeout=10
            )
            r.raise_for_status()
            body = r.json()
            if body.get('code') == 0:
                v = body['data']
                return jsonify({
                    "success":   True,
                    "title":     v.get('title', 'TikTok Video'),
                    "thumbnail": v.get('cover', 'https://via.placeholder.com/150'),
                    "video_url": v.get('play', '')
                })
            return jsonify({"success": False, "error": "ØªÙŠÙƒ ØªÙˆÙƒ Ø±ÙØ¶ Ø§Ù„Ø±Ø§Ø¨Ø·. ØªØ£ÙƒØ¯ Ù…Ù† ØµØ­ØªÙ‡."})
        except requests.exceptions.Timeout:
            return jsonify({"success": False, "error": "Ø§Ù†ØªÙ‡Øª Ù…Ù‡Ù„Ø© Ø§Ù„Ø§ØªØµØ§Ù„. Ø­Ø§ÙˆÙ„ Ù…Ø¬Ø¯Ø¯Ø§Ù‹."})
        except requests.exceptions.RequestException as e:
            return jsonify({"success": False, "error": f"ÙØ´Ù„ Ø§ØªØµØ§Ù„ Ø§Ù„Ø³ÙŠØ±ÙØ±: {e}"})

    # ------------------------------------------------------------------
    # 2. INSTAGRAM / FACEBOOK â€” Cobalt API
    #    NOTE: Cobalt updated its API. The new endpoint uses /api/json
    #    with {"url": "..."} and returns {"status": "...", "url": "..."}
    #    or {"status": "picker", "picker": [...]} for multi-media posts.
    # ------------------------------------------------------------------
    if platform in ('insta', 'facebook'):

        # Auto-expand bare Instagram username â†’ Stories URL
        if platform == 'insta' and not url.startswith('http'):
            username = url.lstrip('@').strip()
            url = f"https://www.instagram.com/stories/{username}/"

        common_headers = {
            'Accept':       'application/json',
            'Content-Type': 'application/json',
            'User-Agent':   'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        }

        cobalt_nodes = [
            "https://api.cobalt.tools/",  # official instance (updated endpoint)
            "https://co.wuk.sh/",         # community mirror
        ]

        for node in cobalt_nodes:
            try:
                r = requests.post(
                    node + "api/json",
                    json={"url": url},
                    headers=common_headers,
                    timeout=12
                )
                if r.status_code != 200:
                    continue
                res = r.json()

                # Single direct URL
                if res.get('url'):
                    return jsonify({
                        "success":   True,
                        "title":     f"Media - {platform.capitalize()}",
                        "thumbnail": "https://via.placeholder.com/150",
                        "video_url": res['url']
                    })

                # Picker (multiple items) â€” return the first video/image
                if res.get('status') == 'picker' and res.get('picker'):
                    first = res['picker'][0]
                    return jsonify({
                        "success":   True,
                        "title":     f"Media - {platform.capitalize()}",
                        "thumbnail": first.get('thumb', 'https://via.placeholder.com/150'),
                        "video_url": first.get('url', '')
                    })

            except requests.exceptions.RequestException:
                continue  # try next node

        return jsonify({
            "success": False,
            "error": "ØªÙ… Ø­Ø¸Ø± Ø§Ù„Ø·Ù„Ø¨ Ù…Ù† Ù‚Ø¨Ù„ Ø§Ù„Ù…Ù†ØµØ© (Ø§Ù„Ø­Ø³Ø§Ø¨ Ø®Ø§Øµ Ø£Ùˆ Ø¬Ø¯Ø§Ø± Ø­Ù…Ø§ÙŠØ©). Ø­Ø§ÙˆÙ„ Ø¨Ø±Ø§Ø¨Ø· Ø¢Ø®Ø±."
        })

    # ------------------------------------------------------------------
    # 3. GENERAL â€” not yet implemented
    # ------------------------------------------------------------------
    return jsonify({"success": False, "error": "Ù†ÙˆØ¹ Ø§Ù„Ù…Ù†ØµØ© ØºÙŠØ± Ù…Ø¯Ø¹ÙˆÙ… Ø­Ø§Ù„ÙŠØ§Ù‹."})


# ==============================================================================
# CORS Bypass Proxy
# Streams external content through the server so browsers can play/download
# Meta-hosted media that blocks cross-origin requests.
# ==============================================================================
@app.route('/proxy_stream')
def proxy_stream():
    target_url = request.args.get('url', '').strip()
    ext        = request.args.get('ext', 'mp4')

    if not target_url:
        return "Missing URL parameter", 400

    req_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        upstream = requests.get(
            target_url,
            headers=req_headers,
            stream=True,
            verify=False,     # some CDN certs fail validation; warning suppressed above
            timeout=20
        )
        upstream.raise_for_status()

        def generate():
            for chunk in upstream.iter_content(chunk_size=512 * 1024):  # 512 KB
                if chunk:
                    yield chunk

        content_type = upstream.headers.get('Content-Type', f'video/{ext}')
        resp = Response(stream_with_context(generate()), content_type=content_type)
        resp.headers['Content-Disposition'] = f'attachment; filename="Tahmilati_Media.{ext}"'
        resp.headers['Access-Control-Allow-Origin'] = '*'

        # FIX: pass Content-Length through so download progress bars work
        if 'Content-Length' in upstream.headers:
            resp.headers['Content-Length'] = upstream.headers['Content-Length']

        return resp

    except requests.exceptions.Timeout:
        return "Proxy timeout", 504
    except requests.exceptions.RequestException as e:
        return f"Proxy error: {e}", 502


# ==============================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
