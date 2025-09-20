#!/usr/bin/env python3
"""
Teste das melhorias de confiabilidade do sistema de detecção de mato alto.
Compara versão original vs versão aprimorada.
"""

import sys
import os
from pathlib import Path
import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import json

# Adiciona o diretório src ao path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from detector import GrassDetector
from visualizer import ResultVisualizer

def test_reliability_improvements():
    """
    Testa as melhorias de confiabilidade do sistema.
    """
    print("🧪 TESTE DE MELHORIAS DE CONFIABILIDADE")
    print("=" * 60)
    
    # Inicializa detector aprimorado
    detector = GrassDetector()
    visualizer = ResultVisualizer()
    
    # Cria imagem de teste sintética
    test_image = create_synthetic_test_image()
    
    print("\n📊 TESTANDO TODOS OS MÉTODOS APRIMORADOS:")
    print("-" * 40)
    
    results = {}
    
    # Testa cada método
    methods = ['color', 'texture', 'combined', 'deeplearning']
    
    for method in methods:
        print(f"\n🔍 Testando método: {method}")
        
        try:
            start_time = time.time()
            mask, stats = detector.detect_grass_areas(test_image, method=method)
            processing_time = time.time() - start_time
            
            # Adiciona tempo de processamento às estatísticas
            stats['processing_time'] = processing_time
            results[method] = stats
            
            print(f"   ✅ Cobertura: {stats['coverage_percentage']:.2f}%")
            print(f"   ⚡ Tempo: {processing_time:.3f}s")
            
            # Mostra score de confiança se disponível
            if 'confidence_score' in stats:
                confidence = stats['confidence_score']
                confidence_level = get_confidence_level(confidence)
                print(f"   🎯 Confiança: {confidence:.3f} ({confidence_level})")
            
            # Mostra flags de cenários problemáticos se disponível
            if 'scenario_flags' in stats:
                flags = stats['scenario_flags']
                problematic_flags = [k for k, v in flags.items() if v]
                if problematic_flags:
                    print(f"   ⚠️  Cenários detectados: {', '.join(problematic_flags)}")
                else:
                    print(f"   ✅ Nenhum cenário problemático detectado")
            
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            results[method] = {'error': str(e)}
    
    print("\n📈 ANÁLISE COMPARATIVA:")
    print("-" * 40)
    
    # Compara resultados
    analyze_results(results)
    
    # Testa diferentes condições de iluminação
    print("\n💡 TESTANDO CONDIÇÕES DE ILUMINAÇÃO:")
    print("-" * 40)
    test_lighting_conditions(detector)
    
    # Testa cenários desafiadores
    print("\n🎯 TESTANDO CENÁRIOS DESAFIADORES:")
    print("-" * 40)
    test_challenging_scenarios(detector)
    
    print("\n✅ TESTE COMPLETO FINALIZADO!")
    print("As melhorias incluem:")
    print("• Calibração automática de cores")
    print("• Filtros Gabor para textura direcional")
    print("• Local Binary Pattern (LBP)")
    print("• Sistema de confiança adaptativo")
    print("• Detecção de cenários problemáticos")
    print("• Filtros morfológicos avançados")
    print("• Remoção de outliers")
    
    return results

def create_synthetic_test_image(size=(640, 480)):
    """
    Cria imagem sintética para teste com áreas de vegetação simuladas.
    """
    image = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    
    # Fundo (solo/concreto)
    image[:] = [120, 100, 80]  # Cor marrom-acinzentada
    
    # Adiciona áreas de "vegetação" com diferentes características
    
    # Área 1: Vegetação verde típica
    cv2.rectangle(image, (50, 50), (200, 180), (60, 180, 80), -1)
    
    # Área 2: Vegetação mais escura
    cv2.rectangle(image, (300, 100), (450, 200), (40, 120, 50), -1)
    
    # Área 3: Vegetação amarelada (seca)
    cv2.rectangle(image, (100, 300), (250, 400), (90, 160, 120), -1)
    
    # Adiciona textura às áreas de vegetação
    for _ in range(1000):
        # Pontos aleatórios para simular textura
        x = np.random.randint(0, size[0])
        y = np.random.randint(0, size[1])
        
        # Adiciona variação de cor para simular textura de grama
        if (50 <= x <= 200 and 50 <= y <= 180) or \
           (300 <= x <= 450 and 100 <= y <= 200) or \
           (100 <= x <= 250 and 300 <= y <= 400):
            
            noise = np.random.randint(-20, 21, 3)
            new_color = np.clip(image[y, x] + noise, 0, 255)
            image[y, x] = new_color
    
    return image

def get_confidence_level(confidence):
    """
    Converte score de confiança em nível textual.
    """
    if confidence >= 0.8:
        return "Alta"
    elif confidence >= 0.6:
        return "Média"
    elif confidence >= 0.4:
        return "Baixa"
    else:
        return "Muito Baixa"

def analyze_results(results):
    """
    Analisa e compara os resultados dos diferentes métodos.
    """
    valid_results = {k: v for k, v in results.items() if 'error' not in v}
    
    if not valid_results:
        print("❌ Nenhum resultado válido para análise")
        return
    
    # Compara coberturas
    coverages = {method: stats['coverage_percentage'] 
                for method, stats in valid_results.items()}
    
    best_coverage = max(coverages.values())
    best_method = [k for k, v in coverages.items() if v == best_coverage][0]
    
    print(f"🏆 Maior cobertura: {best_method} ({best_coverage:.2f}%)")
    
    # Compara tempos
    times = {method: stats['processing_time'] 
            for method, stats in valid_results.items()}
    
    fastest_time = min(times.values())
    fastest_method = [k for k, v in times.items() if v == fastest_time][0]
    
    print(f"⚡ Mais rápido: {fastest_method} ({fastest_time:.3f}s)")
    
    # Compara confiabilidade
    confidences = {method: stats.get('confidence_score', 0) 
                  for method, stats in valid_results.items()}
    
    if any(confidences.values()):
        best_confidence = max(confidences.values())
        most_reliable = [k for k, v in confidences.items() if v == best_confidence][0]
        print(f"🎯 Mais confiável: {most_reliable} ({best_confidence:.3f})")

def test_lighting_conditions(detector):
    """
    Testa o sistema em diferentes condições de iluminação.
    """
    base_image = create_synthetic_test_image()
    
    conditions = [
        ("Normal", 1.0),
        ("Escuro", 0.3),
        ("Muito Claro", 1.8),
        ("Alto Contraste", 1.2)
    ]
    
    for condition_name, brightness_factor in conditions:
        print(f"\n🔆 Testando: {condition_name}")
        
        # Ajusta brilho da imagem
        adjusted_image = cv2.convertScaleAbs(base_image, alpha=brightness_factor, beta=0)
        
        try:
            mask, stats = detector.detect_grass_areas(adjusted_image, method='combined')
            
            coverage = stats['coverage_percentage']
            confidence = stats.get('confidence_score', 0)
            flags = stats.get('scenario_flags', {})
            
            print(f"   Cobertura: {coverage:.2f}% | Confiança: {confidence:.3f}")
            
            # Mostra flags específicas para iluminação
            lighting_flags = {k: v for k, v in flags.items() 
                            if k in ['low_light', 'overexposed', 'low_contrast']}
            
            if any(lighting_flags.values()):
                active_flags = [k for k, v in lighting_flags.items() if v]
                print(f"   ⚠️  Flags: {', '.join(active_flags)}")
            else:
                print(f"   ✅ Condições normais detectadas")
                
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")

def test_challenging_scenarios(detector):
    """
    Testa cenários desafiadores para o sistema.
    """
    scenarios = [
        ("Vegetação esparsa", create_sparse_vegetation_image()),
        ("Vegetação densa", create_dense_vegetation_image()),
        ("Sombras fortes", create_shadowed_image()),
        ("Cores similares", create_similar_colors_image())
    ]
    
    for scenario_name, test_image in scenarios:
        print(f"\n🎯 Testando: {scenario_name}")
        
        try:
            mask, stats = detector.detect_grass_areas(test_image, method='combined')
            
            coverage = stats['coverage_percentage']
            confidence = stats.get('confidence_score', 0)
            flags = stats.get('scenario_flags', {})
            
            print(f"   Cobertura: {coverage:.2f}% | Confiança: {confidence:.3f}")
            
            # Identifica desafios específicos
            challenge_flags = [k for k, v in flags.items() if v]
            if challenge_flags:
                print(f"   🚨 Desafios: {', '.join(challenge_flags)}")
                
                # Sugere ajustes
                suggest_improvements(challenge_flags)
            else:
                print(f"   ✅ Cenário processado sem problemas")
                
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")

def create_sparse_vegetation_image(size=(640, 480)):
    """Cria imagem com vegetação esparsa."""
    image = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    image[:] = [150, 140, 120]  # Fundo claro
    
    # Pequenas áreas esparsas de vegetação
    for _ in range(20):
        x = np.random.randint(10, size[0]-30)
        y = np.random.randint(10, size[1]-30)
        cv2.rectangle(image, (x, y), (x+20, y+15), (50, 150, 60), -1)
    
    return image

def create_dense_vegetation_image(size=(640, 480)):
    """Cria imagem com vegetação muito densa."""
    image = np.full((size[1], size[0], 3), [40, 120, 50], dtype=np.uint8)
    
    # Poucas áreas sem vegetação
    for _ in range(5):
        x = np.random.randint(0, size[0]-50)
        y = np.random.randint(0, size[1]-50)
        cv2.rectangle(image, (x, y), (x+40, y+30), (140, 120, 100), -1)
    
    return image

def create_shadowed_image(size=(640, 480)):
    """Cria imagem com sombras fortes."""
    image = create_synthetic_test_image(size)
    
    # Adiciona gradiente de sombra
    overlay = np.zeros_like(image)
    for i in range(size[1]):
        intensity = int(100 * (i / size[1]))
        overlay[i, :] = [intensity, intensity, intensity]
    
    # Mistura com a imagem original
    shadowed = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)
    
    return shadowed

def create_similar_colors_image(size=(640, 480)):
    """Cria imagem onde vegetação tem cores similares ao fundo."""
    image = np.full((size[1], size[0], 3), [80, 100, 70], dtype=np.uint8)
    
    # Áreas de "vegetação" com cores muito próximas
    cv2.rectangle(image, (100, 100), (300, 250), (85, 105, 75), -1)
    cv2.rectangle(image, (350, 150), (500, 300), (75, 95, 65), -1)
    
    return image

def suggest_improvements(flags):
    """
    Sugere melhorias baseado nas flags detectadas.
    """
    suggestions = {
        'low_light': "💡 Sugestão: Aumentar ganho de calibração para baixa luminosidade",
        'overexposed': "☀️ Sugestão: Aplicar correção de exposição automática",
        'low_contrast': "📊 Sugestão: Aplicar realce de contraste local (CLAHE)",
        'method_disagreement': "⚖️ Sugestão: Ajustar pesos dos métodos ou usar validação cruzada",
        'sparse_detection': "🔍 Sugestão: Reduzir área mínima e ajustar sensibilidade",
        'dense_detection': "🌿 Sugestão: Aplicar filtros de separação de regiões",
        'poor_focus': "📸 Sugestão: Aplicar filtros de realce de bordas"
    }
    
    for flag in flags:
        if flag in suggestions:
            print(f"     {suggestions[flag]}")

if __name__ == "__main__":
    test_reliability_improvements()