#!/usr/bin/env python3
"""
Sistema de Aprendizado Adaptativo para Deep Learning
====================================================

Este módulo implementa um sistema que "ensina" o detector deep learning
usando exemplos positivos e negativos, melhorando gradualmente sua confiança
e precisão através de feedback adaptativo.
"""

import numpy as np
import cv2
import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AdaptiveLearningSystem:
    """Sistema que aprende e melhora o deep learning com exemplos."""
    
    def __init__(self, knowledge_file: str = "knowledge_base.json"):
        self.knowledge_file = knowledge_file
        self.knowledge_base = self._load_knowledge_base()
        
        # Parâmetros adaptativos que melhoram com o tempo
        self.adaptive_params = {
            'confidence_boost': 1.0,      # Multiplicador de confiança
            'vegetation_threshold': 0.4,   # Threshold para vegetação
            'color_sensitivity': 1.0,      # Sensibilidade de cor
            'texture_weight': 1.0,         # Peso da textura
            'spatial_consistency': 1.0,    # Consistência espacial
            'false_positive_penalty': 0.1, # Penalidade por falsos positivos
            'learning_rate': 0.05,         # Taxa de aprendizado
        }
        
        # Estatísticas de aprendizado
        self.stats = {
            'examples_learned': 0,
            'positive_examples': 0,
            'negative_examples': 0,
            'accuracy_improvements': 0,
            'last_update': None,
        }
    
    def _load_knowledge_base(self) -> Dict:
        """Carrega base de conhecimento de exemplos anteriores."""
        if os.path.exists(self.knowledge_file):
            try:
                with open(self.knowledge_file, 'r') as f:
                    return json.load(f)
            except:
                logger.warning("Erro ao carregar base de conhecimento, criando nova")
        
        return {
            'vegetation_patterns': [],
            'non_vegetation_patterns': [],
            'successful_detections': [],
            'false_positives': [],
            'parameter_history': [],
            'version': '1.0'
        }
    
    def _save_knowledge_base(self):
        """Salva base de conhecimento atualizada."""
        self.knowledge_base['last_updated'] = datetime.now().isoformat()
        try:
            with open(self.knowledge_file, 'w') as f:
                json.dump(self.knowledge_base, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar base de conhecimento: {e}")
    
    def learn_from_example(self, image: np.ndarray, ground_truth_mask: np.ndarray, 
                          is_vegetation: bool, region_info: Dict = None):
        """
        Aprende com um exemplo fornecido.
        
        Args:
            image: Imagem de exemplo
            ground_truth_mask: Máscara correta (onde realmente há vegetação)
            is_vegetation: True se a região deve ser detectada como vegetação
            region_info: Informações adicionais sobre a região
        """
        logger.info(f"🎓 Aprendendo exemplo: {'vegetação' if is_vegetation else 'não-vegetação'}")
        
        # Extrai características do exemplo
        features = self._extract_learning_features(image, ground_truth_mask)
        
        if is_vegetation:
            self.knowledge_base['vegetation_patterns'].append({
                'features': features,
                'timestamp': datetime.now().isoformat(),
                'info': region_info or {}
            })
            self.stats['positive_examples'] += 1
        else:
            self.knowledge_base['non_vegetation_patterns'].append({
                'features': features,
                'timestamp': datetime.now().isoformat(),
                'info': region_info or {}
            })
            self.stats['negative_examples'] += 1
        
        # Ajusta parâmetros baseado no exemplo
        self._adapt_parameters(features, is_vegetation)
        
        self.stats['examples_learned'] += 1
        self.stats['last_update'] = datetime.now().isoformat()
        
        # Limita tamanho da base de conhecimento
        self._prune_knowledge_base()
        
        self._save_knowledge_base()
        
        logger.info(f"✅ Exemplo aprendido! Total: {self.stats['examples_learned']} exemplos")
    
    def _extract_learning_features(self, image: np.ndarray, mask: np.ndarray) -> Dict:
        """Extrai características relevantes para aprendizado."""
        # Região de interesse
        roi = image[mask > 0] if np.any(mask > 0) else image
        
        if len(roi) == 0:
            return {'error': 'empty_region'}
        
        features = {}
        
        # Características de cor
        if len(roi.shape) > 1 and roi.shape[1] == 3:
            features['mean_rgb'] = np.mean(roi, axis=0).tolist()
            features['std_rgb'] = np.std(roi, axis=0).tolist()
            
            # HSV
            roi_bgr = roi if roi.dtype == np.uint8 else (roi * 255).astype(np.uint8)
            hsv_roi = cv2.cvtColor(roi_bgr.reshape(1, -1, 3), cv2.COLOR_BGR2HSV)
            hsv_roi = hsv_roi.reshape(-1, 3)
            
            features['mean_hsv'] = np.mean(hsv_roi, axis=0).astype(float).tolist()
            features['std_hsv'] = np.std(hsv_roi, axis=0).astype(float).tolist()
        
        # Características de textura
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        roi_gray = gray[mask > 0] if np.any(mask > 0) else gray.flatten()
        
        features['texture_variance'] = float(np.var(roi_gray))
        features['texture_mean'] = float(np.mean(roi_gray))
        
        # Características espaciais
        if np.any(mask > 0):
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                features['area'] = float(cv2.contourArea(largest_contour))
                features['perimeter'] = float(cv2.arcLength(largest_contour, True))
                features['compactness'] = float(features['area'] / (features['perimeter']**2)) if features['perimeter'] > 0 else 0
        
        return features
    
    def _adapt_parameters(self, features: Dict, is_vegetation: bool):
        """Adapta parâmetros baseado no exemplo."""
        lr = self.adaptive_params['learning_rate']
        
        if 'error' in features:
            return
        
        # Ajusta threshold de vegetação baseado em exemplos positivos
        if is_vegetation and 'mean_hsv' in features:
            target_hue = features['mean_hsv'][0] / 180.0  # Normaliza hue
            if 0.2 < target_hue < 0.6:  # Verde
                # Ajusta threshold para ficar mais próximo deste exemplo
                current_threshold = self.adaptive_params['vegetation_threshold']
                target_adjustment = -0.05 if target_hue < 0.4 else 0.05
                new_threshold = current_threshold + lr * target_adjustment
                self.adaptive_params['vegetation_threshold'] = np.clip(new_threshold, 0.2, 0.7)
        
        # Ajusta sensibilidade de cor
        if 'std_hsv' in features:
            color_variation = np.mean(features['std_hsv'])
            if is_vegetation and color_variation > 20:  # Vegetação com boa variação
                self.adaptive_params['color_sensitivity'] *= (1 + lr)
            elif not is_vegetation and color_variation < 10:  # Objeto uniforme (artificial)
                self.adaptive_params['color_sensitivity'] *= (1 - lr)
        
        # Ajusta peso da textura
        if 'texture_variance' in features:
            texture_var = features['texture_variance']
            if is_vegetation and texture_var > 100:  # Boa textura para vegetação
                self.adaptive_params['texture_weight'] *= (1 + lr)
            elif not is_vegetation and texture_var < 50:  # Textura lisa (artificial)
                self.adaptive_params['texture_weight'] *= (1 - lr)
        
        # Ajusta boost de confiança baseado no sucesso
        if is_vegetation:
            self.adaptive_params['confidence_boost'] *= (1 + lr * 0.5)
        else:
            # Se é falso positivo, reduz confiança
            self.adaptive_params['confidence_boost'] *= (1 - lr * 0.2)
        
        # Limita parâmetros em faixas razoáveis
        self.adaptive_params['confidence_boost'] = np.clip(self.adaptive_params['confidence_boost'], 0.5, 3.0)
        self.adaptive_params['color_sensitivity'] = np.clip(self.adaptive_params['color_sensitivity'], 0.5, 2.0)
        self.adaptive_params['texture_weight'] = np.clip(self.adaptive_params['texture_weight'], 0.5, 2.0)
    
    def _prune_knowledge_base(self, max_examples: int = 100):
        """Limita o tamanho da base de conhecimento."""
        for pattern_type in ['vegetation_patterns', 'non_vegetation_patterns']:
            patterns = self.knowledge_base[pattern_type]
            if len(patterns) > max_examples:
                # Mantém os exemplos mais recentes
                patterns.sort(key=lambda x: x['timestamp'], reverse=True)
                self.knowledge_base[pattern_type] = patterns[:max_examples]
    
    def get_adaptive_confidence_boost(self, prediction: np.ndarray, image: np.ndarray) -> float:
        """Calcula boost de confiança baseado no aprendizado."""
        if len(self.knowledge_base['vegetation_patterns']) == 0:
            return 1.0  # Sem exemplos, usa padrão
        
        # Extrai características da predição atual
        mask = (prediction > 0.3).astype(np.uint8) * 255
        if not np.any(mask):
            return 0.5  # Sem detecção, baixa confiança
        
        current_features = self._extract_learning_features(image, mask)
        if 'error' in current_features:
            return 0.5
        
        # Compara com exemplos conhecidos de vegetação
        vegetation_similarity = self._calculate_similarity_score(
            current_features, self.knowledge_base['vegetation_patterns']
        )
        
        # Compara com exemplos de não-vegetação
        non_vegetation_similarity = self._calculate_similarity_score(
            current_features, self.knowledge_base['non_vegetation_patterns']
        )
        
        # Calcula boost baseado na similaridade
        if vegetation_similarity > non_vegetation_similarity:
            boost = self.adaptive_params['confidence_boost'] * (1 + vegetation_similarity)
        else:
            boost = self.adaptive_params['confidence_boost'] * (1 - non_vegetation_similarity * 0.5)
        
        return np.clip(boost, 0.1, 5.0)
    
    def _calculate_similarity_score(self, features: Dict, pattern_database: List[Dict]) -> float:
        """Calcula similaridade com base de padrões."""
        if not pattern_database or 'error' in features:
            return 0.0
        
        similarities = []
        
        for pattern in pattern_database[-20:]:  # Usa apenas os 20 exemplos mais recentes
            pattern_features = pattern['features']
            if 'error' in pattern_features:
                continue
            
            similarity = 0.0
            count = 0
            
            # Similaridade de cor HSV
            if 'mean_hsv' in features and 'mean_hsv' in pattern_features:
                hsv_diff = np.array(features['mean_hsv']) - np.array(pattern_features['mean_hsv'])
                hsv_similarity = 1.0 / (1.0 + np.linalg.norm(hsv_diff) / 100.0)
                similarity += hsv_similarity
                count += 1
            
            # Similaridade de textura
            if 'texture_variance' in features and 'texture_variance' in pattern_features:
                texture_diff = abs(features['texture_variance'] - pattern_features['texture_variance'])
                texture_similarity = 1.0 / (1.0 + texture_diff / 1000.0)
                similarity += texture_similarity
                count += 1
            
            if count > 0:
                similarities.append(similarity / count)
        
        return np.mean(similarities) if similarities else 0.0
    
    def get_adaptive_parameters(self) -> Dict:
        """Retorna parâmetros adaptativos atuais."""
        return self.adaptive_params.copy()
    
    def get_learning_stats(self) -> Dict:
        """Retorna estatísticas de aprendizado."""
        return self.stats.copy()
    
    def create_training_examples(self) -> List[Tuple[np.ndarray, np.ndarray, bool]]:
        """Cria exemplos sintéticos para treinamento baseado no conhecimento."""
        examples = []
        
        # Cria exemplos de vegetação
        for i in range(3):
            vegetation_example = self._create_vegetation_example()
            examples.append(vegetation_example)
        
        # Cria exemplos de não-vegetação
        for i in range(3):
            non_vegetation_example = self._create_non_vegetation_example()
            examples.append(non_vegetation_example)
        
        return examples
    
    def _create_vegetation_example(self) -> Tuple[np.ndarray, np.ndarray, bool]:
        """Cria exemplo sintético de vegetação."""
        # Cria imagem de vegetação típica
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Verde natural com variação
        for y in range(200):
            for x in range(200):
                base_green = 70 + np.random.randint(-20, 20)
                r = max(20, base_green - 15 + np.random.randint(-10, 10))
                g = max(40, int(base_green * 2.5) + np.random.randint(-30, 30))
                b = max(20, base_green + np.random.randint(-15, 15))
                image[y, x] = [r, g, b]
        
        # Adiciona textura natural
        noise = np.random.normal(0, 15, image.shape).astype(np.int16)
        image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Suavização para parecer mais orgânico
        image = cv2.bilateralFilter(image, 9, 75, 75)
        
        # Máscara completa (toda a imagem é vegetação neste exemplo)
        mask = np.ones((200, 200), dtype=np.uint8) * 255
        
        return image, mask, True
    
    def _create_non_vegetation_example(self) -> Tuple[np.ndarray, np.ndarray, bool]:
        """Cria exemplo sintético de não-vegetação."""
        # Cria imagem de objeto artificial verde
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Verde artificial uniforme
        artificial_green = [60, 180, 80]  # BGR
        image[:, :] = artificial_green
        
        # Adiciona formas geométricas (não-orgânicas)
        cv2.rectangle(image, (50, 50), (150, 150), [50, 200, 70], -1)
        cv2.circle(image, (100, 100), 30, [70, 160, 90], -1)
        
        # Máscara nas áreas artificiais
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.rectangle(mask, (50, 50), (150, 150), 255, -1)
        cv2.circle(mask, (100, 100), 30, 255, -1)
        
        return image, mask, False