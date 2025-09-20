"""
Sistema de Detecção de Mato Alto - Interface Principal
Autor: Sistema de IA
Data: 2025

Interface principal para o sistema de detecção de áreas com mato alto
usando visão computacional.
"""

import cv2
import numpy as np
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import argparse
from datetime import datetime

# Adiciona o diretório src ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from capture import ImageCapture
from detector import GrassDetector
from visualizer import ResultVisualizer

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GrassDetectionSystem:
    """Sistema principal de detecção de mato alto."""
    
    def __init__(self):
        """Inicializa o sistema."""
        self.capture = ImageCapture()
        self.detector = GrassDetector()
        self.visualizer = ResultVisualizer()
        
        # Configurações
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Modo de visualização padrão
        self.visualization_mode = 'bounding_box'  # 'bounding_box' ou 'overlay'
        
        self.detection_methods = {
            '1': 'color',
            '2': 'texture', 
            '3': 'combined',
            '4': 'deeplearning'
        }
        
        logger.info("Sistema de Detecção de Mato Alto inicializado")
    
    def display_menu(self) -> None:
        """Exibe menu principal."""
        print("\n" + "="*60)
        print("🌿 SISTEMA DE DETECÇÃO DE MATO ALTO 🌿")
        print("="*60)
        print("1. Analisar foto específica")
        print("2. Processar vídeo completo")
        print("3. Captura em tempo real (webcam)")
        print("4. Análise em lote (pasta de imagens)")
        print("5. Comparar métodos de detecção")
        print("6. Configurações")
        print("7. Alternar modo visual")
        print("8. Ajuda")
        print("0. Sair")
        print("="*60)
        current_mode = "Dashboard Moderno" if self.visualization_mode == 'bounding_box' else "Overlay Clássico"
        print(f"🎨 Modo atual: {current_mode}")

    def toggle_visualization_mode(self) -> None:
        """Alterna entre os modos de visualização."""
        print("\n🎨 SELEÇÃO DE MODO VISUAL")
        print("="*40)
        print("1. Dashboard Moderno (bounding boxes + cards)")
        print("2. Overlay Clássico Melhorado (sobreposição)")
        print("="*40)
        
        while True:
            choice = input("Escolha o modo visual (1-2): ").strip()
            if choice == '1':
                self.visualization_mode = 'bounding_box'
                print("✅ Modo Dashboard Moderno ativado!")
                break
            elif choice == '2':
                self.visualization_mode = 'overlay'
                print("✅ Modo Overlay Clássico ativado!")
                break
            else:
                print("❌ Opção inválida. Digite 1 ou 2.")
    
    def display_detection_menu(self) -> str:
        """Exibe menu de métodos de detecção."""
        print("\n🔍 MÉTODOS DE DETECÇÃO:")
        print("1. Baseado em cores (rápido)")
        print("2. Baseado em textura (preciso)")
        print("3. Combinado (recomendado)")
        print("4. Deep Learning (experimental)")
        
        while True:
            choice = input("\nEscolha o método (1-4): ").strip()
            if choice in self.detection_methods:
                return self.detection_methods[choice]
            print("Opção inválida. Tente novamente.")
    
    def analyze_single_image(self) -> None:
        """Analisa uma única imagem."""
        print("\n📷 ANÁLISE DE IMAGEM ÚNICA")
        
        # Solicita caminho da imagem
        image_path = input("Digite o caminho da imagem: ").strip().strip('"')
        
        if not Path(image_path).exists():
            print(f"❌ Arquivo não encontrado: {image_path}")
            return
        
        # Carrega imagem
        image = self.capture.load_image(image_path)
        if image is None:
            print("❌ Erro ao carregar imagem")
            return
        
        # Escolhe método de detecção
        method = self.display_detection_menu()
        
        print(f"\n🔄 Processando imagem com método: {method}...")
        
        try:
            # Executa detecção
            mask, stats = self.detector.detect_grass_areas(image, method)
            
            # Analisa densidade
            density_analysis = self.detector.analyze_grass_density(mask)
            
            # Calcula confiança
            confidence = self.detector.get_detection_confidence(stats)
            
            # Cria visualizações
            overlay_viz = self.visualizer.create_overlay_visualization(image, mask, stats)
            detailed_viz = self.visualizer.create_detailed_analysis_panel(
                image, mask, stats, density_analysis, visualization_type='bounding_box')
            
            # Exibe resultados
            print("\n✅ RESULTADOS DA ANÁLISE:")
            print(f"   Método: {method}")
            print(f"   Cobertura: {stats['coverage_percentage']:.2f}%")
            print(f"   Confiança: {confidence:.2f}")
            print(f"   Densidade: {density_analysis['density_classification']}")
            print(f"   Regiões detectadas: {density_analysis['num_regions']}")
            
            # Salva resultados
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = Path(image_path).stem
            
            output_overlay = self.output_dir / f"{filename}_overlay_{timestamp}.jpg"
            output_detailed = self.output_dir / f"{filename}_detailed_{timestamp}.jpg"
            
            self.visualizer.save_visualization(overlay_viz, str(output_overlay))
            self.visualizer.save_visualization(detailed_viz, str(output_detailed))
            
            print(f"   Resultados salvos em: {self.output_dir}")
            
            # Exibe visualização
            if input("\nDeseja visualizar os resultados? (s/n): ").lower().startswith('s'):
                self.visualizer.display_results(detailed_viz, "Análise Detalhada")
            
        except Exception as e:
            logger.error(f"Erro na análise: {str(e)}")
            print(f"❌ Erro durante a análise: {str(e)}")
    
    def process_video(self) -> None:
        """Processa um arquivo de vídeo."""
        print("\n🎥 PROCESSAMENTO DE VÍDEO")
        
        video_path = input("Digite o caminho do vídeo: ").strip().strip('"')
        
        if not Path(video_path).exists():
            print(f"❌ Arquivo não encontrado: {video_path}")
            return
        
        method = self.display_detection_method()
        
        # Configurações de processamento
        process_every_n_frames = int(input("Processar a cada N frames (padrão: 30): ") or "30")
        save_frames = input("Salvar frames processados? (s/n): ").lower().startswith('s')
        
        print(f"\n🔄 Processando vídeo...")
        
        try:
            frame_count = 0
            processed_count = 0
            total_coverage = 0
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_name = Path(video_path).stem
            
            for frame_number, frame in self.capture.process_video_file(video_path):
                frame_count += 1
                
                # Processa apenas frames selecionados
                if frame_count % process_every_n_frames != 0:
                    continue
                
                processed_count += 1
                print(f"Processando frame {frame_number}...", end='\r')
                
                # Detecta mato
                mask, stats = self.detector.detect_grass_areas(frame, method)
                total_coverage += stats['coverage_percentage']
                
                # Salva frame se solicitado
                if save_frames:
                    viz = self.visualizer.create_overlay_visualization(frame, mask, stats)
                    frame_path = self.output_dir / f"{video_name}_{timestamp}_frame_{frame_number:06d}.jpg"
                    self.visualizer.save_visualization(viz, str(frame_path))
            
            # Estatísticas finais
            avg_coverage = total_coverage / processed_count if processed_count > 0 else 0
            
            print(f"\n✅ PROCESSAMENTO CONCLUÍDO:")
            print(f"   Total de frames: {frame_count}")
            print(f"   Frames processados: {processed_count}")
            print(f"   Cobertura média: {avg_coverage:.2f}%")
            
            if save_frames:
                print(f"   Frames salvos em: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Erro no processamento do vídeo: {str(e)}")
            print(f"❌ Erro durante o processamento: {str(e)}")
    
    def webcam_realtime(self) -> None:
        """Captura e análise em tempo real da webcam."""
        print("\n📹 CAPTURA EM TEMPO REAL")
        
        # Lista câmeras disponíveis
        cameras = self.capture.get_available_cameras()
        if not cameras:
            print("❌ Nenhuma câmera encontrada")
            return
        
        print("Câmeras disponíveis:", cameras)
        camera_index = int(input(f"Escolha a câmera (padrão: {cameras[0]}): ") or cameras[0])
        
        method = self.display_detection_menu()
        
        # Menu de modo de qualidade
        print("\n🎯 MODO DE QUALIDADE:")
        print("1. Tempo real (rápido, precisão média)")
        print("2. Alta precisão (lento, qualidade máxima)")  
        print("3. Adaptativo (escolha automática)")
        
        quality_mode = input("Escolha o modo (1-3, padrão: 3): ").strip() or "3"
        
        # Configurações de qualidade
        if quality_mode == "1":
            # Modo tempo real forçado
            self.detector.set_realtime_mode(True)
            realtime_mode = True
            print("🚀 Modo tempo real selecionado - priorizando velocidade")
        elif quality_mode == "2":
            # Modo alta precisão forçado
            self.detector.set_precision_mode(True)
            realtime_mode = False
            print("🎯 Modo alta precisão selecionado - priorizando qualidade")
        else:
            # Modo adaptativo (padrão anterior)
            realtime_mode = method in ['texture', 'combined', 'deeplearning']
            if realtime_mode:
                print("🤖 Modo adaptativo: tempo real ativado para melhor performance")
                self.detector.set_realtime_mode(True)
            else:
                print("⚡ Modo adaptativo: alta qualidade para método rápido")
                self.detector.set_precision_mode(True)
        
        # Configurações
        save_detections = input("Salvar detecções interessantes? (s/n): ").lower().startswith('s')
        min_coverage_to_save = 10.0  # Salva apenas se cobertura > 10%
        
        print(f"\n🔄 Iniciando captura...")
        print("🎮 CONTROLES: 'Q'=sair, 'S'=salvar, 'V'=trocar visual, 'M'=modo precisão, 'H'=ajuda")
        print("👁️  Mantenha a janela de vídeo em foco para usar os controles!")
        print("⏳ Aguarde alguns segundos para a webcam inicializar...")
        
        # Pré-cria a janela para garantir foco
        cv2.namedWindow('Detecção de Mato - Tempo Real', cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow('Detecção de Mato - Tempo Real', 100, 100)
        
        # Exibe imagem de aguardo
        waiting_img = np.zeros((480, 640, 3), dtype=np.uint8)
        waiting_img[:] = (40, 40, 40)
        cv2.putText(waiting_img, "INICIANDO WEBCAM...", (180, 220), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2)
        cv2.putText(waiting_img, "Aguarde alguns segundos", (200, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)
        cv2.imshow('Detecção de Mato - Tempo Real', waiting_img)
        cv2.waitKey(2000)  # Aguarda 2 segundos
        
        try:
            saved_count = 0
            frame_count = 0
            
            for frame in self.capture.capture_from_webcam(camera_index, realtime_mode):
                frame_count += 1
                
                # Processa frames com frequência ajustada ao modo
                skip_factor = 3 if realtime_mode else 1  # Alta precisão processa todos os frames
                if frame_count % skip_factor != 0:
                    cv2.imshow('Webcam - Original', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    continue
                
                # Detecta mato
                mask, stats = self.detector.detect_grass_areas(frame, method)
                
                # Analisa densidade para o painel detalhado
                density_analysis = self.detector.analyze_grass_density(mask)
                
                # Cria visualização baseada no modo selecionado
                viz = self.visualizer.create_detailed_analysis_panel(frame, mask, stats, 
                                                                   density_analysis,
                                                                   visualization_type=self.visualization_mode)
                
                # Adiciona informações na tela
                coverage = stats['coverage_percentage']
                confidence = self.detector.get_detection_confidence(stats)
                
                # Status detalhado
                mode_text = ""
                if self.detector.precision_params['enabled']:
                    mode_text = " | ALTA PRECISÃO"
                elif self.detector.realtime_params['enabled']:
                    mode_text = " | TEMPO REAL"
                
                status_text = f"Cobertura: {coverage:.1f}% | Confianca: {confidence:.3f}{mode_text}"
                
                cv2.putText(viz, status_text, (10, viz.shape[0] - 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Exibe resultado
                cv2.imshow('Detecção de Mato - Tempo Real', viz)
                
                # Garante que a janela está em foco para capturar teclas
                cv2.setWindowProperty('Detecção de Mato - Tempo Real', cv2.WND_PROP_TOPMOST, 1)
                cv2.setWindowProperty('Detecção de Mato - Tempo Real', cv2.WND_PROP_TOPMOST, 0)
                
                # Salva detecções interessantes automaticamente
                if save_detections and coverage > min_coverage_to_save:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    save_path = self.output_dir / f"webcam_detection_{timestamp}.jpg"
                    self.visualizer.save_visualization(viz, str(save_path))
                    saved_count += 1
                    print(f"Detecção salva: {save_path}")
                
                # Controles de teclado - timeout maior para capturar melhor as teclas
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q') or key == 27:  # 'q' ou ESC
                    print("👋 Saindo da captura...")
                    break
                elif key == ord('s'):
                    # Salva frame atual
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = self.output_dir / f"webcam_manual_{timestamp}.jpg"
                    self.visualizer.save_visualization(viz, str(save_path))
                    print(f"📸 Frame salvo: {save_path}")
                elif key == ord('m'):
                    # Troca modo em tempo real
                    if self.detector.realtime_params['enabled']:
                        self.detector.set_precision_mode(True)
                        print("🎯 Alternado para modo alta precisão")
                    else:
                        self.detector.set_realtime_mode(True)
                        print("🚀 Alternado para modo tempo real")
                elif key == ord('v'):
                    # Troca modo visual
                    if self.visualization_mode == 'bounding_box':
                        self.visualization_mode = 'overlay'
                        print("🎨 Alternado para Overlay Clássico")
                    else:
                        self.visualization_mode = 'bounding_box'
                        print("🎨 Alternado para Dashboard Moderno")
                elif key == ord('h'):
                    # Mostra ajuda
                    print("\n🎮 CONTROLES DISPONÍVEIS:")
                    print("  Q ou ESC = Sair")
                    print("  S = Salvar frame atual")
                    print("  V = Alternar modo visual")
                    print("  M = Alternar modo precisão") 
                    print("  H = Mostrar esta ajuda")
                elif key != 255:  # Alguma tecla foi pressionada (255 = nenhuma tecla)
                    print(f"⌨️  Tecla '{chr(key) if 32 <= key <= 126 else key}' pressionada - Use 'H' para ajuda")
            
            print(f"\n✅ Captura finalizada. {saved_count} imagens salvas.")
            
        except Exception as e:
            logger.error(f"Erro na captura em tempo real: {str(e)}")
            print(f"❌ Erro durante a captura: {str(e)}")
        finally:
            cv2.destroyAllWindows()
    
    def batch_analysis(self) -> None:
        """Análise em lote de múltiplas imagens."""
        print("\n📁 ANÁLISE EM LOTE")
        
        folder_path = input("Digite o caminho da pasta: ").strip().strip('"')
        folder = Path(folder_path)
        
        if not folder.exists() or not folder.is_dir():
            print(f"❌ Pasta não encontrada: {folder_path}")
            return
        
        method = self.display_detection_menu()
        
        # Carrega imagens
        images = self.capture.load_images_from_folder(str(folder))
        
        if not images:
            print("❌ Nenhuma imagem encontrada na pasta")
            return
        
        print(f"\n🔄 Processando {len(images)} imagens...")
        
        results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            for i, (filename, image) in enumerate(images):
                print(f"Processando {i+1}/{len(images)}: {filename}...", end='\r')
                
                # Detecta mato
                mask, stats = self.detector.detect_grass_areas(image, method)
                density_analysis = self.detector.analyze_grass_density(mask)
                confidence = self.detector.get_detection_confidence(stats)
                
                # Salva resultado
                name_without_ext = Path(filename).stem
                viz = self.visualizer.create_detailed_analysis_panel(
                    image, mask, stats, density_analysis)
                
                output_path = self.output_dir / f"batch_{timestamp}_{name_without_ext}.jpg"
                self.visualizer.save_visualization(viz, str(output_path))
                
                # Coleta estatísticas
                results.append({
                    'filename': filename,
                    'coverage': stats['coverage_percentage'],
                    'confidence': confidence,
                    'density': density_analysis['density_classification'],
                    'regions': density_analysis['num_regions']
                })
            
            print(f"\n✅ ANÁLISE EM LOTE CONCLUÍDA:")
            print(f"   Imagens processadas: {len(images)}")
            print(f"   Resultados salvos em: {self.output_dir}")
            
            # Estatísticas gerais
            avg_coverage = sum(r['coverage'] for r in results) / len(results)
            max_coverage = max(results, key=lambda x: x['coverage'])
            
            print(f"   Cobertura média: {avg_coverage:.2f}%")
            print(f"   Maior cobertura: {max_coverage['coverage']:.2f}% ({max_coverage['filename']})")
            
            # Salva relatório
            self._save_batch_report(results, timestamp)
            
        except Exception as e:
            logger.error(f"Erro na análise em lote: {str(e)}")
            print(f"❌ Erro durante a análise: {str(e)}")
    
    def compare_methods(self) -> None:
        """Compara diferentes métodos de detecção."""
        print("\n🔬 COMPARAÇÃO DE MÉTODOS")
        
        image_path = input("Digite o caminho da imagem: ").strip().strip('"')
        
        if not Path(image_path).exists():
            print(f"❌ Arquivo não encontrado: {image_path}")
            return
        
        image = self.capture.load_image(image_path)
        if image is None:
            print("❌ Erro ao carregar imagem")
            return
        
        print("\n🔄 Testando todos os métodos...")
        
        methods = ['color', 'texture', 'combined']
        results = []
        
        try:
            for method in methods:
                print(f"Executando método: {method}...")
                mask, stats = self.detector.detect_grass_areas(image, method)
                results.append((mask, method, stats))
            
            # Cria comparação visual
            comparison_viz = self.visualizer.create_side_by_side_comparison(image, results)
            
            # Salva comparação
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = Path(image_path).stem
            output_path = self.output_dir / f"{filename}_comparison_{timestamp}.jpg"
            self.visualizer.save_visualization(comparison_viz, str(output_path))
            
            print("\n✅ COMPARAÇÃO DE MÉTODOS:")
            for mask, method, stats in results:
                confidence = self.detector.get_detection_confidence(stats)
                print(f"   {method.capitalize()}: {stats['coverage_percentage']:.2f}% "
                      f"(confiança: {confidence:.2f})")
            
            print(f"\n   Comparação salva: {output_path}")
            
            # Exibe resultado
            if input("\nDeseja visualizar a comparação? (s/n): ").lower().startswith('s'):
                self.visualizer.display_results(comparison_viz, "Comparação de Métodos")
            
        except Exception as e:
            logger.error(f"Erro na comparação: {str(e)}")
            print(f"❌ Erro durante a comparação: {str(e)}")
    
    def show_settings(self) -> None:
        """Exibe e permite alterar configurações."""
        print("\n⚙️  CONFIGURAÇÕES ATUAIS:")
        print(f"   Diretório de saída: {self.output_dir}")
        print(f"   Métodos disponíveis: {list(self.detection_methods.values())}")
        print(f"   Câmeras disponíveis: {self.capture.get_available_cameras()}")
        
        # Configurações do detector
        print(f"\n🎯 PARÂMETROS DO DETECTOR:")
        print(f"   Área mínima: {self.detector.texture_params['min_area']}")
        print(f"   Threshold Sobel: {self.detector.texture_params['sobel_threshold']}")
        
        if input("\nDeseja ajustar parâmetros? (s/n): ").lower().startswith('s'):
            try:
                new_min_area = input(f"Nova área mínima ({self.detector.texture_params['min_area']}): ")
                if new_min_area:
                    self.detector.texture_params['min_area'] = int(new_min_area)
                
                new_threshold = input(f"Novo threshold Sobel ({self.detector.texture_params['sobel_threshold']}): ")
                if new_threshold:
                    self.detector.texture_params['sobel_threshold'] = int(new_threshold)
                
                print("✅ Configurações atualizadas!")
                
            except ValueError:
                print("❌ Valores inválidos")
    
    def show_help(self) -> None:
        """Exibe ajuda e informações do sistema."""
        print("\n" + "="*60)
        print("🆘 AJUDA - SISTEMA DE DETECÇÃO DE MATO ALTO")
        print("="*60)
        print("""
📝 DESCRIÇÃO:
   Sistema de visão computacional para identificar áreas com mato alto
   em fotos, vídeos e imagens da webcam.

🎯 MÉTODOS DE DETECÇÃO:
   • Baseado em cores: Rápido, identifica tons de verde/marrom
   • Baseado em textura: Mais preciso, analisa padrões da imagem
   • Combinado: Recomendado, une os dois métodos anteriores
   • Deep Learning: Experimental, usa redes neurais

📷 TIPOS DE ANÁLISE:
   1. Foto única: Análise detalhada de uma imagem
   2. Vídeo: Processamento frame a frame
   3. Webcam: Análise em tempo real
   4. Lote: Processamento de múltiplas imagens

💾 RESULTADOS:
   • Imagens com áreas destacadas salvas na pasta 'output'
   • Relatórios detalhados com estatísticas
   • Visualizações comparativas entre métodos

🎮 CONTROLES (Webcam):
   • 'q' - Sair
   • 's' - Salvar frame atual

⚡ DICAS:
   • Use imagens com boa iluminação para melhores resultados
   • O método 'combinado' oferece melhor equilíbrio
   • Para vídeos longos, processe a cada 30+ frames
   • Ajuste os parâmetros nas configurações se necessário
        """)
        print("="*60)
    
    def _save_batch_report(self, results: List[Dict], timestamp: str) -> None:
        """Salva relatório da análise em lote."""
        report_path = self.output_dir / f"batch_report_{timestamp}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DE ANÁLISE EM LOTE\n")
            f.write("="*50 + "\n\n")
            f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Total de imagens: {len(results)}\n\n")
            
            # Estatísticas gerais
            avg_coverage = sum(r['coverage'] for r in results) / len(results)
            f.write(f"Cobertura média: {avg_coverage:.2f}%\n\n")
            
            # Detalhes por imagem
            f.write("RESULTADOS POR IMAGEM:\n")
            f.write("-" * 50 + "\n")
            
            for result in sorted(results, key=lambda x: x['coverage'], reverse=True):
                f.write(f"Arquivo: {result['filename']}\n")
                f.write(f"  Cobertura: {result['coverage']:.2f}%\n")
                f.write(f"  Confiança: {result['confidence']:.2f}\n")
                f.write(f"  Densidade: {result['density']}\n")
                f.write(f"  Regiões: {result['regions']}\n\n")
        
        print(f"   Relatório salvo: {report_path}")
    
    def run(self) -> None:
        """Executa o sistema principal."""
        print("🌿 Bem-vindo ao Sistema de Detecção de Mato Alto!")
        print("Inicializando componentes...")
        
        # Verifica se as dependências essenciais estão instaladas
        try:
            import cv2
            import numpy
        except ImportError as e:
            print(f"❌ Dependência essencial não encontrada: {e}")
            print("Execute: pip install opencv-python numpy")
            return
            
        # TensorFlow é opcional
        try:
            import tensorflow
            print("✅ TensorFlow disponível")
        except ImportError:
            print("⚠️  TensorFlow não disponível - método deep learning desabilitado")
        
        while True:
            self.display_menu()
            
            try:
                choice = input("\nEscolha uma opção: ").strip()
                
                if choice == '1':
                    self.analyze_single_image()
                elif choice == '2':
                    self.process_video()
                elif choice == '3':
                    self.webcam_realtime()
                elif choice == '4':
                    self.batch_analysis()
                elif choice == '5':
                    self.compare_methods()
                elif choice == '6':
                    self.show_settings()
                elif choice == '7':
                    self.toggle_visualization_mode()
                elif choice == '8':
                    self.show_help()
                elif choice == '0':
                    print("👋 Obrigado por usar o sistema!")
                    break
                else:
                    print("❌ Opção inválida. Tente novamente.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Sistema interrompido pelo usuário.")
                break
            except Exception as e:
                logger.error(f"Erro não esperado: {str(e)}")
                print(f"❌ Erro inesperado: {str(e)}")
                print("O sistema continuará funcionando...")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Sistema de Detecção de Mato Alto")
    parser.add_argument('--image', type=str, help='Caminho da imagem para análise direta')
    parser.add_argument('--method', type=str, default='combined', 
                       choices=['color', 'texture', 'combined', 'deeplearning'],
                       help='Método de detecção')
    parser.add_argument('--output', type=str, help='Diretório de saída personalizado')
    parser.add_argument('--batch', type=str, help='Pasta para análise em lote')
    
    args = parser.parse_args()
    
    # Cria sistema
    system = GrassDetectionSystem()
    
    # Configura diretório de saída personalizado
    if args.output:
        system.output_dir = Path(args.output)
        system.output_dir.mkdir(exist_ok=True)
    
    # Modo de linha de comando
    if args.image:
        print(f"Analisando imagem: {args.image}")
        image = system.capture.load_image(args.image)
        if image is not None:
            mask, stats = system.detector.detect_grass_areas(image, args.method)
            density_analysis = system.detector.analyze_grass_density(mask)
            
            # Cria visualização
            viz = system.visualizer.create_detailed_analysis_panel(
                image, mask, stats, density_analysis)
            
            # Salva resultado
            output_path = system.output_dir / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            system.visualizer.save_visualization(viz, str(output_path))
            
            print(f"Resultado salvo: {output_path}")
            print(f"Cobertura: {stats['coverage_percentage']:.2f}%")
        else:
            print("Erro ao carregar imagem")
    
    elif args.batch:
        print(f"Análise em lote: {args.batch}")
        # Implementar análise em lote via linha de comando
        system.batch_analysis()
    
    else:
        # Modo interativo
        system.run()


if __name__ == "__main__":
    main()