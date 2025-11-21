"""
Simple Detector - Detector otimizado para Raspberry Pi 4
Versão simplificada focada em performance e baixo consumo
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class SimpleDetector:
    """
    Detector simplificado otimizado para Raspberry Pi
    Usa apenas métodos leves e eficientes
    """

    def __init__(
        self,
        detection_type: str = 'pothole',
        min_confidence: float = 0.5,
        resize_width: int = 640
    ):
        """
        Inicializa o detector

        Args:
            detection_type: Tipo de detecção ('pothole' ou 'grass')
            min_confidence: Confiança mínima para detecção válida
            resize_width: Largura para redimensionar imagem (otimização)
        """
        self.detection_type = detection_type
        self.min_confidence = min_confidence
        self.resize_width = resize_width

        logger.info(
            f"Detector inicializado: {detection_type}, "
            f"min_conf={min_confidence}, resize={resize_width}px"
        )

    def detect(self, image_path: str) -> Tuple[bool, float, Optional[np.ndarray]]:
        """
        Detecta objetos na imagem

        Args:
            image_path: Caminho da imagem

        Returns:
            Tupla (detectado, confiança, imagem_anotada)
        """
        try:
            # Carrega imagem
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Não foi possível carregar imagem: {image_path}")
                return False, 0.0, None

            # Redimensiona para otimização
            original_height, original_width = image.shape[:2]
            if original_width > self.resize_width:
                scale = self.resize_width / original_width
                new_height = int(original_height * scale)
                image = cv2.resize(image, (self.resize_width, new_height))
                logger.debug(f"Imagem redimensionada: {original_width}x{original_height} -> {self.resize_width}x{new_height}")

            # Detecção baseada no tipo
            if self.detection_type == 'pothole':
                detected, confidence, annotated = self._detect_pothole(image)
            elif self.detection_type == 'grass':
                detected, confidence, annotated = self._detect_grass(image)
            else:
                logger.error(f"Tipo de detecção inválido: {self.detection_type}")
                return False, 0.0, None

            # Valida confiança mínima
            if confidence < self.min_confidence:
                detected = False
                logger.debug(f"Confiança abaixo do mínimo: {confidence:.2f} < {self.min_confidence:.2f}")

            logger.info(
                f"Detecção: {'✓' if detected else '✗'} "
                f"Confiança: {confidence:.2f} "
                f"Tipo: {self.detection_type}"
            )

            return detected, confidence, annotated

        except Exception as e:
            logger.error(f"Erro na detecção: {e}")
            return False, 0.0, None

    def _detect_pothole(self, image: np.ndarray) -> Tuple[bool, float, np.ndarray]:
        """
        Detecta buracos usando análise de cor e contorno (método leve)

        Args:
            image: Imagem BGR

        Returns:
            Tupla (detectado, confiança, imagem_anotada)
        """
        # Cria cópia para anotação
        annotated = image.copy()

        # Converte para escala de cinza
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Equalização de histograma para melhorar contraste
        gray = cv2.equalizeHist(gray)

        # Blur para reduzir ruído
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Detecção de bordas (Canny)
        edges = cv2.Canny(blurred, 50, 150)

        # Operações morfológicas para fechar contornos
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Encontra contornos
        contours, _ = cv2.findContours(
            closed,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Filtra contornos por área e forma
        min_area = (image.shape[0] * image.shape[1]) * 0.001  # 0.1% da imagem
        max_area = (image.shape[0] * image.shape[1]) * 0.3    # 30% da imagem

        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area < area < max_area:
                # Verifica circularidade (buracos tendem a ser circulares/elípticos)
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter ** 2)
                    if circularity > 0.3:  # Mínimo de circularidade
                        valid_contours.append((contour, area, circularity))

        # Calcula confiança baseada em número e qualidade dos contornos
        if not valid_contours:
            return False, 0.0, annotated

        # Ordena por área (maiores primeiro)
        valid_contours.sort(key=lambda x: x[1], reverse=True)

        # Desenha contornos na imagem
        for i, (contour, area, circularity) in enumerate(valid_contours[:5]):  # Máximo 5 buracos
            # Calcula bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Desenha retângulo
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 2)

            # Adiciona texto
            label = f"Buraco #{i+1}"
            cv2.putText(
                annotated,
                label,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2
            )

        # Calcula confiança (média ponderada da circularidade)
        total_weight = sum(c[1] for c in valid_contours)
        confidence = sum(c[1] * c[2] for c in valid_contours) / total_weight

        # Normaliza confiança para 0-1
        confidence = min(confidence, 1.0)

        detected = len(valid_contours) > 0

        return detected, confidence, annotated

    def _detect_grass(self, image: np.ndarray) -> Tuple[bool, float, np.ndarray]:
        """
        Detecta mato alto usando análise de cor HSV (método leve)

        Args:
            image: Imagem BGR

        Returns:
            Tupla (detectado, confiança, imagem_anotada)
        """
        # Cria cópia para anotação
        annotated = image.copy()

        # Converte para HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Ranges de verde para mato
        # Verde típico
        lower_green1 = np.array([35, 40, 40])
        upper_green1 = np.array([85, 255, 255])

        # Verde amarelado (mato seco)
        lower_green2 = np.array([20, 30, 30])
        upper_green2 = np.array([40, 200, 200])

        # Cria máscaras
        mask1 = cv2.inRange(hsv, lower_green1, upper_green1)
        mask2 = cv2.inRange(hsv, lower_green2, upper_green2)

        # Combina máscaras
        mask = cv2.bitwise_or(mask1, mask2)

        # Operações morfológicas para limpar ruído
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Calcula percentual de cobertura
        total_pixels = image.shape[0] * image.shape[1]
        grass_pixels = cv2.countNonZero(mask)
        coverage_percentage = (grass_pixels / total_pixels) * 100

        # Encontra contornos para anotação
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Filtra contornos por área
        min_area = total_pixels * 0.005  # 0.5% da imagem

        valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]

        # Desenha contornos
        if valid_contours:
            cv2.drawContours(annotated, valid_contours, -1, (0, 255, 0), 2)

            # Adiciona texto com percentual
            text = f"Mato: {coverage_percentage:.1f}%"
            cv2.putText(
                annotated,
                text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        # Calcula confiança baseada na cobertura e continuidade
        # Cobertura entre 5% e 80% é considerada alta confiança
        if coverage_percentage < 5:
            confidence = coverage_percentage / 5.0
        elif coverage_percentage > 80:
            confidence = 0.5 + (0.5 * (100 - coverage_percentage) / 20.0)
        else:
            confidence = 0.8 + (len(valid_contours) / 100.0)  # Bonus por múltiplos contornos

        confidence = min(confidence, 1.0)

        detected = coverage_percentage >= 5.0  # Mínimo 5% de cobertura

        return detected, confidence, annotated

    def save_annotated_image(
        self,
        annotated: np.ndarray,
        output_path: str,
        quality: int = 85
    ) -> bool:
        """
        Salva imagem anotada

        Args:
            annotated: Imagem anotada
            output_path: Caminho de saída
            quality: Qualidade JPEG (0-100)

        Returns:
            True se salvou com sucesso
        """
        try:
            # Cria diretório se não existe
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Salva com compressão JPEG otimizada
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            success = cv2.imwrite(output_path, annotated, encode_param)

            if success:
                logger.info(f"Imagem salva: {output_path}")
            else:
                logger.error(f"Erro ao salvar imagem: {output_path}")

            return success

        except Exception as e:
            logger.error(f"Erro ao salvar imagem: {e}")
            return False


def quick_detect(
    image_path: str,
    detection_type: str = 'pothole',
    save_output: bool = False,
    output_dir: str = 'output'
) -> Tuple[bool, float]:
    """
    Função helper para detecção rápida

    Args:
        image_path: Caminho da imagem
        detection_type: Tipo de detecção
        save_output: Salvar imagem anotada
        output_dir: Diretório de saída

    Returns:
        Tupla (detectado, confiança)
    """
    detector = SimpleDetector(detection_type=detection_type)
    detected, confidence, annotated = detector.detect(image_path)

    if save_output and annotated is not None:
        output_path = Path(output_dir) / f"annotated_{Path(image_path).name}"
        detector.save_annotated_image(annotated, str(output_path))

    return detected, confidence
