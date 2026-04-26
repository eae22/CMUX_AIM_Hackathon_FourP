"""
A-1(AI 팀) 연결 포인트.
각 함수를 실제 구현으로 교체하면 됩니다.
함수 시그니처(인자·반환 타입)는 그대로 유지해 주세요.
"""

import base64
import time
from PIL import Image
import io

from schemas import (
    AIPerception,
    DeepfakeVulnerability,
    FaceAnalysis,
    Landmark,
    ProtectionResult,
    SimulationMetrics,
    TrainingEfficiencyGraph,
)


# ─── 더미 이미지 헬퍼 ────────────────────────────────────────────

def _make_dummy_image_b64(width: int = 128, height: int = 128, color=(180, 200, 220)) -> str:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _make_dummy_heatmap_b64() -> str:
    return _make_dummy_image_b64(128, 128, color=(220, 80, 60))


def _make_dummy_protected_b64(original_b64: str) -> str:
    """원본 이미지에 노이즈를 흉내 낸 더미 이미지를 반환."""
    # TODO(A-1): FGSM/PGD 적용 후 실제 보호 이미지 반환
    return _make_dummy_image_b64(256, 256, color=(210, 200, 195))


# ─── A-1 교체 대상 함수들 ────────────────────────────────────────

def analyze_face(image_b64: str) -> FaceAnalysis:
    """
    원본 이미지에서 얼굴을 분석합니다.

    [A-1 교체]
    - MediaPipe / dlib 으로 랜드마크 추출
    - Grad-CAM / Feature Map 생성
    """
    # TODO(A-1): 실제 얼굴 분석으로 교체
    return FaceAnalysis(
        is_face_detected=True,
        detection_confidence=0.9852,
        landmarks=[
            Landmark(id=0, part="left_eye",    x=145.2, y=210.5),
            Landmark(id=1, part="right_eye",   x=198.4, y=212.1),
            Landmark(id=2, part="nose_tip",    x=172.0, y=245.8),
            Landmark(id=3, part="mouth_left",  x=150.5, y=280.2),
            Landmark(id=4, part="mouth_right", x=195.1, y=282.4),
        ],
        ai_perception=AIPerception(
            label="Human Face (Person)",
            feature_map_url=_make_dummy_image_b64(128, 128, color=(100, 150, 220)),
            grad_cam_heatmap=_make_dummy_heatmap_b64(),
        ),
    )


def apply_protection(image_b64: str, algorithm: str, epsilon: float) -> ProtectionResult:
    """
    FGSM 또는 PGD 적대적 노이즈를 적용합니다.

    [A-1 교체]
    - FGSM / PGD 구현으로 보호 이미지 생성
    - 보호 후 얼굴 재탐지 수행
    - noise_only_map 생성
    """
    # TODO(A-1): 실제 알고리즘으로 교체
    protected_b64 = _make_dummy_protected_b64(image_b64)
    return ProtectionResult(
        protected_image_base64=protected_b64,
        noise_only_map=_make_dummy_image_b64(256, 256, color=(240, 240, 240)),
        is_face_detected=False,
        detection_confidence=0.0814,
        landmarks=[],
        ai_perception=AIPerception(
            label="Noise / Texture / Unknown",
            feature_map_url=_make_dummy_image_b64(128, 128, color=(60, 60, 60)),
            grad_cam_heatmap=_make_dummy_heatmap_b64(),
        ),
    )


def build_simulation_metrics(original_b64: str, protected_b64: str) -> SimulationMetrics:
    """
    딥페이크 취약도 점수 및 학습 효율 그래프 데이터를 반환합니다.

    [B-1 교체 가능]
    - 실제 딥페이크 모델 추론 결과로 교체 가능
    """
    # TODO(B-1): 실제 시뮬레이션 데이터로 교체
    return SimulationMetrics(
        deepfake_vulnerability=DeepfakeVulnerability(
            original_score=95.5,
            protected_score=4.2,
            visual_comparison_sample=_make_dummy_image_b64(512, 256, color=(200, 180, 160)),
        ),
        training_efficiency_graph=TrainingEfficiencyGraph(
            epochs=list(range(1, 11)),
            loss_original=[0.85, 0.62, 0.41, 0.22, 0.12, 0.08, 0.05, 0.03, 0.02, 0.01],
            loss_protected=[0.88, 0.87, 0.89, 0.86, 0.91, 0.88, 0.89, 0.90, 0.87, 0.89],
            accuracy_original=[0.45, 0.68, 0.79, 0.88, 0.94, 0.97, 0.98, 0.99, 0.99, 0.99],
            accuracy_protected=[0.12, 0.11, 0.13, 0.10, 0.12, 0.11, 0.14, 0.12, 0.11, 0.13],
        ),
    )
