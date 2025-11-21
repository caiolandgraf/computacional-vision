#!/usr/bin/env python3
"""
Script de Teste Rápido - Raspberry Pi
Valida instalação e componentes do sistema
"""

import os
import sys


def print_header(text):
    """Print com cabeçalho"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_success(text):
    """Print sucesso"""
    print(f"✓ {text}")

def print_error(text):
    """Print erro"""
    print(f"✗ {text}")

def print_warning(text):
    """Print aviso"""
    print(f"⚠ {text}")

def test_python_version():
    """Testa versão do Python"""
    print_header("TESTANDO PYTHON")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print(f"Versão Python: {version_str}")

    if version.major >= 3 and version.minor >= 8:
        print_success("Versão Python OK (>= 3.8)")
        return True
    else:
        print_error("Python 3.8+ necessário")
        return False

def test_imports():
    """Testa imports dos módulos"""
    print_header("TESTANDO MÓDULOS PYTHON")

    modules = {
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'requests': 'Requests',
        'PIL': 'Pillow'
    }

    all_ok = True

    for module, name in modules.items():
        try:
            mod = __import__(module)
            version = getattr(mod, '__version__', 'N/A')
            print_success(f"{name}: {version}")
        except ImportError:
            print_error(f"{name} não encontrado")
            all_ok = False

    return all_ok

def test_gps_modules():
    """Testa módulos GPS"""
    print_header("TESTANDO MÓDULOS GPS")

    gps_ok = False
    serial_ok = False

    # Testa gps/gps3
    try:
        import gps
        print_success("Módulo 'gps' encontrado")
        gps_ok = True
    except ImportError:
        try:
            import gps3
            print_success("Módulo 'gps3' encontrado")
            gps_ok = True
        except ImportError:
            print_warning("Nenhum módulo GPS encontrado (gps/gps3)")

    # Testa pyserial
    try:
        import serial
        print_success(f"Módulo 'pyserial' encontrado: {serial.__version__}")
        serial_ok = True
    except ImportError:
        print_warning("Módulo 'pyserial' não encontrado")

    if not gps_ok and not serial_ok:
        print_warning("Nenhum backend GPS disponível - apenas modo MOCK funcionará")

    return True  # GPS é opcional

def test_rpi_modules():
    """Testa módulos customizados do RPi"""
    print_header("TESTANDO MÓDULOS CUSTOMIZADOS")

    # Adiciona src ao path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

    modules = [
        ('rpi.gps_handler', 'GPS Handler'),
        ('rpi.network_monitor', 'Network Monitor'),
        ('rpi.api_client', 'API Client'),
        ('rpi.simple_detector', 'Simple Detector')
    ]

    all_ok = True

    for module, name in modules:
        try:
            __import__(module)
            print_success(f"{name}")
        except ImportError as e:
            print_error(f"{name}: {e}")
            all_ok = False

    return all_ok

def test_camera():
    """Testa câmera"""
    print_header("TESTANDO CÂMERA")

    try:
        import cv2

        # Tenta abrir câmera
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print_error("Não foi possível abrir câmera")
            return False

        # Tenta capturar frame
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            print_error("Não foi possível capturar frame")
            return False

        height, width = frame.shape[:2]
        print_success(f"Câmera OK: {width}x{height}")
        return True

    except Exception as e:
        print_error(f"Erro ao testar câmera: {e}")
        return False

def test_gps_connection():
    """Testa conexão GPS"""
    print_header("TESTANDO GPS")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from rpi.gps_handler import GPSHandler

        # Tenta modo mock
        print("Testando GPS em modo MOCK...")
        gps = GPSHandler(backend='mock')
        coords = gps.get_coordinates()

        if coords and coords.is_valid():
            print_success(f"GPS Mock OK: ({coords.latitude:.6f}, {coords.longitude:.6f})")
            gps.close()
            return True
        else:
            print_error("GPS Mock falhou")
            return False

    except Exception as e:
        print_error(f"Erro ao testar GPS: {e}")
        return False

def test_network():
    """Testa conexão de rede"""
    print_header("TESTANDO CONEXÃO DE REDE")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from rpi.network_monitor import quick_check_connection

        if quick_check_connection(timeout=5):
            print_success("Conexão com internet OK")
            return True
        else:
            print_warning("Sem conexão com internet")
            return False

    except Exception as e:
        print_error(f"Erro ao testar rede: {e}")
        return False

def test_directories():
    """Testa estrutura de diretórios"""
    print_header("TESTANDO DIRETÓRIOS")

    dirs = ['captures', 'queue', 'logs', 'src/rpi']

    all_ok = True

    for dir_path in dirs:
        if os.path.exists(dir_path):
            print_success(f"Diretório '{dir_path}' existe")
        else:
            print_warning(f"Diretório '{dir_path}' não encontrado")
            all_ok = False

    return all_ok

def test_config():
    """Testa arquivo de configuração"""
    print_header("TESTANDO CONFIGURAÇÃO")

    config_file = 'config_rpi.json'

    if not os.path.exists(config_file):
        print_error(f"Arquivo '{config_file}' não encontrado")
        return False

    try:
        import json

        with open(config_file, 'r') as f:
            config = json.load(f)

        print_success(f"Arquivo '{config_file}' carregado")

        # Valida campos obrigatórios
        required = ['api', 'gps', 'detector', 'camera']

        for field in required:
            if field in config:
                print_success(f"Campo '{field}' presente")
            else:
                print_error(f"Campo '{field}' faltando")
                return False

        # Verifica URL da API
        if config['api'].get('url'):
            print_success(f"API URL: {config['api']['url']}")
        else:
            print_warning("API URL não configurada")

        return True

    except Exception as e:
        print_error(f"Erro ao ler configuração: {e}")
        return False

def test_detection():
    """Testa detecção com imagem de teste"""
    print_header("TESTANDO DETECÇÃO")

    try:
        import cv2
        import numpy as np
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from rpi.simple_detector import SimpleDetector

        # Cria imagem de teste
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        test_path = 'test_image.jpg'
        cv2.imwrite(test_path, test_image)

        # Testa detector
        detector = SimpleDetector(detection_type='pothole')
        detected, confidence, _ = detector.detect(test_path)

        # Remove imagem de teste
        if os.path.exists(test_path):
            os.remove(test_path)

        print_success(f"Detector OK (confiança: {confidence:.2f})")
        return True

    except Exception as e:
        print_error(f"Erro ao testar detecção: {e}")
        return False

def main():
    """Função principal"""
    print("\n" + "=" * 60)
    print("  🍓 TESTE DE INSTALAÇÃO - RASPBERRY PI")
    print("=" * 60)

    tests = [
        ("Versão Python", test_python_version),
        ("Módulos Básicos", test_imports),
        ("Módulos GPS", test_gps_modules),
        ("Módulos Customizados", test_rpi_modules),
        ("Diretórios", test_directories),
        ("Configuração", test_config),
        ("Câmera", test_camera),
        ("GPS", test_gps_connection),
        ("Rede", test_network),
        ("Detecção", test_detection)
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Erro no teste '{name}': {e}")
            results.append((name, False))

    # Sumário
    print_header("SUMÁRIO DOS TESTES")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} {name}")

    print("\n" + "-" * 60)
    print(f"Total: {passed}/{total} testes passaram")
    print("-" * 60)

    if passed == total:
        print("\n✅ TODOS OS TESTES PASSARAM!")
        print("Sistema pronto para uso.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TESTE(S) FALHARAM")
        print("Verifique os erros acima e corrija antes de usar.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
