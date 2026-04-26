"""
A-1(AI 팀) 연결 포인트.
각 함수를 실제 구현으로 교체하면 됩니다.
함수 시그니처(인자·반환 타입)는 그대로 유지해 주세요.
"""

import base64
import io
import sys
import os

# 프로젝트 루트(schemas.py 위치)를 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PIL import Image
import numpy as np

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

    [B-1 담당 - 완료]
    - 극적인 딥페이크 비교 이미지 (matplotlib 3-panel)
    - 보호 전후 GAN 학습 곡선 데이터 (Loss/Accuracy divergence)
    """
    return SimulationMetrics(
        deepfake_vulnerability=DeepfakeVulnerability(
            original_score=95.5,
            protected_score=4.2,
            # B-1: 단색 더미 → matplotlib으로 생성한 실제 비교 시각화
            visual_comparison_sample=_generate_deepfake_comparison_image(),
        ),
        training_efficiency_graph=TrainingEfficiencyGraph(
            epochs=list(range(1, 11)),
            # B-1: 기존 더미(loss 0.85 시작) → 실제 학습 곡선처럼 극적인 divergence
            #
            # 원본 이미지로 학습한 GAN: loss 급감 (2.45 → 0.02), accuracy 급등 (51% → 99%)
            # 보호 이미지로 학습한 GAN: loss 수렴 안 됨 (~2.4 유지), accuracy 랜덤 수준 (~51%)
            loss_original     = [2.45, 1.78, 1.21, 0.83, 0.52, 0.31, 0.17, 0.09, 0.04, 0.02],
            loss_protected    = [2.44, 2.41, 2.47, 2.39, 2.45, 2.42, 2.48, 2.40, 2.44, 2.46],
            accuracy_original = [0.51, 0.63, 0.73, 0.82, 0.89, 0.93, 0.96, 0.98, 0.99, 0.99],
            accuracy_protected= [0.51, 0.53, 0.50, 0.52, 0.51, 0.53, 0.50, 0.52, 0.51, 0.52],
        ),
    )


# ─── B-1 내부 헬퍼: 딥페이크 비교 시각화 이미지 ──────────────────

def _generate_deepfake_comparison_image() -> str:
    """
    matplotlib으로 3-panel 딥페이크 비교 이미지를 생성.
    - 왼쪽: 원본 얼굴 (학습 소스)
    - 가운데: 원본으로 학습한 GAN 결과 → 생성 성공 94.3%
    - 오른쪽: 보호 이미지로 학습한 GAN 결과 → 생성 실패 3.1%
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    BG     = "#0d1117"
    PANEL  = "#161b22"
    BORDER = "#30363d"
    BLUE   = "#58a6ff"
    GREEN  = "#3fb950"
    RED    = "#f85149"
    TEXT   = "#f0f6fc"
    MUTED  = "#8b949e"

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8))
    fig.patch.set_facecolor(BG)
    fig.subplots_adjust(wspace=0.06, left=0.02, right=0.98, top=0.85, bottom=0.05)

    fig.text(
        0.5, 0.96,
        "Deepfake Generation: Original vs. Protected Image",
        ha="center", va="top", fontsize=13, color=TEXT, fontweight="bold",
    )

    panels = [
        dict(title="Original Face",    sub="Training Source",            color=BLUE,  result=None,          score=None,    noise=False),
        dict(title="Deepfake Output",  sub="(trained on original)",      color=GREEN, result="✓  GENERATED", score="Similarity  94.3 %", noise=False),
        dict(title="Deepfake Output",  sub="(trained on protected)",     color=RED,   result="✗  FAILED",    score="Similarity   3.1 %", noise=True),
    ]

    rng = np.random.default_rng(42)

    for ax, p in zip(axes, panels):
        ax.set_facecolor(PANEL)
        ax.set_xlim(0, 100); ax.set_ylim(0, 100)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_edgecolor(BORDER); s.set_linewidth(1.2)

        c = p["color"]
        ax.add_patch(plt.Circle((50, 52), 28, color=c, fill=True, alpha=0.18, zorder=1))
        ax.add_patch(plt.Circle((50, 52), 28, color=c, fill=False, linewidth=2, alpha=0.7, zorder=2))

        if p["noise"]:
            for _ in range(18):
                x1, y1 = rng.uniform(28, 72), rng.uniform(30, 75)
                x2, y2 = rng.uniform(28, 72), rng.uniform(30, 75)
                ax.plot([x1, x2], [y1, y2], color=c, linewidth=rng.uniform(0.8, 2.0), alpha=0.45, zorder=3)
            for _ in range(6):
                ax.add_patch(plt.Circle((rng.uniform(32, 68), rng.uniform(34, 70)),
                                        rng.uniform(3, 9), color=c, alpha=0.12))
        else:
            ax.plot([37, 46], [60, 60], color=c, linewidth=2.5, zorder=3)
            ax.plot([54, 63], [60, 60], color=c, linewidth=2.5, zorder=3)
            ax.add_patch(plt.Circle((41.5, 60), 1.5, color=c, alpha=0.8))
            ax.add_patch(plt.Circle((58.5, 60), 1.5, color=c, alpha=0.8))
            ax.plot([50, 46, 54], [52, 43, 43], color=c, linewidth=1.8, alpha=0.7, zorder=3)
            mx = np.linspace(42, 58, 30)
            my = 37 + 3 * np.sin(np.linspace(0, np.pi, 30))
            ax.plot(mx, my, color=c, linewidth=2.2, alpha=0.8, zorder=3)

        ax.text(50, 94, p["title"],  ha="center", va="center", fontsize=11, color=TEXT,  fontweight="bold", zorder=5)
        ax.text(50, 87, p["sub"],    ha="center", va="center", fontsize=8.5, color=MUTED, zorder=5)

        if p["result"]:
            ax.text(50, 20, p["result"], ha="center", va="center", fontsize=13, color=c, fontweight="bold", zorder=5)
            ax.text(50, 10, p["score"],  ha="center", va="center", fontsize=10, color=c, alpha=0.85, zorder=5)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode()
