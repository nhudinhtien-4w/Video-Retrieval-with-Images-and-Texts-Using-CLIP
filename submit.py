import requests
from typing import List, Optional, Dict, Any

# ==============================
# 🔧 CẤU HÌNH — ĐIỀN Ở ĐÂY
# ==============================
# DRES_BASE_URL = "192.168.28.151:5000"
# SESSION_ID: Optional[str] = "C0da9byZOq_FWcZ1adbOTpkB4Xvb-qsz"
# USERNAME: Optional[str] = "team007"
# PASSWORD: Optional[str] = "123456"
# DEFAULT_FPS: float = 2   # fps = 2 → 1 frame = 500ms


DRES_BASE_URL = "http://192.168.20.156:5601"
SESSION_ID: Optional[str] = "aIJ3tUD0K9iTm4Ya9jufVArha_Ga9T82"
USERNAME: Optional[str] = "team007"
PASSWORD: Optional[str] = "1234556"
DEFAULT_FPS: float = 2   # fps = 2 → 1 frame = 500ms

# ==============================
# 🧩 KIỂU DỮ LIỆU
# ==============================
ResultItem = Dict[str, Any]


# =========================================
# 🔐 SESSION ID
# =========================================
def get_session_id() -> str:
    if SESSION_ID:
        print("[info] Using manual SESSION_ID.")
        return SESSION_ID

    if not USERNAME or not PASSWORD:
        raise RuntimeError(
            "No SESSION_ID provided and USERNAME/PASSWORD not set."
        )

    login_url = f"{DRES_BASE_URL}/api/v2/login"
    payload = {"username": USERNAME, "password": PASSWORD}
    resp = requests.post(login_url, json=payload, timeout=10)
    if not resp.ok:
        raise RuntimeError(f"Login failed: {resp.status_code} - {resp.text}")

    data = resp.json()
    sid = data.get("sessionId") or data.get("sessionID") or data.get("session_id")
    print("[info] Auto-login success. sessionId =", sid)
    return sid


# =========================================
# 🧭 GET ACTIVE EVALUATION
# =========================================
def get_active_evaluation_id(session_id: str) -> str:
    resp = requests.get(
        f"{DRES_BASE_URL}/api/v2/client/evaluation/list",
        params={"session": session_id},
        timeout=10
    )
    if not resp.ok:
        raise RuntimeError(resp.text)

    evaluations = resp.json()
    active = next((e for e in evaluations if str(e.get("status")).upper() == "ACTIVE"), None)
    if not active:
        raise RuntimeError("No active evaluation found.")
    return str(active.get("id"))


# =========================================
# ⏱️ FRAME INDEX → MILLISECONDS
# =========================================
def ms_from_frame_index(frame_value: Any, fps: float = DEFAULT_FPS) -> int:
    frame_index = int(frame_value)
    ms = int((frame_index / fps) * 1000)

    # ⭐⭐ DEBUG QUAN TRỌNG — kiểm tra timestamp
    print(f"[DEBUG] frame_index={frame_index}, fps={fps} → timestamp_ms={ms}")

    return ms


# =========================================
# 📤 SUBMIT RESULT
# =========================================
def submit_result(
    result: ResultItem,
    session_id: str,
    evaluation_id: str,
    question: Optional[str] = None,
    fps: float = DEFAULT_FPS,
) -> Dict[str, Any]:

    video_id = str(result["videoId"])
    
    # Use timestampMs if provided (from video player), otherwise calculate from frame
    if "timestampMs" in result and result["timestampMs"] is not None:
        ms = int(result["timestampMs"])
        print(f"[DEBUG] Using provided timestamp: {ms} ms")
    else:
        timestamp = result["timestamp"]  # frame index
        ms = ms_from_frame_index(timestamp, fps=fps)  # tính ms

    if question:
        text = f"QA-{question}-{video_id}-{ms}"
        body = {"answerSets": [{"answers": [{"text": text}]}]}
    else:
        body = {
            "answerSets": [
                {
                    "answers": [
                        {"mediaItemName": video_id, "start": ms, "end": ms}
                    ]
                }
            ]
        }

    url = f"{DRES_BASE_URL}/api/v2/submit/{evaluation_id}"
    resp = requests.post(url, params={"session": session_id}, json=body, timeout=15)
    if not resp.ok:
        raise RuntimeError(resp.text)

    data = resp.json()
    print("[DEBUG] DRES response:", data)
    
    # ⭐ Kiểm tra status trong response body (có thể là boolean hoặc string)
    status = data.get("status")
    
    # Trường hợp 1: status là boolean False
    if status is False:
        description = data.get("description", "No description provided")
        raise RuntimeError(f"DRES rejected submission: {description}")
    
    # Trường hợp 2: status là string (WRONG, ERROR, etc.)
    if isinstance(status, str):
        status_upper = status.upper()
        if status_upper in ["WRONG", "ERROR", "UNDECIDABLE"]:
            description = data.get("description", "No description provided")
            raise RuntimeError(f"DRES rejected - Status: {status}, Description: {description}")
        
        # Kiểm tra các status hợp lệ
        if status_upper not in ["CORRECT", "INDETERMINATE", "PENDING"]:
            print(f"[WARNING] Unexpected DRES status: {status}")
    
    print("[OK] DRES submission accepted:", data)
    return data


# =========================================
# 🔄 FULL SUBMISSION FLOW
# =========================================
def full_submission_flow(result: ResultItem, question: Optional[str] = None, fps: float = DEFAULT_FPS) -> Dict[str, Any]:
    session_id = get_session_id()
    evaluation_id = get_active_evaluation_id(session_id)
    return submit_result(result, session_id, evaluation_id, question=question, fps=fps)



# =========================================
# 🧪 CHẠY THỬ
# =========================================
if __name__ == "__main__":

    sample_result = {"videoId": "L22_V012", "timestamp": "2016"}

    try:
        resp1 = full_submission_flow(sample_result)
        print("Submit standard OK:", resp1)
    except Exception as e:
        print("Submit standard error:", e)
