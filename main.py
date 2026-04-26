import base64
import io
import time
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from schemas import ProtectRequest, ProtectResponse
from services.ai_stub import analyze_face, apply_protection, build_simulation_metrics

app = FastAPI(
    title="PixelGuard API",
    description="Adversarial noise injection to protect images from AI facial recognition and deepfake training.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 보호된 이미지 임시 저장소 (다운로드 엔드포인트용)
_result_store: dict[str, ProtectResponse] = {}

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=FileResponse)
def root():
    return "static/index.html"


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/protect", response_model=ProtectResponse)
def protect_image(body: ProtectRequest):
    """
    이미지를 업로드하면 적대적 노이즈가 주입된 보호 이미지를 반환합니다.
    """
    request_id = body.request_id or f"atm_req_{uuid.uuid4().hex[:12]}"
    image_b64 = body.image_data.original_base64
    algo = body.parameters.protection_algorithm
    epsilon = body.parameters.epsilon

    # base64 포맷 유효성 간단 체크
    if not image_b64.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="image_data.original_base64 must include data URI prefix (data:image/...;base64,...)")

    start = time.perf_counter()

    original_analysis = analyze_face(image_b64)
    protection_result = apply_protection(image_b64, algo, epsilon)
    simulation_metrics = build_simulation_metrics(
        image_b64, protection_result.protected_image_base64
    )

    elapsed = round(time.perf_counter() - start, 3)

    response = ProtectResponse(
        request_id=request_id,
        status="success",
        process_time_sec=elapsed,
        original_analysis=original_analysis,
        protection_result=protection_result,
        simulation_metrics=simulation_metrics,
    )

    _result_store[request_id] = response
    return response


@app.get("/api/download/{request_id}")
def download_protected_image(request_id: str):
    """
    보호 이미지를 파일로 다운로드합니다.
    """
    result = _result_store.get(request_id)
    if result is None:
        raise HTTPException(status_code=404, detail="request_id not found. Call /api/protect first.")

    b64_str = result.protection_result.protected_image_base64
    # "data:image/png;base64,..." 형식에서 순수 base64 추출
    if "," in b64_str:
        header, data = b64_str.split(",", 1)
        mime = header.split(":")[1].split(";")[0]
        ext = mime.split("/")[1]
    else:
        data = b64_str
        mime = "image/png"
        ext = "png"

    image_bytes = base64.b64decode(data)
    filename = f"protected_{request_id}.{ext}"

    return StreamingResponse(
        io.BytesIO(image_bytes),
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
