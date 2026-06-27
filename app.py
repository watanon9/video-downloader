import os
import requests
import urllib.parse
import urllib3
from flask import Flask, request, jsonify, Response, stream_with_context

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

HTML_LAYOUT = r"""
<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tahmilati | Media Downloader</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>

    <style>
        :root {
            --bg-color: #f8fafc; --card-bg: #ffffff;
            --text-main: #0f172a; --text-muted: #64748b;
            --primary: #dc2626;
            --border: rgba(0,0,0,0.1); --neon-shadow: none;
        }
        [data-theme="dark"] {
            --bg-color: #0f172a; --card-bg: #1e293b;
            --text-main: #f8fafc; --text-muted: #94a3b8;
            --primary: #ef4444; --border: rgba(255,255,255,0.1);
            --neon-shadow: 0 0 10px var(--primary), 0 0 20px var(--primary);
        }
        body.theme-tiktok   { --primary: #00f2fe; --neon-shadow: 0 0 10px #00f2fe, 0 0 20px #fe0979; }
        body.theme-insta    { --primary: #f56040; --neon-shadow: 0 0 10px #f56040, 0 0 20px #833ab4; }
        body.theme-facebook { --primary: #1877f2; --neon-shadow: 0 0 10px #1877f2, 0 0 20px #0c56b8; }
        body.theme-general  { --primary: #8b5cf6; --neon-shadow: 0 0 10px #8b5cf6, 0 0 20px #6d28d9; }

        *, *::before, *::after { box-sizing: border-box; }
        html, body { height: 100dvh; margin: 0; padding: 0; overflow: hidden; font-family: 'Inter', sans-serif; background-color: var(--bg-color); color: var(--text-main); transition: background-color 0.4s, color 0.4s; }
        .app-container { display: flex; flex-direction: column; height: 100%; max-width: 500px; margin: 0 auto; position: relative; overflow: hidden; }

        /* Top bar */
        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; border-bottom: 1px solid var(--border); background: var(--card-bg); flex-shrink: 0; z-index: 50; }
        .logo-title { margin: 0; font-weight: 900; font-size: 21px; color: var(--primary); text-shadow: var(--neon-shadow); letter-spacing: -0.5px; }
        .nav-btns { display: flex; gap: 8px; }
        .icon-btn { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 7px 11px; border-radius: 10px; cursor: pointer; font-weight: bold; transition: 0.25s; font-size: 15px; }
        .icon-btn:hover { background: var(--primary); color: white; box-shadow: var(--neon-shadow); }

        /* Sidebar */
        .sidebar-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.55); z-index: 99; display: none; opacity: 0; transition: opacity 0.3s; }
        .sidebar { position: fixed; top: 0; right: -300px; width: 270px; height: 100%; background: var(--card-bg); z-index: 100; box-shadow: -4px 0 18px rgba(0,0,0,0.2); transition: right 0.3s ease; display: flex; flex-direction: column; }
        .sidebar.open { right: 0; }
        .sidebar-header { padding: 18px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .sidebar-title { font-weight: 900; font-size: 17px; }
        .close-sidebar { background: none; border: none; font-size: 19px; color: var(--text-muted); cursor: pointer; }
        .menu-list { list-style: none; padding: 8px 0; margin: 0; flex: 1; overflow-y: auto; }
        .menu-item { padding: 14px 18px; border-bottom: 1px solid var(--border); cursor: pointer; font-weight: 700; font-size: 14px; display: flex; align-items: center; gap: 11px; color: var(--text-main); transition: 0.2s; }
        .menu-item:hover { background: rgba(0,0,0,0.04); color: var(--primary); }
        [data-theme="dark"] .menu-item:hover { background: rgba(255,255,255,0.05); }

        /* Main scroll area */
        .main-content { flex: 1; overflow-y: auto; padding: 18px; display: flex; flex-direction: column; gap: 14px; }

        /* Welcome */
        .welcome-screen { text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; gap: 18px; }
        .welcome-title { font-size: 28px; font-weight: 900; color: var(--primary); margin: 0; text-shadow: var(--neon-shadow); }
        .welcome-desc { font-size: 14px; color: var(--text-muted); line-height: 1.65; }
        .welcome-steps { background: var(--card-bg); border: 1px solid var(--border); padding: 14px 18px; border-radius: 14px; text-align: left; width: 100%; font-size: 13px; font-weight: 600; list-style: none; margin: 0; display: flex; flex-direction: column; gap: 8px; }
        .welcome-steps li { display: flex; align-items: center; gap: 8px; }
        .creator-btn { display: flex; align-items: center; justify-content: center; gap: 8px; background: linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888); color: white; padding: 12px; border-radius: 14px; text-decoration: none; font-weight: 700; font-size: 14px; width: 100%; }

        /* View sections */
        .view-section { display: none; flex-direction: column; gap: 14px; animation: slideUp 0.35s ease; }
        @keyframes slideUp { from { opacity:0; transform:translateY(18px); } to { opacity:1; transform:translateY(0); } }

        /* Input card */
        .input-card { background: var(--card-bg); padding: 16px; border-radius: 18px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 11px; }
        .card-title { font-size: 14px; font-weight: 700; display: flex; align-items: center; gap: 8px; }
        .input-row { display: flex; align-items: center; background: rgba(0,0,0,0.03); border: 1px solid var(--border); border-radius: 11px; padding: 0 12px; }
        [data-theme="dark"] .input-row { background: rgba(255,255,255,0.03); }
        input[type="text"] { flex: 1; padding: 14px 6px; background: transparent; border: none; color: var(--text-main); font-size: 14px; outline: none; font-family: 'Inter'; }
        .paste-icon { padding: 8px; color: var(--text-muted); cursor: pointer; font-size: 15px; flex-shrink: 0; }
        .paste-icon:hover { color: var(--primary); }
        .btn-main { padding: 14px; background: var(--primary); color: white; border: none; border-radius: 11px; font-size: 15px; font-weight: 800; cursor: pointer; font-family: 'Inter'; box-shadow: var(--neon-shadow); transition: 0.25s; }
        .btn-main:disabled { opacity: 0.55; cursor: not-allowed; }
        .btn-main:not(:disabled):hover { filter: brightness(1.1); }

        /* Result container */
        .result-container { display: none; flex-direction: column; gap: 13px; background: var(--card-bg); padding: 14px; border-radius: 18px; border: 1px solid var(--border); }
        .video-header { display: flex; gap: 13px; align-items: center; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
        .thumb { width: 58px; height: 58px; border-radius: 10px; object-fit: cover; border: 1px solid var(--border); flex-shrink: 0; }
        .vid-title { font-size: 13px; font-weight: 600; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .video-wrapper { border-radius: 11px; overflow: hidden; background: #000; max-height: 290px; }
        .plyr-player { width: 100%; max-height: 290px; object-fit: contain; }
        .btn-group { display: flex; gap: 8px; }
        .btn-action { flex: 1; padding: 11px; border: none; border-radius: 11px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 7px; font-size: 13px; color: white; font-family: 'Inter'; transition: 0.2s; }
        .btn-action:hover { filter: brightness(1.1); }
        .btn-icon-sq { background: rgba(0,0,0,0.05); width: 44px; flex: none; border-radius: 11px; display: flex; align-items: center; justify-content: center; color: var(--text-main); cursor: pointer; border: 1px solid var(--border); font-size: 15px; transition: 0.2s; }
        .btn-icon-sq:hover { background: var(--primary); color: white; border-color: var(--primary); }
        [data-theme="dark"] .btn-icon-sq { background: rgba(255,255,255,0.05); }
        .bg-mp4 { background: #10b981; }

        /* Status */
        .status-msg { text-align: center; font-size: 13px; display: none; font-weight: 600; padding: 10px; border-radius: 10px; }

        /* QR modal */
        .qr-modal { display: none; position: absolute; inset: 0; background: rgba(0,0,0,0.78); z-index: 1000; justify-content: center; align-items: center; flex-direction: column; backdrop-filter: blur(5px); }
        .qr-box { background: var(--card-bg); padding: 24px; border-radius: 18px; display: flex; flex-direction: column; align-items: center; gap: 14px; }
        .qr-box span { font-weight: 700; font-size: 14px; }
        .close-qr { background: #ef4444; color: white; border: none; padding: 9px 24px; border-radius: 9px; font-weight: 700; cursor: pointer; font-family: 'Inter'; }
    </style>
</head>
<body data-theme="dark">

<div class="app-container">

    <!-- Top bar -->
    <div class="top-bar">
        <h3 class="logo-title">Tahmilati</h3>
        <div class="nav-btns">
            <button class="icon-btn" onclick="location.reload()" title="Refresh"><i class="fas fa-sync-alt"></i></button>
            <button class="icon-btn" onclick="toggleTheme()" title="Toggle theme"><i class="fas fa-moon"></i></button>
            <button class="icon-btn" onclick="toggleSidebar()" title="Menu"><i class="fas fa-bars"></i></button>
        </div>
    </div>

    <!-- Sidebar -->
    <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <span class="sidebar-title">Download Sections</span>
            <button class="close-sidebar" onclick="toggleSidebar()"><i class="fas fa-times"></i></button>
        </div>
        <ul class="menu-list">
            <li class="menu-item" onclick="switchView('insta','theme-insta')">
                <i class="fab fa-instagram" style="color:#f56040;"></i> Instagram (Post / Story)
            </li>
            <li class="menu-item" onclick="switchView('tiktok','theme-tiktok')">
                <i class="fab fa-tiktok" style="color:#00f2fe;"></i> TikTok (Video / Story)
            </li>
            <li class="menu-item" onclick="switchView('facebook','theme-facebook')">
                <i class="fab fa-facebook" style="color:#1877f2;"></i> Facebook (Video / Reels)
            </li>
            <li class="menu-item" onclick="switchView('general','theme-general')">
                <i class="fas fa-link" style="color:#8b5cf6;"></i> General Download
            </li>
        </ul>
    </div>

    <!-- Main content -->
    <div class="main-content">

        <!-- Welcome -->
        <div id="view-welcome" class="view-section welcome-screen">
            <h1 class="welcome-title">Tahmilati</h1>
            <p class="welcome-desc">Smart all-in-one media downloader.<br>Extract &amp; save media at the highest quality.</p>
            <ul class="welcome-steps">
                <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 1. Tap the menu icon (&#9776;) in the top right.</li>
                <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 2. Choose the platform you want to download from.</li>
                <li><i class="fas fa-check-circle" style="color:var(--primary)"></i> 3. Paste a link or a username, then hit Process.</li>
            </ul>
            <div style="margin-top:auto; width:100%;">
                <a href="https://www.instagram.com/_otnn?igsh=d3hybTN2M2Zlanl0" target="_blank" class="creator-btn">
                    <i class="fab fa-instagram"></i> Designer: @_otnn
                </a>
            </div>
        </div>

        <!-- Instagram -->
        <div id="view-insta" class="view-section">
            <div class="input-card">
                <div class="card-title"><i class="fab fa-instagram" style="color:#f56040;"></i> Download from Instagram</div>
                <div class="input-row">
                    <input type="text" id="input-insta" placeholder="Post URL or @username for stories...">
                    <i class="fas fa-paste paste-icon" onclick="pasteText('input-insta')" title="Paste"></i>
                </div>
                <button class="btn-main" onclick="processClientRequest('insta')">Process Link</button>
            </div>
            <div id="res-insta" class="result-container">
                <div class="status-msg"></div>
                <div class="media-box" style="display:none;"></div>
            </div>
        </div>

        <!-- TikTok -->
        <div id="view-tiktok" class="view-section">
            <div class="input-card">
                <div class="card-title"><i class="fab fa-tiktok" style="color:#00f2fe;"></i> Download from TikTok</div>
                <div class="input-row">
                    <input type="text" id="input-tiktok" placeholder="Paste video URL...">
                    <i class="fas fa-paste paste-icon" onclick="pasteText('input-tiktok')" title="Paste"></i>
                </div>
                <button class="btn-main" onclick="processClientRequest('tiktok')">Process Link</button>
            </div>
            <div id="res-tiktok" class="result-container">
                <div class="status-msg"></div>
                <div class="media-box" style="display:none;"></div>
            </div>
        </div>

        <!-- Facebook -->
        <div id="view-facebook" class="view-section">
            <div class="input-card">
                <div class="card-title"><i class="fab fa-facebook" style="color:#1877f2;"></i> Download from Facebook</div>
                <div class="input-row">
                    <input type="text" id="input-facebook" placeholder="Paste video or Reels URL...">
                    <i class="fas fa-paste paste-icon" onclick="pasteText('input-facebook')" title="Paste"></i>
                </div>
                <button class="btn-main" onclick="processClientRequest('facebook')">Process Link</button>
            </div>
            <div id="res-facebook" class="result-container">
                <div class="status-msg"></div>
                <div class="media-box" style="display:none;"></div>
            </div>
        </div>

        <!-- General -->
        <div id="view-general" class="view-section">
            <div class="input-card">
                <div class="card-title"><i class="fas fa-link" style="color:#8b5cf6;"></i> General Download</div>
                <div class="input-row">
                    <input type="text" id="input-general" placeholder="Paste any supported URL...">
                    <i class="fas fa-paste paste-icon" onclick="pasteText('input-general')" title="Paste"></i>
                </div>
                <button class="btn-main" onclick="processClientRequest('general')">Process Link</button>
            </div>
            <div id="res-general" class="result-container">
                <div class="status-msg"></div>
                <div class="media-box" style="display:none;"></div>
            </div>
        </div>

    </div><!-- /main-content -->
</div><!-- /app-container -->

<!-- QR Modal -->
<div class="qr-modal" id="qrModal">
    <div class="qr-box">
        <span>Scan to download directly</span>
        <div id="qrCodeDiv"></div>
        <button class="close-qr" onclick="document.getElementById('qrModal').style.display='none'">Close</button>
    </div>
</div>

<script>
    // Show welcome on load
    document.getElementById('view-welcome').style.display = 'flex';

    let activePlayer = null;

    // â”€â”€ Theme â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    function toggleTheme() {
        const next = document.body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.body.setAttribute('data-theme', next);
    }

    // â”€â”€ Sidebar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        document.body.className = themeClass;
        if (isDark) document.body.setAttribute('data-theme', 'dark');
        toggleSidebar();
    }

    // â”€â”€ Clipboard paste â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async function pasteText(inputId) {
        try {
            const text = await navigator.clipboard.readText();
            document.getElementById(inputId).value = text;
        } catch (e) {
            alert('Clipboard permission denied. Please paste manually.');
        }
    }

    // â”€â”€ QR Code â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    function showQR(url) {
        document.getElementById('qrModal').style.display = 'flex';
        document.getElementById('qrCodeDiv').innerHTML = '';
        new QRCode(document.getElementById('qrCodeDiv'), { text: url, width: 180, height: 180 });
    }

    // â”€â”€ Download helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async function forceAutoDownload(url, filename) {
        try {
            if (url.includes('/proxy_stream')) {
                const a = document.createElement('a');
                a.href = url; a.download = filename;
                document.body.appendChild(a); a.click(); document.body.removeChild(a);
                return;
            }
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

    // â”€â”€ Main request handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async function processClientRequest(platform) {
        const inputEl = document.getElementById('input-' + platform);
        const val = inputEl.value.trim();
        if (!val) { inputEl.focus(); return; }

        const resContainer = document.getElementById('res-' + platform);
        const statusMsg    = resContainer.querySelector('.status-msg');
        const mediaBox     = resContainer.querySelector('.media-box');
        const btn          = resContainer.closest('.view-section').querySelector('.btn-main');

        // Reset UI
        resContainer.style.display = 'flex';
        statusMsg.style.display    = 'block';
        statusMsg.style.color      = 'var(--primary)';
        statusMsg.innerHTML        = '<i class="fas fa-spinner fa-spin"></i> Connecting to servers, extracting media...';
        mediaBox.style.display     = 'none';
        mediaBox.innerHTML         = '';

        if (activePlayer) {
            try { activePlayer.destroy(); } catch (_) {}
            activePlayer = null;
        }

        btn.disabled = true;

        try {
            const r   = await fetch('/api/process', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ url: val, platform })
            });
            const res = await r.json();

            if (res.success) {
                statusMsg.style.display = 'none';
                const useProxy     = ['insta', 'facebook'].includes(platform);
                const vidUrlToPlay = useProxy
                    ? '/proxy_stream?url=' + encodeURIComponent(res.video_url) + '&ext=mp4'
                    : res.video_url;
                renderMediaResult(res.title, res.thumbnail, vidUrlToPlay, res.video_url, 'res-' + platform);
            } else {
                statusMsg.innerHTML   = '<i class="fas fa-exclamation-triangle"></i> ' + res.error;
                statusMsg.style.color = '#ef4444';
            }
        } catch (e) {
            statusMsg.innerHTML   = '<i class="fas fa-exclamation-triangle"></i> Connection lost. Check your internet and try again.';
            statusMsg.style.color = '#ef4444';
        } finally {
            btn.disabled = false;
        }
    }

    // â”€â”€ Render result card â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    function renderMediaResult(title, thumbnail, playUrl, externalUrl, cid) {
        const mediaBox     = document.querySelector('#' + cid + ' .media-box');
        const safePlay     = playUrl.replace(/'/g, '%27');
        const safeExternal = externalUrl.replace(/'/g, '%27');
        const safeTitle    = title.replace(/</g, '&lt;').replace(/>/g, '&gt;');

        mediaBox.innerHTML = `
            <div class="video-header">
                <img src="${thumbnail}" class="thumb" onerror="this.src='https://via.placeholder.com/58'">
                <div class="vid-title">${safeTitle}</div>
            </div>
            <div class="video-wrapper">
                <video class="plyr-player" playsinline controls></video>
            </div>
            <div style="display:flex;flex-direction:column;gap:9px;margin-top:8px;">
                <div class="btn-group">
                    <button onclick="forceAutoDownload('${safePlay}','Tahmilati.mp4')" class="btn-action bg-mp4">
                        <i class="fas fa-download"></i> Download Video
                    </button>
                    <button onclick="showQR('${safeExternal}')" class="btn-icon-sq" title="QR Code">
                        <i class="fas fa-qrcode"></i>
                    </button>
                </div>
            </div>
        `;

        const videoEl = mediaBox.querySelector('.plyr-player');
        videoEl.src   = playUrl;
        activePlayer  = new Plyr(videoEl, {
            controls: ['play-large','play','progress','current-time','mute','fullscreen']
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
    return Response(HTML_LAYOUT, mimetype='text/html')


@app.route('/api/process', methods=['POST'])
def process_api():
    data     = request.json or {}
    url      = data.get('url', '').strip()
    platform = data.get('platform', '').strip()

    if not url:
        return jsonify({"success": False, "error": "URL or username is empty."})

    # â”€â”€ 1. TIKTOK â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
            return jsonify({"success": False, "error": "TikTok rejected the link. Please check it and try again."})
        except requests.exceptions.Timeout:
            return jsonify({"success": False, "error": "Request timed out. Please try again."})
        except requests.exceptions.RequestException as e:
            return jsonify({"success": False, "error": f"Server connection failed: {e}"})

    # â”€â”€ 2. INSTAGRAM â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Handles both post URLs and bare usernames (for stories).
    # Strategy: try multiple scraper APIs with fallbacks.
    if platform == 'insta':
        # Detect if it's a username (not a URL) â†’ build stories URL
        if not url.startswith('http'):
            username = url.lstrip('@').strip()
            story_url = f"https://www.instagram.com/stories/{username}/"
        else:
            username  = None
            story_url = url

        common_headers = {
            'Accept':       'application/json',
            'Content-Type': 'application/json',
            'User-Agent':   'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        }

        # â”€â”€ Attempt A: Cobalt (stories & posts) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        cobalt_nodes = [
            "https://api.cobalt.tools/",
            "https://co.wuk.sh/",
        ]
        for node in cobalt_nodes:
            try:
                r = requests.post(
                    node + "api/json",
                    json={"url": story_url},
                    headers=common_headers,
                    timeout=12
                )
                if r.status_code != 200:
                    continue
                res = r.json()
                if res.get('url'):
                    return jsonify({
                        "success":   True,
                        "title":     f"Instagram Story â€” @{username}" if username else "Instagram Media",
                        "thumbnail": "https://via.placeholder.com/150",
                        "video_url": res['url']
                    })
                if res.get('status') == 'picker' and res.get('picker'):
                    first = res['picker'][0]
                    return jsonify({
                        "success":   True,
                        "title":     f"Instagram Story â€” @{username}" if username else "Instagram Media",
                        "thumbnail": first.get('thumb', 'https://via.placeholder.com/150'),
                        "video_url": first.get('url', '')
                    })
            except requests.exceptions.RequestException:
                continue

        # â”€â”€ Attempt B: SnapSave / SaveFrom (post URLs only) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if not username and url.startswith('http'):
            try:
                r2 = requests.post(
                    "https://snapsave.app/action.php",
                    data={"url": url},
                    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://snapsave.app/"},
                    timeout=12
                )
                if r2.status_code == 200:
                    import re
                    m = re.search(r'href="(https://[^"]+\.mp4[^"]*)"', r2.text)
                    if m:
                        return jsonify({
                            "success":   True,
                            "title":     "Instagram Media",
                            "thumbnail": "https://via.placeholder.com/150",
                            "video_url": m.group(1)
                        })
            except requests.exceptions.RequestException:
                pass

        # â”€â”€ Attempt C: Instagram oEmbed (thumbnail + title fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Only useful to confirm the post exists; doesn't give a direct video.
        if username:
            return jsonify({
                "success": False,
                "error":   (
                    f"Could not fetch stories for @{username}. "
                    "Stories require the account to be public and the API to be available. "
                    "Try again in a moment."
                )
            })

        return jsonify({
            "success": False,
            "error": "The platform blocked the request (private account or firewall). Try a different link."
        })

    # â”€â”€ 3. FACEBOOK â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if platform == 'facebook':
        common_headers = {
            'Accept':       'application/json',
            'Content-Type': 'application/json',
            'User-Agent':   'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        }
        cobalt_nodes = [
            "https://api.cobalt.tools/",
            "https://co.wuk.sh/",
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
                if res.get('url'):
                    return jsonify({
                        "success":   True,
                        "title":     "Facebook Media",
                        "thumbnail": "https://via.placeholder.com/150",
                        "video_url": res['url']
                    })
                if res.get('status') == 'picker' and res.get('picker'):
                    first = res['picker'][0]
                    return jsonify({
                        "success":   True,
                        "title":     "Facebook Media",
                        "thumbnail": first.get('thumb', 'https://via.placeholder.com/150'),
                        "video_url": first.get('url', '')
                    })
            except requests.exceptions.RequestException:
                continue

        return jsonify({
            "success": False,
            "error": "The platform blocked the request (private or firewall). Try a different link."
        })

    # â”€â”€ 4. GENERAL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    return jsonify({"success": False, "error": "Platform not supported yet."})


# ==============================================================================
# CORS Bypass Proxy
# ==============================================================================
@app.route('/proxy_stream')
def proxy_stream():
    target_url = request.args.get('url', '').strip()
    ext        = request.args.get('ext', 'mp4')

    if not target_url:
        return "Missing URL parameter", 400

    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        upstream = requests.get(
            target_url, headers=req_headers,
            stream=True, verify=False, timeout=20
        )
        upstream.raise_for_status()

        def generate():
            for chunk in upstream.iter_content(chunk_size=512 * 1024):
                if chunk:
                    yield chunk

        content_type = upstream.headers.get('Content-Type', f'video/{ext}')
        resp = Response(stream_with_context(generate()), content_type=content_type)
        resp.headers['Content-Disposition'] = f'attachment; filename="Tahmilati_Media.{ext}"'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        if 'Content-Length' in upstream.headers:
            resp.headers['Content-Length'] = upstream.headers['Content-Length']
        return resp

    except requests.exceptions.Timeout:
        return "Proxy timeout", 504
    except requests.exceptions.RequestException as e:
        return f"Proxy error: {e}", 502


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
