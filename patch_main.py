#!/usr/bin/env python3
"""Script para adicionar funcionalidade de detecção combinada ao main.py"""

# Ler o arquivo atual
with open('src/main.py', 'r') as f:
    content = f.read()

# 1. Adicionar import do PotholeDetector se não existir
if 'from pothole_detector import PotholeDetector' not in content:
    import_line = "from visualizer import ResultVisualizer"
    new_import = "from visualizer import ResultVisualizer\nfrom pothole_detector import PotholeDetector"
    content = content.replace(import_line, new_import)
    print("✅ Import do PotholeDetector adicionado")

# 2. Adicionar pothole_detector no __init__ se não existir  
if 'self.pothole_detector' not in content:
    init_line = "self.detector = GrassDetector()"
    new_init = "self.detector = GrassDetector()\n        self.pothole_detector = PotholeDetector()"
    content = content.replace(init_line, new_init)
    print("✅ PotholeDetector adicionado ao __init__")

# 3. Adicionar opções no menu se não existirem
if '"12. Webcam - Mato + Buracos (tempo real)"' not in content:
    menu_old = '''        print("8. Ajuda")
        print("0. Sair")'''
    menu_new = '''        print("8. Ajuda")
        print("\n🕳️  DETECÇÃO DE BURACOS:")
        print("9. Analisar buracos em foto")
        print("10. Análise em lote de buracos")
        print("11. Comparar métodos (buracos)")
        print("\n🔄 DETECÇÃO COMBINADA:")
        print("12. Webcam - Mato + Buracos (tempo real)")
        print("\n⚙️  OPÇÕES:")
        print("0. Sair")'''
    content = content.replace(menu_old, menu_new)
    print("✅ Menu atualizado")

# 4. Adicionar chamadas no método run() se não existirem
if "'12':" not in content:
    run_section_old = '''                elif choice == '8':
                    self.show_help()
                elif choice == '0':'''
    run_section_new = '''                elif choice == '8':
                    self.show_help()
                elif choice == '9':
                    self.analyze_potholes_single()
                elif choice == '10':
                    self.analyze_potholes_batch()
                elif choice == '11':
                    self.compare_pothole_methods()
                elif choice == '12':
                    self.webcam_combined_realtime()
                elif choice == '0':'''
    content = content.replace(run_section_old, run_section_new)
    print("✅ Chamadas de métodos adicionadas ao run()")

# Salvar
with open('src/main.py', 'w') as f:
    f.write(content)

print("\n✅ Patch básico aplicado! Agora vamos adicionar os métodos...")
