#!/usr/bin/env python3
"""
Script para copiar imagens de output/ para training_data/ automaticamente
Organiza as imagens com base na análise da detecção existente
"""

import os
import shutil
import cv2
import numpy as np
from pathlib import Path
import json
from datetime import datetime

def analyze_image_vegetation(image_path):
    """
    Analisa se uma imagem contém vegetação ou não
    Baseado na quantidade de pixels verdes
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return None
    
    # Converter para HSV para detectar tons verdes
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Range para tons verdes (grama/vegetação)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([80, 255, 255])
    
    mask = cv2.inRange(hsv, lower_green, upper_green)
    green_percentage = (cv2.countNonZero(mask) / (img.shape[0] * img.shape[1])) * 100
    
    return green_percentage

def copy_to_training_data():
    """
    Copia imagens de output/ para training_data/ organizadamente
    """
    output_dir = Path("/Users/caiocampos/www/projects/visao-computacional/output")
    training_dir = Path("/Users/caiocampos/www/projects/visao-computacional/training_data")
    
    # Garantir que as pastas existem
    (training_dir / "vegetation").mkdir(parents=True, exist_ok=True)
    (training_dir / "non_vegetation").mkdir(parents=True, exist_ok=True)
    (training_dir / "ambiguous").mkdir(parents=True, exist_ok=True)
    
    # Contadores
    vegetation_count = 0
    non_vegetation_count = 0
    ambiguous_count = 0
    processed_count = 0
    
    # Estatísticas
    stats = {
        'processed': 0,
        'vegetation': 0,
        'non_vegetation': 0,
        'ambiguous': 0,
        'skipped': 0,
        'copied_at': datetime.now().isoformat()
    }
    
    print("🚀 Iniciando cópia organizada de imagens...")
    print(f"📁 Origem: {output_dir}")
    print(f"📁 Destino: {training_dir}")
    print()
    
    # Listar todas as imagens
    image_files = list(output_dir.glob("*.jpg"))
    total_files = len(image_files)
    
    print(f"📸 Encontradas {total_files} imagens para processar")
    print("🔍 Analisando vegetação em cada imagem...")
    print()
    
    # Processar cada imagem (máximo 200 para não sobrecarregar)
    max_images = min(200, total_files)
    
    for i, img_path in enumerate(image_files[:max_images]):
        if i % 20 == 0:  # Mostrar progresso a cada 20 imagens
            print(f"📊 Progresso: {i}/{max_images} ({i/max_images*100:.1f}%)")
        
        try:
            green_percentage = analyze_image_vegetation(img_path)
            
            if green_percentage is None:
                stats['skipped'] += 1
                continue
            
            # Categorizar com base na porcentagem de vegetação
            if green_percentage > 15:  # Muita vegetação
                dest_dir = training_dir / "vegetation"
                vegetation_count += 1
                category = "vegetation"
                stats['vegetation'] += 1
            elif green_percentage < 5:  # Pouca vegetação
                dest_dir = training_dir / "non_vegetation" 
                non_vegetation_count += 1
                category = "non_vegetation"
                stats['non_vegetation'] += 1
            else:  # Caso ambíguo (entre 5-15%)
                dest_dir = training_dir / "ambiguous"
                ambiguous_count += 1
                category = "ambiguous"
                stats['ambiguous'] += 1
            
            # Nome do arquivo de destino
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_filename = f"copied_{category}_{processed_count:04d}_{timestamp}.jpg"
            dest_path = dest_dir / dest_filename
            
            # Copiar arquivo
            shutil.copy2(img_path, dest_path)
            processed_count += 1
            stats['processed'] += 1
            
        except Exception as e:
            print(f"❌ Erro ao processar {img_path.name}: {e}")
            stats['skipped'] += 1
            continue
    
    print("\n✅ Cópia concluída!")
    print(f"📊 Estatísticas:")
    print(f"  🌱 Vegetação: {vegetation_count} imagens")
    print(f"  🏢 Não-vegetação: {non_vegetation_count} imagens") 
    print(f"  ❓ Ambíguos: {ambiguous_count} imagens")
    print(f"  📸 Total processado: {processed_count} imagens")
    print(f"  ⚠️  Ignoradas: {stats['skipped']} imagens")
    
    # Salvar estatísticas
    stats_file = training_dir / "copy_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\n📄 Estatísticas salvas em: {stats_file}")
    print(f"\n🎓 Agora execute: python src/training_system.py")
    
    return stats

if __name__ == "__main__":
    copy_to_training_data()