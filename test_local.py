import base64
import os
from ai_stub import analyze_face, apply_protection, build_simulation_metrics

# ── 유틸리티 ──────────────────────────────────────────────────────────────────

def image_to_b64(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()

def save_b64_image(b64_str: str, output_path: str):
    data = b64_str.split(',', 1)[1] if ',' in b64_str else b64_str
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(data))

# ── 메인 테스트 ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    TEST_IMAGE = "test_face.jpg"

    if not os.path.exists(TEST_IMAGE):
        print(f"[ERROR] '{TEST_IMAGE}' 파일이 없습니다.")
        exit(1)

    print("=" * 55)
    print("  ATM ai_stub.py 로컬 테스트")
    print("=" * 55)

    # ── [1] Base64 변환 ────────────────────────────────────────
    print("\n[1/3] Base64 변환 중...")
    b64_input = image_to_b64(TEST_IMAGE)
    print(f"  완료 (길이: {len(b64_input):,} chars)")

    # ── [2] analyze_face ───────────────────────────────────────
    print("\n[2/3] analyze_face() 실행 중...")
    face_result = analyze_face(b64_input)

    print(f"  얼굴 감지       : {face_result.is_face_detected}")
    print(f"  탐지 신뢰도     : {face_result.detection_confidence:.4f}")
    print(f"  키포인트 수     : {len(face_result.landmarks)}개")
    for lm in face_result.landmarks:
        print(f"    [{lm.id}] {lm.part:<20} x={lm.x:.1f}, y={lm.y:.1f}")
    print(f"  AI 라벨         : {face_result.ai_perception.label}")

    save_b64_image(face_result.ai_perception.feature_map_url,  "out_feature_map.png")
    save_b64_image(face_result.ai_perception.grad_cam_heatmap, "out_grad_cam.png")
    print("  저장: out_feature_map.png / out_grad_cam.png")

    if not face_result.is_face_detected:
        print("\n  [WARN] 얼굴을 찾지 못했습니다. 다른 사진으로 테스트해보세요.")

    # ── [3] apply_protection ───────────────────────────────────
    print("\n[3/3] apply_protection() 실행 중... (epsilon=0.03)")
    prot_result = apply_protection(b64_input, algorithm="FGSM", epsilon=0.03)

    print(f"  방어 후 얼굴 감지  : {prot_result.is_face_detected}")
    print(f"  방어 후 탐지 신뢰도: {prot_result.detection_confidence:.4f}")
    print(f"  방어 후 AI 라벨    : {prot_result.ai_perception.label}")
    print(f"  키포인트 수        : {len(prot_result.landmarks)}개")

    save_b64_image(prot_result.protected_image_base64,         "out_protected.jpg")
    save_b64_image(prot_result.noise_only_map,                 "out_noise_map.png")
    save_b64_image(prot_result.ai_perception.grad_cam_heatmap, "out_grad_cam_protected.png")
    print("  저장: out_protected.jpg / out_noise_map.png / out_grad_cam_protected.png")

    # ── [4] build_simulation_metrics ──────────────────────────
    print("\n[4/4] build_simulation_metrics() 실행 중...")
    metrics = build_simulation_metrics(b64_input, prot_result.protected_image_base64)

    vuln = metrics.deepfake_vulnerability
    graph = metrics.training_efficiency_graph
    print(f"  원본 취약도 점수   : {vuln.original_score:.2f} / 100")
    print(f"  보호 취약도 점수   : {vuln.protected_score:.2f} / 100")
    print(f"  취약도 감소        : {vuln.original_score - vuln.protected_score:.2f} point")
    print(f"  학습 곡선 epoch 수 : {len(graph.epochs)}")
    print(f"  원본 최종 loss     : {graph.loss_original[-1]}")
    print(f"  보호 최종 loss     : {graph.loss_protected[-1]}")
    print(f"  원본 최종 accuracy : {graph.accuracy_original[-1]}")
    print(f"  보호 최종 accuracy : {graph.accuracy_protected[-1]}")

    save_b64_image(vuln.visual_comparison_sample, "out_comparison.jpg")
    print("  저장: out_comparison.jpg (좌: 원본 / 우: 보호)")

    # ── 결과 요약 ──────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  테스트 완료 — 생성된 파일 목록")
    print("=" * 55)
    outputs = [
        ("out_feature_map.png",        "원본 이미지 Feature Map (layer1)"),
        ("out_grad_cam.png",           "원본 이미지 Grad-CAM 히트맵"),
        ("out_protected.jpg",          "노이즈 주입 후 보호 이미지"),
        ("out_noise_map.png",          "노이즈 분포 맵 (PNG, 무손실)"),
        ("out_grad_cam_protected.png", "보호 이미지 Grad-CAM 히트맵"),
        ("out_comparison.jpg",         "원본 vs 보호 비교"),
    ]
    for fname, desc in outputs:
        exists = "OK" if os.path.exists(fname) else "MISSING"
        print(f"  [{exists}] {fname:<30} {desc}")
