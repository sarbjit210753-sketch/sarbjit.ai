import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import base64

app = Flask(__name__)
app.secret_key = 'sarbjit_secret_key_security'

UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Render te safety layi API Keys sirf Environment Variable ton hi lainiya ne
API_KEYS_env = os.environ.get('API_KEYS', '')
API_KEYS = [key.strip() for key in API_KEYS_env.split(',') if key.strip()]

current_key_index = 0

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]

MODEL_NAME = 'gemini-1.5-flash'
chat_history = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    error = None
    success = None
    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']
            if username == 'admin' and password == '@@@@':
                session['logged_in'] = True
            else:
                error = "⚠️ Galat Username ya Password!"

        if session.get('logged_in') and 'bg_image' in request.files:
            file = request.files['bg_image']
            if file.filename != '':
                filename = 'bg.jpg'
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                success = "✅ Wallpaper successfully change ho gaya hai!"

    is_logged_in = session.get('logged_in', False)
    return render_template('admin.html', error=error, success=success, logged_in=is_logged_in)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_panel'))

@app.route('/chat', methods=['POST'])
def chat():
    global chat_history, current_key_index
    try:
        if not API_KEYS:
            return jsonify({'reply': "⚠️ Veer, Render de Environment Variables vich API_KEYS set nahi kitiyan गईyan!"})

        user_message = request.json.get('message', '')
        file_data = request.json.get('file', None)
        file_type = request.json.get('fileType', 'image')

        if not user_message and not file_data:
            return jsonify({'error': 'Message or File is required'})

        current_key = API_KEYS[current_key_index].strip()
        current_key_index = (current_key_index + 1) % len(API_KEYS)
        genai.configure(api_key=current_key)

        system_instruction = """You are Sarbjit Flash-Lite, an advanced AI built by Sarbjit Singh.
- Talk naturally in Punjabi (Gurmukhi or Roman) or English.
- If anyone asks who built you or created you, reply back with full swag and attitude: "Menu mere veer Sarbjit Singh ne banaya aa!" or a savage equivalent in Punjabi/Hindi.
- Do not randomly bring up BCA, semester, or loops unless specifically asked about programming. 
- If an image or PDF/code file is provided, analyze it thoroughly.
- SURVIVE & ROAST MODE: If anyone talks rudely, acts smart, or tries to mess with you, reply back with such a savage, brutal, and witty roast in Punjabi/Hindi that their mouth is shut permanently and they are totally put in their place on the spot without using explicit abuse."""

        model = genai.GenerativeModel(
            MODEL_NAME,
            system_instruction=system_instruction
        )

        content_parts = []
        if user_message:
            content_parts.append(user_message)

        if file_data:
            try:
                if "," in file_data:
                    header, encoded = file_data.split(",", 1)
                else:
                    encoded = file_data

                file_bytes = base64.b64decode(encoded)
                mime = 'application/pdf' if file_type == 'pdf' else 'image/jpeg'

                content_parts.append({
                    'mime_type': mime,
                    'data': file_bytes
                })
            except Exception as img_err:
                return jsonify({'reply': "⚠️ File process karn vich dikkat aayi hai."})

        chat_history.append({"role": "user", "parts": content_parts})

        response = model.generate_content(chat_history, safety_settings=safety_settings)
        chat_history.append({"role": "model", "parts": [response.text]})

        return jsonify({'reply': response.text})

    except Exception as e:
        if chat_history:
            chat_history.pop()

        error_msg = str(e)
        if "429" in error_msg:
             return jsonify({'reply': "⚠️ Veer, saari Keys di speed limit poori ho gayi hai. Thodi der baad try karo!"})

        return jsonify({'reply': f"⚠️ Server Error: {error_msg}"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

