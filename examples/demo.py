#!/usr/bin/env python3
"""
Script de exemplo para demonstrar o uso básico do sistema
de detecção de mato alto.
"""

import sys
import os
from pathlib import Path
import numpy as np
import cv2

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from capture import ImageCapture
from detector import GrassDetector
from visualizer import ResultVisualizer


def create_sample_images():
    """Cria imagens de exemplo para teste."""
    print("Criando imagens de exemplo...")
    
    # Diretório de exemplos
    examples_dir = Path(__file__).parent
    
    # Imagem 1: Paisagem com mato alto
    img1 = np.zeros((600, 800, 3), dtype=np.uint8)
    
    # Céu azul
    img1[:200, :] = [200, 150, 100]  # BGR
    
    # Área com mato alto (verde)
    img1[200:450, 100:700] = [50, 180, 50]
    
    # Adiciona textura no mato
    for i in range(200, 450, 3):
        for j in range(100, 700, 4):
            if np.random.random() > 0.7:
                img1[i:i+2, j:j+2] = [30, 150, 30]
    
    # Terra/caminho
    img1[450:, :] = [80, 120, 140]
    
    # Salva imagem 1
    cv2.imwrite(str(examples_dir / "exemplo_mato_alto.jpg"), img1)
    
    # Imagem 2: Área urbana com pouco mato
    img2 = np.ones((600, 800, 3), dtype=np.uint8) * 120
    
    # Algumas áreas pequenas de vegetação
    img2[400:500, 50:150] = [40, 160, 40]
    img2[300:380, 600:750] = [60, 140, 45]
    
    # Concreto/asfalto
    img2[500:, :] = [100, 100, 100]
    
    cv2.imwrite(str(examples_dir / "exemplo_urbano.jpg"), img2)
    
    # Imagem 3: Jardim bem cuidado
    img3 = np.ones((600, 800, 3), dtype=np.uint8) * 180
    
    # Grama baixa e uniforme
    img3[300:550, 100:700] = [65, 120, 65]
    
    # Adiciona padrão uniforme
    for i in range(300, 550, 2):
        for j in range(100, 700, 2):
            img3[i, j] = [70, 125, 70]
    
    cv2.imwrite(str(examples_dir / "exemplo_jardim.jpg"), img3)
    
    print("✅ Imagens de exemplo criadas:")
    print(f"   - {examples_dir / 'exemplo_mato_alto.jpg'}")
    print(f"   - {examples_dir / 'exemplo_urbano.jpg'}")
    print(f"   - {examples_dir / 'exemplo_jardim.jpg'}")


def test_detection_methods():
    """Testa diferentes métodos de detecção."""
    print("\n🔬 Testando métodos de detecção...")
    
    # Inicializa componentes
    capture = ImageCapture()
    detector = GrassDetector()
    visualizer = ResultVisualizer()
    
    # Caminho das imagens de exemplo
    examples_dir = Path(__file__).parent
    
    methods = ['color', 'texture', 'combined']
    
    for image_name in ['exemplo_mato_alto.jpg', 'exemplo_urbano.jpg', 'exemplo_jardim.jpg']:
        image_path = examples_dir / image_name
        
        if not image_path.exists():
            print(f"❌ Imagem não encontrada: {image_path}")
            continue
        
        print(f"\n📷 Analisando: {image_name}")
        
        # Carrega imagem
        image = capture.load_image(str(image_path))
        if image is None:
            continue
        
        results = []
        
        # Testa cada método
        for method in methods:
            mask, stats = detector.detect_grass_areas(image, method)
            confidence = detector.get_detection_confidence(stats)
            results.append((mask, method, stats))
            
            print(f"   {method.capitalize()}: {stats['coverage_percentage']:.1f}% "
                  f"(confiança: {confidence:.2f})")
        
        # Cria comparação visual
        comparison = visualizer.create_side_by_side_comparison(image, results)
        
        # Salva resultado
        output_path = examples_dir.parent / "output" / f"test_{image_name.replace('.jpg', '_comparison.jpg')}"
        output_path.parent.mkdir(exist_ok=True)
        visualizer.save_visualization(comparison, str(output_path))
        
        print(f"   Comparação salva: {output_path}")


def demonstrate_features():
    """Demonstra as principais funcionalidades."""
    print("\n🎯 Demonstrando funcionalidades...")
    
    # Inicializa sistema
    capture = ImageCapture()
    detector = GrassDetector()
    visualizer = ResultVisualizer()
    
    examples_dir = Path(__file__).parent
    image_path = examples_dir / "exemplo_mato_alto.jpg"
    
    if not image_path.exists():
        print("❌ Imagem de exemplo não encontrada. Execute create_sample_images() primeiro.")
        return
    
    # Carrega imagem
    image = capture.load_image(str(image_path))
    if image is None:
        return
    
    print("1. Detecção básica...")
    mask, stats = detector.detect_grass_areas(image, 'combined')
    
    print("2. Análise de densidade...")
    density_analysis = detector.analyze_grass_density(mask)
    
    print("3. Criando visualizações...")
    
    # Visualização com overlay
    overlay_viz = visualizer.create_overlay_visualization(image, mask, stats)
    
    # Mapa de densidade
    density_viz = visualizer.create_density_heatmap(image, mask, density_analysis)
    
    # Análise detalhada
    detailed_viz = visualizer.create_detailed_analysis_panel(image, mask, stats, density_analysis)
    
    # Salva resultados
    output_dir = examples_dir.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    visualizer.save_visualization(overlay_viz, str(output_dir / "demo_overlay.jpg"))
    visualizer.save_visualization(density_viz, str(output_dir / "demo_density.jpg"))
    visualizer.save_visualization(detailed_viz, str(output_dir / "demo_detailed.jpg"))
    
    print("✅ Demonstração concluída!")
    print(f"   Cobertura detectada: {stats['coverage_percentage']:.2f}%")
    print(f"   Densidade: {density_analysis['density_classification']}")
    print(f"   Confiança: {detector.get_detection_confidence(stats):.2f}")
    print(f"   Resultados salvos em: {output_dir}")


def run_performance_test():
    """Executa teste de performance."""
    print("\n⚡ Teste de performance...")
    
    import time
    
    detector = GrassDetector()
    
    # Cria imagem de teste
    test_sizes = [(640, 480), (1280, 720), (1920, 1080)]
    methods = ['color', 'texture', 'combined']
    
    print("Tamanho\t\tMétodo\t\tTempo (s)")
    print("-" * 40)
    
    for width, height in test_sizes:
        # Cria imagem de teste
        test_image = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        
        # Adiciona algumas áreas verdes
        test_image[height//3:2*height//3, width//4:3*width//4] = [50, 180, 50]
        
        for method in methods:
            start_time = time.time()
            mask, stats = detector.detect_grass_areas(test_image, method)
            end_time = time.time()
            
            processing_time = end_time - start_time
            print(f"{width}x{height}\t{method}\t\t{processing_time:.3f}")


def main():
    """Função principal do script de exemplo."""
    print("🌿 SCRIPT DE EXEMPLO - DETECÇÃO DE MATO ALTO")
    print("=" * 50)
    
    while True:
        print("\nOpções disponíveis:")
        print("1. Criar imagens de exemplo")
        print("2. Testar métodos de detecção")
        print("3. Demonstrar funcionalidades")
        print("4. Teste de performance")
        print("5. Executar tudo")
        print("0. Sair")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        try:
            if choice == '1':
                create_sample_images()
            elif choice == '2':
                test_detection_methods()
            elif choice == '3':
                demonstrate_features()
            elif choice == '4':
                run_performance_test()
            elif choice == '5':
                create_sample_images()
                test_detection_methods()
                demonstrate_features()
                run_performance_test()
                print("\n✅ Todos os testes concluídos!")
                break
            elif choice == '0':
                break
            else:
                print("❌ Opção inválida")
                
        except KeyboardInterrupt:
            print("\n\nScript interrompido.")
            break
        except Exception as e:
            print(f"❌ Erro: {str(e)}")


if __name__ == "__main__":
    main()