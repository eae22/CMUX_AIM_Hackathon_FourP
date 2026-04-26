# CMUX_AIM_Hackathon_FourP
CMUX x AIM Hackathon 팀 FourP 레포지토리입니다.

# 🛡️ PixelGuard — AI 복제·딥페이크 방지 서비스

> "AI가 내 얼굴을 훔치려는 순간, 에이전트가 독을 심는다"

**트랙:** AI Safety & Security 

---

## 📌 서비스 개요

SNS에 올릴 사진을 업로드하면, 육안으로는 원본과 동일하지만  
AI가 얼굴 인식 · 학습 · 딥페이크 생성을 못하는 보호 이미지로 변환해주는 서비스.

---

## 🏗️ 시스템 아키텍처

```
[프론트엔드 B-2]
      ↓ POST /api/protect (Base64 이미지)
[FastAPI 서버 A-2]
      ↓ analyze_face()
      ↓ apply_protection()
      ↓ build_simulation_metrics()
[AI 엔진 A-1]
      ↓ JSON 응답
[프론트엔드 B-2]
```

---

## 📁 프로젝트 구조

```
CMUX_AIM_Hackathon_FourP/
├── main.py                  # FastAPI 앱 + 엔드포인트
├── schemas.py               # Pydantic 모델 (API 스펙)
├── services/
│   ├── __init__.py
│   └── ai_stub.py           # A-1 교체 대상 함수 3개
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

API 문서: http://localhost:8000/docs

---

## 🔌 API 스펙

### `POST /api/protect`

**Request**
```json
{ "image_base64": "data:image/png;base64,..." }
```

**Response**
```json
{
  "request_id": "string",
  "original_image_base64": "data:image/png;base64,...",
  "face_analysis": {
    "is_face_detected": true,
    "detection_confidence": 0.98,
    "landmarks": [
      { "id": 0, "part": "left_eye", "x": 145.2, "y": 210.5 }
    ],
    "ai_perception": {
      "label": "Human Face",
      "feature_map_url": "data:image/png;base64,...",
      "grad_cam_heatmap": "data:image/png;base64,..."
    }
  },
  "protection_result": {
    "protected_image_base64": "data:image/png;base64,...",
    "noise_only_map": "data:image/png;base64,...",
    "is_face_detected": false,
    "detection_confidence": 0.08,
    "ai_perception": {
      "label": "Noise / Unknown",
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
      "loss_original": [0.85, 0.62, 0.41, 0.22, 0.12, 0.08, 0.05, 0.03, 0.02, 0.01],
      "loss_protected": [0.88, 0.87, 0.89, 0.86, 0.91, 0.88, 0.89, 0.90, 0.87, 0.89],
      "accuracy_original": [0.45, 0.68, 0.79, 0.88, 0.94, 0.97, 0.98, 0.99, 0.99, 0.99],
      "accuracy_protected": [0.12, 0.11, 0.13, 0.10, 0.12, 0.11, 0.14, 0.12, 0.11, 0.13]
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

| 역할 | 담당 | 작업 |
|------|------|------|
| A-1 | AI 알고리즘 | MediaPipe 얼굴 특징점, FGSM/PGD 노이즈, Grad-CAM |
| A-2 | 백엔드 인프라 | FastAPI 서버, Base64 처리, JSON API |
| B-1 | 데이터 시뮬레이션 | 딥페이크 샘플, Loss/Accuracy 그래프 데이터 |
| B-2 | 프론트엔드 | 업로드 UI, 비교 슬라이더, 히트맵, 대시보드 |

---

## 🔗 A-1 연결 가이드

`services/ai_stub.py`에서 `TODO(A-1)` 달린 함수 3개만 실제 구현으로 교체:

```python
# 1. 얼굴 특징점 추출
def analyze_face(image_b64: str) -> FaceAnalysis

# 2. FGSM/PGD 보호 이미지 생성
def apply_protection(image_b64: str, algorithm: str, epsilon: float) -> ProtectionResult

# 3. 시뮬레이션 데이터 (B-1 교체 가능)
def build_simulation_metrics(original_b64: str, protected_b64: str) -> SimulationMetrics
```

⚠️ 함수 이름, 인자, 리턴 타입 절대 변경 금지

---

## 🌿 브랜치 전략

```
main         ← 데모 직전 최종 머지
dev          ← 통합 브랜치
├── feat/a1-ai-core
├── feat/a2-backend
├── feat/b1-data
└── feat/b2-frontend
```

