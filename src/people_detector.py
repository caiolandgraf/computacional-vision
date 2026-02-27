"""
Módulo de Detecção de Pessoas v2 — otimizado para 30+ FPS.

Hierarquia de detectores (melhor → pior):
  Pessoa : YOLOv8-nano (ultralytics)  → HOG + SVM
  Rosto  : YuNet (OpenCV DNN)         → Haar Cascade frontal

Melhorias v2 vs v1:
  - YOLO nano: +60 % precisão, 2-4× mais rápido que HOG no mesmo hardware
  - YuNet: detecção de rosto multi-ângulo, robusto a oclusão (~5 ms/frame)
  - Thread-safe via threading.Lock (seguro para run_in_executor)
  - Warm-up automático na inicialização (sem spike no 1.º frame)
  - Download automático de modelos faltantes
"""

import logging
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ── Diretórios ─────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# ── Ultralytics / YOLO ─────────────────────────────────────────────────────────
try:
    from ultralytics import YOLO as _UltralyticsYOLO  # type: ignore[import]
    _HAVE_YOLO = True
except ImportError:
    _HAVE_YOLO = False
    logger.warning(
        "ultralytics não encontrado – usando HOG como fallback para pessoas.\n"
        "  Para ativar YOLO: pip install ultralytics"
    )

# ── Seleciona o melhor dispositivo disponível ──────────────────────────────────
def _best_device() -> str:
    """Retorna 'mps', 'cuda' ou 'cpu' dependendo do hardware disponível."""
    try:
        import torch
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"

_DEVICE = _best_device()
logger.info(f"Dispositivo de inferência YOLO: {_DEVICE}")

# ── YuNet (detector de rosto DNN) ──────────────────────────────────────────────
_YUNET_FILENAME = "face_detection_yunet_2023mar.onnx"
_YUNET_PATH     = MODELS_DIR / _YUNET_FILENAME
_YUNET_URL      = (
    "https://github.com/opencv/opencv_zoo/raw/main/"
    f"models/face_detection_yunet/{_YUNET_FILENAME}"
)

# ── Haar Cascade (fallback de rosto) ──────────────────────────────────────────
_CV2_DATA = Path(cv2.__file__).parent / "data"
_FACE_CASCADE_PATHS = [
    str(_CV2_DATA / "haarcascade_frontalface_default.xml"),
    str(_CV2_DATA / "haarcascade_frontalface_alt2.xml"),
    str(_CV2_DATA / "haarcascade_frontalface_alt.xml"),
]


# ── Estruturas de dados ────────────────────────────────────────────────────────

@dataclass
class DetectionBox:
    """Bounding box de uma detecção."""
    x: int
    y: int
    w: int
    h: int
    confidence: float = 1.0
    label: str = "person"


@dataclass
class PeopleDetectionResult:
    """Resultado completo de detecção de pessoas."""
    person_count: int = 0
    face_count:   int = 0
    body_count:   int = 0
    faces:  List[DetectionBox] = field(default_factory=list)
    bodies: List[DetectionBox] = field(default_factory=list)
    processing_time_ms: float = 0.0
    method:       str  = "yolo+yunet"
    blur_applied: bool = False
    image_width:  int  = 0
    image_height: int  = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  Detector principal
# ═══════════════════════════════════════════════════════════════════════════════

class PeopleDetector:
    """
    Detecta e conta pessoas em imagens.

    Usa YOLOv8-nano para corpos e YuNet para rostos quando disponíveis.
    Recua automaticamente para HOG + Haar Cascade em ambientes sem GPU ou
    sem as dependências opcionais instaladas.

    Thread-safe: pode ser chamado concorrentemente via run_in_executor.
    """

    def __init__(self):
        self._lock = threading.Lock()

        # Configurações (ajustáveis por set_*_mode)
        self.blur_strength:   int   = 51      # kernel Gaussian (ímpar)
        self.blur_faces_only: bool  = True    # True → blur só rostos
        self.min_person_area: int   = 1500    # px² mínimos para detecção válida
        self.yolo_conf:       float = 0.40    # threshold de confiança YOLO
        self.face_conf:       float = 0.55    # threshold de confiança YuNet
        self.realtime_mode:   bool  = True

        # Handles dos detectores
        self._yolo:         Optional[object]                = None
        self._face_net:     Optional[cv2.FaceDetectorYN]    = None  # type: ignore[type-arg]
        self._face_cascade: Optional[cv2.CascadeClassifier] = None
        self._hog:          Optional[cv2.HOGDescriptor]     = None

        self._person_method = "hog"   # atualizado após init
        self._face_method   = "haar"  # atualizado após init

        self._init_person_detector()
        self._init_face_detector()

    # ══════════════════════════════════════════════════════════════════════════
    #  Inicialização
    # ══════════════════════════════════════════════════════════════════════════

    def _init_person_detector(self) -> None:
        if _HAVE_YOLO:
            try:
                yolo_path = str(MODELS_DIR / "yolov8n.pt")
                logger.info(f"Carregando YOLOv8 nano (device={_DEVICE})…")
                self._yolo = _UltralyticsYOLO(yolo_path)
                # Warm-up: compila grafos e aloca memória antes do primeiro frame real
                dummy = np.zeros((320, 320, 3), dtype=np.uint8)
                for _ in range(2):   # 2 passes eliminam spikes de JIT
                    self._yolo.predict(  # type: ignore[union-attr]
                        dummy,
                        classes=[0],
                        verbose=False,
                        imgsz=320,
                        device=_DEVICE,
                    )
                self._person_method = "yolo"
                logger.info(f"YOLOv8 nano carregado e aquecido ✓ (device={_DEVICE})")
                return
            except Exception as exc:
                logger.warning(f"Falha ao carregar YOLO: {exc} → usando HOG")
                self._yolo = None

        # HOG fallback
        self._hog = cv2.HOGDescriptor()
        self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())  # type: ignore[attr-defined]
        self._person_method = "hog"
        logger.info("HOG+SVM inicializado como fallback de pessoas.")

    def _init_face_detector(self) -> None:
        # Tenta baixar YuNet se ainda não existe localmente
        if not _YUNET_PATH.exists():
            try:
                logger.info(f"Baixando YuNet: {_YUNET_URL}")
                urllib.request.urlretrieve(_YUNET_URL, str(_YUNET_PATH))
                logger.info("YuNet baixado ✓")
            except Exception as exc:
                logger.warning(f"Falha ao baixar YuNet: {exc} → usando Haar Cascade")

        if _YUNET_PATH.exists():
            try:
                self._face_net = cv2.FaceDetectorYN.create(  # type: ignore[attr-defined]
                    str(_YUNET_PATH),
                    "",
                    (320, 320),
                    score_threshold=self.face_conf,
                    nms_threshold=0.30,
                    top_k=200,
                )
                self._face_method = "yunet"
                logger.info("YuNet carregado ✓")
                return
            except Exception as exc:
                logger.warning(f"Falha ao carregar YuNet: {exc} → usando Haar Cascade")
                self._face_net = None

        # Haar Cascade fallback
        for p in _FACE_CASCADE_PATHS:
            if Path(p).exists():
                clf = cv2.CascadeClassifier(p)
                if not clf.empty():
                    self._face_cascade = clf
                    self._face_method = "haar"
                    logger.info(f"Haar Cascade carregado como fallback: {p}")
                    return
        logger.warning("Nenhum detector de rosto disponível.")

    # ── Modo de operação ───────────────────────────────────────────────────────

    def set_realtime_mode(self) -> None:
        """Parâmetros otimizados para latência baixa (webcam)."""
        self.realtime_mode = True
        self.yolo_conf     = 0.40
        self.face_conf     = 0.55
        if self._face_net is not None:
            self._face_net.setScoreThreshold(self.face_conf)

    def set_precision_mode(self) -> None:
        """Parâmetros otimizados para máxima precisão (imagem/vídeo)."""
        self.realtime_mode = False
        self.yolo_conf     = 0.30
        self.face_conf     = 0.45
        if self._face_net is not None:
            self._face_net.setScoreThreshold(self.face_conf)

    @property
    def active_method(self) -> str:
        return f"{self._person_method}+{self._face_method}"

    # ══════════════════════════════════════════════════════════════════════════
    #  Detecção de pessoas (corpo)
    # ══════════════════════════════════════════════════════════════════════════

    def _detect_persons_yolo(self, frame: np.ndarray) -> List[DetectionBox]:
        """Detecção de pessoas com YOLOv8 nano."""
        h, w = frame.shape[:2]

        # 320 px no modo tempo real = ~2× mais rápido que 640, qualidade suficiente
        infer_size = 320 if self.realtime_mode else 640
        scale = min(infer_size / max(h, w), 1.0)
        proc = (
            cv2.resize(frame, (int(w * scale), int(h * scale)),
                       interpolation=cv2.INTER_LINEAR)
            if scale < 1.0 else frame
        )

        results = self._yolo.predict(  # type: ignore[union-attr]
            proc,
            classes=[0],           # classe 0 = "person" no COCO
            conf=self.yolo_conf,
            iou=0.45,
            verbose=False,
            imgsz=infer_size,
            device=_DEVICE,
            augment=False,         # desativa TTA (test-time augmentation)
            half=(_DEVICE != "cpu"),  # FP16 em GPU/MPS acelera ~2×
        )

        boxes: List[DetectionBox] = []
        for r in results:
            if r.boxes is None or len(r.boxes) == 0:
                continue
            for i in range(len(r.boxes)):
                x1, y1, x2, y2 = [float(v) for v in r.boxes.xyxy[i].tolist()]
                conf = float(r.boxes.conf[i])
                if scale < 1.0:
                    x1 /= scale; y1 /= scale
                    x2 /= scale; y2 /= scale
                bw = int(x2 - x1)
                bh = int(y2 - y1)
                if bw * bh < self.min_person_area:
                    continue
                boxes.append(DetectionBox(
                    x=max(0, int(x1)), y=max(0, int(y1)),
                    w=bw, h=bh,
                    confidence=round(conf, 3),
                    label="person",
                ))
        return boxes

    def _detect_persons_hog(self, frame: np.ndarray) -> List[DetectionBox]:
        """Detecção de pessoas com HOG + SVM (fallback)."""
        h, w = frame.shape[:2]
        max_dim = 480 if self.realtime_mode else 640
        scale   = min(max_dim / max(h, w), 1.0)
        small   = (
            cv2.resize(frame, (int(w * scale), int(h * scale)))
            if scale < 1.0 else frame
        )

        gray     = cv2.equalizeHist(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY))
        small_eq = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        win_stride = (16, 16) if self.realtime_mode else (8, 8)
        padding    = (8, 8)   if self.realtime_mode else (4, 4)
        hog_scale  = 1.10     if self.realtime_mode else 1.05

        try:
            rects, weights = self._hog.detectMultiScale(  # type: ignore[union-attr,call-overload]
                small_eq, winStride=win_stride, padding=padding, scale=hog_scale
            )
        except cv2.error:
            return []

        if len(rects) == 0:
            return []

        boxes: List[DetectionBox] = []
        for i, (bx, by, bw, bh) in enumerate(rects):
            rx = int(bx / scale); ry = int(by / scale)
            rw = int(bw / scale); rh = int(bh / scale)
            if rw * rh < self.min_person_area:
                continue
            w_val = float(weights[i]) if i < len(weights) else 1.0
            boxes.append(DetectionBox(x=rx, y=ry, w=rw, h=rh,
                                      confidence=round(w_val, 3), label="body"))
        return self._nms(boxes, 0.45)

    # ══════════════════════════════════════════════════════════════════════════
    #  Detecção de rostos
    # ══════════════════════════════════════════════════════════════════════════

    def _detect_faces_yunet(self, frame: np.ndarray) -> List[DetectionBox]:
        """Detecção de rostos com YuNet (OpenCV DNN)."""
        h, w = frame.shape[:2]
        self._face_net.setInputSize((w, h))  # type: ignore[union-attr]
        _, faces = self._face_net.detect(frame)  # type: ignore[union-attr]

        if faces is None:
            return []

        boxes: List[DetectionBox] = []
        for face in faces:
            fx, fy, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
            conf = float(face[14])
            fx = max(0, fx);  fy = max(0, fy)
            fw = min(fw, w - fx); fh = min(fh, h - fy)
            if fw > 10 and fh > 10:
                boxes.append(DetectionBox(
                    x=fx, y=fy, w=fw, h=fh,
                    confidence=round(conf, 3), label="face",
                ))
        return boxes

    def _detect_faces_cascade(self, frame: np.ndarray) -> List[DetectionBox]:
        """Detecção de rostos com Haar Cascade (fallback)."""
        if self._face_cascade is None or self._face_cascade.empty():
            return []

        gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        h, w = frame.shape[:2]
        min_face = max(20, min(h, w) // 12)

        dets = self._face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.15 if self.realtime_mode else 1.10,
            minNeighbors=4   if self.realtime_mode else 3,
            minSize=(min_face, min_face),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )
        if not len(dets):
            return []

        boxes = [
            DetectionBox(x=int(x), y=int(y), w=int(w_), h=int(h_), label="face")
            for x, y, w_, h_ in dets
        ]
        return self._nms(boxes, 0.40)

    # ══════════════════════════════════════════════════════════════════════════
    #  NMS
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _nms(boxes: List[DetectionBox], iou_thresh: float = 0.45) -> List[DetectionBox]:
        """Non-Maximum Suppression simples ordenado por confiança."""
        if not boxes:
            return []
        kept: List[DetectionBox] = []
        for cand in sorted(boxes, key=lambda b: b.confidence, reverse=True):
            cx1, cy1 = cand.x, cand.y
            cx2, cy2 = cand.x + cand.w, cand.y + cand.h
            ca = cand.w * cand.h
            discard = False
            for k in kept:
                ix = max(0, min(cx2, k.x + k.w) - max(cx1, k.x))
                iy = max(0, min(cy2, k.y + k.h) - max(cy1, k.y))
                inter = ix * iy
                if inter / max(ca + k.w * k.h - inter, 1) > iou_thresh:
                    discard = True
                    break
            if not discard:
                kept.append(cand)
        return kept

    # ══════════════════════════════════════════════════════════════════════════
    #  Contagem inteligente  (evita dupla contagem corpo + rosto da mesma pessoa)
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _estimate_count(bodies: List[DetectionBox], faces: List[DetectionBox]) -> int:
        if not bodies and not faces:
            return 0
        if not bodies:
            return len(faces)
        if not faces:
            return len(bodies)

        matched = 0
        for face in faces:
            fcx = face.x + face.w // 2
            fcy = face.y + face.h // 2
            for body in bodies:
                mx = body.w * 0.25
                my = body.h * 0.25
                if (body.x - mx <= fcx <= body.x + body.w + mx and
                        body.y - my <= fcy <= body.y + body.h + my):
                    matched += 1
                    break
        return len(bodies) + (len(faces) - matched)

    # ══════════════════════════════════════════════════════════════════════════
    #  Blur
    # ══════════════════════════════════════════════════════════════════════════

    def _apply_blur(
        self,
        image: np.ndarray,
        faces: List[DetectionBox],
        bodies: List[DetectionBox],
    ) -> np.ndarray:
        result   = image.copy()
        h_img, w_img = result.shape[:2]
        k = max(1, self.blur_strength | 1)   # garante ímpar
        targets  = faces if self.blur_faces_only else (faces + bodies)

        for box in targets:
            x1 = max(0, box.x);         y1 = max(0, box.y)
            x2 = min(w_img, box.x + box.w); y2 = min(h_img, box.y + box.h)
            if x2 <= x1 or y2 <= y1:
                continue
            roi    = result[y1:y2, x1:x2]
            rh, rw = roi.shape[:2]
            ps     = max(4, min(rw, rh) // 8)
            sm     = cv2.resize(roi, (max(1, rw // ps), max(1, rh // ps)),
                                interpolation=cv2.INTER_LINEAR)
            pix    = cv2.resize(sm, (rw, rh), interpolation=cv2.INTER_NEAREST)
            result[y1:y2, x1:x2] = cv2.GaussianBlur(pix, (k, k), 0)
        return result

    # ══════════════════════════════════════════════════════════════════════════
    #  Visualização (HUD + bounding boxes)
    # ══════════════════════════════════════════════════════════════════════════

    def _draw_detections(
        self,
        image:        np.ndarray,
        faces:        List[DetectionBox],
        bodies:       List[DetectionBox],
        person_count: int,
        fps:          Optional[float],
        blur_applied: bool,
        method_label: str,
    ) -> np.ndarray:
        result = image.copy()
        h, w   = result.shape[:2]

        C_BODY   = (0, 200, 255)   # laranja-ciano → corpo
        C_FACE   = (80, 255, 80)   # verde          → rosto
        C_ACCENT = (0, 200, 255)
        C_WHITE  = (255, 255, 255)
        C_DARK   = (15, 15, 15)

        # ── Desenha corpos ─────────────────────────────────────────────────────
        for body in bodies:
            x1, y1 = body.x, body.y
            x2, y2 = x1 + body.w, y1 + body.h
            cv2.rectangle(result, (x1, y1), (x2, y2), C_BODY, 2)

            cn = min(14, body.w // 5, body.h // 5)
            for dx, dy, sx, sy in [
                (0, 0, 1, 1), (body.w, 0, -1, 1),
                (0, body.h, 1, -1), (body.w, body.h, -1, -1),
            ]:
                cv2.line(result, (x1+dx, y1+dy), (x1+dx+cn*sx, y1+dy), C_BODY, 3)
                cv2.line(result, (x1+dx, y1+dy), (x1+dx, y1+dy+cn*sy), C_BODY, 3)

            conf_txt = f"{body.confidence:.0%}"
            (tw, th), _ = cv2.getTextSize(conf_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
            cv2.rectangle(result, (x1, y1 - th - 7), (x1 + tw + 6, y1), C_BODY, -1)
            cv2.putText(result, conf_txt, (x1 + 3, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, C_DARK, 1, cv2.LINE_AA)

        # ── Desenha rostos ─────────────────────────────────────────────────────
        for face in faces:
            x1, y1 = face.x, face.y
            x2, y2 = x1 + face.w, y1 + face.h

            if blur_applied:
                # Indicador sutil sobre região desfocada
                cv2.rectangle(result, (x1-2, y1-2), (x2+2, y2+2), (90, 90, 90), 1)
                cx_ = (x1 + x2) // 2
                cy_ = (y1 + y2) // 2
                cv2.ellipse(result, (cx_, cy_),
                            (face.w // 4, face.h // 6), 0, 0, 360, (130, 130, 130), 2)
                cv2.line(result,
                         (cx_ - face.w // 4, cy_ - face.h // 6),
                         (cx_ + face.w // 4, cy_ + face.h // 6),
                         (130, 130, 130), 2)
            else:
                cv2.rectangle(result, (x1, y1), (x2, y2), C_FACE, 2)
                cn = min(9, face.w // 4, face.h // 4)
                for dx, dy, sx, sy in [
                    (0, 0, 1, 1), (face.w, 0, -1, 1),
                    (0, face.h, 1, -1), (face.w, face.h, -1, -1),
                ]:
                    cv2.line(result, (x1+dx, y1+dy), (x1+dx+cn*sx, y1+dy), C_FACE, 2)
                    cv2.line(result, (x1+dx, y1+dy), (x1+dx, y1+dy+cn*sy), C_FACE, 2)

                conf_txt = f"{face.confidence:.0%}"
                (tw, th), _ = cv2.getTextSize(conf_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.40, 1)
                cv2.rectangle(result, (x1, y2), (x1 + tw + 6, y2 + th + 6), C_FACE, -1)
                cv2.putText(result, conf_txt, (x1 + 3, y2 + th + 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.40, C_DARK, 1, cv2.LINE_AA)

        # ── HUD superior ──────────────────────────────────────────────────────
        hud_h = 50
        ovl   = result.copy()
        cv2.rectangle(ovl, (0, 0), (w, hud_h), C_DARK, -1)
        cv2.addWeighted(ovl, 0.72, result, 0.28, 0, result)
        cv2.rectangle(result, (0, 0), (w, 3), C_ACCENT, -1)

        cv2.putText(result, f"PESSOAS: {person_count}", (12, 28),
                    cv2.FONT_HERSHEY_DUPLEX, 0.72, C_WHITE, 1, cv2.LINE_AA)

        parts: List[str] = [
            f"rostos:{len(faces)}",
            f"corpos:{len(bodies)}",
            f"[{method_label}]",
        ]
        if fps is not None:
            parts.append(f"{fps:.0f} fps")
        if blur_applied:
            parts.append("[BLUR]")
        cv2.putText(result, "  ".join(parts), (12, 44),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, C_ACCENT, 1, cv2.LINE_AA)

        # Contador grande (canto superior direito)
        count_str = str(person_count)
        (cw, _ch), _ = cv2.getTextSize(count_str, cv2.FONT_HERSHEY_DUPLEX, 1.5, 3)
        cv2.putText(result, count_str, (w - cw - 14, hud_h - 8),
                    cv2.FONT_HERSHEY_DUPLEX, 1.5, C_ACCENT, 3, cv2.LINE_AA)

        return result

    # ══════════════════════════════════════════════════════════════════════════
    #  API pública principal
    # ══════════════════════════════════════════════════════════════════════════

    def detect(
        self,
        frame:        np.ndarray,
        blur_faces:   bool           = False,
        draw_overlay: bool           = True,
        fps:          Optional[float] = None,
    ) -> Tuple[np.ndarray, "PeopleDetectionResult"]:
        """
        Detecta pessoas num frame BGR.

        Args:
            frame        : imagem OpenCV (BGR)
            blur_faces   : se True, desfoca os rostos detectados
            draw_overlay : se True, desenha bounding boxes e HUD
            fps          : FPS atual para exibir no HUD (opcional)

        Returns:
            (processed_image, PeopleDetectionResult)

        Thread-safe: adquire lock interno antes de usar os modelos.
        """
        t0  = time.perf_counter()
        img = frame.copy()

        with self._lock:
            # ── Detecção de pessoas ────────────────────────────────────────────
            if self._yolo is not None:
                bodies = self._detect_persons_yolo(img)
            elif self._hog is not None:
                bodies = self._detect_persons_hog(img)
            else:
                bodies = []

            # ── Detecção de rostos ─────────────────────────────────────────────
            if self._face_net is not None:
                faces = self._detect_faces_yunet(img)
            elif self._face_cascade is not None:
                faces = self._detect_faces_cascade(img)
            else:
                faces = []

        # ── Contagem ──────────────────────────────────────────────────────────
        person_count = self._estimate_count(bodies, faces)
        face_count   = len(faces)
        body_count   = len(bodies)

        # ── Blur ──────────────────────────────────────────────────────────────
        if blur_faces and (faces or (not self.blur_faces_only and bodies)):
            img = self._apply_blur(img, faces, bodies)

        # ── Overlay visual ────────────────────────────────────────────────────
        if draw_overlay:
            img = self._draw_detections(
                img, faces, bodies, person_count,
                fps=fps,
                blur_applied=blur_faces,
                method_label=self.active_method,
            )

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        result = PeopleDetectionResult(
            person_count=person_count,
            face_count=face_count,
            body_count=body_count,
            faces=faces,
            bodies=bodies,
            processing_time_ms=round(elapsed_ms, 2),
            method=self.active_method,
            blur_applied=blur_faces,
            image_width=frame.shape[1],
            image_height=frame.shape[0],
        )
        return img, result

    # ── Serialização para API ──────────────────────────────────────────────────

    @staticmethod
    def result_to_dict(result: "PeopleDetectionResult") -> Dict:
        """Converte PeopleDetectionResult em dicionário JSON-serializável."""
        return {
            "person_count":       result.person_count,
            "face_count":         result.face_count,
            "body_count":         result.body_count,
            "blur_applied":       result.blur_applied,
            "processing_time_ms": result.processing_time_ms,
            "method":             result.method,
            "image_width":        result.image_width,
            "image_height":       result.image_height,
            "faces": [
                {"x": f.x, "y": f.y, "w": f.w, "h": f.h,
                 "confidence": round(f.confidence, 3), "label": f.label}
                for f in result.faces
            ],
            "bodies": [
                {"x": b.x, "y": b.y, "w": b.w, "h": b.h,
                 "confidence": round(b.confidence, 3), "label": b.label}
                for b in result.bodies
            ],
        }
