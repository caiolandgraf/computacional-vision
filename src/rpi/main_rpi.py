"""
Sistema de Detecção Otimizado para Raspberry Pi 4
Sistema simplificado com GPS, detecção e upload automático para API
"""

import argparse
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
from api_client import APIClient

# Importa módulos locais
from gps_handler import GPSHandler, create_gps_handler
from network_monitor import NetworkMonitor
from simple_detector import SimpleDetector

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('detection_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DetectionSystemRPi:
    """
    Sistema de detecção simplificado para Raspberry Pi
    Captura -> Detecta -> Envia para API -> Deleta
    """

    def __init__(self, config: dict):
        """
        Inicializa o sistema

        Args:
            config: Dicionário de configuração
        """
        self.config = config
        self.running = False

        # Inicializa componentes
        logger.info("=" * 60)
        logger.info("🚀 Inicializando Sistema de Detecção - Raspberry Pi")
        logger.info("=" * 60)

        # GPS Handler
        gps_config = config.get('gps', {})
        self.gps = create_gps_handler(gps_config)
        logger.info("✓ GPS Handler inicializado")

        # Detector
        detector_config = config.get('detector', {})
        self.detector = SimpleDetector(
            detection_type=detector_config.get('type', 'pothole'),
            min_confidence=detector_config.get('min_confidence', 0.5),
            resize_width=detector_config.get('resize_width', 640)
        )
        logger.info("✓ Detector inicializado")

        # API Client
        api_config = config.get('api', {})
        self.api_client = APIClient(
            api_url=api_config['url'],
            api_key=api_config.get('key'),
            queue_dir=api_config.get('queue_dir', 'queue'),
            max_retries=api_config.get('max_retries', 3),
            timeout=api_config.get('timeout', 30.0),
            auto_process=True
        )
        logger.info("✓ API Client inicializado")

        # Câmera
        camera_config = config.get('camera', {})
        self.camera_index = camera_config.get('index', 0)
        self.camera_width = camera_config.get('width', 1280)
        self.camera_height = camera_config.get('height', 720)
        self.camera = None

        # Diretórios
        self.capture_dir = Path(config.get('capture_dir', 'captures'))
        self.capture_dir.mkdir(parents=True, exist_ok=True)

        # Configurações de captura
        self.capture_interval = config.get('capture_interval', 5.0)
        self.save_annotated = config.get('save_annotated', False)

        # Estatísticas
        self.stats = {
            'captures': 0,
            'detections': 0,
            'uploads': 0,
            'errors': 0
        }

        logger.info("=" * 60)
        logger.info("✅ Sistema inicializado com sucesso!")
        logger.info("=" * 60)

    def init_camera(self) -> bool:
        """
        Inicializa câmera

        Returns:
            True se inicializou com sucesso
        """
        try:
            logger.info(f"Inicializando câmera {self.camera_index}...")
            self.camera = cv2.VideoCapture(self.camera_index)

            if not self.camera.isOpened():
                logger.error("Não foi possível abrir câmera")
                return False

            # Configura resolução
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)

            # Testa captura
            ret, frame = self.camera.read()
            if not ret or frame is None:
                logger.error("Não foi possível capturar frame de teste")
                return False

            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            logger.info(f"✓ Câmera inicializada: {actual_width}x{actual_height}")

            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar câmera: {e}")
            return False

    def capture_image(self) -> Optional[str]:
        """
        Captura imagem da câmera

        Returns:
            Caminho da imagem capturada ou None
        """
        try:
            if self.camera is None or not self.camera.isOpened():
                logger.error("Câmera não está inicializada")
                return None

            # Captura frame
            ret, frame = self.camera.read()
            if not ret or frame is None:
                logger.error("Erro ao capturar frame")
                return None

            # Gera nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
            filepath = self.capture_dir / filename

            # Salva imagem com compressão otimizada
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            success = cv2.imwrite(str(filepath), frame, encode_param)

            if not success:
                logger.error("Erro ao salvar imagem")
                return None

            self.stats['captures'] += 1
            logger.info(f"📷 Imagem capturada: {filename}")

            return str(filepath)

        except Exception as e:
            logger.error(f"Erro ao capturar imagem: {e}")
            return None

    def process_image(self, image_path: str):
        """
        Processa imagem: detecta e envia para API

        Args:
            image_path: Caminho da imagem
        """
        try:
            logger.info(f"🔍 Processando: {os.path.basename(image_path)}")

            # Obtém coordenadas GPS
            coordinates = self.gps.get_coordinates()
            if coordinates is None or not coordinates.is_valid():
                logger.warning("⚠️  Sem coordenadas GPS válidas - usando última conhecida")
                coordinates = self.gps.get_last_known_coordinates()

            if coordinates is None:
                logger.error("❌ Sem coordenadas GPS disponíveis - pulando imagem")
                self.stats['errors'] += 1
                # Remove imagem não processada
                if os.path.exists(image_path):
                    os.remove(image_path)
                return

            # Detecta
            detected, confidence, annotated = self.detector.detect(image_path)

            if detected:
                self.stats['detections'] += 1
                logger.info(
                    f"✅ Detecção positiva! "
                    f"Confiança: {confidence:.2f} | "
                    f"GPS: ({coordinates.latitude:.6f}, {coordinates.longitude:.6f})"
                )

                # Salva imagem anotada se configurado
                if self.save_annotated and annotated is not None:
                    annotated_path = self.capture_dir / f"annotated_{os.path.basename(image_path)}"
                    self.detector.save_annotated_image(annotated, str(annotated_path))

                # Adiciona à fila de upload
                success = self.api_client.add_detection(
                    image_path=image_path,
                    coordinates=coordinates,
                    confidence=confidence,
                    detection_type=self.detector.detection_type
                )

                if success:
                    logger.info("📤 Adicionado à fila de upload")
                else:
                    logger.error("❌ Erro ao adicionar à fila")
                    self.stats['errors'] += 1

            else:
                logger.info(f"⚪ Sem detecção (confiança: {confidence:.2f})")
                # Remove imagem sem detecção
                if os.path.exists(image_path):
                    os.remove(image_path)
                    logger.debug(f"🗑️  Imagem removida: {os.path.basename(image_path)}")

        except Exception as e:
            logger.error(f"Erro ao processar imagem: {e}")
            self.stats['errors'] += 1

    def run_continuous(self):
        """
        Executa captura e processamento contínuo
        """
        logger.info("\n" + "=" * 60)
        logger.info("🎬 Iniciando modo contínuo")
        logger.info(f"⏱️  Intervalo de captura: {self.capture_interval}s")
        logger.info(f"🎯 Tipo de detecção: {self.detector.detection_type}")
        logger.info("=" * 60 + "\n")

        # Inicializa câmera
        if not self.init_camera():
            logger.error("❌ Falha ao inicializar câmera - abortando")
            return

        # Aguarda fix GPS inicial
        logger.info("📡 Aguardando fix GPS...")
        if not self.gps.wait_for_fix(timeout=60):
            logger.warning("⚠️  Sem fix GPS - continuando mesmo assim")

        self.running = True
        last_capture_time = 0

        try:
            while self.running:
                current_time = time.time()

                # Verifica se é hora de capturar
                if (current_time - last_capture_time) >= self.capture_interval:
                    # Captura imagem
                    image_path = self.capture_image()

                    if image_path:
                        # Processa imagem
                        self.process_image(image_path)

                    last_capture_time = current_time

                    # Exibe estatísticas
                    self._print_stats()

                # Pequena pausa para não sobrecarregar CPU
                time.sleep(0.5)

        except KeyboardInterrupt:
            logger.info("\n⏹️  Interrupção recebida - encerrando...")
        finally:
            self.cleanup()

    def run_single(self, image_path: str):
        """
        Processa uma única imagem

        Args:
            image_path: Caminho da imagem
        """
        logger.info("\n" + "=" * 60)
        logger.info("📸 Modo imagem única")
        logger.info("=" * 60 + "\n")

        if not os.path.exists(image_path):
            logger.error(f"❌ Imagem não encontrada: {image_path}")
            return

        # Aguarda fix GPS
        logger.info("📡 Aguardando fix GPS...")
        if not self.gps.wait_for_fix(timeout=30):
            logger.warning("⚠️  Sem fix GPS - continuando mesmo assim")

        # Processa
        self.process_image(image_path)

        # Exibe estatísticas
        self._print_stats()

        # Aguarda processamento da fila
        logger.info("\n⏳ Aguardando processamento da fila...")
        time.sleep(5)

        # Processa fila manualmente
        processed = self.api_client.process_queue()
        logger.info(f"✓ {processed} itens processados")

        self.cleanup()

    def _print_stats(self):
        """Exibe estatísticas"""
        api_stats = self.api_client.get_stats()

        logger.info("\n" + "-" * 60)
        logger.info("📊 ESTATÍSTICAS")
        logger.info("-" * 60)
        logger.info(f"  📷 Capturas: {self.stats['captures']}")
        logger.info(f"  🎯 Detecções: {self.stats['detections']}")
        logger.info(f"  📤 Enviados: {api_stats['total_sent']}")
        logger.info(f"  📋 Na fila: {api_stats['queue_size']}")
        logger.info(f"  ❌ Erros: {self.stats['errors']}")
        logger.info(f"  🌐 Conexão: {'✓' if api_stats['connected'] else '✗'}")
        logger.info("-" * 60 + "\n")

    def cleanup(self):
        """Limpeza de recursos"""
        logger.info("\n🧹 Limpando recursos...")

        self.running = False

        # Fecha câmera
        if self.camera is not None:
            self.camera.release()
            logger.info("✓ Câmera liberada")

        # Fecha GPS
        self.gps.close()
        logger.info("✓ GPS fechado")

        # Para API client
        self.api_client.stop_auto_processing()
        logger.info("✓ API client parado")

        logger.info("\n✅ Sistema encerrado")


def load_config(config_file: str) -> dict:
    """
    Carrega configuração do arquivo JSON

    Args:
        config_file: Caminho do arquivo de configuração

    Returns:
        Dicionário de configuração
    """
    import json

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        logger.info(f"✓ Configuração carregada: {config_file}")
        return config
    except Exception as e:
        logger.error(f"❌ Erro ao carregar configuração: {e}")
        sys.exit(1)


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Sistema de Detecção Otimizado para Raspberry Pi'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config_rpi.json',
        help='Arquivo de configuração JSON'
    )

    parser.add_argument(
        '--mode',
        type=str,
        choices=['continuous', 'single'],
        default='continuous',
        help='Modo de operação: continuous (contínuo) ou single (imagem única)'
    )

    parser.add_argument(
        '--image',
        type=str,
        help='Caminho da imagem (para modo single)'
    )

    args = parser.parse_args()

    # Carrega configuração
    config = load_config(args.config)

    # Cria sistema
    system = DetectionSystemRPi(config)

    # Handler para sinais de interrupção
    def signal_handler(sig, frame):
        logger.info("\n⚠️  Sinal de interrupção recebido")
        system.running = False
        system.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Executa
    if args.mode == 'continuous':
        system.run_continuous()
    elif args.mode == 'single':
        if not args.image:
            logger.error("❌ --image é obrigatório no modo single")
            sys.exit(1)
        system.run_single(args.image)


if __name__ == '__main__':
    main()
