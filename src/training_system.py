#!/usr/bin/env python3
"""
Sistema de Treinamento Automático para Detecção de Vegetação
Processa imagens e vídeos das pastas de treinamento para melhorar o sistema de aprendizado adaptativo.
"""

import os
import cv2
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from datetime import datetime
import glob

from detector import GrassDetector
from adaptive_learning import AdaptiveLearningSystem

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingSystem:
    def __init__(self, training_data_dir: str = "training_data"):
        """
        Inicializa o sistema de treinamento.
        
        Args:
            training_data_dir: Diretório com os dados de treinamento
        """
        self.training_data_dir = Path(training_data_dir)
        self.detector = GrassDetector()
        self.learning_system = AdaptiveLearningSystem()
        
        # Criar estrutura de pastas se não existir
        self._ensure_directories()
        
        # Estatísticas de treinamento
        self.training_stats = {
            'total_images_processed': 0,
            'vegetation_examples': 0,
            'non_vegetation_examples': 0,
            'ambiguous_examples': 0,
            'videos_processed': 0,
            'frames_extracted': 0,
            'training_sessions': 0,
            'last_training': None
        }
        
        # Carregar estatísticas existentes
        self._load_training_stats()
    
    def _ensure_directories(self):
        """Garante que todas as pastas necessárias existem."""
        dirs_to_create = [
            self.training_data_dir,
            self.training_data_dir / "vegetation",
            self.training_data_dir / "non_vegetation", 
            self.training_data_dir / "ambiguous",
            self.training_data_dir / "videos",
            self.training_data_dir / "processed_frames",
            self.training_data_dir / "validation_results"
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(exist_ok=True, parents=True)
            logger.info(f"📁 Diretório garantido: {dir_path}")
    
    def _load_training_stats(self):
        """Carrega estatísticas de treinamento existentes."""
        stats_file = self.training_data_dir / "training_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.training_stats.update(json.load(f))
                logger.info(f"📊 Estatísticas carregadas: {stats_file}")
            except Exception as e:
                logger.warning(f"❌ Erro ao carregar estatísticas: {e}")
    
    def _save_training_stats(self):
        """Salva estatísticas de treinamento."""
        stats_file = self.training_data_dir / "training_stats.json"
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.training_stats, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Estatísticas salvas: {stats_file}")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar estatísticas: {e}")
    
    def get_supported_image_formats(self) -> List[str]:
        """Retorna formatos de imagem suportados."""
        return ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.webp']
    
    def get_supported_video_formats(self) -> List[str]:
        """Retorna formatos de vídeo suportados.""" 
        return ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.webm', '*.flv']
    
    def find_images_in_directory(self, directory: Path) -> List[Path]:
        """Encontra todas as imagens em um diretório."""
        images = []
        for pattern in self.get_supported_image_formats():
            images.extend(directory.glob(pattern))
            images.extend(directory.glob(pattern.upper()))
        return sorted(images)
    
    def find_videos_in_directory(self, directory: Path) -> List[Path]:
        """Encontra todos os vídeos em um diretório.""" 
        videos = []
        for pattern in self.get_supported_video_formats():
            videos.extend(directory.glob(pattern))
            videos.extend(directory.glob(pattern.upper()))
        return sorted(videos)
    
    def extract_frames_from_video(self, video_path: Path, max_frames: int = 30) -> List[np.ndarray]:
        """
        Extrai frames de um vídeo para treinamento.
        
        Args:
            video_path: Caminho para o vídeo
            max_frames: Número máximo de frames a extrair
            
        Returns:
            Lista de frames como arrays numpy
        """
        frames = []
        
        try:
            cap = cv2.VideoCapture(str(video_path))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames == 0:
                logger.warning(f"⚠️ Vídeo vazio: {video_path}")
                return frames
            
            # Calcular intervalo para pegar frames distribuídos
            frame_interval = max(1, total_frames // max_frames)
            
            frame_count = 0
            extracted_count = 0
            
            while cap.isOpened() and extracted_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Extrair frame no intervalo calculado
                if frame_count % frame_interval == 0:
                    frames.append(frame.copy())
                    extracted_count += 1
                
                frame_count += 1
            
            cap.release()
            
            logger.info(f"🎬 Extraídos {len(frames)} frames de {video_path}")
            self.training_stats['frames_extracted'] += len(frames)
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair frames de {video_path}: {e}")
        
        return frames
    
    def save_extracted_frames(self, frames: List[np.ndarray], video_name: str, category: str = "unknown"):
        """
        Salva frames extraídos no disco.
        
        Args:
            frames: Lista de frames
            video_name: Nome base para os arquivos
            category: Categoria (vegetation, non_vegetation, ambiguous)
        """
        output_dir = self.training_data_dir / "processed_frames" / category
        output_dir.mkdir(exist_ok=True, parents=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, frame in enumerate(frames):
            filename = f"{video_name}_{timestamp}_frame_{i:03d}.jpg"
            output_path = output_dir / filename
            
            try:
                cv2.imwrite(str(output_path), frame)
                logger.info(f"💾 Frame salvo: {output_path}")
            except Exception as e:
                logger.error(f"❌ Erro ao salvar frame {filename}: {e}")
    
    def process_training_image(self, image_path: Path, is_vegetation: bool) -> Dict:
        """
        Processa uma imagem de treinamento.
        
        Args:
            image_path: Caminho para a imagem
            is_vegetation: True se a imagem contém vegetação
            
        Returns:
            Resultado do processamento
        """
        try:
            # Carregar imagem
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"Não foi possível carregar a imagem: {image_path}")
            
            # Fazer detecção atual
            mask, result = self.detector.detect_grass_areas(image, method='combined')
            
            # Criar máscara baseada na expectativa (para aprendizado)
            if is_vegetation:
                # Para exemplos de vegetação, usar máscara detectada como "correta"
                ground_truth_mask = mask
            else:
                # Para não-vegetação, criar máscara vazia (sem vegetação)
                ground_truth_mask = np.zeros_like(mask)
            
            # Treinar sistema adaptativo
            self.learning_system.learn_from_example(image, ground_truth_mask, is_vegetation)
            
            # Preparar resultado
            processing_result = {
                'image_path': str(image_path),
                'is_vegetation': is_vegetation,
                'detection_result': result,
                'processed_at': datetime.now().isoformat(),
                'image_size': image.shape[:2]
            }
            
            # Atualizar estatísticas
            self.training_stats['total_images_processed'] += 1
            if is_vegetation:
                self.training_stats['vegetation_examples'] += 1
            else:
                self.training_stats['non_vegetation_examples'] += 1
            
            logger.info(f"✅ Processada: {image_path.name} (vegetação: {is_vegetation})")
            
            return processing_result
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {image_path}: {e}")
            return {
                'image_path': str(image_path),
                'error': str(e),
                'processed_at': datetime.now().isoformat()
            }
    
    def train_from_directory(self, directory_name: str, is_vegetation: bool) -> List[Dict]:
        """
        Treina com todas as imagens de um diretório.
        
        Args:
            directory_name: Nome do diretório (vegetation, non_vegetation, ambiguous)
            is_vegetation: Se as imagens contêm vegetação
            
        Returns:
            Lista de resultados de processamento
        """
        directory_path = self.training_data_dir / directory_name
        
        if not directory_path.exists():
            logger.warning(f"⚠️ Diretório não encontrado: {directory_path}")
            return []
        
        # Encontrar todas as imagens
        images = self.find_images_in_directory(directory_path)
        
        if not images:
            logger.info(f"📭 Nenhuma imagem encontrada em: {directory_path}")
            return []
        
        logger.info(f"🎯 Processando {len(images)} imagens de {directory_path}")
        
        results = []
        for image_path in images:
            result = self.process_training_image(image_path, is_vegetation)
            results.append(result)
        
        return results
    
    def process_videos(self) -> List[Dict]:
        """Processa todos os vídeos na pasta de vídeos."""
        videos_dir = self.training_data_dir / "videos"
        videos = self.find_videos_in_directory(videos_dir)
        
        if not videos:
            logger.info(f"📭 Nenhum vídeo encontrado em: {videos_dir}")
            return []
        
        logger.info(f"🎬 Processando {len(videos)} vídeos")
        
        results = []
        for video_path in videos:
            try:
                # Extrair frames
                frames = self.extract_frames_from_video(video_path)
                
                if frames:
                    # Salvar frames extraídos
                    video_name = video_path.stem
                    self.save_extracted_frames(frames, video_name, "unknown")
                    
                    # Processar cada frame
                    for i, frame in enumerate(frames):
                        # Por enquanto, assumir que vídeos podem ter vegetação
                        # O usuário pode mover frames depois para categorias corretas
                        frame_result = {
                            'video_path': str(video_path),
                            'frame_index': i,
                            'extracted_at': datetime.now().isoformat(),
                            'frame_saved': True
                        }
                        results.append(frame_result)
                
                self.training_stats['videos_processed'] += 1
                logger.info(f"✅ Vídeo processado: {video_path.name}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar vídeo {video_path}: {e}")
                results.append({
                    'video_path': str(video_path),
                    'error': str(e),
                    'processed_at': datetime.now().isoformat()
                })
        
        return results
    
    def run_full_training(self) -> Dict:
        """
        Executa treinamento completo com todos os dados disponíveis.
        
        Returns:
            Relatório completo do treinamento
        """
        logger.info("🚀 Iniciando treinamento completo...")
        
        training_report = {
            'started_at': datetime.now().isoformat(),
            'vegetation_results': [],
            'non_vegetation_results': [],
            'ambiguous_results': [], 
            'video_results': [],
            'errors': [],
            'summary': {}
        }
        
        try:
            # Processar imagens de vegetação
            logger.info("🌱 Processando imagens de vegetação...")
            training_report['vegetation_results'] = self.train_from_directory("vegetation", True)
            
            # Processar imagens de não-vegetação  
            logger.info("🏢 Processando imagens de não-vegetação...")
            training_report['non_vegetation_results'] = self.train_from_directory("non_vegetation", False)
            
            # Processar casos ambíguos (assumir que podem ter vegetação)
            logger.info("❓ Processando casos ambíguos...")
            training_report['ambiguous_results'] = self.train_from_directory("ambiguous", True)
            self.training_stats['ambiguous_examples'] += len(training_report['ambiguous_results'])
            
            # Processar vídeos
            logger.info("🎬 Processando vídeos...")
            training_report['video_results'] = self.process_videos()
            
            # O sistema de aprendizado salva automaticamente
            logger.info("💾 Sistema de aprendizado salvo automaticamente!")
            
            # Atualizar estatísticas
            self.training_stats['training_sessions'] += 1
            self.training_stats['last_training'] = datetime.now().isoformat()
            self._save_training_stats()
            
            # Preparar sumário
            training_report['summary'] = {
                'total_images': len(training_report['vegetation_results']) + 
                              len(training_report['non_vegetation_results']) + 
                              len(training_report['ambiguous_results']),
                'total_videos': len([r for r in training_report['video_results'] if 'frame_index' not in r]),
                'total_frames': len([r for r in training_report['video_results'] if 'frame_index' in r]),
                'training_stats': self.training_stats.copy()
            }
            
            training_report['completed_at'] = datetime.now().isoformat()
            training_report['status'] = 'success'
            
            logger.info("✅ Treinamento completo finalizado!")
            
        except Exception as e:
            logger.error(f"❌ Erro durante treinamento: {e}")
            training_report['error'] = str(e)
            training_report['status'] = 'error'
            training_report['completed_at'] = datetime.now().isoformat()
        
        # Salvar relatório
        self._save_training_report(training_report)
        
        return training_report
    
    def _save_training_report(self, report: Dict):
        """Salva relatório de treinamento."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.training_data_dir / "validation_results" / f"training_report_{timestamp}.json"
        
        # Função para serializar objetos não-JSON
        def json_serializer(obj):
            if isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return str(obj)
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=json_serializer)
            logger.info(f"📄 Relatório salvo: {report_file}")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar relatório: {e}")
    
    def get_training_progress(self) -> Dict:
        """Retorna progresso atual do treinamento."""
        # Contar arquivos disponíveis
        vegetation_count = len(self.find_images_in_directory(self.training_data_dir / "vegetation"))
        non_vegetation_count = len(self.find_images_in_directory(self.training_data_dir / "non_vegetation"))
        ambiguous_count = len(self.find_images_in_directory(self.training_data_dir / "ambiguous"))
        video_count = len(self.find_videos_in_directory(self.training_data_dir / "videos"))
        
        return {
            'available_data': {
                'vegetation_images': vegetation_count,
                'non_vegetation_images': non_vegetation_count,
                'ambiguous_images': ambiguous_count,
                'videos': video_count
            },
            'processing_stats': self.training_stats.copy(),
            'knowledge_base_size': self.learning_system.get_learning_stats(),
            'recommendations': self._generate_recommendations(vegetation_count, non_vegetation_count, video_count)
        }
    
    def _generate_recommendations(self, veg_count: int, non_veg_count: int, video_count: int) -> List[str]:
        """Gera recomendações baseadas nos dados disponíveis."""
        recommendations = []
        
        if veg_count == 0:
            recommendations.append("🌱 Adicione imagens de vegetação na pasta 'training_data/vegetation'")
        
        if non_veg_count == 0:
            recommendations.append("🏢 Adicione imagens sem vegetação na pasta 'training_data/non_vegetation'")
        
        if veg_count < 10:
            recommendations.append(f"📸 Adicione mais imagens de vegetação (atual: {veg_count}, recomendado: 10+)")
        
        if non_veg_count < 10:
            recommendations.append(f"📸 Adicione mais imagens sem vegetação (atual: {non_veg_count}, recomendado: 10+)")
        
        if video_count > 0:
            recommendations.append(f"🎬 {video_count} vídeo(s) disponível(eis) - execute o treinamento para extrair frames")
        
        if abs(veg_count - non_veg_count) > 20:
            recommendations.append("⚖️ Balance melhor os dados - tenha quantidades similares de vegetação e não-vegetação")
        
        if not recommendations:
            recommendations.append("✅ Dados balanceados! Execute o treinamento para melhorar o sistema")
        
        return recommendations

def main():
    """Função principal para execução do sistema de treinamento."""
    print("🎓 Sistema de Treinamento de Vegetação")
    print("=" * 50)
    
    # Inicializar sistema
    training_system = TrainingSystem()
    
    # Mostrar progresso atual
    progress = training_system.get_training_progress()
    
    print("\n📊 Estado Atual dos Dados:")
    print(f"  🌱 Imagens de vegetação: {progress['available_data']['vegetation_images']}")
    print(f"  🏢 Imagens sem vegetação: {progress['available_data']['non_vegetation_images']}")  
    print(f"  ❓ Casos ambíguos: {progress['available_data']['ambiguous_images']}")
    print(f"  🎬 Vídeos: {progress['available_data']['videos']}")
    
    print(f"\n📈 Estatísticas de Processamento:")
    stats = progress['processing_stats']
    print(f"  📸 Total processado: {stats['total_images_processed']} imagens")
    print(f"  🎬 Vídeos processados: {stats['videos_processed']}")
    print(f"  🎭 Frames extraídos: {stats['frames_extracted']}")
    print(f"  🎯 Sessões de treinamento: {stats['training_sessions']}")
    
    if stats['last_training']:
        print(f"  ⏰ Último treinamento: {stats['last_training']}")
    
    print(f"\n💡 Recomendações:")
    for rec in progress['recommendations']:
        print(f"  {rec}")
    
    # Perguntar se quer executar treinamento
    if progress['available_data']['vegetation_images'] > 0 or progress['available_data']['non_vegetation_images'] > 0 or progress['available_data']['videos'] > 0:
        print(f"\n❓ Executar treinamento com dados disponíveis? (s/n): ", end="")
        response = input().lower().strip()
        
        if response in ['s', 'sim', 'y', 'yes']:
            print("\n🚀 Iniciando treinamento...")
            report = training_system.run_full_training()
            
            if report['status'] == 'success':
                summary = report['summary']
                print(f"\n✅ Treinamento concluído com sucesso!")
                print(f"  📸 Imagens processadas: {summary['total_images']}")
                print(f"  🎬 Vídeos processados: {summary['total_videos']}")
                print(f"  🎭 Frames extraídos: {summary['total_frames']}")
                print(f"\n🧠 Sistema de aprendizado atualizado e salvo!")
            else:
                print(f"\n❌ Erro durante treinamento: {report.get('error', 'Erro desconhecido')}")
        else:
            print("\n📋 Treinamento cancelado. Adicione mais dados e execute novamente.")
    else:
        print(f"\n📭 Nenhum dado de treinamento encontrado.")
        print(f"   Adicione imagens nas pastas:")
        print(f"   - training_data/vegetation/ (imagens com vegetação)")
        print(f"   - training_data/non_vegetation/ (imagens sem vegetação)")
        print(f"   - training_data/videos/ (vídeos para extrair frames)")

if __name__ == "__main__":
    main()