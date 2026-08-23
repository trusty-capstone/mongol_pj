import os
import random
import subprocess
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".")

BASE_DIR = "/home/user/mongol_pj/output.csv/bird_alarm"

# 천적 소리 목록 (awk, bubo)
PREDATOR_SOUNDS = [
    os.path.join(BASE_DIR, "awk_sound.mp3"),
    os.path.join(BASE_DIR, "bubo_sound.mp3"),
]

# 유해조류 4종 키워드 매핑 테이블
BIRD_SOUND_MAP = {
    "bulbul": "bulbul_alarm.mp3",
    "직박구리": "bulbul_alarm.mp3",
    "magpie": "magpie_alarm.mp3",
    "까치": "magpie_alarm.mp3",
    "rook": "rook_alarm.mp3",
    "떼까마귀": "rook_alarm.mp3",
    "sparrow": "sparrow_alarm.mp3",
    "참새": "sparrow_alarm.mp3",
}


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
    bird_name = data.get("bird", "").lower()

    # 기존 실행 중인 모든 mpg123 프로세스 강제 정리
    subprocess.run(["pkill", "-9", "mpg123"], stderr=subprocess.DEVNULL)

    try:
        played_files = []

        # 4종 유해조류 매칭 여부 확인
        matched_alarm = None
        for key, sound_file in BIRD_SOUND_MAP.items():
            if key in bird_name:
                matched_alarm = sound_file
                break

        # 천적 소리(awk vs bubo) 중 1개 랜덤 선택
        chosen_predator = random.choice(PREDATOR_SOUNDS)

        if matched_alarm:
            # [4종 유해조류 감지 시] 해당 새 경고음 + 천적 소리 동시 재생
            bird_sound_path = os.path.join(BASE_DIR, matched_alarm)
            subprocess.Popen(["mpg123", bird_sound_path])
            subprocess.Popen(["mpg123", chosen_predator])
            played_files.extend([bird_sound_path, chosen_predator])
        else:
            # [그 외의 새 감지 시] 천적 소리(awk 또는 bubo) 1종만 단독 재생
            subprocess.Popen(["mpg123", chosen_predator])
            played_files.append(chosen_predator)

        return jsonify(
            {
                "status": "success",
                "detected_bird": bird_name,
                "is_target_bird": bool(matched_alarm),
                "played_files": played_files,
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# 2. 소리 정지 API (모든 소리 일괄 중단)
@app.route("/api/stop-sound", methods=["POST"])
def stop_sound():
    try:
        subprocess.run(["pkill", "-9", "mpg123"], stderr=subprocess.DEVNULL)
        return jsonify({"status": "success", "message": "모든 소리 정지 완료"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500)