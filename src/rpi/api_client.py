"""
API Client - Cliente otimizado com sistema de fila offline
Envia dados (GPS + confiabilidade + imagem) para API com retry automático
"""

import json
import logging
import os
import pickle
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from queue import PriorityQueue
from threading import Event, Lock, Thread
from typing import Any, Dict, Optional

import requests

from .gps_handler import GPSCoordinates
from .network_monitor import NetworkMonitor

logger = logging.getLogger(__name__)


@dataclass
class DetectionData:
    """Estrutura de dados para detecção"""
    image_path: str
    latitude: float
    longitude: float
    confidence: float
    timestamp: float
    altitude: Optional[float] = None
    detection_type: str = 'pothole'  # 'pothole' ou 'grass'
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'altitude': self.altitude,
            'detection_type': self.detection_type
        }


class APIClient:
    """
    Cliente API com sistema de fila offline e retry automático
    Otimizado para Raspberry Pi com conexão intermitente
    """

    def __init__(
        self,
        api_url: str,
        api_key: Optional[str] = None,
        queue_dir: str = 'queue',
        max_retries: int = 3,
        retry_delay: float = 5.0,
        timeout: float = 30.0,
        auto_process: bool = True
    ):
        """
        Inicializa o cliente API

        Args:
            api_url: URL base da API
            api_key: Chave de API (se necessário)
            queue_dir: Diretório para fila offline
            max_retries: Número máximo de tentativas
            retry_delay: Delay entre tentativas em segundos
            timeout: Timeout para requests HTTP
            auto_process: Processar fila automaticamente quando houver conexão
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Fila de prioridade (timestamp = prioridade)
        self._queue: PriorityQueue = PriorityQueue()
        self._queue_dir = Path(queue_dir)
        self._queue_dir.mkdir(parents=True, exist_ok=True)

        self._lock = Lock()
        self._processing = False
        self._stop_event = Event()
        self._worker_thread: Optional[Thread] = None

        # Monitor de rede
        self.network_monitor = NetworkMonitor(check_interval=10.0)

        # Estatísticas
        self.stats = {
            'total_sent': 0,
            'total_failed': 0,
            'total_queued': 0,
            'images_deleted': 0
        }

        # Carrega fila persistida
        self._load_queue()

        # Inicia processamento automático
        if auto_process:
            self.start_auto_processing()

        logger.info(f"API Client inicializado: {self.api_url}")

    def add_detection(
        self,
        image_path: str,
        coordinates: GPSCoordinates,
        confidence: float,
        detection_type: str = 'pothole'
    ) -> bool:
        """
        Adiciona detecção à fila para envio

        Args:
            image_path: Caminho da imagem
            coordinates: Coordenadas GPS
            confidence: Confiabilidade da detecção (0.0 - 1.0)
            detection_type: Tipo de detecção ('pothole' ou 'grass')

        Returns:
            True se adicionou com sucesso
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"Imagem não encontrada: {image_path}")
                return False

            data = DetectionData(
                image_path=image_path,
                latitude=coordinates.latitude,
                longitude=coordinates.longitude,
                confidence=confidence,
                timestamp=time.time(),
                altitude=coordinates.altitude,
                detection_type=detection_type
            )

            # Adiciona à fila (prioridade = timestamp negativo para FIFO)
            self._queue.put((-data.timestamp, data))
            self.stats['total_queued'] += 1

            # Persiste fila
            self._save_queue()

            logger.info(
                f"Detecção adicionada à fila: {detection_type} "
                f"({coordinates.latitude:.6f}, {coordinates.longitude:.6f}) "
                f"conf={confidence:.2f}"
            )

            return True

        except Exception as e:
            logger.error(f"Erro ao adicionar detecção à fila: {e}")
            return False

    def send_detection(self, data: DetectionData) -> bool:
        """
        Envia detecção para API

        Args:
            data: Dados da detecção

        Returns:
            True se enviou com sucesso (status 200)
        """
        try:
            # Verifica se tem conexão
            if not self.network_monitor.is_connected(force_check=True):
                logger.warning("Sem conexão - detecção permanecerá na fila")
                return False

            # Verifica se imagem existe
            if not os.path.exists(data.image_path):
                logger.error(f"Imagem não encontrada: {data.image_path}")
                return False

            # Prepara headers
            headers = {}
            if self.api_key:
                headers['Authorization'] = f"Bearer {self.api_key}"

            # Prepara dados do formulário
            form_data = data.to_dict()

            # Prepara arquivo de imagem
            with open(data.image_path, 'rb') as img_file:
                files = {
                    'image': (
                        os.path.basename(data.image_path),
                        img_file,
                        'image/jpeg'
                    )
                }

                # Envia POST request
                response = requests.post(
                    f"{self.api_url}/detections",
                    data=form_data,
                    files=files,
                    headers=headers,
                    timeout=self.timeout
                )

            # Verifica resposta
            if response.status_code == 200:
                logger.info(
                    f"✅ Detecção enviada com sucesso: {data.image_path} "
                    f"(tentativa {data.retry_count + 1})"
                )

                # Deleta imagem após sucesso
                self._delete_image(data.image_path)

                self.stats['total_sent'] += 1
                return True

            else:
                logger.warning(
                    f"❌ Falha ao enviar detecção: HTTP {response.status_code} "
                    f"- {response.text[:100]}"
                )
                return False

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout ao enviar detecção: {data.image_path}")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning(f"Erro de conexão ao enviar: {data.image_path}")
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar detecção: {e}")
            return False

    def _delete_image(self, image_path: str):
        """
        Deleta imagem após envio bem-sucedido

        Args:
            image_path: Caminho da imagem
        """
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                self.stats['images_deleted'] += 1
                logger.info(f"🗑️  Imagem deletada: {image_path}")
        except Exception as e:
            logger.error(f"Erro ao deletar imagem {image_path}: {e}")

    def process_queue(self, max_items: Optional[int] = None) -> int:
        """
        Processa fila de detecções pendentes

        Args:
            max_items: Máximo de itens a processar (None = todos)

        Returns:
            Número de itens processados com sucesso
        """
        if self._processing:
            logger.warning("Fila já está sendo processada")
            return 0

        self._processing = True
        processed = 0
        failed_items = []

        try:
            items_to_process = max_items or self._queue.qsize()

            for _ in range(min(items_to_process, self._queue.qsize())):
                if self._stop_event.is_set():
                    break

                try:
                    priority, data = self._queue.get_nowait()
                except:
                    break

                # Tenta enviar
                success = self.send_detection(data)

                if success:
                    processed += 1
                else:
                    # Recoloca na fila se não excedeu max_retries
                    data.retry_count += 1
                    if data.retry_count < self.max_retries:
                        failed_items.append((priority, data))
                        logger.info(
                            f"Recolocando na fila (tentativa {data.retry_count + 1}/"
                            f"{self.max_retries}): {data.image_path}"
                        )
                    else:
                        logger.error(
                            f"Descartando após {self.max_retries} tentativas: "
                            f"{data.image_path}"
                        )
                        self.stats['total_failed'] += 1

                # Delay entre envios
                if not success:
                    time.sleep(self.retry_delay)

            # Recoloca itens que falharam
            for item in failed_items:
                self._queue.put(item)

            # Persiste fila atualizada
            self._save_queue()

            logger.info(
                f"Processamento concluído: {processed} enviados, "
                f"{len(failed_items)} pendentes"
            )

        finally:
            self._processing = False

        return processed

    def start_auto_processing(self):
        """Inicia processamento automático da fila em background"""
        if self._worker_thread and self._worker_thread.is_alive():
            logger.warning("Worker já está rodando")
            return

        self._stop_event.clear()
        self._worker_thread = Thread(target=self._auto_process_loop, daemon=True)
        self._worker_thread.start()

        # Inicia monitoramento de rede
        self.network_monitor.start_monitoring()

        logger.info("Processamento automático iniciado")

    def stop_auto_processing(self):
        """Para processamento automático"""
        self._stop_event.set()

        if self._worker_thread:
            self._worker_thread.join(timeout=10)
            self._worker_thread = None

        self.network_monitor.stop_monitoring()

        logger.info("Processamento automático parado")

    def _auto_process_loop(self):
        """Loop de processamento automático"""
        while not self._stop_event.is_set():
            try:
                # Só processa se tiver itens na fila
                if not self._queue.empty():
                    # Aguarda conexão se necessário
                    if self.network_monitor.wait_for_connection(timeout=60):
                        self.process_queue(max_items=10)

                # Aguarda antes da próxima verificação
                self._stop_event.wait(30)

            except Exception as e:
                logger.error(f"Erro no loop de processamento: {e}")
                time.sleep(10)

    def _save_queue(self):
        """Persiste fila em disco"""
        try:
            queue_file = self._queue_dir / 'queue.pkl'

            # Converte fila para lista
            items = []
            temp_queue = PriorityQueue()

            while not self._queue.empty():
                try:
                    item = self._queue.get_nowait()
                    items.append(item)
                    temp_queue.put(item)
                except:
                    break

            # Restaura fila original
            self._queue = temp_queue

            # Salva em arquivo
            with open(queue_file, 'wb') as f:
                pickle.dump(items, f)

        except Exception as e:
            logger.error(f"Erro ao salvar fila: {e}")

    def _load_queue(self):
        """Carrega fila persistida do disco"""
        try:
            queue_file = self._queue_dir / 'queue.pkl'

            if not queue_file.exists():
                return

            with open(queue_file, 'rb') as f:
                items = pickle.load(f)

            for item in items:
                self._queue.put(item)

            logger.info(f"Fila carregada: {len(items)} itens")

        except Exception as e:
            logger.error(f"Erro ao carregar fila: {e}")

    def get_queue_size(self) -> int:
        """Retorna tamanho da fila"""
        return self._queue.qsize()

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas"""
        return {
            **self.stats,
            'queue_size': self.get_queue_size(),
            'processing': self._processing,
            'connected': self.network_monitor.is_connected()
        }

    def clear_queue(self):
        """Limpa toda a fila (USE COM CUIDADO!)"""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except:
                break

        self._save_queue()
        logger.warning("Fila limpa!")

    def __enter__(self):
        """Context manager enter"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_auto_processing()
        self._save_queue()
        return False
