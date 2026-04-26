import base64
import io
import os
import threading
import urllib.request
import numpy as np
import torch
import torch.nn as nn
import cv2
import mediapipe as mp
from mediapipe.tasks import python as _mp_python
from mediapipe.tasks.python import vision as _mp_vision
from PIL import Image
from torchvision import models, transforms

from schemas import (
    Landmark, AIPerception, FaceAnalysis,
    ProtectionResult, DeepfakeVulnerability,
    TrainingEfficiencyGraph, SimulationMetrics,
)

# ── 장치 & 모델 ──────────────────────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_weights = models.ResNet50_Weights.IMAGENET1K_V1
model = models.resnet50(weights=_weights).to(device).eval()
IMAGENET_CLASSES: list[str] = _weights.meta["categories"]

# ResNet50 표준 입력 크기 — 이 값 하나만 바꾸면 resize/mask/canvas 전체 반영
INPUT_SIZE: int = 224

# ── 동시 요청 gradient 충돌 방지용 락 ────────────────────────────────────────
# FastAPI 멀티스레드 환경에서 model.zero_grad() 와 backward() 는 전역 model 을
# 동시에 건드리므로, 한 번에 하나의 요청만 gradient 구간을 실행하도록 직렬화
_grad_lock = threading.Lock()

# ── MediaPipe Tasks API : 스레드별 독립 인스턴스 (thread-safe) ───────────────
# solutions API 는 0.10.13+ 에서 제거됨 → Tasks API 사용
_mp_local   = threading.local()
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "face_detector.tflite")
_MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
)

def _get_face_detector():
    if not hasattr(_mp_local, "detector"):
        if not os.path.exists(_MODEL_PATH):
            print("[MediaPipe] face_detector.tflite 다운로드 중...")
            urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        options = _mp_vision.FaceDetectorOptions(
            base_options=_mp_python.BaseOptions(model_asset_path=_MODEL_PATH),
            min_detection_confidence=0.5,
        )
        _mp_local.detector = _mp_vision.FaceDetector.create_from_options(options)
    return _mp_local.detector

def _detect_faces(rgb_np: np.ndarray):
    """numpy RGB 배열 → Tasks API FaceDetector 결과 반환"""
    return _get_face_detector().detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_np))

# ── Base64 유틸리티 ──────────────────────────────────────────────────────────
def _decode_b64(b64_str: str) -> bytes:
    # data URL("data:image/...;base64,XXX")과 순수 base64 문자열 모두 처리
    raw = b64_str.split(',', 1)[1] if ',' in b64_str else b64_str
    return base64.b64decode(raw)

def b64_to_tensor(b64_str: str) -> tuple[torch.Tensor, Image.Image]:
    image = Image.open(io.BytesIO(_decode_b64(b64_str))).convert('RGB')
    tf = transforms.Compose([
        transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
        transforms.ToTensor(),
    ])
    return tf(image).unsqueeze(0).to(device), image

def tensor_to_b64(tensor: torch.Tensor, fmt: str = "JPEG") -> str:
    img = transforms.ToPILImage()(tensor.squeeze().cpu())
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    mime = "jpeg" if fmt == "JPEG" else "png"
    return f"data:image/{mime};base64," + base64.b64encode(buf.getvalue()).decode()

# ── Grad-CAM ─────────────────────────────────────────────────────────────────
class GradCAM:
    """ResNet layer4[-1] 기준 Grad-CAM 히트맵 생성기"""

    def __init__(self, target_layer: nn.Module):
        self.activations: torch.Tensor | None = None
        self.gradients:   torch.Tensor | None = None
        self._fwd = target_layer.register_forward_hook(
            lambda m, i, o: setattr(self, "activations", o.detach())
        )
        self._bwd = target_layer.register_full_backward_hook(
            lambda m, gi, go: setattr(self, "gradients", go[0].detach())
        )

    def generate(self, input_tensor: torch.Tensor, target_class: int) -> torch.Tensor:
        # 호출 전 _grad_lock 을 반드시 획득한 상태여야 함
        model.zero_grad()
        out = model(input_tensor)
        one_hot = torch.zeros_like(out)
        one_hot[0][target_class] = 1.0
        out.backward(gradient=one_hot)

        if self.gradients is None or self.activations is None:
            raise RuntimeError("Grad-CAM: hook 이 gradient/activation 을 캡처하지 못했습니다.")

        weights = self.gradients.mean(dim=[2, 3], keepdim=True)
        cam = torch.relu((weights * self.activations).sum(dim=1, keepdim=True))
        return cam / (cam.max() + 1e-8)

    def remove(self):
        self._fwd.remove()
        self._bwd.remove()

# ── 키포인트 파트 매핑 (MediaPipe 6-keypoint 순서) ───────────────────────────
_KP_PARTS = ["right_eye", "left_eye", "nose_tip", "mouth_center", "right_ear", "left_ear"]

def _extract_landmarks(detection, img_w: int, img_h: int) -> list[Landmark]:
    # Tasks API: detection.keypoints 는 NormalizedKeypoint (x, y 가 0~1 비율)
    return [
        Landmark(
            id=i,
            part=_KP_PARTS[i] if i < len(_KP_PARTS) else f"keypoint_{i}",
            x=round(kp.x * img_w, 2),
            y=round(kp.y * img_h, 2),
        )
        for i, kp in enumerate(detection.keypoints)
    ]

def _detection_confidence(detection) -> float:
    # Tasks API: categories[0].score
    return float(detection.categories[0].score) if detection.categories else 0.0

# ── AI 지각 시각화 (feature map + Grad-CAM) ──────────────────────────────────
def _build_ai_perception(input_tensor: torch.Tensor) -> AIPerception:
    base = input_tensor.detach().clone()

    # 1. 예측 라벨 (gradient 불필요)
    with torch.no_grad():
        pred_class = model(base).argmax(dim=1).item()
    label = IMAGENET_CLASSES[pred_class]

    # 2. Feature map — layer1 채널 평균 활성화 (VIRIDIS 컬러맵, gradient 불필요)
    feat_bucket: list[torch.Tensor] = []
    fwd_hook = model.layer1.register_forward_hook(
        lambda m, i, o: feat_bucket.append(o.detach())
    )
    with torch.no_grad():
        model(base)
    fwd_hook.remove()

    feat = feat_bucket[0].squeeze(0).mean(0).cpu().numpy()
    feat = ((feat - feat.min()) / (feat.max() - feat.min() + 1e-8) * 255).astype(np.uint8)
    feat_img = cv2.applyColorMap(cv2.resize(feat, (INPUT_SIZE, INPUT_SIZE)), cv2.COLORMAP_VIRIDIS)
    _, buf = cv2.imencode(".png", feat_img)
    feature_map_url = "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode()

    # 3. Grad-CAM — layer4[-1], JET 컬러맵 오버레이 (backward 필요 → 락 획득)
    gc = GradCAM(model.layer4[-1])
    try:
        with _grad_lock:
            cam = gc.generate(base.requires_grad_(True), target_class=pred_class)
            model.zero_grad()
    finally:
        gc.remove()  # 예외 발생해도 hook 반드시 제거

    cam_np = (cam.squeeze().detach().cpu().numpy() * 255).astype(np.uint8)
    heatmap = cv2.applyColorMap(cv2.resize(cam_np, (INPUT_SIZE, INPUT_SIZE)), cv2.COLORMAP_JET)
    orig_np = (base.detach().squeeze().permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
    blended = cv2.addWeighted(cv2.cvtColor(orig_np, cv2.COLOR_RGB2BGR), 0.5, heatmap, 0.5, 0)
    _, buf = cv2.imencode(".png", blended)
    grad_cam_heatmap = "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode()

    return AIPerception(label=label, feature_map_url=feature_map_url, grad_cam_heatmap=grad_cam_heatmap)


# ── 공개 API ──────────────────────────────────────────────────────────────────

def analyze_face(image_b64: str) -> FaceAnalysis:
    """얼굴 위치 파악 + AI 지각 시각화 (FaceAnalysis 반환)"""
    nparr = np.frombuffer(_decode_b64(image_b64), np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_h, img_w = img_bgr.shape[:2]

    result      = _detect_faces(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))

    is_detected = bool(result.detections)
    confidence  = _detection_confidence(result.detections[0]) if is_detected else 0.0
    landmarks   = _extract_landmarks(result.detections[0], img_w, img_h) if is_detected else []

    input_tensor, _ = b64_to_tensor(image_b64)
    ai_perception   = _build_ai_perception(input_tensor)

    return FaceAnalysis(
        is_face_detected=is_detected,
        detection_confidence=confidence,
        landmarks=landmarks,
        ai_perception=ai_perception,
    )


def apply_protection(image_b64: str, algorithm: str = "FGSM", epsilon: float = 0.03) -> ProtectionResult:
    """Dynamic Masked FGSM 노이즈 주입 (ProtectionResult 반환)"""
    if algorithm != "FGSM":
        raise NotImplementedError(f"'{algorithm}'은 미구현. 현재는 'FGSM'만 지원.")

    input_tensor, original_pil = b64_to_tensor(image_b64)
    input_tensor.requires_grad = True

    # FGSM backward — 전역 model 상태를 변경하므로 락으로 직렬화
    with _grad_lock:
        model.zero_grad()
        outputs = model(input_tensor)
        target  = outputs.argmax(dim=1).detach()
        nn.CrossEntropyLoss()(outputs, target).backward()

        if input_tensor.grad is None:
            raise RuntimeError("FGSM gradient 계산 실패: input_tensor.grad 가 None 입니다.")
        sign_data_grad = input_tensor.grad.data.sign()

    # 얼굴 탐지 — 원본 해상도 PIL 사용 (INPUT_SIZE 리사이즈 후보다 탐지 정확도 높음)
    orig_w, orig_h = original_pil.size
    orig_rgb = cv2.cvtColor(np.array(original_pil), cv2.COLOR_RGB2BGR)
    orig_rgb = cv2.cvtColor(orig_rgb, cv2.COLOR_BGR2RGB)
    result   = _detect_faces(orig_rgb)

    is_detected = bool(result.detections)
    confidence  = _detection_confidence(result.detections[0]) if is_detected else 0.0
    landmarks   = _extract_landmarks(result.detections[0], orig_w, orig_h) if is_detected else []

    # 얼굴 영역 마스크 — Tasks API bbox 는 픽셀 좌표 → INPUT_SIZE 비율로 변환
    mask = torch.zeros_like(sign_data_grad)
    if result.detections:
        for det in result.detections:
            bbox = det.bounding_box          # origin_x, origin_y, width, height (픽셀)
            x  = int(bbox.origin_x / orig_w * INPUT_SIZE)
            y  = int(bbox.origin_y / orig_h * INPUT_SIZE)
            x2 = min(int((bbox.origin_x + bbox.width)  / orig_w * INPUT_SIZE), INPUT_SIZE)
            y2 = min(int((bbox.origin_y + bbox.height) / orig_h * INPUT_SIZE), INPUT_SIZE)
            mask[:, :, y:y2, x:x2] = 1.0

    # [Plan A] 224×224 기준 노이즈를 원본 해상도로 업스케일 후 고화질 이미지에 적용
    raw_noise_224 = (epsilon * sign_data_grad * mask).detach()  # (1, 3, 224, 224)

    # 노이즈 224×224 → 원본 해상도 (bilinear interpolation으로 부드럽게 확대)
    noise_np      = raw_noise_224.squeeze(0).permute(1, 2, 0).cpu().numpy()       # (224, 224, 3)
    noise_full_np = cv2.resize(noise_np, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)  # (H, W, 3)
    noise_full    = torch.from_numpy(noise_full_np).permute(2, 0, 1).unsqueeze(0) # (1, 3, H, W)

    # 원본 고해상도 PIL → 텐서로 변환 후 노이즈 합산
    orig_tensor_full = transforms.ToTensor()(original_pil).unsqueeze(0)           # (1, 3, H, W)
    perturbed        = torch.clamp(orig_tensor_full + noise_full, 0, 1)

    # noise_map 시각화도 원본 해상도 기준 (×10 증폭으로 육안 확인 가능하게)
    noise_map = noise_full.abs() * 10

    # AI 지각(Grad-CAM) 은 ResNet50 입력 크기인 224×224 기준 perturbed 사용
    perturbed_224 = torch.clamp(input_tensor + raw_noise_224, 0, 1).detach()
    ai_perception = _build_ai_perception(perturbed_224)

    return ProtectionResult(
        protected_image_base64=tensor_to_b64(perturbed, fmt="JPEG"),
        noise_only_map=tensor_to_b64(noise_map, fmt="PNG"),
        is_face_detected=is_detected,
        detection_confidence=confidence,
        landmarks=landmarks,
        ai_perception=ai_perception,
    )


def build_simulation_metrics(original_b64: str, protected_b64: str) -> SimulationMetrics:
    """원본 vs 보호 이미지 기반 취약도 점수 + 학습 곡선 시뮬레이션 (SimulationMetrics 반환)"""
    orig_tensor, orig_pil = b64_to_tensor(original_b64)
    prot_tensor, prot_pil = b64_to_tensor(protected_b64)

    # 취약도 점수: softmax 최대 신뢰도 — 높을수록 모델이 확신 → 딥페이크에 취약
    with torch.no_grad():
        orig_score = torch.softmax(model(orig_tensor), dim=1).max().item() * 100
        prot_score = torch.softmax(model(prot_tensor), dim=1).max().item() * 100

    # 시각 비교 샘플 (좌: 원본, 우: 보호) — INPUT_SIZE 기준으로 캔버스 계산
    canvas = Image.new("RGB", (INPUT_SIZE * 2, INPUT_SIZE))
    canvas.paste(orig_pil.resize((INPUT_SIZE, INPUT_SIZE)), (0, 0))
    canvas.paste(prot_pil.resize((INPUT_SIZE, INPUT_SIZE)), (INPUT_SIZE, 0))
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG")
    visual_sample = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    # 학습 곡선: 실제 perturbation L-inf norm으로 epsilon 역산 → 시뮬레이션 시드
    epsilon_est = float((prot_tensor - orig_tensor).abs().max().item())
    rng = np.random.default_rng(seed=int(epsilon_est * 10000))
    epochs = list(range(1, 11))

    loss_orig = [round(float(0.9 * (0.55 ** e) + rng.normal(0, 0.008)), 4) for e in epochs]
    acc_orig  = [round(float(min(0.99, 1.0 - 0.9 * (0.55 ** e) + rng.normal(0, 0.008))), 4) for e in epochs]
    base_loss = 0.88 + epsilon_est * 3.0
    base_acc  = max(0.05, 0.13 - epsilon_est * 2.0)
    loss_prot = [round(float(base_loss + rng.normal(0, 0.015)), 4) for _ in epochs]
    acc_prot  = [round(float(max(0.04, base_acc + rng.normal(0, 0.008))), 4) for _ in epochs]

    return SimulationMetrics(
        deepfake_vulnerability=DeepfakeVulnerability(
            original_score=round(orig_score, 2),
            protected_score=round(prot_score, 2),
            visual_comparison_sample=visual_sample,
        ),
        training_efficiency_graph=TrainingEfficiencyGraph(
            epochs=epochs,
            loss_original=loss_orig,
            loss_protected=loss_prot,
            accuracy_original=acc_orig,
            accuracy_protected=acc_prot,
        ),
    )
