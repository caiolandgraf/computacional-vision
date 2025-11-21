"""
Sistema de Detecção Otimizado para Raspberry Pi 4
Módulo com GPS, detecção e upload automático para API
"""

__version__ = '1.0.0'
__author__ = 'Sistema de Detecção'

from .api_client import APIClient, DetectionData
from .gps_handler import GPSCoordinates, GPSHandler, create_gps_handler
from .network_monitor import NetworkMonitor, quick_check_connection
from .simple_detector import SimpleDetector, quick_detect

__all__ = [
    'GPSHandler',
    'GPSCoordinates',
    'create_gps_handler',
    'NetworkMonitor',
    'quick_check_connection',
    'APIClient',
    'DetectionData',
    'SimpleDetector',
    'quick_detect',
]
