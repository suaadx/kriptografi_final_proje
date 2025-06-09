#Suad Wajaheddin_2112721310

from flask import Flask, render_template, request, send_file
from Crypto.Cipher import AES
from werkzeug.utils import secure_filename
import os, base64, hashlib

app = Flask(__name__)

# 📁 Yükleme dizini
UPLOAD_DIR = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 🔐 AES Key padding helper
def prepare_key(raw_key):
    return raw_key.ljust(16)[:16].encode("utf-8")

# 🔒 AES ile metin şifreleme
def aes_encrypt(key, plain_text):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plain_text.encode("utf-8"))
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode("utf-8")

# 🔓 AES ile metin çözme
def aes_decrypt(key, encoded_data):
    try:
        raw = base64.b64decode(encoded_data)
        nonce, tag, ciphertext = raw[:16], raw[16:32], raw[32:]
        cipher = AES.new(key, AES.MODE_EAX, nonce)
        decrypted = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted.decode("utf-8")
    except:
        return "Şifre çözme hatası!"

# 🏠 Ana sayfa
@app.route("/")
def home():
    return render_template("index.html")

# ✏️ Metin şifreleme/çözme
@app.route("/text-aes", methods=["GET", "POST"])
def handle_text_aes():
    result = ""
    if request.method == "POST":
        content = request.form.get("text", "")
        raw_key = request.form.get("key", "")
        action = request.form.get("action")
        key = prepare_key(raw_key)

        if action == "encrypt":
            result = aes_encrypt(key, content)
        elif action == "decrypt":
            result = aes_decrypt(key, content)

    return render_template("text_aes.html", result=result)

# 📄 SHA256 özeti
@app.route("/sha256", methods=["GET", "POST"])
def handle_sha256():
    result = ""
    if request.method == "POST":
        action = request.form.get("action")

        if action == "hash_text":
            text = request.form.get("text", "")
            result = hashlib.sha256(text.encode()).hexdigest()

        elif action == "hash_file":
            file = request.files.get("file")
            if file:
                filepath = os.path.join(UPLOAD_DIR, secure_filename(file.filename))
                file.save(filepath)
                with open(filepath, "rb") as f:
                    hasher = hashlib.sha256()
                    while chunk := f.read(4096):
                        hasher.update(chunk)
                    result = hasher.hexdigest()
            else:
                result = "Dosya yok!"

    return render_template("sha256.html", result=result)

# 📁 Dosya şifreleme/çözme
@app.route("/file-crypto", methods=["GET", "POST"])
def handle_file_crypto():
    result = ""
    download_link = ""

    if request.method == "POST":
        action = request.form.get("action")
        key = prepare_key(request.form.get("key", ""))
        uploaded = request.files.get("file")

        if uploaded:
            filename = secure_filename(uploaded.filename)
            source_path = os.path.join(UPLOAD_DIR, filename)
            uploaded.save(source_path)

            with open(source_path, "rb") as f:
                file_data = f.read()

            if action == "encrypt":
                cipher = AES.new(key, AES.MODE_EAX)
                ciphertext, tag = cipher.encrypt_and_digest(file_data)
                encrypted = cipher.nonce + tag + ciphertext
                out_path = os.path.join(UPLOAD_DIR, "encrypted_" + filename)
                with open(out_path, "wb") as out:
                    out.write(encrypted)
                result = "Şifreleme başarılı"
                download_link = f"/download/encrypted_{filename}"

            elif action == "decrypt":
                try:
                    nonce, tag, ciphertext = file_data[:16], file_data[16:32], file_data[32:]
                    cipher = AES.new(key, AES.MODE_EAX, nonce)
                    decrypted = cipher.decrypt_and_verify(ciphertext, tag)
                    out_path = os.path.join(UPLOAD_DIR, "decrypted_" + filename)
                    with open(out_path, "wb") as out:
                        out.write(decrypted)
                    result = "Çözme başarılı"
                    download_link = f"/download/decrypted_{filename}"
                except:
                    result = "Şifre çözme hatası"
        else:
            result = "Dosya seçilmedi!"

    return render_template("file_crypto.html", result=result, download_link=download_link)

# 📥 Dosya indirme
@app.route("/download/<filename>")
def download_file(filename):
    return send_file(os.path.join(UPLOAD_DIR, filename), as_attachment=True)

# ▶️ Uygulamayı çalıştır
if __name__ == "__main__":
    app.run(debug=True)
