from flask import Flask, request, jsonify, render_template_string
import subprocess, os, tempfile
from openai import OpenAI

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TikTok Transcriber</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0a0a0a;
    color: #f0f0f0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }
  .card {
    background: #141414;
    border: 1px solid #222;
    border-radius: 16px;
    padding: 40px;
    width: 100%;
    max-width: 640px;
  }
  h1 { font-size: 20px; font-weight: 600; margin-bottom: 8px; color: #fff; }
  p.sub { font-size: 13px; color: #666; margin-bottom: 32px; }
  label {
    display: block; font-size: 12px; font-weight: 500; color: #888;
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;
  }
  input[type="text"] {
    width: 100%; background: #1e1e1e; border: 1px solid #2a2a2a;
    border-radius: 8px; color: #f0f0f0; font-size: 14px;
    padding: 12px 14px; outline: none; transition: border-color 0.2s; margin-bottom: 20px;
  }
  input[type="text"]:focus { border-color: #444; }
  .divider {
    display: flex; align-items: center; gap: 12px;
    margin: 4px 0 20px; color: #444; font-size: 12px;
  }
  .divider::before, .divider::after { content: ''; flex: 1; height: 1px; background: #222; }
  .upload-zone {
    border: 1px dashed #2a2a2a; border-radius: 8px; padding: 28px;
    text-align: center; cursor: pointer; transition: border-color 0.2s, background 0.2s;
    margin-bottom: 20px; position: relative;
  }
  .upload-zone:hover { border-color: #444; background: #1a1a1a; }
  .upload-zone input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
  .upload-zone .icon { font-size: 28px; margin-bottom: 8px; }
  .upload-zone p { font-size: 13px; color: #666; }
  .upload-zone p span { color: #aaa; }
  #filename { font-size: 12px; color: #888; margin-top: 6px; }
  button {
    width: 100%; background: #fff; color: #000; border: none;
    border-radius: 8px; font-size: 14px; font-weight: 600;
    padding: 14px; cursor: pointer; transition: opacity 0.2s;
  }
  button:hover { opacity: 0.85; }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  .status { margin-top: 20px; font-size: 13px; color: #666; text-align: center; min-height: 20px; }
  .result { margin-top: 24px; display: none; }
  .result label { margin-bottom: 8px; }
  .transcript-box {
    background: #1e1e1e; border: 1px solid #2a2a2a; border-radius: 8px;
    padding: 16px; font-size: 14px; line-height: 1.7; color: #e0e0e0;
    white-space: pre-wrap; max-height: 400px; overflow-y: auto;
  }
  .copy-btn {
    margin-top: 12px; background: #1e1e1e; color: #aaa;
    border: 1px solid #2a2a2a; font-weight: 500;
  }
  .copy-btn:hover { opacity: 1; background: #252525; }
  .error { color: #ff6b6b; }
  .spinner {
    display: inline-block; width: 14px; height: 14px;
    border: 2px solid #333; border-top-color: #aaa; border-radius: 50%;
    animation: spin 0.8s linear infinite; margin-right: 8px; vertical-align: middle;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="card">
  <h1>TikTok Transcriber</h1>
  <p class="sub">Paste a TikTok link or upload an MP4 — get the full transcript.</p>

  <label>TikTok URL</label>
  <input type="text" id="url" placeholder="https://www.tiktok.com/@..." />

  <div class="divider">or</div>

  <div class="upload-zone" id="dropzone">
    <input type="file" id="fileInput" accept="video/mp4,audio/*" onchange="handleFile(this)">
    <div class="icon">🎬</div>
    <p><span>Click to upload</span> or drag & drop</p>
    <p>MP4, MOV, M4A</p>
    <div id="filename"></div>
  </div>

  <button id="btn" onclick="transcribe()">Transcribe</button>
  <div class="status" id="status"></div>

  <div class="result" id="result">
    <label>Transcript</label>
    <div class="transcript-box" id="transcript"></div>
    <button class="copy-btn" onclick="copy()">Copy transcript</button>
  </div>
</div>

<script>
let selectedFile = null;

function handleFile(input) {
  selectedFile = input.files[0];
  document.getElementById('filename').textContent = selectedFile ? selectedFile.name : '';
}

async function transcribe() {
  const url = document.getElementById('url').value.trim();
  const btn = document.getElementById('btn');
  const result = document.getElementById('result');

  if (!url && !selectedFile) { setStatus('Paste a URL or upload a file.', true); return; }

  btn.disabled = true;
  result.style.display = 'none';
  setStatus('<span class="spinner"></span>Processing...');

  const formData = new FormData();
  if (url) formData.append('url', url);
  if (selectedFile) formData.append('file', selectedFile);

  try {
    const res = await fetch('/transcribe', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.error) {
      setStatus(data.error, true);
    } else {
      document.getElementById('transcript').textContent = data.transcript;
      result.style.display = 'block';
      setStatus('');
    }
  } catch(e) {
    setStatus('Something went wrong.', true);
  } finally {
    btn.disabled = false;
  }
}

function setStatus(msg, isError) {
  const s = document.getElementById('status');
  s.innerHTML = msg;
  s.className = 'status' + (isError ? ' error' : '');
}

function copy() {
  const text = document.getElementById('transcript').textContent;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.querySelector('.copy-btn');
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = 'Copy transcript', 2000);
  });
}

document.addEventListener('dragover', e => e.preventDefault());
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    url = request.form.get('url', '').strip()
    file = request.files.get('file')

    client = OpenAI(api_key=OPENAI_API_KEY)

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, 'audio.mp3')

        if url:
            try:
                result = subprocess.run([
                    'yt-dlp',
                    '--extract-audio',
                    '--audio-format', 'mp3',
                    '--audio-quality', '0',
                    '-o', audio_path,
                    '--no-playlist',
                    url
                ], capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    return jsonify({'error': f'Could not download video: {result.stderr[-300:]}'})
            except subprocess.TimeoutExpired:
                return jsonify({'error': 'Download timed out'})

        elif file:
            raw_path = os.path.join(tmpdir, 'input_video')
            file.save(raw_path)
            subprocess.run([
                'ffmpeg', '-i', raw_path,
                '-q:a', '0', '-map', 'a',
                audio_path, '-y'
            ], capture_output=True)

        else:
            return jsonify({'error': 'No URL or file provided'})

        if not os.path.exists(audio_path):
            return jsonify({'error': 'Audio extraction failed'})

        try:
            with open(audio_path, 'rb') as f:
                response = client.audio.transcriptions.create(
                    model='whisper-1',
                    file=f,
                    response_format='text'
                )
            return jsonify({'transcript': response})
        except Exception as e:
            return jsonify({'error': f'Transcription error: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5055))
    print(f'\n✅ Transcriber running → http://localhost:{port}\n')
    app.run(host='0.0.0.0', port=port, debug=False)
