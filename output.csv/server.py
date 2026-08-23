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

# 유해조류 키워드 매핑 테이블 (한국어 / 영어 학명 및 일반명 대응)
BIRD_SOUND_MAP = {
    "bulbul": "bulbul_alarm.mp3",
    "직박구리": "bulbul_alarm.mp3",
    "magpie": "magpie_alarm.mp3",
    "까치": "magpie_alarm.mp3",
    "rook": "rook_alarm.mp3",
    "떼까마귀": "rook_alarm.mp3",
    "crow": "rook_alarm.mp3",  # 까마귀류 대응
    "까마귀": "rook_alarm.mp3",
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

        # 감지된 새 이름 매칭 확인
        matched_alarm = None
        for key, sound_file in BIRD_SOUND_MAP.items():
            if key in bird_name:
                matched_alarm = sound_file
                break

        # 일치하는 새가 없으면 기본값으로 참새 경고음 사용
        if not matched_alarm:
            matched_alarm = "sparrow_alarm.mp3"

        bird_sound_path = os.path.join(BASE_DIR, matched_alarm)

        # 천적 소리(awk vs bubo) 중 1개 랜덤 선택
        chosen_predator_path = random.choice(PREDATOR_SOUNDS)

        # 1) 해당 유해조류 경고음 재생
        subprocess.Popen(["mpg123", bird_sound_path])
        played_files.append(bird_sound_path)

        # 2) 랜덤 천적 소리 동시 재생
        subprocess.Popen(["mpg123", chosen_predator_path])
        played_files.append(chosen_predator_path)

        return jsonify(
            {
                "status": "success",
                "detected_bird": bird_name,
                "alarm_file": bird_sound_path,
                "predator_file": chosen_predator_path,
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# 2. 소리 정지 API (모든 사운드 일괄 정지)
@app.route("/api/stop-sound", methods=["POST"])
def stop_sound():
    try:
        # 재생 중인 모든 오디오 프로세스 강제 종료
        subprocess.run(["pkill", "-9", "mpg123"], stderr=subprocess.DEVNULL)
        return jsonify({"status": "success", "message": "모든 소리 정지 성공"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500)