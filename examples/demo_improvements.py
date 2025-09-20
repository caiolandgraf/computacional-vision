#!/usr/bin/env python3
"""
Demonstração das melhorias automáticas implementadas no sistema.
Mostra antes/depois das correções CLAHE, realce de bordas, área adaptativa e watershed.
"""

import sys
import os
from pathlib import Path
import cv2
import numpy as np
import matplotlib.pyplot as plt
import time

# Adiciona o diretório src ao path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from detector import GrassDetector

def demonstrate_improvements():
    """
    Demonstra as melhorias automáticas implementadas.
    """
    print("🌟 DEMONSTRAÇÃO DAS MELHORIAS AUTOMÁTICAS")
    print("=" * 60)
    
    detector = GrassDetector()
    
    print("\n📊 MELHORIAS IMPLEMENTADAS:")
    print("• ✅ CLAHE automático para baixo contraste")
    print("• ✅ Realce de bordas para foco pobre")  
    print("• ✅ Área mínima adaptativa para detecção esparsa")
    print("• ✅ Separação Watershed para vegetação densa")
    
    # Testa diferentes cenários
    scenarios = [
        ("🔍 Baixo Contraste", create_low_contrast_image()),
        ("📸 Foco Pobre", create_blurry_image()),
        ("🌿 Vegetação Esparsa", create_sparse_vegetation()),
        ("🌲 Vegetação Densa", create_dense_vegetation())
    ]
    
    print("\n🎯 TESTANDO CENÁRIOS COM MELHORIAS:")
    print("-" * 50)
    
    for scenario_name, test_image in scenarios:
        print(f"\n{scenario_name}")
        print("-" * 30)
        
        # Testa método combinado (que usa todas as melhorias)
        start_time = time.time()
        mask, stats = detector.detect_grass_areas(test_image, method='combined')
        processing_time = time.time() - start_time
        
        coverage = stats['coverage_percentage']
        confidence = stats.get('confidence_score', 0)
        flags = stats.get('scenario_flags', {})
        
        print(f"Cobertura: {coverage:.2f}%")
        print(f"Confiança: {confidence:.3f} ({get_confidence_level(confidence)})")
        print(f"Tempo: {processing_time:.3f}s")
        
        # Mostra melhorias aplicadas
        improvements_applied = []
        
        if 'clahe_applied' in stats.get('individual_stats', {}).get('color', {}):
            if stats['individual_stats']['color']['clahe_applied']:
                improvements_applied.append("📊 CLAHE aplicado")
        
        if 'adaptive_min_area' in stats.get('individual_stats', {}).get('color', {}):
            area = stats['individual_stats']['color']['adaptive_min_area']
            base_area = detector.texture_params['min_area'] // 2
            if area != base_area:
                improvements_applied.append(f"🔧 Área adaptativa: {area} (base: {base_area})")
        
        # Detecta se watershed foi aplicado (cobertura muito reduzida)
        initial_coverage = stats.get('individual_stats', {}).get('color', {}).get('initial_coverage', coverage)
        if abs(initial_coverage - coverage/100) > 0.3:  # Redução significativa
            improvements_applied.append("🌊 Separação Watershed aplicada")
        
        # Verifica flags problemáticas resolvidas
        critical_flags = [k for k, v in flags.items() if v and k in ['low_contrast', 'poor_focus', 'sparse_detection', 'dense_detection']]
        
        if improvements_applied:
            print("🚀 Melhorias aplicadas:")
            for improvement in improvements_applied:
                print(f"   {improvement}")
        
        if critical_flags:
            print("⚠️ Desafios ainda presentes:")
            for flag in critical_flags:
                print(f"   {flag_descriptions.get(flag, flag)}")
        else:
            print("✅ Nenhum desafio crítico detectado")
    
    print("\n🎉 DEMONSTRAÇÃO COMPLETA!")
    print("\nAs melhorias são aplicadas automaticamente quando:")
    print("• Contraste < 0.4 → CLAHE ativado")
    print("• Variância Laplaciana < 100 → Realce de bordas")
    print("• Cobertura < 5% → Área mínima reduzida em 70%")
    print("• Cobertura > 80% → Separação Watershed")

def create_low_contrast_image(size=(400, 300)):
    """Cria imagem com baixo contraste."""
    image = np.full((size[1], size[0], 3), [100, 100, 100], dtype=np.uint8)
    
    # Adiciona vegetação com contraste muito baixo
    cv2.rectangle(image, (50, 50), (150, 120), (110, 110, 105), -1)
    cv2.rectangle(image, (200, 150), (300, 220), (105, 105, 110), -1)
    
    return image

def create_blurry_image(size=(400, 300)):
    """Cria imagem com foco pobre."""
    # Cria imagem nítida primeiro
    image = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    image[:] = [120, 100, 80]  # Fundo
    
    # Adiciona vegetação
    cv2.rectangle(image, (50, 50), (180, 150), (60, 150, 70), -1)
    cv2.rectangle(image, (220, 100), (350, 200), (40, 130, 50), -1)
    
    # Aplica blur gaussiano para simular foco pobre
    blurred = cv2.GaussianBlur(image, (15, 15), 0)
    
    return blurred

def create_sparse_vegetation(size=(400, 300)):
    """Cria imagem com vegetação muito esparsa."""
    image = np.full((size[1], size[0], 3), [140, 130, 110], dtype=np.uint8)
    
    # Pequenos pontos espalhados de vegetação
    points = [(50, 50), (120, 80), (200, 120), (280, 160), (100, 200), (250, 220)]
    
    for x, y in points:
        # Pequenos círculos de vegetação
        cv2.circle(image, (x, y), 8, (50, 140, 60), -1)
        cv2.circle(image, (x+15, y+10), 6, (45, 120, 55), -1)
    
    return image

def create_dense_vegetation(size=(400, 300)):
    """Cria imagem com vegetação muito densa (quase 100%)."""
    # Quase toda a imagem é vegetação
    image = np.full((size[1], size[0], 3), [45, 130, 55], dtype=np.uint8)
    
    # Apenas pequenas áreas sem vegetação
    cv2.rectangle(image, (10, 10), (40, 40), (130, 120, 100), -1)
    cv2.rectangle(image, (350, 250), (390, 290), (140, 110, 90), -1)
    cv2.circle(image, (200, 150), 20, (125, 115, 95), -1)
    
    return image

def get_confidence_level(confidence):
    """Converte score de confiança em nível textual."""
    if confidence >= 0.8:
        return "Alta"
    elif confidence >= 0.6:
        return "Média"
    elif confidence >= 0.4:
        return "Baixa"
    else:
        return "Muito Baixa"

# Descrições amigáveis para flags
flag_descriptions = {
    'low_contrast': '📊 Baixo contraste',
    'poor_focus': '📸 Foco inadequado', 
    'sparse_detection': '🔍 Detecção esparsa',
    'dense_detection': '🌿 Detecção muito densa',
    'low_light': '🌑 Baixa iluminação',
    'overexposed': '☀️ Superexposição',
    'method_disagreement': '⚖️ Métodos discordam'
}

if __name__ == "__main__":
    demonstrate_improvements()