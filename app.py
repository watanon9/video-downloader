from flask import Flask, request, jsonify, render_template_string
import yt_dlp

app = Flask(__name__)

# هنانه دمجنا كود الـ HTML والـ JavaScript بمتغير داخل البايثون
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تحميل الفيديوهات</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f4f4f9; color: #333; }
        input { padding: 12px; width: 80%; max-width: 400px; border: 1px solid #ccc; border-radius: 5px; font-size: 16px; }
        button { padding: 12px 24px; background-color: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-top: 10px; }
        #result { margin-top: 30px; }
        .download-btn { display: inline-block; margin: 8px; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }
    </style>
</head>
<body>

    <h2>موقع تحميل الفيديوهات السريع 🚀</h2>
    <p>حمل من تيك توك، انستغرام، وغيرها بدون علامة مائية وبأعلى دقة!</p>
    
    <input type="text" id="videoUrl" placeholder="خلي رابط الفيديو هنا...">
    <br>
    <button onclick="fetchVideo()">ابدأ التحميل</button>

    <div id="result"></div>

    <script>
        async function fetchVideo() {
            const url = document.getElementById('videoUrl').value;
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = "جاري استخراج الروابط... ⏳";

            try {
                const response = await fetch('/get_video', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                if (data.error) {
                    resultDiv.innerHTML = `<p style="color:red;">${data.error}</p>`;
                    return;
                }

                let html = `<h3>${data.title}</h3>`;
                if(data.thumbnail) {
                    html += `<img src="${data.thumbnail}" width="200" style="border-radius:10px;"><br><br>`;
                }
                
                if(data.formats.length === 0) {
                    html += `<p style="color:orange;">اضغط بالأسفل للتحميل المباشر</p>`;
                }

                data.formats.forEach(format => {
                    html += `<a href="${format.url}" target="_blank" class="download-btn">تحميل دقة ${format.resolution}</a>`;
                });

                resultDiv.innerHTML = html;

            } catch (error) {
                resultDiv.innerHTML = `<p style="color:red;">صار خطأ أثناء الاتصال بالسيرفر.</p>`;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    # هنا يستدعي الـ HTML المدمج فوق مباشرة
    return render_template_string(HTML_LAYOUT)

@app.route('/get_video', methods=['POST'])
def get_video():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "الرجاء إدخال رابط صحيح"}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    formats.append({
                        'resolution': f.get('resolution', 'Unknown'),
                        'url': f.get('url')
                    })
            
            return jsonify({
                "title": info.get('title', 'فيديو'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats
            })
            
    except Exception as e:
        return jsonify({"error": "ما كدرنا نسحب الفيديو، تأكد من الرابط"}), 500

if __name__ == '__main__':
    app.run(debug=True)
