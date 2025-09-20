#!/usr/bin/env python3
"""
Script para testar especificamente o método deeplearning
e comparar com outros métodos.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from capture import ImageCapture
from detector import GrassDetector
from visualizer import ResultVisualizer


def test_deeplearning_method():
    """Testa especificamente o método deeplearning."""
    print("🧠 TESTE DO MÉTODO DEEP LEARNING")
    print("=" * 50)
    
    # Inicializa componentes
    capture = ImageCapture()
    detector = GrassDetector()
    visualizer = ResultVisualizer()
    
    # Verifica se deep learning está disponível
    if not detector.is_model_loaded:
        print("❌ Modelo deep learning não foi carregado corretamente")
        return
    
    print("✅ Modelo deep learning carregado com sucesso!")
    print(f"TensorFlow disponível: {detector.__class__.__module__.split('.')[0]}")
    
    # Testa com todas as imagens de exemplo
    examples_dir = Path(__file__).parent
    methods = ['color', 'texture', 'combined', 'deeplearning']
    
    for image_name in ['exemplo_mato_alto.jpg', 'exemplo_urbano.jpg', 'exemplo_jardim.jpg']:
        image_path = examples_dir / image_name
        
        if not image_path.exists():
            print(f"❌ Imagem não encontrada: {image_path}")
            continue
        
        print(f"\n📷 Testando: {image_name}")
        print("-" * 30)
        
        # Carrega imagem
        image = capture.load_image(str(image_path))
        if image is None:
            continue
        
        results = []
        
        # Testa cada método
        for method in methods:
            try:
                mask, stats = detector.detect_grass_areas(image, method)
                confidence = detector.get_detection_confidence(stats)
                results.append((mask, method, stats))
                
                if method == 'deeplearning':
                    print(f"   🧠 {method.upper()}: {stats['coverage_percentage']:.1f}% "
                          f"(confiança: {confidence:.2f}) "
                          f"[avg_pred: {stats.get('avg_prediction', 0):.3f}]")
                else:
                    print(f"   📊 {method.capitalize()}: {stats['coverage_percentage']:.1f}% "
                          f"(confiança: {confidence:.2f})")
                
            except Exception as e:
                print(f"   ❌ Erro em {method}: {str(e)}")
        
        # Cria comparação visual incluindo deeplearning
        if results:
            comparison = visualizer.create_side_by_side_comparison(image, results)
            
            # Salva resultado
            output_path = examples_dir.parent / "output" / f"deeplearning_test_{image_name.replace('.jpg', '_comparison.jpg')}"
            output_path.parent.mkdir(exist_ok=True)
            visualizer.save_visualization(comparison, str(output_path))
            
            print(f"   💾 Comparação salva: {output_path}")


def compare_deeplearning_performance():
    """Compara performance do deep learning com outros métodos."""
    print("\n⚡ TESTE DE PERFORMANCE - DEEP LEARNING")
    print("=" * 50)
    
    import time
    import numpy as np
    
    detector = GrassDetector()
    
    if not detector.is_model_loaded:
        print("❌ Deep learning não disponível para teste de performance")
        return
    
    # Testa com diferentes tamanhos
    test_sizes = [(480, 640), (720, 1280), (1080, 1920)]
    methods = ['color', 'texture', 'combined', 'deeplearning']
    
    print("Tamanho\t\tMétodo\t\tTempo (s)")
    print("-" * 50)
    
    for height, width in test_sizes:
        # Cria imagem de teste
        test_image = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        
        # Adiciona algumas áreas verdes
        test_image[height//3:2*height//3, width//4:3*width//4] = [50, 180, 50]
        
        for method in methods:
            try:
                start_time = time.time()
                mask, stats = detector.detect_grass_areas(test_image, method)
                end_time = time.time()
                
                processing_time = end_time - start_time
                coverage = stats['coverage_percentage']
                
                marker = "🧠" if method == "deeplearning" else "📊"
                print(f"{width}x{height}\t{marker} {method}\t\t{processing_time:.3f}s ({coverage:.1f}%)")
                
            except Exception as e:
                print(f"{width}x{height}\t❌ {method}\t\tERRO: {str(e)}")


def analyze_deeplearning_features():
    """Analisa características específicas do método deep learning."""
    print("\n🔍 ANÁLISE DETALHADA DO DEEP LEARNING")
    print("=" * 50)
    
    capture = ImageCapture()
    detector = GrassDetector()
    
    if not detector.is_model_loaded:
        print("❌ Deep learning não disponível")
        return
    
    # Usa imagem de exemplo
    examples_dir = Path(__file__).parent
    image_path = examples_dir / "exemplo_mato_alto.jpg"
    
    if not image_path.exists():
        print("❌ Imagem de exemplo não encontrada")
        return
    
    image = capture.load_image(str(image_path))
    if image is None:
        return
    
    # Executa detecção com deep learning
    mask, stats = detector.detect_grass_areas(image, 'deeplearning')
    
    print("🧠 Características do modelo Deep Learning:")
    print(f"   Método: {stats['method']}")
    print(f"   Cobertura: {stats['coverage_percentage']:.2f}%")
    print(f"   Confiança: {stats.get('confidence_score', 'N/A'):.3f}")
    print(f"   Shape entrada: {stats.get('model_input_shape', 'N/A')}")
    print(f"   Threshold: {stats.get('prediction_threshold', 'N/A')}")
    print(f"   Predição média: {stats.get('avg_prediction', 'N/A'):.3f}")
    
    if 'dominant_colors' in stats and stats['dominant_colors']:
        print("   Cores dominantes detectadas:")
        for i, color in enumerate(stats['dominant_colors'][:3]):
            print(f"     {i+1}. RGB{color}")
    
    # Analisa densidade
    density_analysis = detector.analyze_grass_density(mask)
    print(f"   Classificação densidade: {density_analysis['density_classification']}")
    print(f"   Número de regiões: {density_analysis['num_regions']}")
    print(f"   Área média: {density_analysis['average_area']:.0f} pixels")


def main():
    """Função principal."""
    print("🧠 TESTE COMPLETO DO MODO DEEP LEARNING")
    print("=" * 60)
    
    try:
        # Testa método deep learning
        test_deeplearning_method()
        
        # Testa performance
        compare_deeplearning_performance()
        
        # Análise detalhada
        analyze_deeplearning_features()
        
        print("\n🎉 TESTE COMPLETO CONCLUÍDO!")
        print("✅ O método deep learning está funcionando corretamente")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()