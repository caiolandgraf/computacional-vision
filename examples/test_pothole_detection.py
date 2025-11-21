"""
Script de teste para o sistema de detecção de buracos.
Demonstra o uso da classe PotholeDetector com múltiplos métodos.
"""

import sys
import os
from pathlib import Path

# Adiciona src ao path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from pothole_detector import PotholeDetector
import cv2
import numpy as np


def create_synthetic_pothole_image(output_path: str = 'examples/synthetic_pothole.jpg'):
    """
    Cria uma imagem sintética com buracos para teste.
    Simula uma estrada com vários buracos de diferentes tamanhos.
    """
    print("🎨 Gerando imagem sintética de teste com buracos...")

    # Criar imagem de asfalto (640x480)
    width, height = 640, 480
    image = np.ones((height, width, 3), dtype=np.uint8) * 80  # Asfalto cinza escuro

    # Adicionar textura de asfalto
    noise = np.random.randint(-20, 20, (height, width, 3), dtype=np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Aplicar blur para textura mais realista
    image = cv2.GaussianBlur(image, (5, 5), 0)

    # Criar buracos sintéticos
    potholes = [
        # (centro_x, centro_y, raio, profundidade)
        (150, 200, 40, 0.7),   # Buraco grande
        (400, 150, 25, 0.6),   # Buraco médio
        (320, 350, 30, 0.8),   # Buraco médio-grande
        (500, 300, 20, 0.5),   # Buraco pequeno
        (200, 400, 35, 0.65),  # Buraco médio
    ]

    for cx, cy, radius, depth in potholes:
        # Criar máscara circular para o buraco
        y, x = np.ogrid[:height, :width]
        mask = ((x - cx)**2 + (y - cy)**2) <= radius**2

        # Escurecer área do buraco (simular profundidade)
        darkening = int(depth * 60)
        image[mask] = np.clip(image[mask].astype(np.int16) - darkening, 0, 255).astype(np.uint8)

        # Adicionar borda irregular (erosão)
        edge_mask = cv2.circle(np.zeros((height, width), dtype=np.uint8),
                               (cx, cy), radius + 5, 255, 2)
        edge_mask = edge_mask > 0
        image[edge_mask] = np.clip(image[edge_mask].astype(np.int16) - 30, 0, 255).astype(np.uint8)

        # Adicionar sombra característica
        shadow_offset = 3
        shadow_cx = cx - shadow_offset
        shadow_cy = cy - shadow_offset
        shadow_mask = ((x - shadow_cx)**2 + (y - shadow_cy)**2) <= (radius * 0.6)**2
        image[shadow_mask] = np.clip(image[shadow_mask].astype(np.int16) - 40, 0, 255).astype(np.uint8)

    # Salvar imagem
    output_dir = Path(output_path).parent
    output_dir.mkdir(exist_ok=True)
    cv2.imwrite(output_path, image)

    print(f"✅ Imagem sintética criada: {output_path}")
    print(f"   Buracos simulados: {len(potholes)}")

    return output_path


def test_single_method(detector: PotholeDetector, image_path: str, method: str):
    """Testa um único método de detecção."""
    print(f"\n{'='*60}")
    print(f"🔍 TESTANDO MÉTODO: {method.upper()}")
    print(f"{'='*60}")

    try:
        result = detector.detect_image(image_path, method=method)

        print(f"\n📊 Resultados:")
        print(f"   Buracos detectados: {result['num_potholes']}")
        print(f"   Área total: {result['total_area']:.0f} pixels")
        print(f"   Cobertura: {result['coverage']:.2f}%")
        print(f"   Confiança: {result['confidence']:.2f}")
        print(f"   Nível: {result['confidence_level']}")

        if result['flags']:
            print(f"   ⚠️  Flags: {', '.join(result['flags'])}")

        # Mostrar detalhes dos buracos detectados
        if result['potholes']:
            print(f"\n   Detalhes dos {min(5, len(result['potholes']))} maiores buracos:")
            sorted_potholes = sorted(result['potholes'],
                                   key=lambda x: x['area'],
                                   reverse=True)

            for i, pothole in enumerate(sorted_potholes[:5], 1):
                x, y, w, h = pothole['bounding_box']
                print(f"   {i}. Centro: {pothole['center']}, "
                      f"Tamanho: {w}x{h}, "
                      f"Área: {pothole['area']:.0f}px, "
                      f"Confiança: {pothole['confidence_score']:.2f}")

        # Criar visualização
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"test_pothole_{method}_{Path(image_path).stem}.jpg"

        detector.visualize_detections(image_path, result, str(output_path))
        print(f"\n   💾 Visualização salva: {output_path}")

        return result

    except Exception as e:
        print(f"❌ Erro ao testar método {method}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_all_methods(detector: PotholeDetector, image_path: str):
    """Testa todos os métodos disponíveis."""
    print(f"\n{'='*60}")
    print(f"🔬 TESTANDO TODOS OS MÉTODOS")
    print(f"{'='*60}")
    print(f"Imagem: {image_path}\n")

    methods = ['contour', 'texture', 'shadow', 'combined']
    results = {}

    for method in methods:
        result = test_single_method(detector, image_path, method)
        if result:
            results[method] = result

    # Comparação final
    if results:
        print(f"\n{'='*60}")
        print(f"📊 COMPARAÇÃO DE MÉTODOS")
        print(f"{'='*60}\n")

        print(f"{'Método':<12} {'Buracos':<10} {'Área':<12} {'Cobertura':<12} {'Confiança':<12} {'Nível':<10}")
        print('-' * 70)

        for method, result in results.items():
            print(f"{method:<12} "
                  f"{result['num_potholes']:<10} "
                  f"{result['total_area']:<12.0f} "
                  f"{result['coverage']:<12.2f} "
                  f"{result['confidence']:<12.2f} "
                  f"{result['confidence_level']:<10}")

        print(f"\n{'='*60}")

        # Melhor método
        best_method = max(results.items(), key=lambda x: x[1]['confidence'])
        print(f"💡 Melhor método (por confiança): {best_method[0].upper()}")
        print(f"   Confiança: {best_method[1]['confidence']:.2f}")
        print(f"   Buracos detectados: {best_method[1]['num_potholes']}")

        # Método mais conservador (menos detecções)
        conservative = min(results.items(), key=lambda x: x[1]['num_potholes'])
        print(f"\n🎯 Método mais conservador: {conservative[0].upper()}")
        print(f"   Buracos: {conservative[1]['num_potholes']}")

        # Método mais liberal (mais detecções)
        liberal = max(results.items(), key=lambda x: x[1]['num_potholes'])
        print(f"\n📢 Método mais liberal: {liberal[0].upper()}")
        print(f"   Buracos: {liberal[1]['num_potholes']}")


def test_with_real_images():
    """Testa com imagens reais se disponíveis."""
    print(f"\n{'='*60}")
    print(f"📷 PROCURANDO IMAGENS REAIS PARA TESTE")
    print(f"{'='*60}\n")

    examples_dir = Path('examples')

    # Procurar imagens de exemplo
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
    real_images = []

    for ext in image_extensions:
        real_images.extend(examples_dir.glob(ext))

    if real_images:
        print(f"✅ Encontradas {len(real_images)} imagens:")
        for img in real_images:
            print(f"   - {img.name}")

        # Testar com a primeira imagem
        print(f"\n🔍 Testando com: {real_images[0].name}")

        detector = PotholeDetector()
        test_all_methods(detector, str(real_images[0]))
    else:
        print("⚠️  Nenhuma imagem real encontrada em examples/")
        print("💡 Dica: Adicione imagens de estradas com buracos em examples/")


def demo_custom_config():
    """Demonstra uso de configuração personalizada."""
    print(f"\n{'='*60}")
    print(f"⚙️  TESTE COM CONFIGURAÇÃO PERSONALIZADA")
    print(f"{'='*60}\n")

    # Configuração mais sensível (detecta buracos menores)
    sensitive_config = {
        'contour': {
            'min_area': 200,  # Menor que padrão (500)
            'max_area': 100000,
            'min_circularity': 0.2,  # Mais tolerante
            'max_circularity': 1.0,
        },
        'confidence': {
            'min_confidence': 0.4,  # Aceita confiança menor
        }
    }

    print("Configuração sensível (detecta mais buracos):")
    print(f"  - Área mínima: {sensitive_config['contour']['min_area']} pixels")
    print(f"  - Circularidade: {sensitive_config['contour']['min_circularity']}-{sensitive_config['contour']['max_circularity']}")

    detector = PotholeDetector(config=sensitive_config)

    # Criar imagem sintética
    image_path = create_synthetic_pothole_image()

    # Testar
    result = detector.detect_image(image_path, method='combined')

    print(f"\n📊 Resultado com configuração sensível:")
    print(f"   Buracos detectados: {result['num_potholes']}")
    print(f"   Confiança: {result['confidence']:.2f}")


def main():
    """Função principal de teste."""
    print("\n" + "="*60)
    print("🕳️  SISTEMA DE TESTE - DETECÇÃO DE BURACOS")
    print("="*60)

    # Criar detector
    detector = PotholeDetector()

    # Menu de testes
    print("\n📋 Opções de teste:")
    print("1. Gerar imagem sintética e testar")
    print("2. Testar com imagem específica")
    print("3. Testar todos os métodos (imagem sintética)")
    print("4. Testar com imagens reais em examples/")
    print("5. Demonstração de configuração personalizada")
    print("6. Executar todos os testes")

    choice = input("\nEscolha uma opção (1-6): ").strip()

    if choice == '1':
        image_path = create_synthetic_pothole_image()
        method = input("Método (contour/texture/shadow/combined): ").strip() or 'combined'
        test_single_method(detector, image_path, method)

    elif choice == '2':
        image_path = input("Caminho da imagem: ").strip().strip('"')
        if Path(image_path).exists():
            method = input("Método (contour/texture/shadow/combined): ").strip() or 'combined'
            test_single_method(detector, image_path, method)
        else:
            print(f"❌ Imagem não encontrada: {image_path}")

    elif choice == '3':
        image_path = create_synthetic_pothole_image()
        test_all_methods(detector, image_path)

    elif choice == '4':
        test_with_real_images()

    elif choice == '5':
        demo_custom_config()

    elif choice == '6':
        print("\n🚀 Executando todos os testes...\n")

        # 1. Teste com imagem sintética
        print("\n" + "="*60)
        print("TESTE 1: Imagem Sintética")
        print("="*60)
        image_path = create_synthetic_pothole_image()
        test_all_methods(detector, image_path)

        # 2. Teste com configuração personalizada
        demo_custom_config()

        # 3. Teste com imagens reais
        test_with_real_images()

        print("\n" + "="*60)
        print("✅ TODOS OS TESTES CONCLUÍDOS!")
        print("="*60)
        print("\n💾 Verifique os resultados no diretório 'output/'")

    else:
        print("❌ Opção inválida")


if __name__ == "__main__":
    main()
