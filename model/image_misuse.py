from flask import (
    Flask,
    request,
    render_template_string,
    send_from_directory
)

from PIL import Image, ImageStat
import imagehash

import os
import re
import hashlib
import sqlite3
from datetime import datetime


# ============================================================
# CYBERSHIELD AI
# IMAGE MISUSE CHECKER
# Single File Version
# ============================================================

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "image_uploads")
DATABASE = os.path.join(BASE_DIR, "image_misuse.db")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ============================================================
# DATABASE
# ============================================================

def init_database():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            sha256 TEXT,
            phash TEXT,
            width INTEGER,
            height INTEGER,
            similarity INTEGER,
            risk TEXT,
            score INTEGER,
            result TEXT,
            scan_time TEXT
        )
    """)

    conn.commit()
    conn.close()


init_database()


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# SHA-256 HASH
# ============================================================

def calculate_sha256(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while True:

            data = file.read(8192)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()


# ============================================================
# PERCEPTUAL HASH
# ============================================================

def calculate_phash(file_path):

    image = Image.open(file_path)

    return str(imagehash.phash(image))


# ============================================================
# IMAGE SIMILARITY
# ============================================================

def calculate_similarity(hash1, hash2):

    try:

        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)

        distance = h1 - h2

        similarity = 100 - int((distance / 64) * 100)

        if similarity < 0:
            similarity = 0

        if similarity > 100:
            similarity = 100

        return similarity

    except:

        return 0


# ============================================================
# IMAGE ANALYSIS
# ============================================================

def analyze_image(file_path):

    image = Image.open(file_path)

    width, height = image.size

    file_size = os.path.getsize(file_path)

    image_format = image.format or "UNKNOWN"

    mode = image.mode

    megapixels = round(
        (width * height) / 1000000,
        2
    )

    if height > 0:

        aspect_ratio = round(
            width / height,
            2
        )

    else:

        aspect_ratio = 0


    # Brightness

    try:

        gray = image.convert("L")

        statistics = ImageStat.Stat(gray)

        brightness = round(
            statistics.mean[0],
            2
        )

    except:

        brightness = 0


    # Quality

    if megapixels >= 8:

        quality = "HIGH"

    elif megapixels >= 2:

        quality = "GOOD"

    elif megapixels >= 1:

        quality = "MEDIUM"

    else:

        quality = "LOW"


    return {

        "width": width,

        "height": height,

        "file_size": file_size,

        "format": image_format,

        "mode": mode,

        "megapixels": megapixels,

        "aspect_ratio": aspect_ratio,

        "brightness": brightness,

        "quality": quality

    }


# ============================================================
# FIND PREVIOUS SIMILAR IMAGE
# ============================================================

def find_previous_match(current_hash):

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM scans
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    best_similarity = 0

    best_match = None

    for row in rows:

        old_hash = row["phash"]

        similarity = calculate_similarity(
            current_hash,
            old_hash
        )

        if similarity > best_similarity:

            best_similarity = similarity

            best_match = row

    return best_similarity, best_match


# ============================================================
# RISK CALCULATION
# ============================================================

def calculate_risk(similarity):

    if similarity >= 95:

        return "HIGH", 90

    elif similarity >= 85:

        return "HIGH", 80

    elif similarity >= 70:

        return "MEDIUM", 60

    elif similarity >= 50:

        return "MEDIUM", 45

    else:

        return "LOW", 15


# ============================================================
# HTML
# ============================================================

HTML = """

<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>
CyberShield AI - Image Misuse Checker
</title>


<style>

* {
    box-sizing: border-box;
}


body {

    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        radial-gradient(
            circle at top,
            #10202b,
            #030609 65%
        );

    color: #eaf7ff;

    min-height: 100vh;
}


.container {

    width: 92%;

    max-width: 1150px;

    margin: auto;

    padding: 35px 0 60px;
}


.header {

    text-align: center;

    margin-bottom: 35px;
}


.logo {

    font-size: 14px;

    color: #00eaff;

    letter-spacing: 4px;

    font-weight: bold;
}


.header h1 {

    margin: 12px 0;

    font-size: 38px;

    letter-spacing: 2px;

    color: #ffffff;
}


.header h1 span {

    color: #00eaff;
}


.header p {

    color: #8da1b3;

    font-size: 15px;
}


.card {

    background:
        rgba(9, 16, 24, 0.94);

    border:

        1px solid #193346;

    border-radius: 18px;

    padding: 28px;

    margin-bottom: 22px;

    box-shadow:
        0 15px 45px
        rgba(0, 0, 0, .35);
}


.card h2 {

    margin-top: 0;

    color: #00eaff;

    font-size: 21px;
}


.upload-area {

    border:

        2px dashed #00bcd4;

    border-radius: 16px;

    padding: 45px 20px;

    text-align: center;

    transition: .3s;
}


.upload-area:hover {

    background:
        rgba(0, 234, 255, .04);

    border-color: #00eaff;
}


.upload-icon {

    font-size: 50px;

    margin-bottom: 15px;
}


input[type="file"] {

    width: 100%;

    max-width: 500px;

    padding: 14px;

    background: #081019;

    border: 1px solid #233c4d;

    color: white;

    border-radius: 8px;

    margin: 15px 0;
}


button {

    background:

        linear-gradient(
            90deg,
            #00bcd4,
            #00eaff
        );

    color: #001015;

    border: none;

    padding: 14px 30px;

    border-radius: 8px;

    font-weight: bold;

    font-size: 14px;

    cursor: pointer;

    margin-top: 10px;
}


button:hover {

    transform: translateY(-1px);

    box-shadow:
        0 8px 25px
        rgba(0, 234, 255, .2);
}


.preview {

    text-align: center;

    margin-top: 25px;
}


.preview img {

    max-width: 100%;

    max-height: 420px;

    border-radius: 15px;

    border: 1px solid #254354;

    box-shadow:
        0 10px 35px
        rgba(0,0,0,.4);
}


.stats {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(180px, 1fr)
        );

    gap: 15px;
}


.stat {

    background: #070e15;

    border: 1px solid #1b3342;

    border-radius: 12px;

    padding: 20px;
}


.stat-label {

    color: #7890a2;

    font-size: 12px;

    letter-spacing: 1px;

    margin-bottom: 10px;
}


.stat-value {

    font-size: 26px;

    font-weight: bold;
}


.low {

    color: #00f5a0;
}


.medium {

    color: #ffc107;
}


.high {

    color: #ff5268;
}


.progress {

    height: 16px;

    background: #17232d;

    border-radius: 20px;

    overflow: hidden;

    margin-top: 15px;
}


.progress-bar {

    height: 100%;

    background:
        linear-gradient(
            90deg,
            #00bcd4,
            #00eaff
        );

    transition: width .6s;
}


.result {

    background: #071019;

    border-left:
        4px solid #00eaff;

    padding: 18px;

    border-radius: 8px;

    line-height: 1.7;
}


.warning {

    background: #211a08;

    border:
        1px solid #685014;

    color: #ffd45a;

    padding: 17px;

    border-radius: 10px;

    line-height: 1.6;
}


.success {

    background: #061c15;

    border:
        1px solid #0b6046;

    color: #6fffc8;

    padding: 17px;

    border-radius: 10px;
}


.error {

    background: #240b10;

    border:
        1px solid #6d202c;

    color: #ff7180;

    padding: 17px;

    border-radius: 10px;

    margin-bottom: 20px;
}


.social-buttons {

    display: flex;

    flex-wrap: wrap;

    gap: 12px;

    margin-top: 20px;
}


.social-buttons a {

    text-decoration: none;

    color: white;

    background: #111c27;

    border:
        1px solid #294354;

    padding: 13px 20px;

    border-radius: 8px;
}


.social-buttons a:hover {

    border-color: #00eaff;

    color: #00eaff;
}


.hash {

    word-break: break-all;

    background: #050a0f;

    padding: 12px;

    border-radius: 7px;

    color: #91a5b5;

    font-size: 12px;
}


.footer {

    text-align: center;

    color: #506675;

    margin-top: 35px;

    font-size: 12px;
}


@media(max-width:600px) {

    .header h1 {

        font-size: 27px;
    }

    .card {

        padding: 20px;
    }

}

</style>

</head>


<body>


<div class="container">


<div class="header">

<div class="logo">
CYBERSHIELD AI
</div>

<h1>
IMAGE <span>MISUSE CHECKER</span>
</h1>

<p>
AI-assisted image reuse and similarity detection
</p>

</div>


{% if error %}

<div class="error">

<strong>ERROR:</strong>

{{ error }}

</div>

{% endif %}


<!-- =====================================================
     UPLOAD
===================================================== -->

<div class="card">

<h2>
📸 Upload Your Photo
</h2>

<p>
Upload a photo to check for possible duplicate,
reused or modified copies.
</p>


<form
    method="POST"
    action="/check"
    enctype="multipart/form-data"
>


<div class="upload-area">

<div class="upload-icon">
🖼️
</div>

<strong>
SELECT IMAGE
</strong>

<br>

<input
    type="file"
    name="image"
    accept="image/png,image/jpeg,image/jpg,image/webp"
    onchange="previewImage(event)"
    required
>


<br>


<button type="submit">
🔍 CHECK IMAGE
</button>


<div
    class="preview"
    id="previewBox"
    style="display:none;"
>

<img
    id="previewImage"
    alt="Image Preview"
>

</div>


</div>


</form>

</div>


{% if result %}


<!-- =====================================================
     IMAGE
===================================================== -->

<div class="card">

<h2>
🖼️ Uploaded Image
</h2>


<div class="preview">

<img
    src="/image/{{ filename }}"
    alt="Uploaded Image"
>

</div>

</div>


<!-- =====================================================
     SECURITY RESULT
===================================================== -->

<div class="card">

<h2>
🛡️ Security Analysis
</h2>


<div class="stats">


<div class="stat">

<div class="stat-label">
SECURITY SCORE
</div>

<div class="stat-value">
{{ score }}/100
</div>

</div>


<div class="stat">

<div class="stat-label">
MISUSE RISK
</div>

<div class="stat-value {{ risk|lower }}">
{{ risk }}
</div>

</div>


<div class="stat">

<div class="stat-label">
SIMILARITY
</div>

<div class="stat-value">
{{ similarity }}%
</div>

</div>


<div class="stat">

<div class="stat-label">
IMAGE QUALITY
</div>

<div class="stat-value">
{{ analysis.quality }}
</div>

</div>


</div>

</div>


<!-- =====================================================
     SIMILARITY
===================================================== -->

<div class="card">

<h2>
🔍 Similarity Detection
</h2>


<p>

Image similarity:

<strong>
{{ similarity }}%
</strong>

</p>


<div class="progress">

<div
    class="progress-bar"
    style="width: {{ similarity }}%;">
</div>

</div>


<br>


<div class="result">

<strong>
Detection Result
</strong>

<br>

{{ result }}

</div>

</div>


<!-- =====================================================
     IMAGE INFORMATION
===================================================== -->

<div class="card">

<h2>
📊 Image Information
</h2>


<div class="stats">


<div class="stat">

<div class="stat-label">
WIDTH
</div>

<div class="stat-value">
{{ analysis.width }} px
</div>

</div>


<div class="stat">

<div class="stat-label">
HEIGHT
</div>

<div class="stat-value">
{{ analysis.height }} px
</div>

</div>


<div class="stat">

<div class="stat-label">
FORMAT
</div>

<div class="stat-value">
{{ analysis.format }}
</div>

</div>


<div class="stat">

<div class="stat-label">
SIZE
</div>

<div class="stat-value">
{{ analysis.file_size_kb }} KB
</div>

</div>


<div class="stat">

<div class="stat-label">
MEGAPIXELS
</div>

<div class="stat-value">
{{ analysis.megapixels }} MP
</div>

</div>


<div class="stat">

<div class="stat-label">
BRIGHTNESS
</div>

<div class="stat-value">
{{ analysis.brightness }}
</div>

</div>


</div>

</div>


<!-- =====================================================
     MATCH
===================================================== -->

<div class="card">

<h2>
🔎 Previous Image Match
</h2>


{% if match %}

<div class="warning">

<strong>
Possible Similar Image Found
</strong>

<br><br>

CyberShield found a previously scanned image
with approximately

<strong>
{{ similarity }}%
</strong>

similarity.

<br><br>

Previous scan time:

<strong>
{{ match["scan_time"] }}
</strong>

</div>

{% else %}

<div class="success">

<strong>
No Strong Local Match Found
</strong>

<br><br>

No highly similar image was found in the
CyberShield local scan database.

</div>

{% endif %}

</div>


<!-- =====================================================
     IMAGE FINGERPRINT
===================================================== -->

<div class="card">

<h2>
🔐 Image Fingerprint
</h2>


<p>
<strong>SHA-256</strong>
</p>

<div class="hash">
{{ sha256 }}
</div>


<br>


<p>
<strong>Perceptual Hash</strong>
</p>

<div class="hash">
{{ phash }}
</div>

</div>


<!-- =====================================================
     SOCIAL MEDIA
===================================================== -->

<div class="card">

<h2>
🌐 Social Media Verification
</h2>


<div class="warning">

<strong>
Important:
</strong>

<br><br>

CyberShield does not directly access private or
restricted Instagram, Facebook or X/Twitter
content.

This local scanner detects image similarity
inside the CyberShield scan database.

For social-media verification, check the
official platforms manually.

</div>


<div class="social-buttons">


<a
    href="https://www.instagram.com/"
    target="_blank"
>

📷 Instagram

</a>


<a
    href="https://www.facebook.com/"
    target="_blank"
>

📘 Facebook

</a>


<a
    href="https://x.com/"
    target="_blank"
>

𝕏 X / Twitter

</a>


</div>

</div>


<!-- =====================================================
     RISK MESSAGE
===================================================== -->

<div class="card">

<h2>
🚨 Security Recommendation
</h2>


{% if risk == "HIGH" %}

<div class="warning">

<strong class="high">
HIGH MISUSE RISK
</strong>

<br><br>

A highly similar image was detected.
Verify the source, account and post manually
before taking action.

</div>


{% elif risk == "MEDIUM" %}

<div class="warning">

<strong class="medium">
MEDIUM MISUSE RISK
</strong>

<br><br>

Some similarity was detected.
Perform additional verification on the
relevant social-media platform.

</div>


{% else %}

<div class="success">

<strong class="low">
LOW MISUSE RISK
</strong>

<br><br>

No strong similarity was detected in the
current CyberShield local database.

</div>

{% endif %}


</div>


{% endif %}


<div class="footer">

CYBERSHIELD AI • IMAGE MISUSE CHECKER

<br>

AI-assisted security awareness system

</div>


</div>


<script>

function previewImage(event) {

    const file =
        event.target.files[0];

    const previewBox =
        document.getElementById(
            "previewBox"
        );

    const previewImage =
        document.getElementById(
            "previewImage"
        );


    if (!file) {

        previewBox.style.display =
            "none";

        return;
    }


    const reader =
        new FileReader();


    reader.onload = function(e) {

        previewImage.src =
            e.target.result;

        previewBox.style.display =
            "block";

    };


    reader.readAsDataURL(file);

}

</script>


</body>

</html>

"""


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template_string(
        HTML
    )


# ============================================================
# CHECK IMAGE
# ============================================================

@app.route("/check", methods=["POST"])
def check_image():

    uploaded_file = request.files.get("image")


    if not uploaded_file:

        return render_template_string(
            HTML,
            error="Please select an image."
        )


    if uploaded_file.filename == "":

        return render_template_string(
            HTML,
            error="No image selected."
        )


    # Allowed extensions

    allowed = {
        "jpg",
        "jpeg",
        "png",
        "webp"
    }


    original_name = uploaded_file.filename


    extension = (
        original_name
        .rsplit(".", 1)[-1]
        .lower()
    )


    if extension not in allowed:

        return render_template_string(
            HTML,
            error=(
                "Only JPG, JPEG, PNG and WEBP "
                "images are supported."
            )
        )


    # Safe filename

    safe_name = re.sub(
        r"[^a-zA-Z0-9_.-]",
        "_",
        original_name
    )


    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )


    filename = (
        timestamp
        + "_"
        + safe_name
    )


    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )


    uploaded_file.save(file_path)


    try:

        # ----------------------------------------------------
        # Validate image
        # ----------------------------------------------------

        image = Image.open(file_path)

        image.verify()


        # ----------------------------------------------------
        # Hash
        # ----------------------------------------------------

        sha256 = calculate_sha256(
            file_path
        )


        phash = calculate_phash(
            file_path
        )


        # ----------------------------------------------------
        # Analysis
        # ----------------------------------------------------

        analysis = analyze_image(
            file_path
        )


        analysis["file_size_kb"] = round(
            analysis["file_size"] / 1024,
            2
        )


        # ----------------------------------------------------
        # Compare
        # ----------------------------------------------------

        similarity, match = find_previous_match(
            phash
        )


        # ----------------------------------------------------
        # Risk
        # ----------------------------------------------------

        risk, score = calculate_risk(
            similarity
        )


        # ----------------------------------------------------
        # Result message
        # ----------------------------------------------------

        if similarity >= 95:

            result = (
                "Very high visual similarity detected. "
                "The image is almost identical to a "
                "previously scanned image."
            )

        elif similarity >= 85:

            result = (
                "High visual similarity detected. "
                "The image may be a reused or modified copy."
            )

        elif similarity >= 70:

            result = (
                "Moderate similarity detected. "
                "Additional verification is recommended."
            )

        elif similarity >= 50:

            result = (
                "Some visual similarity was detected, "
                "but there is not enough evidence to "
                "confirm image reuse."
            )

        else:

            result = (
                "No strong similarity was found in "
                "the current CyberShield scan database."
            )


        # ----------------------------------------------------
        # Save scan
        # ----------------------------------------------------

        conn = get_db()


        conn.execute("""
            INSERT INTO scans
            (
                filename,
                sha256,
                phash,
                width,
                height,
                similarity,
                risk,
                score,
                result,
                scan_time
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            filename,

            sha256,

            phash,

            analysis["width"],

            analysis["height"],

            similarity,

            risk,

            score,

            result,

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        ))


        conn.commit()

        conn.close()


        # ----------------------------------------------------
        # Display result
        # ----------------------------------------------------

        return render_template_string(

            HTML,

            result=result,

            filename=filename,

            sha256=sha256,

            phash=phash,

            analysis=analysis,

            similarity=similarity,

            risk=risk,

            score=score,

            match=match

        )


    except Exception as error:

        if os.path.exists(file_path):

            os.remove(file_path)


        return render_template_string(

            HTML,

            error=(
                "Invalid image or image processing error: "
                + str(error)
            )

        )


# ============================================================
# SERVE IMAGE
# ============================================================

@app.route("/image/<filename>")
def serve_image(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# ============================================================
# CLEAR HISTORY
# ============================================================

@app.route("/clear-history")
def clear_history():

    conn = get_db()

    conn.execute(
        "DELETE FROM scans"
    )

    conn.commit()

    conn.close()


    return """

    <script>

        alert("Image scan history cleared.");

        window.location.href="/";

    </script>

    """


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print(" CYBERSHIELD AI - IMAGE MISUSE CHECKER")
    print("=" * 60)
    print()
    print(" Server running at:")
    print(" http://127.0.0.1:5001")
    print()
    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )