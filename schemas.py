from pydantic import BaseModel
from typing import Literal, Optional


class ImageData(BaseModel):
    original_base64: str
    format: Literal["jpeg", "png", "webp"] = "jpeg"


class ProtectParameters(BaseModel):
    protection_algorithm: Literal["FGSM", "PGD"] = "FGSM"
    epsilon: float = 0.03
    target_detector: str = "FaceNet_v1"


class ProtectRequest(BaseModel):
    request_id: Optional[str] = None
    image_data: ImageData
    parameters: ProtectParameters = ProtectParameters()


class Landmark(BaseModel):
    id: int
    part: str
    x: float
    y: float


class AIPerception(BaseModel):
    label: str
    feature_map_url: str
    grad_cam_heatmap: str


class FaceAnalysis(BaseModel):
    is_face_detected: bool
    detection_confidence: float
    landmarks: list[Landmark]
    ai_perception: AIPerception


class ProtectionResult(BaseModel):
    protected_image_base64: str
    noise_only_map: str
    is_face_detected: bool
    detection_confidence: float
    landmarks: list[Landmark]
    ai_perception: AIPerception


class DeepfakeVulnerability(BaseModel):
    original_score: float
    protected_score: float
    visual_comparison_sample: str


class TrainingEfficiencyGraph(BaseModel):
    epochs: list[int]
    loss_original: list[float]
    loss_protected: list[float]
    accuracy_original: list[float]
    accuracy_protected: list[float]


class SimulationMetrics(BaseModel):
    deepfake_vulnerability: DeepfakeVulnerability
    training_efficiency_graph: TrainingEfficiencyGraph


class ProtectResponse(BaseModel):
    request_id: str
    status: str
    process_time_sec: float
    original_analysis: FaceAnalysis
    protection_result: ProtectionResult
    simulation_metrics: SimulationMetrics
