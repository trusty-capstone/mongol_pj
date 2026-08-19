import subprocess
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".")


@app.route("/")
def index():
    return send_from_directory(".", "sound.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)


# 1. 소리 재생 API
@app.route("/api/play-sound", methods=["POST"])
def play_sound():
    data = request.get_json(silent=True) or {}
    bird = data.get("bird", "").lower()

    # 참새 매칭 조건 유연화
    if "sparrow" in bird or "참새" in bird:
        sound_path = "/home/user/mongol_pj/output.csv/bird_alarm/sparrow_alarm.mp3"
    else:
        sound_path = "/home/user/mongol_pj/output.csv/bird_alarm/sparrow_alarm.mp3"

    try:
        # 기존 재생 중인 mpg123 중지 후 재생
        subprocess.run(["pkill", "-9", "mpg123"], stderr=subprocess.DEVNULL)
        subprocess.Popen(["mpg123", sound_path])
        return jsonify({"status": "success", "file": sound_path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# 2. 소리 정지 API
@app.route("/api/stop-sound", methods=["POST"])
def stop_sound():
    try:
        subprocess.run(["pkill", "-9", "mpg123"], check=False)
        return jsonify({"status": "success", "message": "정지 성공"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # 5500번 포트로 실행
    app.run(host="0.0.0.0", port=5500)