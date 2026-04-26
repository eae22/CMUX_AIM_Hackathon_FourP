## CMUX_AIM_Hackathon_FourP

# 🛡️ 404 Face Not Found — AI 복제·딥페이크 방지 서비스

> "우리 눈엔 같은 사진, AI 눈엔 노이즈"

**트랙:** AI Safety & Security

---

## 📌 서비스 개요

SNS에 올릴 사진을 업로드하면, 육안으로는 원본과 동일하지만  
AI가 얼굴 인식 · 학습 · 딥페이크 생성을 못하는 보호 이미지로 변환해주는 서비스.

---

## 🏗️ 시스템 아키텍처

```
[프론트엔드]
      ↓ POST /api/protect (Base64 이미지)
[FastAPI 서버]
      ↓ analyze_face()
      ↓ apply_protection()
      ↓ build_simulation_metrics()
[AI 엔진]
      ↓ JSON 응답
[프론트엔드]
```

---

## 📁 프로젝트 구조

```
CMUX_AIM_Hackathon_FourP/
├── main.py                  # FastAPI 앱 + 엔드포인트
├── schemas.py               # Pydantic 모델 (API 스펙)
├── services/
│   ├── __init__.py
│   └── ai_stub.py           # AI 알고리즘 교체 대상 함수 3개
├── static/                  # 프론트엔드 (FastAPI가 / 로 서빙)
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   ├── analysis.html
│   ├── analysis.css
│   ├── analysis.js
│   └── icon.svg
├── requirements.txt
└── README.md
```

---

## 🚀 빠른 시작

```bash
git clone https://github.com/eae22/CMUX_AIM_Hackathon_FourP.git
cd CMUX_AIM_Hackathon_FourP
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

- 프론트엔드: http://localhost:8000
- API 문서: http://localhost:8000/docs

---

## 🔌 API

### `POST /api/protect`

**Request**
```json
{
  "request_id": "optional_string",
  "image_data": {
    "original_base64": "data:image/png;base64,...",
    "format": "jpeg | png | webp"
  },
  "parameters": {
    "protection_algorithm": "FGSM | PGD",
    "epsilon": 0.03,
    "target_detector": "FaceNet_v1"
  }
}
```

**Response**
```json
{
  "request_id": "string",
  "status": "success",
  "process_time_sec": 0.123,
  "original_analysis": {
    "is_face_detected": true,
    "detection_confidence": 0.98,
    "landmarks": [
      { "id": 0, "part": "left_eye", "x": 145.2, "y": 210.5 }
    ],
    "ai_perception": {
      "label": "Human Face (Person)",
      "feature_map_url": "data:image/png;base64,...",
      "grad_cam_heatmap": "data:image/png;base64,..."
    }
  },
  "protection_result": {
    "protected_image_base64": "data:image/png;base64,...",
    "noise_only_map": "data:image/png;base64,...",
    "is_face_detected": false,
    "detection_confidence": 0.08,
    "landmarks": [],
    "ai_perception": {
      "label": "Noise / Texture / Unknown",
      "feature_map_url": "data:image/png;base64,...",
      "grad_cam_heatmap": "data:image/png;base64,..."
    }
  },
  "simulation_metrics": {
    "deepfake_vulnerability": {
      "original_score": 95.5,
      "protected_score": 4.2,
      "visual_comparison_sample": "data:image/png;base64,..."
    },
    "training_efficiency_graph": {
      "epochs": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
      "loss_original":      [2.45, 1.78, 1.21, 0.83, 0.52, 0.31, 0.17, 0.09, 0.04, 0.02],
      "loss_protected":     [2.44, 2.41, 2.47, 2.39, 2.45, 2.42, 2.48, 2.40, 2.44, 2.46],
      "accuracy_original":  [0.51, 0.63, 0.73, 0.82, 0.89, 0.93, 0.96, 0.98, 0.99, 0.99],
      "accuracy_protected": [0.51, 0.53, 0.50, 0.52, 0.51, 0.53, 0.50, 0.52, 0.51, 0.52]
    }
  }
}
```

### `GET /api/download/{request_id}`
보호 이미지 파일 다운로드

### `GET /health`
서버 상태 확인

---

## 👥 팀 역할

| 담당 | 작업 |
|------|------|
| AI 알고리즘 | MediaPipe 얼굴 특징점, FGSM/PGD 노이즈, Grad-CAM |
| 백엔드 | FastAPI 서버, Base64 처리, JSON API, 정적 파일 서빙 |
| 데이터 시뮬레이션 | 딥페이크 비교 시각화, Loss/Accuracy 그래프 데이터 |
| 프론트엔드 | 업로드 UI, 보호 결과 비교, 히트맵, 분석 대시보드 |

---

## 🔗 AI 알고리즘 연결 가이드

`services/ai_stub.py`에서 `TODO(A-1)` 달린 함수 3개만 실제 구현으로 교체:

```python
# 1. 얼굴 특징점 추출
def analyze_face(image_b64: str) -> FaceAnalysis

# 2. FGSM/PGD 보호 이미지 생성
def apply_protection(image_b64: str, algorithm: str, epsilon: float) -> ProtectionResult

# 3. 시뮬레이션 데이터
def build_simulation_metrics(original_b64: str, protected_b64: str) -> SimulationMetrics
```

⚠️ 함수 이름, 인자, 리턴 타입 절대 변경 금지

---

## 🌿 브랜치 전략

```
main    ← 데모 직전 최종 머지
dev     ← 통합 브랜치
├── feat/a1-model       # AI 알고리즘
├── feat/a2-backend     # 백엔드
├── feat/b1-data        # 데이터 시뮬레이션
└── feat/b2-frontend    # 프론트엔드
```
