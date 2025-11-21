"""
GPS Handler - Módulo otimizado para captura de coordenadas GPS
Compatível com Raspberry Pi 4 + módulos GPS (UART/USB)
"""

import logging
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class GPSCoordinates:
    """Estrutura de dados para coordenadas GPS"""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    timestamp: float = None
    accuracy: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'timestamp': self.timestamp or time.time(),
            'accuracy': self.accuracy
        }

    def is_valid(self) -> bool:
        """Verifica se as coordenadas são válidas"""
        return (
            -90 <= self.latitude <= 90 and
            -180 <= self.longitude <= 180
        )


class GPSHandler:
    """
    Handler para GPS com suporte a múltiplos backends:
    - gpsd (recomendado para Raspberry Pi)
    - serial (GPS UART direto)
    - mock (para testes sem GPS)
    """

    def __init__(self, backend: str = 'gpsd', device: str = '/dev/ttyAMA0',
                 baudrate: int = 9600, timeout: float = 5.0):
        """
        Inicializa o handler GPS

        Args:
            backend: Tipo de backend ('gpsd', 'serial', 'mock')
            device: Dispositivo serial (para backend 'serial')
            baudrate: Baudrate da serial
            timeout: Timeout para obter coordenadas
        """
        self.backend = backend
        self.device = device
        self.baudrate = baudrate
        self.timeout = timeout
        self.lock = Lock()

        self._last_coordinates: Optional[GPSCoordinates] = None
        self._connection = None

        # Inicializa backend
        self._init_backend()

    def _init_backend(self):
        """Inicializa o backend GPS apropriado"""
        try:
            if self.backend == 'gpsd':
                self._init_gpsd()
            elif self.backend == 'serial':
                self._init_serial()
            elif self.backend == 'mock':
                self._init_mock()
            else:
                raise ValueError(f"Backend GPS inválido: {self.backend}")

            logger.info(f"GPS Handler inicializado com backend '{self.backend}'")

        except Exception as e:
            logger.error(f"Erro ao inicializar GPS: {e}")
            logger.warning("Usando modo MOCK como fallback")
            self.backend = 'mock'
            self._init_mock()

    def _init_gpsd(self):
        """Inicializa conexão com gpsd daemon"""
        try:
            import gps
            self._connection = gps.gps(mode=gps.WATCH_ENABLE)
            logger.info("Conectado ao gpsd daemon")
        except ImportError:
            raise ImportError(
                "Módulo 'gps' não encontrado. Instale com: pip install gps3 ou sudo apt-get install python3-gps"
            )
        except Exception as e:
            raise ConnectionError(f"Não foi possível conectar ao gpsd: {e}")

    def _init_serial(self):
        """Inicializa conexão serial direta com GPS"""
        try:
            import serial
            self._connection = serial.Serial(
                self.device,
                baudrate=self.baudrate,
                timeout=1
            )
            logger.info(f"Conexão serial aberta em {self.device}")
        except ImportError:
            raise ImportError(
                "Módulo 'serial' não encontrado. Instale com: pip install pyserial"
            )
        except Exception as e:
            raise ConnectionError(f"Erro ao abrir porta serial {self.device}: {e}")

    def _init_mock(self):
        """Inicializa GPS mock para testes"""
        # Coordenadas de exemplo (São Paulo, Brasil)
        self._mock_lat = -23.550520
        self._mock_lon = -46.633308
        logger.warning("GPS em modo MOCK - usando coordenadas fictícias")

    def get_coordinates(self) -> Optional[GPSCoordinates]:
        """
        Obtém coordenadas GPS atuais

        Returns:
            GPSCoordinates ou None se não conseguir obter
        """
        with self.lock:
            try:
                if self.backend == 'gpsd':
                    return self._get_gpsd_coordinates()
                elif self.backend == 'serial':
                    return self._get_serial_coordinates()
                elif self.backend == 'mock':
                    return self._get_mock_coordinates()
            except Exception as e:
                logger.error(f"Erro ao obter coordenadas GPS: {e}")
                return self._last_coordinates

    def _get_gpsd_coordinates(self) -> Optional[GPSCoordinates]:
        """Obtém coordenadas do gpsd"""
        import gps

        start_time = time.time()
        while (time.time() - start_time) < self.timeout:
            try:
                report = self._connection.next()

                if report['class'] == 'TPV':
                    if hasattr(report, 'lat') and hasattr(report, 'lon'):
                        coords = GPSCoordinates(
                            latitude=report.lat,
                            longitude=report.lon,
                            altitude=getattr(report, 'alt', None),
                            timestamp=getattr(report, 'time', time.time()),
                            accuracy=getattr(report, 'eph', None)
                        )

                        if coords.is_valid():
                            self._last_coordinates = coords
                            return coords

            except StopIteration:
                time.sleep(0.1)
            except Exception as e:
                logger.debug(f"Erro ao ler gpsd: {e}")
                time.sleep(0.1)

        logger.warning("Timeout ao obter coordenadas GPS")
        return None

    def _get_serial_coordinates(self) -> Optional[GPSCoordinates]:
        """Obtém coordenadas via serial (NMEA)"""
        start_time = time.time()

        while (time.time() - start_time) < self.timeout:
            try:
                line = self._connection.readline().decode('ascii', errors='ignore').strip()

                if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                    coords = self._parse_nmea_gga(line)
                    if coords and coords.is_valid():
                        self._last_coordinates = coords
                        return coords

            except Exception as e:
                logger.debug(f"Erro ao ler serial GPS: {e}")
                time.sleep(0.1)

        logger.warning("Timeout ao obter coordenadas GPS via serial")
        return None

    def _parse_nmea_gga(self, sentence: str) -> Optional[GPSCoordinates]:
        """Parse de sentença NMEA GGA"""
        try:
            parts = sentence.split(',')

            if len(parts) < 10:
                return None

            # Latitude
            lat_str = parts[2]
            lat_dir = parts[3]
            if lat_str and lat_dir:
                lat_deg = float(lat_str[:2])
                lat_min = float(lat_str[2:])
                latitude = lat_deg + (lat_min / 60.0)
                if lat_dir == 'S':
                    latitude = -latitude
            else:
                return None

            # Longitude
            lon_str = parts[4]
            lon_dir = parts[5]
            if lon_str and lon_dir:
                lon_deg = float(lon_str[:3])
                lon_min = float(lon_str[3:])
                longitude = lon_deg + (lon_min / 60.0)
                if lon_dir == 'W':
                    longitude = -longitude
            else:
                return None

            # Altitude
            altitude = None
            if parts[9]:
                try:
                    altitude = float(parts[9])
                except ValueError:
                    pass

            return GPSCoordinates(
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                timestamp=time.time()
            )

        except Exception as e:
            logger.debug(f"Erro ao parsear NMEA: {e}")
            return None

    def _get_mock_coordinates(self) -> GPSCoordinates:
        """Retorna coordenadas mock (para testes)"""
        # Adiciona pequena variação para simular movimento
        import random
        variation = 0.0001

        coords = GPSCoordinates(
            latitude=self._mock_lat + random.uniform(-variation, variation),
            longitude=self._mock_lon + random.uniform(-variation, variation),
            altitude=750.0,
            timestamp=time.time(),
            accuracy=5.0
        )

        self._last_coordinates = coords
        return coords

    def get_last_known_coordinates(self) -> Optional[GPSCoordinates]:
        """Retorna última coordenada conhecida (pode estar desatualizada)"""
        return self._last_coordinates

    def is_fix_available(self) -> bool:
        """Verifica se há fix GPS disponível"""
        coords = self.get_coordinates()
        return coords is not None and coords.is_valid()

    def wait_for_fix(self, timeout: float = 60.0) -> bool:
        """
        Aguarda por fix GPS

        Args:
            timeout: Tempo máximo de espera em segundos

        Returns:
            True se conseguiu fix, False caso contrário
        """
        logger.info("Aguardando fix GPS...")
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            if self.is_fix_available():
                logger.info("Fix GPS obtido!")
                return True
            time.sleep(1)

        logger.warning(f"Timeout ao aguardar fix GPS ({timeout}s)")
        return False

    def close(self):
        """Fecha conexão GPS"""
        try:
            if self._connection:
                if self.backend == 'serial':
                    self._connection.close()
                elif self.backend == 'gpsd':
                    # gpsd não precisa fechar explicitamente
                    pass
                logger.info("Conexão GPS fechada")
        except Exception as e:
            logger.error(f"Erro ao fechar GPS: {e}")

    def __enter__(self):
        """Context manager enter"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False


# Função helper para criar handler GPS com configuração automática
def create_gps_handler(config: Optional[Dict[str, Any]] = None) -> GPSHandler:
    """
    Cria handler GPS com configuração

    Args:
        config: Dicionário de configuração ou None para padrão

    Returns:
        GPSHandler configurado
    """
    if config is None:
        config = {}

    backend = config.get('backend', 'gpsd')
    device = config.get('device', '/dev/ttyAMA0')
    baudrate = config.get('baudrate', 9600)
    timeout = config.get('timeout', 5.0)

    return GPSHandler(
        backend=backend,
        device=device,
        baudrate=baudrate,
        timeout=timeout
    )
