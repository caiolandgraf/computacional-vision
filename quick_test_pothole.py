#!/usr/bin/env python3
"""
Script de teste rápido para detecção de buracos.
Gera uma imagem sintética e testa o sistema.
"""

import sys
import os
from pathlib import Path

# Adiciona src ao path
sys.path.append(str(Path(__file__).parent / 'src'))

import cv2
import numpy as np


def create_test_image():
    """Cria uma imagem sintética com buracos para teste."""
    print("🎨 Gerando imagem de teste...")

    # Criar imagem de asfalto (800x600)
    width, height = 800, 600
    image = np.ones((height, width, 3), dtype=np.uint8) * 75  # Asfalto cinza

    # Adicionar textura realista
    noise = np.random.randint(-15, 15, (height, width, 3), dtype=np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    image = cv2.GaussianBlur(image, (3, 3), 0)

    # Criar 5 buracos de diferentes tamanhos
    potholes = [
        (200, 250, 50),   # x, y, raio
        (500, 200, 35),
        (350, 400, 45),
        (650, 350, 30),
        (150, 450, 40),
    ]

    for cx, cy, radius in potholes:
        # Criar máscara circular
        y, x = np.ogrid[:height, :width]
        mask = ((x - cx)**2 + (y - cy)**2) <= radius**2

        # Escurecer área (simular profundidade)
        image[mask] = np.clip(image[mask].astype(np.int16) - 50, 0, 255).astype(np.uint8)

        # Adicionar borda irregular
        edge_mask = cv2.circle(np.zeros((height, width), dtype=np.uint8),
                               (cx, cy), radius + 3, 255, 2)
        edge_mask = edge_mask > 0
        image[edge_mask] = np.clip(image[edge_mask].astype(np.int16) - 25, 0, 255).astype(np.uint8)

        # Adicionar sombra
        shadow_cx = cx - 2
        shadow_cy = cy - 2
        shadow_mask = ((x - shadow_cx)**2 + (y - shadow_cy)**2) <= (radius * 0.7)**2
        image[shadow_mask] = np.clip(image[shadow_mask].astype(np.int16) - 35, 0, 255).astype(np.uint8)

    # Salvar
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    test_image_path = output_dir / "test_pothole_synthetic.jpg"
    cv2.imwrite(str(test_image_path), image)

    print(f"✅ Imagem criada: {test_image_path}")
    print(f"   Dimensões: {width}x{height}")
    print(f"   Buracos simulados: {len(potholes)}")

    return str(test_image_path)


def test_detection(image_path):
    """Testa a detecção de buracos."""
    print(f"\n{'='*70}")
    print("🕳️  TESTE DE DETECÇÃO DE BURACOS")
    print(f"{'='*70}\n")

    try:
        from pothole_detector import PotholeDetector

        # Criar detector
        print("🔧 Inicializando detector...")
        detector = PotholeDetector()

        # Testar método combinado
        print(f"🔍 Analisando imagem com método: COMBINED")
        print(f"⏳ Aguarde...\n")

        result = detector.detect_image(image_path, method="combined")

        # Exibir resultados
        print(f"{'='*70}")
        print("📊 RESULTADOS DA DETECÇÃO")
        print(f"{'='*70}")
        print(f"🕳️  Buracos detectados: {result['num_potholes']}")
        print(f"📏 Área total: {result['total_area']:.0f} pixels")
        print(f"📊 Cobertura: {result['coverage']:.2f}%")
        print(f"🎯 Confiança: {result['confidence']:.2f}")
        print(f"📈 Nível: {result['confidence_level']}")

        if result['flags']:
            print(f"⚠️  Flags: {', '.join(result['flags'])}")

        # Mostrar detalhes dos buracos
        if result['potholes']:
            print(f"\n🔍 Detalhes dos buracos detectados:")
            print(f"{'-'*70}")

            for i, pothole in enumerate(result['potholes'][:5], 1):
                x, y, w, h = pothole['bounding_box']
                cx, cy = pothole['center']
                conf = pothole['confidence_score']
                area = pothole['area']

                print(f"  {i}. Centro: ({cx}, {cy}) | "
                      f"Tamanho: {w}x{h}px | "
                      f"Área: {area:.0f}px | "
                      f"Conf: {conf:.2f}")

            if len(result['potholes']) > 5:
                print(f"  ... e mais {len(result['potholes']) - 5} buracos")

        # Criar visualização
        print(f"\n💾 Gerando visualização...")
        output_path = Path("output") / "test_pothole_result.jpg"
        detector.visualize_detections(image_path, result, str(output_path))

        print(f"✅ Visualização salva: {output_path}")
        print(f"{'='*70}\n")

        # Interpretação dos resultados
        print("📝 INTERPRETAÇÃO:")
        if result['confidence'] >= 0.8:
            print("  🟢 Excelente! Detecção muito confiável.")
        elif result['confidence'] >= 0.6:
            print("  🟡 Bom! Detecção confiável, mas verifique manualmente.")
        elif result['confidence'] >= 0.4:
            print("  🟠 Regular. Recomenda-se revisão manual das detecções.")
        else:
            print("  🔴 Baixa confiança. Considere melhorar a qualidade da imagem.")

        if result['num_potholes'] == 0:
            print("  ℹ️  Nenhum buraco detectado. Isso pode indicar:")
            print("     - Via em boas condições")
            print("     - Imagem de baixa qualidade")
            print("     - Ajuste de parâmetros necessário")
        elif result['num_potholes'] > 15:
            print("  ⚠️  Muitos buracos detectados. Pode indicar:")
            print("     - Via em condições críticas")
            print("     - Falsos positivos devido à textura da superfície")
        else:
            print(f"  ✓ {result['num_potholes']} buracos detectados - quantidade razoável")

        print(f"\n{'='*70}")
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print(f"{'='*70}\n")

        print("💡 PRÓXIMOS PASSOS:")
        print("  1. Abra a imagem em: output/test_pothole_result.jpg")
        print("  2. Teste com suas próprias imagens usando:")
        print("     python3 src/pothole_detector.py sua_imagem.jpg")
        print("  3. Ou use o menu interativo:")
        print("     python3 src/main.py")
        print("     (Opções 9-11 para detecção de buracos)")

        return True

    except ImportError as e:
        print(f"❌ Erro ao importar módulo: {e}")
        print("\n💡 Certifique-se de que todas as dependências estão instaladas:")
        print("   pip install opencv-python numpy scikit-image scikit-learn scipy")
        return False

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal."""
    print("\n" + "="*70)
    print("🕳️  TESTE RÁPIDO - DETECÇÃO DE BURACOS")
    print("="*70)
    print("\nEste script irá:")
    print("  1. Gerar uma imagem sintética com 5 buracos")
    print("  2. Testar o sistema de detecção")
    print("  3. Criar uma visualização dos resultados")
    print("\n" + "="*70 + "\n")

    # Verificar se output existe
    output_dir = Path("output")
    if not output_dir.exists():
        print("📁 Criando diretório output/...")
        output_dir.mkdir(exist_ok=True)

    # Criar imagem de teste
    image_path = create_test_image()

    # Testar detecção
    success = test_detection(image_path)

    if success:
        print("\n🎉 Tudo funcionando perfeitamente!")
        print("\n📂 Arquivos gerados em: output/")
        print("   - test_pothole_synthetic.jpg (imagem de teste)")
        print("   - test_pothole_result.jpg (resultado da detecção)")
    else:
        print("\n😞 Houve problemas durante o teste.")
        print("Verifique as mensagens de erro acima.")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
