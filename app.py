import os
import requests
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB limit

# Make sure the uploads folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/edit", methods=["POST"])
def edit_image():
    # 1. Check a file was uploaded
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    prompt = request.form.get("prompt", "Replace the curtains with elegant white sheer linen curtains")

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # 2. Save the uploaded image
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # 3. Send to OpenAI Image Edit API (gpt-image-1)
    try:
        with open(filepath, "rb") as image_file:
            response = requests.post(
                "https://api.openai.com/v1/images/edits",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                files={"image": ("image.png", image_file, "image/png")},
                data={
                    "model": "gpt-image-1",
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024",
                },
            )

        result = response.json()

        # 4. Check for API errors
        if "error" in result:
            return jsonify({"error": result["error"]["message"]}), 500

        # 5. gpt-image-1 returns b64_json by default
        image_data = result["data"][0]
        image_b64 = image_data.get("b64_json") or image_data.get("url")
        return jsonify({"image": image_b64, "is_url": "url" in image_data and "b64_json" not in image_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
