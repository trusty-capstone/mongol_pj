from datetime import datetime
import os
import random
import subprocess
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".")

# 기본 경로 설정
BASE_DIR = "/home/user/mongol_pj/output.csv/bird_alarm"
STREAMDATA_DIR = "/home/user/mongol_pj/BirdNET-Analyzer-main/Recorded/StreamData"
OUTPUT_DIR = "/home/user/mongol_pj/output.csv"
VENV_PYTHON = "/home/user/mongol_pj/BirdNET-Analyzer-main/venv/bin/python3"

# 천적 소리 목록 (mp3)
PREDATOR_SOUNDS = [
    os.path.join(BASE_DIR, "awk_sound.mp3"),
    os.path.join(BASE_DIR, "bubo_sound.mp3"),
]

# 유해조류 키워드 매핑 테이블
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


# 1. 웹에서 버튼 눌러 녹음 & 분석 실행 API
@app.route("/api/record-and-analyze", methods=["POST"])
def record_and_analyze():
    data = request.get_json(silent=True) or {}
    duration = str(data.get("duration", 5))

    os.makedirs(STREAMDATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    file_name = datetime.now().strftime("%Y-%m-%d-birdnet-%H:%M:%S.wav")
    file_path = os.path.join(STREAMDATA_DIR, file_name)

    try:
        # 1. 마이크로 녹음
        record_cmd = [
            "arecord",
            "-D",
            "plughw:2,0",
            "-d",
            duration,
            "-c",
            "1",
            "-r",
            "48000",
            "-f",
            "S16_LE",
            file_path,
        ]
        subprocess.run(record_cmd, check=True)

        # 2. BirdNET 환경 설정
        birdnet_root = "/home/user/mongol_pj/BirdNET-Analyzer-main"
        env = os.environ.copy()
        env["PYTHONPATH"] = (
            birdnet_root + (":" + env["PYTHONPATH"] if "PYTHONPATH" in env else "")
        )

        # 3. BirdNET 분석 실행
        analyze_cmd = [
            VENV_PYTHON,
            "-m",
            "birdnet_analyzer.analyze",
            "-o",
            OUTPUT_DIR,
            "--rtype",
            "csv",
            "--min_conf",
            "0.25",
            file_path,
        ]

        result = subprocess.run(
            analyze_cmd,
            cwd=birdnet_root,
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"[BirdNET Error] {result.stderr}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"분석 엔진 오류: {result.stderr}",
                    }
                ),
                500,
            )

        return jsonify(
            {
                "status": "success",
                "message": "녹음 및 분석 완료",
                "file": file_name,
            }
        )

    except subprocess.CalledProcessError as e:
        return (
            jsonify({"status": "error", "message": f"녹음 장치 오류: {str(e)}"}),
            500,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# 2. 소리 재생 API
@app.route("/api/play-sound", methods=["POST"])
def play_sound():
    data = request.get_json(silent=True) or {}
    bird_name = data.get("bird", "").lower()

    # 기존 실행 중인 모든 mpg123 프로세스 종료
    subprocess.run(["pkill", "-9", "mpg123"], stderr=subprocess.DEVNULL)

    try:
        played_files = []

        # 4종 유해조류 매칭 확인
        matched_alarm = None
        for key, sound_file in BIRD_SOUND_MAP.items():
            if key in bird_name:
                matched_alarm = sound_file
                break

        # 천적 소리(awk vs bubo) 중 1개 랜덤 선택
        chosen_predator = random.choice(PREDATOR_SOUNDS)

        if matched_alarm:
            # 유해조류 4종: 경고음 + 천적 소리 동시 재생
            bird_sound_path = os.path.join(BASE_DIR, matched_alarm)
            subprocess.Popen(["mpg123", bird_sound_path])
            subprocess.Popen(["mpg123", chosen_predator])
            played_files.extend([bird_sound_path, chosen_predator])
        else:
            # 기타 조류 / 미확인: 천적 소리 1종만 단독 재생
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


# 3. 소리 정지 API (모든 소리 정지)
@app.route("/api/stop-sound", methods=["POST"])
def stop_sound():
    try:
        subprocess.run(["pkill", "-9", "mpg123"], stderr=subprocess.DEVNULL)
        return jsonify({"status": "success", "message": "모든 소리 정지 완료"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500)