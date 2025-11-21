"""
Detector de buracos (potholes) usando visão computacional.
Utiliza múltiplas técnicas: análise de contornos, textura, profundidade e CNN.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict, Optional
import logging
from scipy import ndimage
from skimage.feature import local_binary_pattern
from skimage.morphology import disk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PotholeDetector:
    """Detector de buracos em asfalto usando múltiplas técnicas."""

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o detector de buracos.

        Args:
            config: Configurações personalizadas (opcional)
        """
        self.config = config or {}

        # Parâmetros para detecção por contorno
        self.contour_params = {
            'canny_low': 50,
            'canny_high': 150,
            'min_area': 500,  # Área mínima em pixels
            'max_area': 50000,  # Área máxima em pixels
            'min_circularity': 0.3,  # Buracos tendem a ser circulares
            'max_circularity': 0.9,
            'min_convexity': 0.4,  # Buracos são relativamente convexos
            'aspect_ratio_range': (0.3, 3.0),  # Proporção largura/altura
        }

        # Parâmetros para análise de textura
        self.texture_params = {
            'lbp_radius': 3,
            'lbp_points': 24,
            'variance_threshold': 50,  # Buracos têm textura irregular
            'darkness_threshold': 80,  # Buracos são mais escuros
        }

        # Parâmetros para análise de sombras e profundidade
        self.depth_params = {
            'shadow_threshold': 60,  # Buracos criam sombras
            'gradient_threshold': 30,
            'morphology_kernel_size': 5,
        }

        # Parâmetros de confiabilidade
        self.confidence_params = {
            'min_confidence': 0.5,
            'consensus_threshold': 0.6,
        }

        # Atualizar com config personalizada
        if self.config:
            for key, value in self.config.items():
                if hasattr(self, f'{key}_params'):
                    getattr(self, f'{key}_params').update(value)

        logger.info("✅ PotholeDetector inicializado")

    def detect_image(self, image_path: str, method: str = 'combined') -> Dict:
        """
        Detecta buracos em uma imagem.

        Args:
            image_path: Caminho da imagem
            method: Método a usar ('contour', 'texture', 'shadow', 'combined')

        Returns:
            Dict com resultados da detecção
        """
        # Carregar imagem
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Não foi possível carregar imagem: {image_path}")

        logger.info(f"🔍 Analisando buracos com método: {method}")

        # Executar detecção baseada no método
        if method == 'contour':
            mask, potholes = self._detect_by_contour(image)
        elif method == 'texture':
            mask, potholes = self._detect_by_texture(image)
        elif method == 'shadow':
            mask, potholes = self._detect_by_shadow(image)
        elif method == 'combined':
            mask, potholes = self._detect_combined(image)
        else:
            raise ValueError(f"Método desconhecido: {method}")

        # Calcular métricas
        num_potholes = len(potholes)
        total_area = sum([p['area'] for p in potholes])
        coverage = (np.sum(mask > 0) / mask.size) * 100

        # Calcular confiabilidade
        confidence_info = self._calculate_confidence(
            image, mask, potholes, method
        )

        result = {
            'method': method,
            'num_potholes': num_potholes,
            'potholes': potholes,
            'total_area': total_area,
            'coverage': coverage,
            'mask': mask,
            'confidence': confidence_info['confidence'],
            'confidence_level': confidence_info['confidence_level'],
            'flags': confidence_info['flags'],
            'image_path': image_path
        }

        logger.info(f"✅ Detectados {num_potholes} buracos")
        logger.info(f"📊 Área total: {total_area:.0f} pixels")
        logger.info(f"📊 Cobertura: {coverage:.2f}%")
        logger.info(f"🎯 Confiança: {confidence_info['confidence']:.2f} ({confidence_info['confidence_level']})")

        return result

    def _detect_by_contour(self, image: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """
        Detecta buracos usando análise de contornos e características geométricas.
        """
        logger.info("🔍 Método: Análise de Contornos")

        # Converter para escala de cinza
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Pré-processamento
        # 1. Equalização de histograma para melhorar contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # 2. Blur gaussiano para reduzir ruído
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 3. Detecção de bordas com Canny
        edges = cv2.Canny(
            blurred,
            self.contour_params['canny_low'],
            self.contour_params['canny_high']
        )

        # 4. Operações morfológicas para fechar contornos
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        # Encontrar contornos
        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Filtrar contornos que parecem buracos
        potholes = []
        mask = np.zeros(gray.shape, dtype=np.uint8)

        for contour in contours:
            pothole_info = self._analyze_contour(contour, gray)

            if pothole_info['is_pothole']:
                potholes.append(pothole_info)
                cv2.drawContours(mask, [contour], -1, 255, -1)

        return mask, potholes

    def _analyze_contour(self, contour: np.ndarray, gray: np.ndarray) -> Dict:
        """
        Analisa se um contorno representa um buraco.
        """
        # Calcular propriedades geométricas
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        # Evitar divisão por zero
        if perimeter == 0:
            return {'is_pothole': False}

        # Circularidade (1.0 = círculo perfeito)
        circularity = 4 * np.pi * area / (perimeter ** 2)

        # Bounding box e aspect ratio
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h if h > 0 else 0

        # Convexidade
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        convexity = area / hull_area if hull_area > 0 else 0

        # Calcular darkness (buracos são geralmente mais escuros)
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)
        mean_intensity = cv2.mean(gray, mask=mask)[0]

        # Critérios para ser considerado um buraco
        is_valid_area = (self.contour_params['min_area'] < area <
                        self.contour_params['max_area'])
        is_valid_circularity = (self.contour_params['min_circularity'] < circularity <
                               self.contour_params['max_circularity'])
        is_valid_convexity = convexity > self.contour_params['min_convexity']
        is_valid_aspect = (self.contour_params['aspect_ratio_range'][0] < aspect_ratio <
                          self.contour_params['aspect_ratio_range'][1])
        is_dark = mean_intensity < 100  # Buracos tendem a ser escuros

        is_pothole = (is_valid_area and is_valid_circularity and
                     is_valid_convexity and is_valid_aspect)

        return {
            'is_pothole': is_pothole,
            'contour': contour,
            'area': area,
            'perimeter': perimeter,
            'circularity': circularity,
            'convexity': convexity,
            'aspect_ratio': aspect_ratio,
            'bounding_box': (x, y, w, h),
            'center': (x + w//2, y + h//2),
            'mean_intensity': mean_intensity,
            'confidence_score': self._calculate_contour_confidence(
                circularity, convexity, aspect_ratio, mean_intensity
            )
        }

    def _calculate_contour_confidence(self, circularity: float, convexity: float,
                                     aspect_ratio: float, intensity: float) -> float:
        """
        Calcula confiança baseada nas características do contorno.
        """
        # Score de circularidade (buracos tendem a ser circulares)
        circ_score = min(circularity / 0.8, 1.0)

        # Score de convexidade
        conv_score = convexity

        # Score de aspect ratio (mais próximo de 1.0 = mais quadrado/circular)
        aspect_score = 1.0 - abs(aspect_ratio - 1.0) / 2.0
        aspect_score = max(0, min(aspect_score, 1.0))

        # Score de intensidade (mais escuro = mais confiança)
        intensity_score = 1.0 - (intensity / 255.0)

        # Média ponderada
        confidence = (
            circ_score * 0.3 +
            conv_score * 0.3 +
            aspect_score * 0.2 +
            intensity_score * 0.2
        )

        return confidence

    def _detect_by_texture(self, image: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """
        Detecta buracos usando análise de textura (LBP, variância).
        """
        logger.info("🔍 Método: Análise de Textura")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 1. Local Binary Pattern (LBP)
        lbp = local_binary_pattern(
            gray,
            self.texture_params['lbp_points'],
            self.texture_params['lbp_radius'],
            method='uniform'
        )

        # 2. Calcular variância local (textura irregular)
        # Buracos têm textura mais irregular que asfalto liso
        kernel_size = 15
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size ** 2)

        # Média local
        local_mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)

        # Variância local
        local_sq_mean = cv2.filter2D((gray.astype(np.float32) ** 2), -1, kernel)
        local_variance = local_sq_mean - (local_mean ** 2)

        # 3. Detectar áreas com alta variância e baixa intensidade
        variance_mask = (local_variance > self.texture_params['variance_threshold']).astype(np.uint8) * 255
        darkness_mask = (gray < self.texture_params['darkness_threshold']).astype(np.uint8) * 255

        # Combinar máscaras
        texture_mask = cv2.bitwise_and(variance_mask, darkness_mask)

        # Operações morfológicas para limpar
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        texture_mask = cv2.morphologyEx(texture_mask, cv2.MORPH_CLOSE, kernel)
        texture_mask = cv2.morphologyEx(texture_mask, cv2.MORPH_OPEN, kernel)

        # Encontrar componentes conectados
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            texture_mask, connectivity=8
        )

        potholes = []
        mask = np.zeros(gray.shape, dtype=np.uint8)

        for i in range(1, num_labels):  # Pular background (0)
            area = stats[i, cv2.CC_STAT_AREA]

            if area > self.contour_params['min_area']:
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                w = stats[i, cv2.CC_STAT_WIDTH]
                h = stats[i, cv2.CC_STAT_HEIGHT]

                # Criar máscara para esta região
                region_mask = (labels == i).astype(np.uint8)
                mask = cv2.bitwise_or(mask, region_mask * 255)

                potholes.append({
                    'is_pothole': True,
                    'area': area,
                    'bounding_box': (x, y, w, h),
                    'center': (int(centroids[i][0]), int(centroids[i][1])),
                    'confidence_score': 0.7  # Confiança média para textura
                })

        return mask, potholes

    def _detect_by_shadow(self, image: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """
        Detecta buracos usando análise de sombras e gradientes.
        Buracos criam sombras características devido à profundidade.
        """
        logger.info("🔍 Método: Análise de Sombras")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 1. Detectar áreas escuras (sombras)
        shadow_mask = (gray < self.depth_params['shadow_threshold']).astype(np.uint8) * 255

        # 2. Calcular gradientes (bordas de buracos têm gradientes fortes)
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
        gradient_mask = (gradient_magnitude > self.depth_params['gradient_threshold']).astype(np.uint8) * 255

        # 3. Análise de forma de sombra
        # Buracos têm sombras em forma de crescente ou anel
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (self.depth_params['morphology_kernel_size'],
             self.depth_params['morphology_kernel_size'])
        )

        # Dilatar gradientes para conectar
        gradient_dilated = cv2.dilate(gradient_mask, kernel, iterations=1)

        # Combinar sombras com gradientes
        combined_mask = cv2.bitwise_and(shadow_mask, gradient_dilated)

        # Limpar ruído
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)

        # Encontrar contornos
        contours, _ = cv2.findContours(
            combined_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        potholes = []
        mask = np.zeros(gray.shape, dtype=np.uint8)

        for contour in contours:
            area = cv2.contourArea(contour)

            if area > self.contour_params['min_area']:
                x, y, w, h = cv2.boundingRect(contour)

                cv2.drawContours(mask, [contour], -1, 255, -1)

                potholes.append({
                    'is_pothole': True,
                    'area': area,
                    'bounding_box': (x, y, w, h),
                    'center': (x + w//2, y + h//2),
                    'confidence_score': 0.65  # Confiança média-baixa para sombras
                })

        return mask, potholes

    def _detect_combined(self, image: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """
        Combina múltiplos métodos para máxima precisão.
        """
        logger.info("🔍 Método: Combinado (Contorno + Textura + Sombra)")

        # Executar todos os métodos
        contour_mask, contour_potholes = self._detect_by_contour(image)
        texture_mask, texture_potholes = self._detect_by_texture(image)
        shadow_mask, shadow_potholes = self._detect_by_shadow(image)

        # Normalizar máscaras
        contour_norm = contour_mask.astype(np.float32) / 255.0
        texture_norm = texture_mask.astype(np.float32) / 255.0
        shadow_norm = shadow_mask.astype(np.float32) / 255.0

        # Fusão ponderada
        # Contorno é mais confiável, seguido por textura, depois sombra
        combined = (
            contour_norm * 0.5 +
            texture_norm * 0.3 +
            shadow_norm * 0.2
        )

        # Aplicar threshold
        threshold = 0.4
        final_mask = (combined > threshold).astype(np.uint8) * 255

        # Limpar resultado final
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel)
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, kernel)

        # Encontrar contornos finais
        contours, _ = cv2.findContours(
            final_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        potholes = []

        for contour in contours:
            pothole_info = self._analyze_contour(contour, gray)

            if pothole_info['is_pothole']:
                # Aumentar confiança para detecções combinadas
                pothole_info['confidence_score'] = min(
                    pothole_info['confidence_score'] * 1.2,
                    1.0
                )
                pothole_info['detected_by'] = 'combined'
                potholes.append(pothole_info)

        # Calcular consenso
        consensus = self._calculate_method_consensus(
            len(contour_potholes),
            len(texture_potholes),
            len(shadow_potholes),
            len(potholes)
        )

        # Adicionar informação de consenso aos resultados
        for pothole in potholes:
            pothole['consensus_score'] = consensus

        return final_mask, potholes

    def _calculate_method_consensus(self, n_contour: int, n_texture: int,
                                   n_shadow: int, n_combined: int) -> float:
        """
        Calcula score de consenso entre métodos.
        """
        methods_counts = [n_contour, n_texture, n_shadow]

        if n_combined == 0:
            return 0.5

        # Quanto mais próximos os números, maior o consenso
        avg = np.mean(methods_counts)
        if avg == 0:
            return 0.5

        variance = np.var(methods_counts)
        normalized_variance = variance / (avg ** 2) if avg > 0 else 1.0

        # Converter variância em score de consenso (0-1)
        consensus = 1.0 / (1.0 + normalized_variance)

        return consensus

    def _calculate_confidence(self, image: np.ndarray, mask: np.ndarray,
                             potholes: List[Dict], method: str) -> Dict:
        """
        Calcula confiabilidade geral da detecção.
        """
        factors = {}

        # 1. Qualidade da imagem (30%)
        factors['image_quality'] = self._assess_image_quality(image)

        # 2. Confiança média dos buracos detectados (25%)
        if potholes:
            avg_pothole_confidence = np.mean([p['confidence_score'] for p in potholes])
            factors['detection_confidence'] = avg_pothole_confidence
        else:
            factors['detection_confidence'] = 0.3

        # 3. Consenso entre métodos (20%)
        if method == 'combined' and potholes:
            factors['consensus'] = potholes[0].get('consensus_score', 0.7)
        else:
            factors['consensus'] = 0.7

        # 4. Número razoável de detecções (15%)
        num_potholes = len(potholes)
        if 0 < num_potholes < 20:  # Range esperado
            factors['count_score'] = 1.0
        elif num_potholes == 0:
            factors['count_score'] = 0.0
        else:  # Muitos buracos pode indicar falso positivo
            factors['count_score'] = max(0.3, 1.0 - (num_potholes - 20) / 30)

        # 5. Distribuição espacial (10%)
        factors['distribution'] = self._analyze_spatial_distribution(mask)

        # Calcular confiança ponderada
        confidence = (
            factors['image_quality'] * 0.30 +
            factors['detection_confidence'] * 0.25 +
            factors['consensus'] * 0.20 +
            factors['count_score'] * 0.15 +
            factors['distribution'] * 0.10
        )

        # Detectar flags
        flags = self._detect_scenario_flags(factors, image, len(potholes))

        return {
            'confidence': confidence,
            'confidence_level': self._get_confidence_level(confidence),
            'factors': factors,
            'flags': flags
        }

    def _assess_image_quality(self, image: np.ndarray) -> float:
        """
        Avalia qualidade técnica da imagem.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Brilho
        brightness = np.mean(gray) / 255.0
        brightness_score = 1.0 - abs(brightness - 0.5) * 2

        # Contraste
        contrast = gray.std() / 128.0
        contrast_score = min(contrast, 1.0)

        # Nitidez (variância do Laplaciano)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        sharpness_score = min(sharpness / 500.0, 1.0)

        # Score combinado
        quality = (
            brightness_score * 0.4 +
            contrast_score * 0.3 +
            sharpness_score * 0.3
        )

        return quality

    def _analyze_spatial_distribution(self, mask: np.ndarray) -> float:
        """
        Analisa distribuição espacial das detecções.
        """
        if np.sum(mask) == 0:
            return 0.5

        # Encontrar componentes conectados
        num_labels = cv2.connectedComponents(mask)[0]

        # Calcular centro de massa
        M = cv2.moments(mask)
        if M['m00'] == 0:
            return 0.5

        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])

        # Buracos bem distribuídos têm centro próximo ao centro da imagem
        img_center_x = mask.shape[1] // 2
        img_center_y = mask.shape[0] // 2

        max_distance = np.sqrt(img_center_x**2 + img_center_y**2)
        distance = np.sqrt((cx - img_center_x)**2 + (cy - img_center_y)**2)

        distribution_score = 1.0 - (distance / max_distance)

        return distribution_score

    def _detect_scenario_flags(self, factors: Dict, image: np.ndarray,
                               num_potholes: int) -> List[str]:
        """
        Detecta cenários problemáticos.
        """
        flags = []

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray) / 255.0

        # Iluminação
        if brightness < 0.25:
            flags.append('low_light')
        elif brightness > 0.75:
            flags.append('overexposed')

        # Contraste
        if factors.get('image_quality', 1.0) < 0.4:
            flags.append('low_quality')

        # Consenso
        if factors.get('consensus', 1.0) < 0.5:
            flags.append('method_disagreement')

        # Número de detecções
        if num_potholes == 0:
            flags.append('no_detection')
        elif num_potholes > 30:
            flags.append('too_many_detections')

        # Confiança de detecção
        if factors.get('detection_confidence', 1.0) < 0.4:
            flags.append('low_detection_confidence')

        return flags

    def _get_confidence_level(self, confidence: float) -> str:
        """
        Classifica nível de confiança.
        """
        if confidence >= 0.8:
            return "HIGH"
        elif confidence >= 0.6:
            return "MEDIUM"
        elif confidence >= 0.4:
            return "LOW"
        else:
            return "VERY_LOW"

    def visualize_detections(self, image_path: str, result: Dict,
                           output_path: Optional[str] = None) -> np.ndarray:
        """
        Cria visualização dos buracos detectados.

        Args:
            image_path: Caminho da imagem original
            result: Resultado da detecção
            output_path: Caminho para salvar (opcional)

        Returns:
            Imagem com visualização
        """
        # Carregar imagem original
        image = cv2.imread(image_path)
        overlay = image.copy()

        # Desenhar buracos detectados
        for pothole in result['potholes']:
            x, y, w, h = pothole['bounding_box']
            center = pothole['center']
            confidence = pothole['confidence_score']

            # Cor baseada na confiança
            if confidence >= 0.7:
                color = (0, 255, 0)  # Verde = alta confiança
            elif confidence >= 0.5:
                color = (0, 255, 255)  # Amarelo = média confiança
            else:
                color = (0, 0, 255)  # Vermelho = baixa confiança

            # Desenhar retângulo
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)

            # Desenhar círculo no centro
            cv2.circle(overlay, center, 5, color, -1)

            # Adicionar texto com confiança
            label = f"{confidence:.2f}"
            cv2.putText(overlay, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Adicionar informações gerais
        info_text = [
            f"Buracos: {result['num_potholes']}",
            f"Area: {result['total_area']:.0f} px",
            f"Conf: {result['confidence']:.2f} ({result['confidence_level']})",
            f"Metodo: {result['method']}"
        ]

        y_offset = 30
        for i, text in enumerate(info_text):
            cv2.putText(overlay, text, (10, y_offset + i * 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(overlay, text, (10, y_offset + i * 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

        # Misturar com a imagem original (overlay transparente)
        result_image = cv2.addWeighted(overlay, 0.7, image, 0.3, 0)

        # Salvar se output_path fornecido
        if output_path:
            cv2.imwrite(output_path, result_image)
            logger.info(f"💾 Visualização salva em: {output_path}")

        return result_image


def main():
    """Função principal para testes."""
    import sys

    if len(sys.argv) < 2:
        print("Uso: python pothole_detector.py <caminho_imagem> [método]")
        print("Métodos disponíveis: contour, texture, shadow, combined")
        sys.exit(1)

    image_path = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else 'combined'

    # Criar detector
    detector = PotholeDetector()

    # Detectar buracos
    result = detector.detect_image(image_path, method=method)

    # Visualizar
    output_path = f"output/pothole_detection_{Path(image_path).stem}.jpg"
    detector.visualize_detections(image_path, result, output_path)

    print(f"\n✅ Análise concluída!")
    print(f"📊 {result['num_potholes']} buracos detectados")
    print(f"🎯 Confiança: {result['confidence']:.2f} ({result['confidence_level']})")
    print(f"💾 Resultado salvo em: {output_path}")


if __name__ == "__main__":
    main()
