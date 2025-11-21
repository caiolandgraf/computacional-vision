"""
Network Monitor - Módulo otimizado para monitoramento de conexão
Verifica conectividade com internet de forma eficiente para Raspberry Pi
"""

import logging
import socket
import time
from threading import Event, Lock, Thread
from typing import Callable, List, Optional

import requests

logger = logging.getLogger(__name__)


class NetworkMonitor:
    """
    Monitor de conexão de rede otimizado para Raspberry Pi
    Verifica conectividade e notifica callbacks quando o status muda
    """

    def __init__(
        self,
        check_interval: float = 10.0,
        timeout: float = 5.0,
        check_hosts: Optional[List[str]] = None
    ):
        """
        Inicializa o monitor de rede

        Args:
            check_interval: Intervalo entre verificações em segundos
            timeout: Timeout para cada verificação
            check_hosts: Lista de hosts para verificar conectividade
        """
        self.check_interval = check_interval
        self.timeout = timeout

        # Hosts padrão para verificação (rápidos e confiáveis)
        self.check_hosts = check_hosts or [
            ('8.8.8.8', 53),  # Google DNS
            ('1.1.1.1', 53),  # Cloudflare DNS
        ]

        self._is_connected = False
        self._last_check_time = 0
        self._running = False
        self._monitor_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._lock = Lock()

        # Callbacks
        self._on_connected_callbacks: List[Callable] = []
        self._on_disconnected_callbacks: List[Callable] = []

        logger.info("Network Monitor inicializado")

    def is_connected(self, force_check: bool = False) -> bool:
        """
        Verifica se há conexão com internet

        Args:
            force_check: Força nova verificação ignorando cache

        Returns:
            True se conectado, False caso contrário
        """
        with self._lock:
            # Usa cache se verificação foi recente
            if not force_check:
                time_since_check = time.time() - self._last_check_time
                if time_since_check < self.check_interval:
                    return self._is_connected

            # Realiza nova verificação
            connected = self._check_connectivity()

            # Notifica mudança de status
            if connected != self._is_connected:
                self._is_connected = connected
                self._notify_status_change(connected)
            else:
                self._is_connected = connected

            self._last_check_time = time.time()
            return self._is_connected

    def _check_connectivity(self) -> bool:
        """
        Verifica conectividade testando múltiplos hosts

        Returns:
            True se conseguiu conectar em pelo menos um host
        """
        for host, port in self.check_hosts:
            if self._check_host(host, port):
                return True
        return False

    def _check_host(self, host: str, port: int) -> bool:
        """
        Verifica conectividade com um host específico via socket

        Args:
            host: Endereço do host
            port: Porta

        Returns:
            True se conseguiu conectar
        """
        try:
            socket.setdefaulttimeout(self.timeout)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.close()
            return True
        except (socket.error, socket.timeout):
            return False
        except Exception as e:
            logger.debug(f"Erro ao verificar host {host}:{port}: {e}")
            return False

    def check_http_connectivity(self, url: str = "https://www.google.com") -> bool:
        """
        Verifica conectividade HTTP (útil para validar acesso completo à internet)

        Args:
            url: URL para testar

        Returns:
            True se conseguiu fazer request HTTP
        """
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={'User-Agent': 'NetworkMonitor/1.0'}
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
        except Exception as e:
            logger.debug(f"Erro ao verificar HTTP: {e}")
            return False

    def wait_for_connection(self, timeout: Optional[float] = None) -> bool:
        """
        Aguarda até haver conexão disponível

        Args:
            timeout: Timeout máximo em segundos (None = infinito)

        Returns:
            True se conseguiu conexão, False se deu timeout
        """
        logger.info("Aguardando conexão com internet...")
        start_time = time.time()

        while True:
            if self.is_connected(force_check=True):
                logger.info("Conexão com internet estabelecida!")
                return True

            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.warning(f"Timeout ao aguardar conexão ({timeout}s)")
                    return False

            time.sleep(2)

    def start_monitoring(self):
        """Inicia monitoramento contínuo em background"""
        if self._running:
            logger.warning("Monitor já está rodando")
            return

        self._running = True
        self._stop_event.clear()
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Monitoramento de rede iniciado")

    def stop_monitoring(self):
        """Para o monitoramento contínuo"""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
            self._monitor_thread = None

        logger.info("Monitoramento de rede parado")

    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        while self._running and not self._stop_event.is_set():
            try:
                self.is_connected(force_check=True)
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")

            # Aguarda próxima verificação
            self._stop_event.wait(self.check_interval)

    def on_connected(self, callback: Callable):
        """
        Registra callback para quando conectar

        Args:
            callback: Função a ser chamada quando conectar
        """
        if callback not in self._on_connected_callbacks:
            self._on_connected_callbacks.append(callback)

    def on_disconnected(self, callback: Callable):
        """
        Registra callback para quando desconectar

        Args:
            callback: Função a ser chamada quando desconectar
        """
        if callback not in self._on_disconnected_callbacks:
            self._on_disconnected_callbacks.append(callback)

    def _notify_status_change(self, connected: bool):
        """
        Notifica callbacks sobre mudança de status

        Args:
            connected: True se conectou, False se desconectou
        """
        callbacks = (
            self._on_connected_callbacks if connected
            else self._on_disconnected_callbacks
        )

        status_text = "conectado" if connected else "desconectado"
        logger.info(f"Status de rede mudou: {status_text}")

        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Erro ao executar callback de status: {e}")

    def get_connection_info(self) -> dict:
        """
        Retorna informações sobre a conexão

        Returns:
            Dicionário com informações de status
        """
        return {
            'connected': self._is_connected,
            'last_check': self._last_check_time,
            'monitoring': self._running,
            'check_interval': self.check_interval
        }

    def __enter__(self):
        """Context manager enter"""
        self.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_monitoring()
        return False


# Função helper para verificação rápida de conexão
def quick_check_connection(timeout: float = 3.0) -> bool:
    """
    Verificação rápida de conexão sem instanciar monitor

    Args:
        timeout: Timeout em segundos

    Returns:
        True se há conexão
    """
    try:
        socket.setdefaulttimeout(timeout)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('8.8.8.8', 53))
        sock.close()
        return True
    except (socket.error, socket.timeout):
        return False
    except Exception:
        return False
