"""
Módulo de captura de imagens para o sistema de detecção de mato alto.
Suporta captura de fotos, vídeos e webcam.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Generator, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageCapture:
    """Classe para captura e processamento de imagens de diferentes fontes."""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        self.video_formats = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Carrega uma imagem do disco.
        
        Args:
            image_path: Caminho para a imagem
            
        Returns:
            Imagem carregada como array NumPy ou None se erro
        """
        try:
            path = Path(image_path)
            if not path.exists():
                logger.error(f"Arquivo não encontrado: {image_path}")
                return None
            
            if path.suffix.lower() not in self.supported_formats:
                logger.error(f"Formato não suportado: {path.suffix}")
                return None
            
            image = cv2.imread(str(path))
            if image is None:
                logger.error(f"Erro ao carregar imagem: {image_path}")
                return None
            
            logger.info(f"Imagem carregada: {image_path} - Dimensões: {image.shape}")
            return image
            
        except Exception as e:
            logger.error(f"Erro ao carregar imagem {image_path}: {str(e)}")
            return None
    
    def load_images_from_folder(self, folder_path: str) -> List[Tuple[str, np.ndarray]]:
        """
        Carrega todas as imagens de uma pasta.
        
        Args:
            folder_path: Caminho para a pasta
            
        Returns:
            Lista de tuplas (nome_arquivo, imagem)
        """
        images = []
        folder = Path(folder_path)
        
        if not folder.exists() or not folder.is_dir():
            logger.error(f"Pasta não encontrada: {folder_path}")
            return images
        
        for file_path in folder.iterdir():
            if file_path.suffix.lower() in self.supported_formats:
                image = self.load_image(str(file_path))
                if image is not None:
                    images.append((file_path.name, image))
        
        logger.info(f"Carregadas {len(images)} imagens da pasta {folder_path}")
        return images
    
    def capture_from_webcam(self, camera_index: int = 0, realtime_mode: bool = False) -> Generator[np.ndarray, None, None]:
        """
        Captura imagens em tempo real da webcam.
        
        Args:
            camera_index: Índice da câmera (0 para padrão)
            realtime_mode: Se True, ativa otimizações para tempo real
            
        Yields:
            Frames capturados da webcam
        """
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            logger.error(f"Erro ao acessar câmera {camera_index}")
            return
        
        # Configurações da câmera otimizadas para modo
        if realtime_mode:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # Reduz resolução
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 15)            # Reduz FPS
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)      # Buffer mínimo
            logger.info("🚀 Modo tempo real ativado para câmera")
        else:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Alta resolução
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
        
        logger.info(f"Câmera {camera_index} iniciada com sucesso")
        
        frame_count = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Falha na captura do frame")
                    break
                
                # Em modo tempo real, pula alguns frames para manter fluidez
                if realtime_mode:
                    frame_count += 1
                    if frame_count % 2 == 0:  # Processa apenas frames ímpares
                        continue
                
                yield frame
                
        except KeyboardInterrupt:
            logger.info("Captura interrompida pelo usuário")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            logger.info("Câmera liberada")
    
    def process_video_file(self, video_path: str) -> Generator[Tuple[int, np.ndarray], None, None]:
        """
        Processa frames de um arquivo de vídeo.
        
        Args:
            video_path: Caminho para o arquivo de vídeo
            
        Yields:
            Tuplas (frame_number, frame)
        """
        path = Path(video_path)
        
        if not path.exists():
            logger.error(f"Arquivo de vídeo não encontrado: {video_path}")
            return
        
        if path.suffix.lower() not in self.video_formats:
            logger.error(f"Formato de vídeo não suportado: {path.suffix}")
            return
        
        cap = cv2.VideoCapture(str(path))
        
        if not cap.isOpened():
            logger.error(f"Erro ao abrir vídeo: {video_path}")
            return
        
        # Informações do vídeo
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Processando vídeo: {video_path}")
        logger.info(f"Total de frames: {total_frames}, FPS: {fps:.2f}, Duração: {duration:.2f}s")
        
        frame_number = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                yield frame_number, frame
                frame_number += 1
                
        except Exception as e:
            logger.error(f"Erro ao processar vídeo: {str(e)}")
        finally:
            cap.release()
            logger.info(f"Processamento concluído. {frame_number} frames processados")
    
    def save_image(self, image: np.ndarray, output_path: str, quality: int = 95) -> bool:
        """
        Salva uma imagem no disco.
        
        Args:
            image: Imagem como array NumPy
            output_path: Caminho de destino
            quality: Qualidade da imagem (0-100)
            
        Returns:
            True se salvo com sucesso, False caso contrário
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Parâmetros de qualidade para JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            
            success = cv2.imwrite(str(output_path), image, encode_params)
            
            if success:
                logger.info(f"Imagem salva: {output_path}")
                return True
            else:
                logger.error(f"Erro ao salvar imagem: {output_path}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao salvar imagem {output_path}: {str(e)}")
            return False
    
    def get_available_cameras(self) -> List[int]:
        """
        Detecta câmeras disponíveis no sistema.
        
        Returns:
            Lista de índices de câmeras disponíveis
        """
        available_cameras = []
        
        for i in range(10):  # Testa até 10 câmeras
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        
        logger.info(f"Câmeras disponíveis: {available_cameras}")
        return available_cameras
    
    def resize_image(self, image: np.ndarray, max_width: int = 1920, max_height: int = 1080) -> np.ndarray:
        """
        Redimensiona imagem mantendo proporção.
        
        Args:
            image: Imagem original
            max_width: Largura máxima
            max_height: Altura máxima
            
        Returns:
            Imagem redimensionada
        """
        height, width = image.shape[:2]
        
        if width <= max_width and height <= max_height:
            return image
        
        # Calcula fator de escala
        scale_w = max_width / width
        scale_h = max_height / height
        scale = min(scale_w, scale_h)
        
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        logger.info(f"Imagem redimensionada: {width}x{height} -> {new_width}x{new_height}")
        
        return resized


if __name__ == "__main__":
    # Teste básico do módulo
    capture = ImageCapture()
    
    print("Câmeras disponíveis:", capture.get_available_cameras())
    
    # Teste de captura da webcam por 5 segundos
    print("Testando captura da webcam (pressione 'q' para sair)...")
    for frame in capture.capture_from_webcam():
        cv2.imshow('Teste Webcam', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break