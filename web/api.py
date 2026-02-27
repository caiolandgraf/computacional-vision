"""
API REST para o Sistema de Detecção de Mato Alto e Buracos.
Servidor FastAPI que expõe os comandos do sistema de visão computacional
para consumo pelo frontend Vue.js.

Em produção, também serve o frontend Vue.js buildado (pasta dist/).
"""

import asyncio
import base64
import io
import json
import logging
import os
import sys
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles

# Adiciona o diretório src ao path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from capture import ImageCapture
from detector import GrassDetector
from people_detector import PeopleDetector
from pothole_detector import PotholeDetector
from visualizer import ResultVisualizer

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── Diretórios ───────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR = BASE_DIR / "uploads"
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend" / "dist"
OUTPUT_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

# ── Instâncias do sistema de detecção ────────────────────────
capture = ImageCapture()
detector = GrassDetector()
pothole_detector = PotholeDetector()
visualizer = ResultVisualizer()
people_detector_inst = PeopleDetector()

# ── Rastreamento de jobs assíncronos (processamento de vídeo) ─
video_jobs: Dict[str, Dict[str, Any]] = {}
people_video_jobs: Dict[str, Dict[str, Any]] = {}

# ── FastAPI App ──────────────────────────────────────────────
app = FastAPI(
    title="Sistema de Detecção - Visão Computacional",
    description="API REST para detecção de mato alto e buracos em imagens e vídeos.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve os arquivos de output e uploads como estáticos
app.mount("/files/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output_files")
app.mount("/files/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="upload_files")

# ── Serve frontend buildado (SPA) ────────────────────────────
# Os assets estáticos do frontend são montados em /assets
# O catch-all para SPA é registrado no final do arquivo (após todos os endpoints da API)
_frontend_available = FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists()
if _frontend_available:
    # Assets JS/CSS do Vite
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="frontend_assets",
        )
    logger.info(f"Frontend buildado encontrado em {FRONTEND_DIR}")
else:
    logger.warning(
        f"Frontend buildado NÃO encontrado em {FRONTEND_DIR}. "
        "Execute 'cd web/frontend && npm run build' para gerar o frontend."
    )


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════

def _image_to_base64(image: np.ndarray, ext: str = ".jpg") -> str:
    """Codifica imagem OpenCV para base64 string."""
    success, buffer = cv2.imencode(ext, image)
    if not success:
        raise ValueError("Falha ao codificar imagem")
    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def _read_upload(contents: bytes) -> np.ndarray:
    """Converte bytes de upload para imagem OpenCV."""
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Não foi possível decodificar a imagem")
    return image


def _save_upload(contents: bytes, filename: str) -> Path:
    """Salva arquivo de upload no disco e retorna o caminho."""
    safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    path = UPLOAD_DIR / safe_name
    path.write_bytes(contents)
    return path


# ═══════════════════════════════════════════════════════════════
#  Endpoints de Saúde / Info
# ═══════════════════════════════════════════════════════════════

@app.get("/vite.svg", include_in_schema=False)
async def serve_vite_svg():
    """Serve o favicon SVG do Vite (referenciado no index.html)."""
    svg_path = FRONTEND_DIR / "vite.svg"
    if svg_path.exists():
        return FileResponse(str(svg_path), media_type="image/svg+xml")
    raise HTTPException(404, "Arquivo não encontrado")


@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    """Serve o favicon (tenta vite.svg ou retorna 204 no content)."""
    svg_path = FRONTEND_DIR / "vite.svg"
    if svg_path.exists():
        return FileResponse(str(svg_path), media_type="image/svg+xml")
    # Favicon não disponível — retorna 204 para evitar erros 404 repetidos no console
    return JSONResponse(status_code=204, content=None)


@app.get("/")
async def root(request: Request):
    """
    Rota raiz: serve o frontend Vue.js se buildado, senão retorna info da API.
    """
    if _frontend_available:
        return HTMLResponse(content=(FRONTEND_DIR / "index.html").read_text(encoding="utf-8"))
    return {
        "system": "Sistema de Detecção - Visão Computacional",
        "version": "1.0.0",
        "frontend": "não buildado — execute 'cd web/frontend && npm run build'",
        "endpoints": {
            "health": "/health",
            "analyze_image": "POST /api/analyze/image",
            "analyze_pothole": "POST /api/analyze/pothole",
            "compare_methods": "POST /api/analyze/compare",
            "process_video": "POST /api/video/process",
            "video_status": "GET /api/video/status/{job_id}",
            "webcam_ws": "WS /api/ws/webcam",
            "results": "GET /api/results",
            "settings": "GET /api/settings",
        },
    }


@app.get("/health")
async def health_check():
    has_tf = False
    try:
        import tensorflow  # noqa: F401
        has_tf = True
    except ImportError:
        pass

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "detector": True,
            "pothole_detector": True,
            "visualizer": True,
            "tensorflow": has_tf,
        },
        "output_dir": str(OUTPUT_DIR),
    }


# ═══════════════════════════════════════════════════════════════
#  Detecção de Mato Alto em Imagem
# ═══════════════════════════════════════════════════════════════

@app.post("/api/analyze/image")
async def analyze_image(
    file: UploadFile = File(...),
    method: str = Form("combined"),
    visual_mode: str = Form("overlay"),
):
    """
    Analisa uma imagem para detecção de mato alto.

    - **method**: color | texture | combined | deeplearning
    - **visual_mode**: overlay | bounding_box | contour
    """
    if method not in ("color", "texture", "combined", "deeplearning"):
        raise HTTPException(400, f"Método inválido: {method}")

    contents = await file.read()
    try:
        image = _read_upload(contents)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    # Detecção
    mask, stats = detector.detect_grass_areas(image, method)
    density = detector.analyze_grass_density(mask)
    confidence = detector.get_detection_confidence(stats)

    # Visualizações
    overlay_img = visualizer.create_overlay_visualization(image, mask, stats)
    detailed_img = visualizer.create_detailed_analysis_panel(
        image, mask, stats, density, visualization_type=visual_mode
    )

    # Salva resultados
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(file.filename or "upload").stem
    overlay_path = OUTPUT_DIR / f"{stem}_overlay_{ts}.jpg"
    detailed_path = OUTPUT_DIR / f"{stem}_detailed_{ts}.jpg"
    visualizer.save_visualization(overlay_img, str(overlay_path))
    visualizer.save_visualization(detailed_img, str(detailed_path))

    return {
        "success": True,
        "method": method,
        "stats": {
            "coverage_percentage": round(stats.get("coverage_percentage", 0), 2),
            "grass_pixels": int(stats.get("grass_pixels", 0)),
            "total_pixels": int(stats.get("total_pixels", 0)),
            "confidence": round(confidence, 4),
        },
        "density": {
            "classification": density.get("density_classification", "N/A"),
            "num_regions": int(density.get("num_regions", 0)),
            "average_area": round(density.get("average_area", 0), 1),
            "largest_area": round(density.get("largest_area", 0), 1),
        },
        "images": {
            "overlay": _image_to_base64(overlay_img),
            "detailed": _image_to_base64(detailed_img),
        },
        "files": {
            "overlay": f"/files/output/{overlay_path.name}",
            "detailed": f"/files/output/{detailed_path.name}",
        },
    }


# ═══════════════════════════════════════════════════════════════
#  Detecção de Buracos em Imagem
# ═══════════════════════════════════════════════════════════════

@app.post("/api/analyze/pothole")
async def analyze_pothole(
    file: UploadFile = File(...),
    method: str = Form("combined"),
):
    """
    Analisa uma imagem para detecção de buracos.

    - **method**: contour | texture | shadow | combined
    """
    if method not in ("contour", "texture", "shadow", "combined"):
        raise HTTPException(400, f"Método inválido: {method}")

    contents = await file.read()
    try:
        image = _read_upload(contents)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    # Salva temporariamente para o detector de buracos (ele recebe path)
    upload_path = _save_upload(contents, file.filename or "pothole.jpg")

    try:
        result = pothole_detector.detect_image(str(upload_path), method=method)
    except Exception as exc:
        raise HTTPException(500, f"Erro na detecção: {str(exc)}")

    # Visualização
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(file.filename or "upload").stem
    output_path = OUTPUT_DIR / f"pothole_{stem}_{method}_{ts}.jpg"
    pothole_detector.visualize_detections(str(upload_path), result, str(output_path))

    # Lê a imagem de saída para base64
    output_img = cv2.imread(str(output_path))
    output_b64 = _image_to_base64(output_img) if output_img is not None else ""

    potholes_list = []
    for p in result.get("potholes", [])[:20]:
        potholes_list.append({
            "bounding_box": list(p.get("bounding_box", [0, 0, 0, 0])),
            "area": round(p.get("area", 0), 1),
            "confidence_score": round(p.get("confidence_score", 0), 2),
        })

    return {
        "success": True,
        "method": method,
        "stats": {
            "num_potholes": result.get("num_potholes", 0),
            "total_area": round(result.get("total_area", 0), 1),
            "coverage": round(result.get("coverage", 0), 2),
            "confidence": round(result.get("confidence", 0), 2),
            "confidence_level": result.get("confidence_level", "N/A"),
        },
        "potholes": potholes_list,
        "flags": result.get("flags", []),
        "image": output_b64,
        "file": f"/files/output/{output_path.name}",
    }


# ═══════════════════════════════════════════════════════════════
#  Comparação de Métodos
# ═══════════════════════════════════════════════════════════════

@app.post("/api/analyze/compare")
async def compare_methods(
    file: UploadFile = File(...),
    detection_type: str = Form("grass"),
):
    """
    Compara todos os métodos de detecção em uma imagem.

    - **detection_type**: grass | pothole
    """
    contents = await file.read()

    if detection_type == "grass":
        try:
            image = _read_upload(contents)
        except ValueError as exc:
            raise HTTPException(400, str(exc))

        methods = ["color", "texture", "combined"]
        results_list = []

        for m in methods:
            mask, stats = detector.detect_grass_areas(image, m)
            confidence = detector.get_detection_confidence(stats)
            results_list.append({
                "method": m,
                "coverage_percentage": round(stats.get("coverage_percentage", 0), 2),
                "confidence": round(confidence, 4),
            })

        # Comparação visual
        compare_data = []
        for m in methods:
            mask, stats = detector.detect_grass_areas(image, m)
            compare_data.append((mask, m, stats))

        comparison_img = visualizer.create_side_by_side_comparison(image, compare_data)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        comp_path = OUTPUT_DIR / f"comparison_grass_{ts}.jpg"
        visualizer.save_visualization(comparison_img, str(comp_path))

        return {
            "success": True,
            "detection_type": "grass",
            "results": results_list,
            "comparison_image": _image_to_base64(comparison_img),
            "file": f"/files/output/{comp_path.name}",
        }

    elif detection_type == "pothole":
        upload_path = _save_upload(contents, "compare_pothole.jpg")
        methods = ["contour", "texture", "shadow", "combined"]
        results_list = []

        for m in methods:
            try:
                result = pothole_detector.detect_image(str(upload_path), method=m)
                results_list.append({
                    "method": m,
                    "num_potholes": result.get("num_potholes", 0),
                    "total_area": round(result.get("total_area", 0), 1),
                    "confidence": round(result.get("confidence", 0), 2),
                    "confidence_level": result.get("confidence_level", "N/A"),
                })
            except Exception:
                results_list.append({
                    "method": m,
                    "error": True,
                })

        return {
            "success": True,
            "detection_type": "pothole",
            "results": results_list,
        }

    raise HTTPException(400, f"Tipo de detecção inválido: {detection_type}")


# ═══════════════════════════════════════════════════════════════
#  Análise em Lote
# ═══════════════════════════════════════════════════════════════

@app.post("/api/analyze/batch")
async def analyze_batch(
    files: List[UploadFile] = File(...),
    method: str = Form("combined"),
    detection_type: str = Form("grass"),
):
    """Processa múltiplas imagens de uma vez."""
    results = []
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, f in enumerate(files):
        contents = await f.read()
        try:
            image = _read_upload(contents)
        except ValueError:
            results.append({"filename": f.filename, "error": "Formato inválido"})
            continue

        if detection_type == "grass":
            mask, stats = detector.detect_grass_areas(image, method)
            density = detector.analyze_grass_density(mask)
            confidence = detector.get_detection_confidence(stats)

            viz = visualizer.create_detailed_analysis_panel(
                image, mask, stats, density, visualization_type="bounding_box"
            )
            stem = Path(f.filename or f"img_{i}").stem
            out_path = OUTPUT_DIR / f"batch_{ts}_{stem}.jpg"
            visualizer.save_visualization(viz, str(out_path))

            results.append({
                "filename": f.filename,
                "coverage": round(stats.get("coverage_percentage", 0), 2),
                "confidence": round(confidence, 4),
                "density": density.get("density_classification", "N/A"),
                "regions": int(density.get("num_regions", 0)),
                "image": _image_to_base64(viz),
                "file": f"/files/output/{out_path.name}",
            })
        else:
            upload_path = _save_upload(contents, f.filename or f"pothole_{i}.jpg")
            try:
                result = pothole_detector.detect_image(str(upload_path), method=method)
                results.append({
                    "filename": f.filename,
                    "num_potholes": result.get("num_potholes", 0),
                    "coverage": round(result.get("coverage", 0), 2),
                    "confidence": round(result.get("confidence", 0), 2),
                })
            except Exception as exc:
                results.append({"filename": f.filename, "error": str(exc)})

    # Estatísticas gerais (para grass)
    valid = [r for r in results if "error" not in r]
    summary: Dict[str, Any] = {"total": len(files), "processed": len(valid)}
    if valid and detection_type == "grass":
        coverages = [r["coverage"] for r in valid]
        summary["avg_coverage"] = round(sum(coverages) / len(coverages), 2)
        summary["max_coverage"] = max(coverages)
        summary["min_coverage"] = min(coverages)

    return {"success": True, "summary": summary, "results": results}


# ═══════════════════════════════════════════════════════════════
#  Processamento de Vídeo (assíncrono com polling)
# ═══════════════════════════════════════════════════════════════

def _process_video_worker(job_id: str, video_path: str, method: str, visual_mode: str, quality: str):
    """Função que roda em thread separada para processar vídeo."""
    job = video_jobs[job_id]

    try:
        # Configurações de qualidade
        if quality == "2":
            detector.set_precision_mode(True)
        else:
            detector.set_realtime_mode(True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            job["status"] = "error"
            job["error"] = "Não foi possível abrir o vídeo"
            return

        fps_in = cap.get(cv2.CAP_PROP_FPS) or 30
        w_in = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h_in = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        job["total_frames"] = total
        job["fps"] = fps_in
        job["resolution"] = f"{w_in}x{h_in}"
        job["duration"] = round(total / fps_in, 1) if fps_in > 0 else 0

        # Dimensões de saída
        if visual_mode == "3":
            panel_w = int(w_in * 0.3)
            out_w, out_h = w_in + panel_w, h_in
        else:
            out_w, out_h = w_in, h_in

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        vname = Path(video_path).stem
        out_filename = f"{vname}_overlay_{method}_{ts}.mp4"
        out_path = OUTPUT_DIR / out_filename

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, fps_in, (out_w, out_h))

        job["output_file"] = out_filename
        job["status"] = "processing"

        frame_count = 0
        total_coverage = 0.0
        max_cov = 0.0
        min_cov = 100.0
        t_start = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            mask, stats = detector.detect_grass_areas(frame, method)
            cov = stats.get("coverage_percentage", 0)
            total_coverage += cov
            max_cov = max(max_cov, cov)
            min_cov = min(min_cov, cov)

            elapsed = time.time() - t_start
            proc_fps = frame_count / elapsed if elapsed > 0 else 0

            # Visualização
            if visual_mode == "2":
                viz = visualizer.create_overlay_visualization(frame, mask, stats)
            elif visual_mode == "3":
                density = detector.analyze_grass_density(mask)
                viz = visualizer.create_detailed_analysis_panel(
                    frame, mask, stats, density, visualization_type="bounding_box"
                )
            else:
                # Overlay leve (modo 1 / padrão)
                viz = _create_video_overlay_static(
                    frame, mask, stats, proc_fps, frame_count, total
                )

            vh, vw = viz.shape[:2]
            if vw != out_w or vh != out_h:
                viz = cv2.resize(viz, (out_w, out_h))

            writer.write(viz)

            # Atualiza progresso a cada 5 frames
            if frame_count % 5 == 0 or frame_count == total:
                progress = (frame_count / total * 100) if total > 0 else 0
                eta = ((total - frame_count) / proc_fps) if proc_fps > 0 else 0
                job.update({
                    "current_frame": frame_count,
                    "progress": round(progress, 1),
                    "current_coverage": round(cov, 2),
                    "processing_fps": round(proc_fps, 1),
                    "eta_seconds": round(eta, 1),
                })

        cap.release()
        writer.release()

        avg_cov = total_coverage / frame_count if frame_count > 0 else 0
        job.update({
            "status": "completed",
            "current_frame": frame_count,
            "progress": 100.0,
            "avg_coverage": round(avg_cov, 2),
            "max_coverage": round(max_cov, 2),
            "min_coverage": round(min_cov, 2),
            "processing_fps": round(proc_fps, 1),
            "output_url": f"/files/output/{out_filename}",
            "completed_at": datetime.now().isoformat(),
        })

    except Exception as exc:
        logger.error(f"Erro processando vídeo job {job_id}: {exc}", exc_info=True)
        job["status"] = "error"
        job["error"] = str(exc)


def _create_video_overlay_static(
    frame: np.ndarray,
    mask: np.ndarray,
    stats: dict,
    fps: float,
    current_frame: int,
    total_frames: int,
) -> np.ndarray:
    """Versão estática (fora da classe) do overlay de vídeo."""
    result = frame.copy()
    height, width = result.shape[:2]

    green_overlay = result.copy()
    green_overlay[mask > 0] = [0, 200, 80]
    cv2.addWeighted(green_overlay, 0.35, result, 0.65, 0, result)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    significant = [c for c in contours if cv2.contourArea(c) > 300]
    cv2.drawContours(result, significant, -1, (0, 255, 100), 2)

    for cnt in significant:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 100), 2)

        corner = min(15, w // 4, h // 4)
        for dx, dy, sx, sy in [
            (0, 0, 1, 1), (w, 0, -1, 1), (0, h, 1, -1), (w, h, -1, -1)
        ]:
            cv2.line(result, (x + dx, y + dy), (x + dx + corner * sx, y + dy), (50, 255, 50), 3)
            cv2.line(result, (x + dx, y + dy), (x + dx, y + dy + corner * sy), (50, 255, 50), 3)

        area_m2 = cv2.contourArea(cnt) * 0.0001
        if area_m2 >= 0.01:
            label = f"{area_m2:.2f}m2"
            sz = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(result, (x, y - sz[1] - 8), (x + sz[0] + 6, y), (30, 30, 30), -1)
            cv2.putText(result, label, (x + 3, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 100), 1, cv2.LINE_AA)

    coverage = stats.get("coverage_percentage", 0)

    # Barra topo
    cv2.rectangle(result, (0, 0), (width, 50), (30, 30, 30), -1)
    cv2.rectangle(result, (0, 0), (width, 3), (0, 255, 100), -1)
    method_label = stats.get("method", "combined").upper()
    txt = f"DETECCAO MATO | {method_label} | Cobertura: {coverage:.1f}% | Regioes: {len(significant)}"
    cv2.putText(result, txt, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

    # Barra de progresso
    prog = current_frame / total_frames if total_frames > 0 else 0
    bw = int(width * prog)
    cv2.rectangle(result, (0, 46), (bw, 50), (0, 255, 100), -1)
    cv2.rectangle(result, (bw, 46), (width, 50), (60, 60, 60), -1)

    # Painel inferior
    bpy = height - 45
    cv2.rectangle(result, (0, bpy), (width, height), (30, 30, 30), -1)
    cv2.rectangle(result, (0, bpy), (width, bpy + 3), (0, 255, 100), -1)

    ptxt = f"Frame: {current_frame}/{total_frames} ({prog * 100:.1f}%)"
    cv2.putText(result, ptxt, (10, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    ftxt = f"FPS: {fps:.1f}"
    fsz = cv2.getTextSize(ftxt, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)[0]
    cv2.putText(result, ftxt, (width // 2 - fsz[0] // 2, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 100), 1, cv2.LINE_AA)

    cov_color = (0, 0, 255) if coverage > 50 else (0, 165, 255) if coverage > 25 else (0, 255, 100)
    ctxt = f"Cobertura: {coverage:.1f}%"
    csz = cv2.getTextSize(ctxt, cv2.FONT_HERSHEY_DUPLEX, 0.6, 2)[0]
    cv2.putText(result, ctxt, (width - csz[0] - 15, height - 15), cv2.FONT_HERSHEY_DUPLEX, 0.6, cov_color, 2, cv2.LINE_AA)

    return result


@app.post("/api/video/process")
async def process_video(
    file: UploadFile = File(...),
    method: str = Form("combined"),
    visual_mode: str = Form("1"),
    quality: str = Form("1"),
):
    """
    Inicia processamento assíncrono de vídeo com overlay.
    Retorna um job_id para acompanhar o progresso via polling.
    """
    if method not in ("color", "texture", "combined", "deeplearning"):
        raise HTTPException(400, f"Método inválido: {method}")
    if visual_mode not in ("1", "2", "3"):
        raise HTTPException(400, f"Modo visual inválido: {visual_mode}")

    contents = await file.read()
    upload_path = _save_upload(contents, file.filename or "video.mp4")

    job_id = uuid.uuid4().hex[:12]
    video_jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "filename": file.filename,
        "method": method,
        "visual_mode": visual_mode,
        "quality": quality,
        "created_at": datetime.now().isoformat(),
        "current_frame": 0,
        "total_frames": 0,
        "progress": 0.0,
    }

    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None, _process_video_worker, job_id, str(upload_path), method, visual_mode, quality
    )

    return {"success": True, "job_id": job_id, "status": "queued"}


@app.get("/api/video/status/{job_id}")
async def video_status(job_id: str):
    """Retorna o status atual de um job de processamento de vídeo."""
    if job_id not in video_jobs:
        raise HTTPException(404, "Job não encontrado")
    return video_jobs[job_id]


@app.get("/api/video/jobs")
async def list_video_jobs():
    """Lista todos os jobs de processamento de vídeo."""
    return {"jobs": list(video_jobs.values())}


# ═══════════════════════════════════════════════════════════════
#  WebSocket para Webcam em Tempo Real
# ═══════════════════════════════════════════════════════════════

@app.websocket("/api/ws/webcam")
async def websocket_webcam(ws: WebSocket):
    """
    WebSocket para análise de frames da webcam em tempo real.
    O cliente envia frames em base64 e recebe frames processados.

    Configurações dinâmicas (via mensagem type=config):
      - method: color | texture | combined | deeplearning
      - visual_mode: fast | overlay | bounding_box | contour
      - quality_mode: "1" (tempo real) | "2" (alta precisão)
    """
    await ws.accept()
    logger.info("WebSocket webcam conectado")

    method = "combined"
    visual_mode = "fast"       # padrão leve para webcam
    quality_mode = "1"         # 1=realtime, 2=precision

    # FPS tracking
    _ws_frame_count = 0
    _ws_fps = 0.0
    _ws_fps_timer = time.time()

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            # ── Configuração dinâmica ────────────────────────
            if msg.get("type") == "config":
                method = msg.get("method", method)
                visual_mode = msg.get("visual_mode", visual_mode)
                quality_mode = msg.get("quality_mode", quality_mode)

                # Aplica modo de qualidade no detector
                if quality_mode == "2":
                    detector.set_precision_mode(True)
                else:
                    detector.set_realtime_mode(True)

                logger.info(
                    f"WS config atualizado: method={method}, "
                    f"visual_mode={visual_mode}, quality_mode={quality_mode}"
                )
                await ws.send_json({
                    "type": "config_ack",
                    "method": method,
                    "visual_mode": visual_mode,
                    "quality_mode": quality_mode,
                })
                continue

            # ── Frame de imagem em base64 ────────────────────
            if msg.get("type") == "frame":
                frame_b64 = msg.get("data", "")
                if not frame_b64:
                    continue

                # Decodifica
                img_bytes = base64.b64decode(frame_b64)
                nparr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is None:
                    continue

                # Calcula FPS
                _ws_frame_count += 1
                now = time.time()
                elapsed = now - _ws_fps_timer
                if elapsed >= 1.0:
                    _ws_fps = _ws_frame_count / elapsed
                    _ws_frame_count = 0
                    _ws_fps_timer = now

                # Processa detecção
                t0 = time.time()
                mask, stats = detector.detect_grass_areas(frame, method)
                proc_time = time.time() - t0

                coverage = stats.get("coverage_percentage", 0)
                contours, _ = cv2.findContours(
                    mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                regions = len([c for c in contours if cv2.contourArea(c) > 300])

                # ── Gera visualização conforme visual_mode ───
                is_realtime = quality_mode != "2"

                if visual_mode == "fast":
                    # Overlay leve (portado de main.py _create_fast_overlay)
                    viz = visualizer.create_fast_overlay(
                        frame, mask, stats,
                        fps=_ws_fps,
                        realtime_mode=is_realtime,
                    )

                elif visual_mode == "bounding_box":
                    if is_realtime:
                        viz = visualizer.create_bounding_box_visualization(
                            frame, mask, stats
                        )
                    else:
                        density = detector.analyze_grass_density(mask)
                        viz = visualizer.create_detailed_analysis_panel(
                            frame, mask, stats, density,
                            visualization_type="bounding_box",
                        )

                elif visual_mode == "contour":
                    viz = visualizer.create_contour_visualization(
                        frame, mask, stats
                    )

                else:
                    # "overlay" — estilo clássico melhorado (padrão)
                    viz = visualizer.create_overlay_visualization(
                        frame, mask, stats
                    )

                result_b64 = _image_to_base64(viz)

                await ws.send_json({
                    "type": "result",
                    "image": result_b64,
                    "stats": {
                        "coverage": round(coverage, 2),
                        "regions": regions,
                        "processing_time_ms": round(proc_time * 1000, 1),
                        "method": method,
                        "visual_mode": visual_mode,
                        "quality_mode": quality_mode,
                        "fps": round(_ws_fps, 1),
                    },
                })

    except WebSocketDisconnect:
        logger.info("WebSocket webcam desconectado")
    except Exception as exc:
        logger.error(f"Erro WebSocket: {exc}", exc_info=True)


# ═══════════════════════════════════════════════════════════════
#  Resultados / Galeria
# ═══════════════════════════════════════════════════════════════

@app.get("/api/results")
async def list_results(limit: int = 50):
    """Lista os resultados gerados na pasta de output."""
    files = sorted(OUTPUT_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    results = []
    for p in files[:limit]:
        if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".mp4", ".avi"):
            stat = p.stat()
            results.append({
                "name": p.name,
                "type": "image" if p.suffix.lower() in (".jpg", ".jpeg", ".png") else "video",
                "size_kb": round(stat.st_size / 1024, 1),
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "url": f"/files/output/{p.name}",
            })
    return {"results": results, "total": len(results)}


@app.delete("/api/results/{filename}")
async def delete_result(filename: str):
    """Deleta um resultado."""
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Arquivo não encontrado")
    path.unlink()
    return {"success": True, "deleted": filename}


# ═══════════════════════════════════════════════════════════════
#  Configurações
# ═══════════════════════════════════════════════════════════════

@app.get("/api/settings")
async def get_settings():
    """Retorna as configurações atuais do detector."""
    return {
        "grass_color_ranges": {
            k: v.tolist() if isinstance(v, np.ndarray) else v
            for k, v in detector.grass_color_ranges.items()
        },
        "texture_params": detector.texture_params,
        "confidence_params": detector.confidence_params,
        "realtime_params": detector.realtime_params,
        "precision_params": detector.precision_params,
    }


@app.put("/api/settings")
async def update_settings(settings: Dict[str, Any]):
    """Atualiza parâmetros do detector."""
    if "texture_params" in settings:
        for k, v in settings["texture_params"].items():
            if k in detector.texture_params:
                detector.texture_params[k] = v

    if "confidence_params" in settings:
        for k, v in settings["confidence_params"].items():
            if k in detector.confidence_params:
                detector.confidence_params[k] = v

    if "realtime_mode" in settings:
        if settings["realtime_mode"]:
            detector.set_realtime_mode(True)
        else:
            detector.set_precision_mode(True)

    return {"success": True, "settings": await get_settings()}


# ═══════════════════════════════════════════════════════════════
#  Download de resultado
# ═══════════════════════════════════════════════════════════════

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Faz download de um arquivo de resultado."""
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Arquivo não encontrado")
    return FileResponse(
        path=str(path),
        filename=filename,
        media_type="application/octet-stream",
    )


# ═══════════════════════════════════════════════════════════════
#  Detecção de Pessoas
# ═══════════════════════════════════════════════════════════════

@app.post("/api/people/analyze")
async def analyze_people_image(
    file: UploadFile = File(...),
    blur_faces: bool = Form(False),
):
    """
    Detecta e conta pessoas em uma imagem.
    Parâmetros:
      - file       : imagem (JPEG, PNG, etc.)
      - blur_faces : se true, aplica desfoque nos rostos detectados
    """
    contents = await file.read()
    try:
        frame = _read_upload(contents)
    except ValueError as e:
        raise HTTPException(400, str(e))

    people_detector_inst.set_precision_mode()

    processed, result = people_detector_inst.detect(
        frame, blur_faces=blur_faces, draw_overlay=True
    )

    result_b64 = _image_to_base64(processed)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = Path(file.filename or "image.jpg").suffix or ".jpg"
    out_name = f"people_{ts}{ext}"
    out_path = OUTPUT_DIR / out_name
    cv2.imwrite(str(out_path), processed)

    return {
        "success": True,
        "image": result_b64,
        "output_file": out_name,
        "output_url": f"/files/output/{out_name}",
        "stats": PeopleDetector.result_to_dict(result),
    }


def _process_people_video_worker(job_id: str, video_path: str, blur_faces: bool):
    """Função que roda em thread separada para processar vídeo de pessoas."""
    job = people_video_jobs[job_id]

    try:
        people_detector_inst.set_precision_mode()

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            job["status"] = "error"
            job["error"] = "Não foi possível abrir o vídeo"
            return

        fps_in  = cap.get(cv2.CAP_PROP_FPS) or 30
        w_in    = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h_in    = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total   = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        job["total_frames"] = total
        job["fps"]          = fps_in
        job["resolution"]   = f"{w_in}x{h_in}"
        job["duration"]     = round(total / fps_in, 1) if fps_in > 0 else 0

        ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
        vname     = Path(video_path).stem
        blur_tag  = "_blur" if blur_faces else ""
        out_filename = f"people_{vname}{blur_tag}_{ts}.mp4"
        out_path  = OUTPUT_DIR / out_filename

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, fps_in, (w_in, h_in))

        job["output_file"] = out_filename
        job["status"]      = "processing"

        frame_count   = 0
        total_people  = 0
        max_people    = 0
        t_start       = time.time()
        _fps_counter  = 0
        _fps_timer    = time.time()
        _proc_fps     = 0.0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count  += 1
            _fps_counter += 1

            now_t = time.time()
            if now_t - _fps_timer >= 1.0:
                _proc_fps    = _fps_counter / (now_t - _fps_timer)
                _fps_counter = 0
                _fps_timer   = now_t

            processed, result = people_detector_inst.detect(
                frame,
                blur_faces=blur_faces,
                draw_overlay=True,
                fps=_proc_fps if _proc_fps > 0 else None,
            )

            count         = result.person_count
            total_people += count
            max_people    = max(max_people, count)

            vh, vw = processed.shape[:2]
            if vw != w_in or vh != h_in:
                processed = cv2.resize(processed, (w_in, h_in))

            writer.write(processed)

            if frame_count % 5 == 0 or frame_count == total:
                elapsed      = time.time() - t_start
                proc_fps_avg = frame_count / elapsed if elapsed > 0 else 0
                progress     = (frame_count / total * 100) if total > 0 else 0
                eta          = ((total - frame_count) / proc_fps_avg) if proc_fps_avg > 0 else 0
                job.update({
                    "current_frame":  frame_count,
                    "progress":       round(progress, 1),
                    "current_people": count,
                    "processing_fps": round(proc_fps_avg, 1),
                    "eta_seconds":    round(eta, 1),
                })

        cap.release()
        writer.release()

        elapsed_total  = time.time() - t_start
        proc_fps_final = frame_count / elapsed_total if elapsed_total > 0 else 0
        avg_people     = total_people / frame_count if frame_count > 0 else 0

        job.update({
            "status":         "completed",
            "current_frame":  frame_count,
            "progress":       100.0,
            "avg_people":     round(avg_people, 2),
            "max_people":     max_people,
            "processing_fps": round(proc_fps_final, 1),
            "output_url":     f"/files/output/{out_filename}",
            "completed_at":   datetime.now().isoformat(),
        })

    except Exception as exc:
        logger.error(f"Erro processando vídeo people job {job_id}: {exc}", exc_info=True)
        job["status"] = "error"
        job["error"]  = str(exc)


@app.post("/api/people/video/process")
async def process_people_video(
    file: UploadFile = File(...),
    blur_faces: bool = Form(False),
):
    """
    Inicia processamento assíncrono de vídeo para detecção de pessoas.
    Retorna job_id para acompanhar via polling.
    """
    contents    = await file.read()
    upload_path = _save_upload(contents, file.filename or "video.mp4")

    job_id = uuid.uuid4().hex[:12]
    people_video_jobs[job_id] = {
        "id":             job_id,
        "status":         "queued",
        "filename":       file.filename,
        "blur_faces":     blur_faces,
        "created_at":     datetime.now().isoformat(),
        "current_frame":  0,
        "total_frames":   0,
        "progress":       0.0,
        "current_people": 0,
        "avg_people":     0,
        "max_people":     0,
    }

    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None, _process_people_video_worker, job_id, str(upload_path), blur_faces
    )

    return {"success": True, "job_id": job_id, "status": "queued"}


@app.get("/api/people/video/status/{job_id}")
async def people_video_status(job_id: str):
    """Retorna o status atual de um job de detecção de pessoas em vídeo."""
    if job_id not in people_video_jobs:
        raise HTTPException(404, "Job não encontrado")
    return people_video_jobs[job_id]


@app.get("/api/people/video/jobs")
async def list_people_video_jobs():
    """Lista todos os jobs de detecção de pessoas em vídeo."""
    return {"jobs": list(people_video_jobs.values())}


@app.websocket("/api/ws/people-webcam")
async def websocket_people_webcam(ws: WebSocket):
    """
    WebSocket para detecção de pessoas em tempo real via webcam.

    Configurações dinâmicas (via mensagem type=config):
      - blur_faces : bool — se true, desfoca os rostos
      - quality    : "1" (tempo real) | "2" (alta precisão)

    Otimizações de FPS:
      - Detecção executada via run_in_executor (não bloqueia o event loop)
      - Frames recebidos enquanto a GPU/CPU está ocupada são descartados
        (skip-if-busy), evitando fila crescente e latência acumulada
      - FPS calculado como round-trip real (frames enviados de volta / seg)
    """
    await ws.accept()
    logger.info("WebSocket people-webcam conectado")

    blur_faces  = False
    quality     = "1"
    _processing = False          # flag skip-if-busy

    # FPS de envio (frames recebidos do cliente)
    _recv_count   = 0
    _recv_fps     = 0.0
    _recv_timer   = time.time()

    # FPS de resultado (frames processados e enviados de volta)
    _result_count = 0
    _result_fps   = 0.0
    _result_timer = time.time()

    loop = asyncio.get_running_loop()

    try:
        while True:
            data = await ws.receive_text()
            msg  = json.loads(data)

            # ── Configuração dinâmica ────────────────────────
            if msg.get("type") == "config":
                blur_faces = bool(msg.get("blur_faces", blur_faces))
                quality    = msg.get("quality", quality)

                if quality == "2":
                    people_detector_inst.set_precision_mode()
                else:
                    people_detector_inst.set_realtime_mode()

                logger.info(
                    f"WS people config: blur_faces={blur_faces}, quality={quality}"
                )
                await ws.send_json({
                    "type":       "config_ack",
                    "blur_faces": blur_faces,
                    "quality":    quality,
                })
                continue

            # ── Frame de imagem em base64 ────────────────────
            if msg.get("type") != "frame":
                continue

            frame_b64 = msg.get("data", "")
            if not frame_b64:
                continue

            # Atualiza FPS de recebimento
            _recv_count += 1
            now_t = time.time()
            if now_t - _recv_timer >= 1.0:
                _recv_fps    = _recv_count / (now_t - _recv_timer)
                _recv_count  = 0
                _recv_timer  = now_t

            # Skip-if-busy: descarta frame se a inferência anterior ainda não terminou
            if _processing:
                continue

            # Decodifica fora do executor (rápido, não vale spawnar thread)
            img_bytes = base64.b64decode(frame_b64)
            nparr     = np.frombuffer(img_bytes, np.uint8)
            frame     = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            # Captura valores locais para a closure (evita race condition)
            _blur   = blur_faces
            _fps_in = _recv_fps if _recv_fps > 0 else None
            _frame  = frame     # já é uma cópia do decode

            _processing = True
            t0 = time.time()

            try:
                # Roda a inferência (CPU-bound) em thread pool → não bloqueia o loop
                processed, result = await loop.run_in_executor(
                    None,
                    lambda: people_detector_inst.detect(
                        _frame,
                        blur_faces=_blur,
                        draw_overlay=True,
                        fps=_fps_in,
                    ),
                )
            finally:
                _processing = False

            proc_time = time.time() - t0

            # Atualiza FPS de resultado
            _result_count += 1
            now_t = time.time()
            if now_t - _result_timer >= 1.0:
                _result_fps   = _result_count / (now_t - _result_timer)
                _result_count = 0
                _result_timer = now_t

            result_b64 = _image_to_base64(processed)

            await ws.send_json({
                "type":  "result",
                "image": result_b64,
                "stats": {
                    "person_count":       result.person_count,
                    "face_count":         result.face_count,
                    "body_count":         result.body_count,
                    "blur_applied":       result.blur_applied,
                    "processing_time_ms": round(proc_time * 1000, 1),
                    "fps":                round(_result_fps, 1),
                    "recv_fps":           round(_recv_fps, 1),
                    "quality":            quality,
                    "method":             result.method,
                },
            })

    except WebSocketDisconnect:
        logger.info("WebSocket people-webcam desconectado")
    except Exception as exc:
        logger.error(f"Erro WebSocket people-webcam: {exc}", exc_info=True)


# ═══════════════════════════════════════════════════════════════
#  SPA Catch-All (deve ser o ÚLTIMO endpoint registrado)
# ═══════════════════════════════════════════════════════════════

@app.get("/{full_path:path}")
async def spa_catch_all(request: Request, full_path: str):
    """
    Catch-all para suportar Vue Router com createWebHistory().
    Qualquer rota que não seja /api/*, /files/*, /health ou /assets/*
    devolve o index.html do frontend para que o Vue Router resolva no cliente.
    """
    # Não intercepta rotas de API, arquivos estáticos ou health
    if full_path.startswith(("api/", "files/", "health", "assets/", "docs", "openapi.json", "redoc")):
        raise HTTPException(404, "Recurso não encontrado")

    # Tenta servir arquivo estático do dist/ (para arquivos raiz como robots.txt, etc.)
    if _frontend_available and "." in full_path.split("/")[-1]:
        static_path = FRONTEND_DIR / full_path
        if static_path.exists() and static_path.is_file():
            return FileResponse(str(static_path))

    # SPA fallback: retorna index.html para que o Vue Router resolva a rota
    if _frontend_available:
        return HTMLResponse(
            content=(FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        )

    raise HTTPException(
        404,
        detail=(
            f"Rota '/{full_path}' não encontrada. "
            "Frontend não está buildado. Execute: cd web/frontend && npm run build"
        ),
    )


# ═══════════════════════════════════════════════════════════════
#  Eventos de Startup
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Log de inicialização com informações do sistema."""
    logger.info("=" * 60)
    logger.info("  Sistema de Detecção - Visão Computacional v1.0.0")
    logger.info("=" * 60)
    logger.info(f"  Output dir:   {OUTPUT_DIR}")
    logger.info(f"  Upload dir:   {UPLOAD_DIR}")
    logger.info(f"  Frontend dir: {FRONTEND_DIR}")
    logger.info(f"  Frontend:     {'✓ disponível' if _frontend_available else '✗ não buildado'}")
    logger.info("")
    if _frontend_available:
        logger.info("  → Acesse http://localhost:8000 para usar o sistema completo")
    else:
        logger.info("  → Frontend não encontrado. Para buildar:")
        logger.info("    cd web/frontend && npm install && npm run build")
        logger.info("  → Ou use em modo dev: cd web/frontend && npm run dev")
        logger.info("    (frontend em :3000, API em :8000)")
    logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    print("🌿 Iniciando servidor API - Sistema de Detecção")
    print(f"📁 Output: {OUTPUT_DIR}")
    print(f"📁 Uploads: {UPLOAD_DIR}")
    print("🌐 Acesse: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
