"""
Sistema de Detecção de Mato Alto - Interface Principal
Autor: Sistema de IA
Data: 2025

Interface principal para o sistema de detecção de áreas com mato alto
usando visão computacional.
"""

import argparse
import logging
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

# Adiciona o diretório src ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from capture import ImageCapture
from detector import GrassDetector
from pothole_detector import PotholeDetector
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
        self.pothole_detector = PotholeDetector()
        self.visualizer = ResultVisualizer()

        # Configurações
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

        # Controle de tempo para salvamento automático
        self._last_save_time = 0.0

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
        print("🌿 SISTEMA DE DETECÇÃO - VISÃO COMPUTACIONAL 🌿")
        print("="*60)
        print("\n🌱 DETECÇÃO DE MATO ALTO:")
        print("1. Analisar foto específica (mato)")
        print("2. Processar vídeo completo (mato)")
        print("3. Captura em tempo real - webcam (mato)")
        print("4. Análise em lote (mato)")
        print("5. Comparar métodos de detecção (mato)")
        print("12. Processar vídeo com overlay (gera vídeo de saída)")
        print("\n🕳️  DETECÇÃO DE BURACOS:")
        print("9. Analisar buracos em foto")
        print("10. Análise em lote de buracos")
        print("11. Comparar métodos (buracos)")
        print("\n⚙️  CONFIGURAÇÕES:")
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

        method = self.display_detection_menu()

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

    def process_video_with_overlay(self) -> None:
        """Processa um vídeo e gera vídeo de saída com overlay de detecção (igual à webcam)."""
        print("\n🎬 PROCESSAMENTO DE VÍDEO COM OVERLAY")
        print("="*60)
        print("Este modo processa cada frame do vídeo, aplica a detecção")
        print("e gera um novo vídeo com as áreas verdes e porcentagens.")
        print("="*60)

        video_path = input("\nDigite o caminho do vídeo de entrada: ").strip().strip('"')

        if not Path(video_path).exists():
            print(f"❌ Arquivo não encontrado: {video_path}")
            return

        # Verifica formato do vídeo
        video_ext = Path(video_path).suffix.lower()
        if video_ext not in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']:
            print(f"❌ Formato de vídeo não suportado: {video_ext}")
            return

        method = self.display_detection_menu()

        # Modo de qualidade
        print("\n🎯 MODO DE PROCESSAMENTO:")
        print("1. Rápido (modo tempo real - menor qualidade de detecção)")
        print("2. Alta precisão (lento - melhor qualidade de detecção)")
        quality_mode = input("Escolha o modo (1-2, padrão: 1): ").strip() or "1"

        if quality_mode == "2":
            self.detector.set_precision_mode(True)
            realtime_mode = False
            print("🎯 Modo alta precisão selecionado")
        else:
            self.detector.set_realtime_mode(True)
            realtime_mode = True
            print("🚀 Modo rápido selecionado")

        # Modo visual
        print("\n🎨 MODO VISUAL DO OVERLAY:")
        print("1. Overlay leve (estilo webcam tempo real)")
        print("2. Overlay completo (estilo clássico)")
        print("3. Dashboard moderno (bounding boxes + painel)")
        visual_mode = input("Escolha o modo visual (1-3, padrão: 1): ").strip() or "1"

        # Preview em tempo real?
        show_preview = input("\nMostrar preview durante processamento? (s/n, padrão: n): ").strip().lower().startswith('s')

        # Abre o vídeo de entrada
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("❌ Erro ao abrir o vídeo")
            return

        # Obtém propriedades do vídeo
        input_fps = cap.get(cv2.CAP_PROP_FPS)
        input_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        input_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / input_fps if input_fps > 0 else 0

        print(f"\n📊 INFORMAÇÕES DO VÍDEO:")
        print(f"   Resolução: {input_width}x{input_height}")
        print(f"   FPS: {input_fps:.2f}")
        print(f"   Total de frames: {total_frames}")
        print(f"   Duração: {duration:.1f}s ({duration/60:.1f}min)")

        # Define caminho de saída
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_name = Path(video_path).stem
        output_filename = f"{video_name}_overlay_{method}_{timestamp}.mp4"
        output_path = self.output_dir / output_filename

        # Determina o tamanho do frame de saída baseado no modo visual
        if visual_mode == "3":
            # Dashboard moderno: imagem principal + painel lateral (30%)
            panel_width = int(input_width * 0.3)
            output_width = input_width + panel_width
            output_height = input_height
        else:
            output_width = input_width
            output_height = input_height

        # Configura o writer de vídeo de saída
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = cv2.VideoWriter(str(output_path), fourcc, input_fps, (output_width, output_height))

        if not out_writer.isOpened():
            print("❌ Erro ao criar arquivo de vídeo de saída")
            cap.release()
            return

        print(f"\n🔄 Processando vídeo... Saída: {output_path}")
        print(f"   Resolução de saída: {output_width}x{output_height}")
        print("   Pressione Ctrl+C para cancelar\n")

        if show_preview:
            window_name = 'Preview - Processamento de Vídeo'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, min(output_width, 1280), min(output_height, 720))

        frame_count = 0
        total_coverage = 0.0
        max_coverage = 0.0
        min_coverage = 100.0
        fps_timer = time.time()
        fps_frame_count = 0
        processing_fps = 0.0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                fps_frame_count += 1

                # Calcula FPS de processamento
                now = time.time()
                elapsed = now - fps_timer
                if elapsed >= 1.0:
                    processing_fps = fps_frame_count / elapsed
                    fps_frame_count = 0
                    fps_timer = now

                # Detecta mato
                mask, stats = self.detector.detect_grass_areas(frame, method)
                coverage = stats.get('coverage_percentage', 0)
                total_coverage += coverage
                max_coverage = max(max_coverage, coverage)
                min_coverage = min(min_coverage, coverage)

                # Cria visualização baseada no modo escolhido
                if visual_mode == "2":
                    # Overlay completo clássico
                    viz = self.visualizer.create_overlay_visualization(frame, mask, stats)
                elif visual_mode == "3":
                    # Dashboard moderno com painel lateral
                    density_analysis = self.detector.analyze_grass_density(mask)
                    viz = self.visualizer.create_detailed_analysis_panel(
                        frame, mask, stats, density_analysis,
                        visualization_type='bounding_box')
                else:
                    # Overlay leve estilo webcam (padrão / modo "1")
                    viz = self._create_video_overlay(frame, mask, stats, processing_fps,
                                                     frame_count, total_frames)

                # Garante que o frame de saída tem o tamanho correto
                viz_h, viz_w = viz.shape[:2]
                if viz_w != output_width or viz_h != output_height:
                    viz = cv2.resize(viz, (output_width, output_height))

                # Escreve frame no vídeo de saída
                out_writer.write(viz)

                # Mostra progresso
                progress = (frame_count / total_frames * 100) if total_frames > 0 else 0
                eta_seconds = ((total_frames - frame_count) / processing_fps) if processing_fps > 0 else 0
                eta_min = int(eta_seconds // 60)
                eta_sec = int(eta_seconds % 60)
                print(f"   Frame {frame_count}/{total_frames} ({progress:.1f}%) | "
                      f"Cobertura: {coverage:.1f}% | "
                      f"FPS: {processing_fps:.1f} | "
                      f"ETA: {eta_min}m{eta_sec:02d}s", end='\r')

                # Preview
                if show_preview:
                    cv2.imshow(window_name, viz)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or key == 27:
                        print("\n\n⚠️  Processamento cancelado pelo usuário")
                        break

            # Estatísticas finais
            avg_coverage = total_coverage / frame_count if frame_count > 0 else 0

            print(f"\n\n✅ PROCESSAMENTO CONCLUÍDO!")
            print(f"="*60)
            print(f"   📁 Vídeo de saída: {output_path}")
            print(f"   🎞️  Frames processados: {frame_count}/{total_frames}")
            print(f"   📊 Cobertura média: {avg_coverage:.2f}%")
            print(f"   📈 Cobertura máxima: {max_coverage:.2f}%")
            print(f"   📉 Cobertura mínima: {min_coverage:.2f}%")
            print(f"   ⚡ FPS de processamento: {processing_fps:.1f}")
            print(f"="*60)

            # Salva relatório
            report_path = self.output_dir / f"{video_name}_report_{timestamp}.txt"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("RELATÓRIO DE PROCESSAMENTO DE VÍDEO\n")
                f.write("="*50 + "\n\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Vídeo de entrada: {video_path}\n")
                f.write(f"Vídeo de saída: {output_path}\n")
                f.write(f"Método de detecção: {method}\n")
                f.write(f"Modo de qualidade: {'Alta precisão' if not realtime_mode else 'Rápido'}\n")
                f.write(f"Modo visual: {visual_mode}\n\n")
                f.write(f"Resolução: {input_width}x{input_height}\n")
                f.write(f"FPS: {input_fps}\n")
                f.write(f"Frames processados: {frame_count}/{total_frames}\n")
                f.write(f"Duração: {duration:.1f}s\n\n")
                f.write(f"Cobertura média: {avg_coverage:.2f}%\n")
                f.write(f"Cobertura máxima: {max_coverage:.2f}%\n")
                f.write(f"Cobertura mínima: {min_coverage:.2f}%\n")
            print(f"   📝 Relatório salvo: {report_path}")

            # Pergunta se quer abrir o vídeo
            if input("\nDeseja abrir o vídeo de saída? (s/n): ").strip().lower() == 's':
                import platform
                if platform.system() == 'Darwin':
                    os.system(f'open "{output_path}"')
                elif platform.system() == 'Windows':
                    os.system(f'start "" "{output_path}"')
                else:
                    os.system(f'xdg-open "{output_path}"')

        except KeyboardInterrupt:
            print("\n\n⚠️  Processamento interrompido pelo usuário")
            avg_coverage = total_coverage / frame_count if frame_count > 0 else 0
            print(f"   Frames processados até agora: {frame_count}")
            print(f"   Cobertura média parcial: {avg_coverage:.2f}%")
        except Exception as e:
            logger.error(f"Erro no processamento do vídeo: {str(e)}")
            print(f"\n❌ Erro durante o processamento: {str(e)}")
        finally:
            cap.release()
            out_writer.release()
            if show_preview:
                cv2.destroyAllWindows()

    def _create_video_overlay(self, frame: np.ndarray, mask: np.ndarray,
                               stats: Dict, fps: float,
                               current_frame: int, total_frames: int) -> np.ndarray:
        """Cria visualização leve para processamento de vídeo (estilo webcam)."""
        result = frame.copy()
        height, width = result.shape[:2]

        # Overlay verde semi-transparente nas áreas detectadas
        green_overlay = result.copy()
        green_overlay[mask > 0] = [0, 200, 80]
        cv2.addWeighted(green_overlay, 0.35, result, 0.65, 0, result)

        # Desenha contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filtra contornos pequenos e desenha
        significant_contours = [c for c in contours if cv2.contourArea(c) > 300]
        cv2.drawContours(result, significant_contours, -1, (0, 255, 100), 2)

        # Desenha bounding boxes nos contornos significativos
        for contour in significant_contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            area_m2 = area * 0.0001

            # Bounding box
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 100), 2)

            # Cantos decorativos
            corner_len = min(15, w // 4, h // 4)
            cv2.line(result, (x, y), (x + corner_len, y), (50, 255, 50), 3)
            cv2.line(result, (x, y), (x, y + corner_len), (50, 255, 50), 3)
            cv2.line(result, (x + w, y), (x + w - corner_len, y), (50, 255, 50), 3)
            cv2.line(result, (x + w, y), (x + w, y + corner_len), (50, 255, 50), 3)
            cv2.line(result, (x, y + h), (x + corner_len, y + h), (50, 255, 50), 3)
            cv2.line(result, (x, y + h), (x, y + h - corner_len), (50, 255, 50), 3)
            cv2.line(result, (x + w, y + h), (x + w - corner_len, y + h), (50, 255, 50), 3)
            cv2.line(result, (x + w, y + h), (x + w, y + h - corner_len), (50, 255, 50), 3)

            # Label com área
            if area_m2 >= 0.01:
                label = f"{area_m2:.2f}m2"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.rectangle(result, (x, y - label_size[1] - 8), (x + label_size[0] + 6, y), (30, 30, 30), -1)
                cv2.putText(result, label, (x + 3, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 100), 1, cv2.LINE_AA)

        coverage = stats.get('coverage_percentage', 0)

        # Barra de status no topo
        cv2.rectangle(result, (0, 0), (width, 50), (30, 30, 30), -1)
        cv2.rectangle(result, (0, 0), (width, 3), (0, 255, 100), -1)

        # Texto principal
        method_label = stats.get('method', 'combined').upper()
        status = f"DETECCAO MATO | {method_label} | Cobertura: {coverage:.1f}% | Regioes: {len(significant_contours)}"
        cv2.putText(result, status, (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        # Barra de progresso no topo
        progress = current_frame / total_frames if total_frames > 0 else 0
        bar_width = int(width * progress)
        cv2.rectangle(result, (0, 46), (bar_width, 50), (0, 255, 100), -1)
        cv2.rectangle(result, (bar_width, 46), (width, 50), (60, 60, 60), -1)

        # Painel inferior
        bottom_panel_y = height - 45
        cv2.rectangle(result, (0, bottom_panel_y), (width, height), (30, 30, 30), -1)
        cv2.rectangle(result, (0, bottom_panel_y), (width, bottom_panel_y + 3), (0, 255, 100), -1)

        # Info no painel inferior
        progress_text = f"Frame: {current_frame}/{total_frames} ({progress*100:.1f}%)"
        cv2.putText(result, progress_text, (10, height - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

        fps_text = f"FPS: {fps:.1f}"
        fps_size = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)[0]
        cv2.putText(result, fps_text, (width // 2 - fps_size[0] // 2, height - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 100), 1, cv2.LINE_AA)

        # Indicador de cobertura com cor dinâmica
        if coverage > 50:
            cov_color = (0, 0, 255)  # Vermelho = muito mato
        elif coverage > 25:
            cov_color = (0, 165, 255)  # Laranja
        else:
            cov_color = (0, 255, 100)  # Verde = pouco mato

        cov_text = f"Cobertura: {coverage:.1f}%"
        cov_size = cv2.getTextSize(cov_text, cv2.FONT_HERSHEY_DUPLEX, 0.6, 2)[0]
        cv2.putText(result, cov_text, (width - cov_size[0] - 15, height - 15),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, cov_color, 2, cv2.LINE_AA)

        # Mini barra de cobertura no canto superior direito
        bar_x = width - 160
        bar_y = 10
        bar_h = 28
        bar_max_w = 145
        cv2.rectangle(result, (bar_x, bar_y), (bar_x + bar_max_w, bar_y + bar_h), (60, 60, 60), -1)
        fill_w = int(bar_max_w * min(coverage / 100.0, 1.0))
        cv2.rectangle(result, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), cov_color, -1)
        cv2.rectangle(result, (bar_x, bar_y), (bar_x + bar_max_w, bar_y + bar_h), (200, 200, 200), 1)
        pct_text = f"{coverage:.0f}%"
        pct_size = cv2.getTextSize(pct_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        cv2.putText(result, pct_text, (bar_x + bar_max_w // 2 - pct_size[0] // 2, bar_y + bar_h - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        return result

    def _create_fast_overlay(self, frame: np.ndarray, mask: np.ndarray,
                             stats: Dict, fps: float) -> np.ndarray:
        """Cria visualização leve e rápida para modo tempo real."""
        result = frame.copy()
        height, width = result.shape[:2]

        # Overlay verde semi-transparente nas áreas detectadas (operação rápida)
        green_overlay = result.copy()
        green_overlay[mask > 0] = [0, 200, 80]
        cv2.addWeighted(green_overlay, 0.35, result, 0.65, 0, result)

        # Desenha contornos (mais rápido que bounding boxes completos)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(result, contours, -1, (0, 255, 100), 2)

        # Barra de status no topo (simples e rápida)
        cv2.rectangle(result, (0, 0), (width, 40), (30, 30, 30), -1)
        cv2.rectangle(result, (0, 0), (width, 3), (0, 255, 100), -1)

        coverage = stats.get('coverage_percentage', 0)
        mode_label = "TEMPO REAL" if self.detector.realtime_params['enabled'] else "PRECISÃO"
        status = f"{mode_label} | Cobertura: {coverage:.1f}% | FPS: {fps:.0f} | Regioes: {len(contours)}"
        cv2.putText(result, status, (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        return result

    def webcam_realtime(self) -> None:
        """Captura e análise em tempo real da webcam com threading."""
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

        quality_mode = input("Escolha o modo (1-3, padrão: 1): ").strip() or "1"

        # Configurações de qualidade
        if quality_mode == "2":
            # Modo alta precisão forçado
            self.detector.set_precision_mode(True)
            realtime_mode = False
            print("🎯 Modo alta precisão selecionado - priorizando qualidade")
        elif quality_mode == "3":
            # Modo adaptativo
            realtime_mode = method in ['texture', 'combined', 'deeplearning']
            if realtime_mode:
                print("🤖 Modo adaptativo: tempo real ativado para melhor performance")
                self.detector.set_realtime_mode(True)
            else:
                print("⚡ Modo adaptativo: alta qualidade para método rápido")
                self.detector.set_precision_mode(True)
        else:
            # Modo tempo real forçado (padrão agora)
            self.detector.set_realtime_mode(True)
            realtime_mode = True
            print("🚀 Modo tempo real selecionado - priorizando velocidade")

        # Configurações
        save_detections = input("Salvar detecções interessantes? (s/n): ").lower().startswith('s')
        min_coverage_to_save = 10.0  # Salva apenas se cobertura > 10%

        print(f"\n🔄 Iniciando captura...")
        print("🎮 CONTROLES: 'Q'=sair, 'S'=salvar, 'V'=trocar visual, 'M'=modo precisão, 'H'=ajuda")
        print("👁️  Mantenha a janela de vídeo em foco para usar os controles!")
        print("⏳ Aguarde alguns segundos para a webcam inicializar...")

        # Pré-cria a janela para garantir foco
        window_name = 'Detecção de Mato - Tempo Real'
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow(window_name, 100, 100)

        # Exibe imagem de aguardo
        waiting_img = np.zeros((480, 640, 3), dtype=np.uint8)
        waiting_img[:] = (40, 40, 40)
        cv2.putText(waiting_img, "INICIANDO WEBCAM...", (180, 220), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2)
        cv2.putText(waiting_img, "Aguarde alguns segundos", (200, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)
        cv2.imshow(window_name, waiting_img)
        cv2.waitKey(500)

        # --- Captura com thread separada para não bloquear processamento ---
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print("❌ Erro ao acessar câmera")
            return

        # Configura câmera
        if realtime_mode:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        else:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)

        # Variáveis compartilhadas com a thread de captura
        latest_frame = [None]  # Usa lista para mutabilidade em closure
        frame_lock = threading.Lock()
        stop_event = threading.Event()

        def capture_thread():
            """Thread dedicada para captura contínua — sempre tem o frame mais recente."""
            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    break
                with frame_lock:
                    latest_frame[0] = frame

        # Inicia thread de captura
        cap_thread = threading.Thread(target=capture_thread, daemon=True)
        cap_thread.start()

        # Aguarda primeiro frame
        for _ in range(50):
            with frame_lock:
                if latest_frame[0] is not None:
                    break
            time.sleep(0.05)

        try:
            saved_count = 0
            frame_count = 0
            fps = 0.0
            fps_timer = time.time()
            fps_frame_count = 0
            last_viz = None

            while not stop_event.is_set():
                # Pega o frame mais recente (não bloqueia)
                with frame_lock:
                    frame = latest_frame[0]

                if frame is None:
                    time.sleep(0.01)
                    continue

                frame_count += 1
                fps_frame_count += 1

                # Calcula FPS a cada 10 frames
                now = time.time()
                elapsed = now - fps_timer
                if elapsed >= 0.5:
                    fps = fps_frame_count / elapsed
                    fps_frame_count = 0
                    fps_timer = now

                # Detecta mato
                mask, stats = self.detector.detect_grass_areas(frame, method)

                coverage = stats['coverage_percentage']

                # Visualização: leve em realtime, detalhada em precisão
                if realtime_mode:
                    viz = self._create_fast_overlay(frame, mask, stats, fps)
                else:
                    density_analysis = self.detector.analyze_grass_density(mask)
                    viz = self.visualizer.create_detailed_analysis_panel(
                        frame, mask, stats, density_analysis,
                        visualization_type=self.visualization_mode)

                    confidence = self.detector.get_detection_confidence(stats)
                    status_text = f"Cobertura: {coverage:.1f}% | Confianca: {confidence:.3f} | ALTA PRECISÃO"
                    cv2.putText(viz, status_text, (10, viz.shape[0] - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                last_viz = viz

                # Exibe resultado
                cv2.imshow(window_name, viz)

                # Salva detecções interessantes automaticamente
                if save_detections and coverage > min_coverage_to_save:
                    # Limita salvamentos a no máximo 1 por segundo
                    if not hasattr(self, '_last_save_time') or (now - self._last_save_time) > 1.0:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                        save_path = self.output_dir / f"webcam_detection_{timestamp}.jpg"
                        self.visualizer.save_visualization(viz, str(save_path))
                        saved_count += 1
                        self._last_save_time = now
                        print(f"Detecção salva: {save_path}")

                # Controles de teclado — waitKey(1) para mínimo delay
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' ou ESC
                    print("👋 Saindo da captura...")
                    break
                elif key == ord('s'):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = self.output_dir / f"webcam_manual_{timestamp}.jpg"
                    if last_viz is not None:
                        self.visualizer.save_visualization(last_viz, str(save_path))
                    print(f"📸 Frame salvo: {save_path}")
                elif key == ord('m'):
                    if self.detector.realtime_params['enabled']:
                        self.detector.set_precision_mode(True)
                        realtime_mode = False
                        print("🎯 Alternado para modo alta precisão")
                    else:
                        self.detector.set_realtime_mode(True)
                        realtime_mode = True
                        print("🚀 Alternado para modo tempo real")
                elif key == ord('v'):
                    if self.visualization_mode == 'bounding_box':
                        self.visualization_mode = 'overlay'
                        print("🎨 Alternado para Overlay Clássico")
                    else:
                        self.visualization_mode = 'bounding_box'
                        print("🎨 Alternado para Dashboard Moderno")
                elif key == ord('h'):
                    print("\n🎮 CONTROLES DISPONÍVEIS:")
                    print("  Q ou ESC = Sair")
                    print("  S = Salvar frame atual")
                    print("  V = Alternar modo visual")
                    print("  M = Alternar modo precisão")
                    print("  H = Mostrar esta ajuda")

            print(f"\n✅ Captura finalizada. {saved_count} imagens salvas. FPS médio: {fps:.1f}")

        except Exception as e:
            logger.error(f"Erro na captura em tempo real: {str(e)}")
            print(f"❌ Erro durante a captura: {str(e)}")
        finally:
            stop_event.set()
            cap_thread.join(timeout=2)
            cap.release()
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

    def analyze_potholes_single(self) -> None:
        """Analisa buracos em uma única imagem."""
        print("\n🕳️  ANÁLISE DE BURACOS - IMAGEM ÚNICA")

        # Solicita caminho da imagem
        image_path = input("Digite o caminho da imagem: ").strip().strip('"')

        if not Path(image_path).exists():
            print(f"❌ Arquivo não encontrado: {image_path}")
            return

        # Escolhe método
        print("\n🔍 MÉTODOS DE DETECÇÃO DE BURACOS:")
        print("1. Análise de contornos (recomendado)")
        print("2. Análise de textura")
        print("3. Análise de sombras")
        print("4. Método combinado (melhor precisão)")

        method_map = {'1': 'contour', '2': 'texture', '3': 'shadow', '4': 'combined'}

        while True:
            choice = input("\nEscolha o método (1-4): ").strip()
            if choice in method_map:
                method = method_map[choice]
                break
            print("❌ Opção inválida. Tente novamente.")

        print(f"\n🔄 Processando imagem com método: {method}...")

        try:
            # Executa detecção
            result = self.pothole_detector.detect_image(image_path, method=method)

            # Exibe resultados
            print("\n" + "="*60)
            print("📊 RESULTADOS DA DETECÇÃO")
            print("="*60)
            print(f"🕳️  Buracos detectados: {result['num_potholes']}")
            print(f"📏 Área total: {result['total_area']:.0f} pixels")
            print(f"📊 Cobertura: {result['coverage']:.2f}%")
            print(f"🎯 Confiança: {result['confidence']:.2f} ({result['confidence_level']})")

            if result['flags']:
                print(f"⚠️  Flags: {', '.join(result['flags'])}")

            # Lista buracos individuais
            if result['potholes']:
                print(f"\n🔍 Detalhes dos buracos:")
                for i, pothole in enumerate(result['potholes'][:10], 1):  # Máximo 10
                    x, y, w, h = pothole['bounding_box']
                    print(f"  {i}. Posição: ({x}, {y}), Tamanho: {w}x{h}, "
                          f"Área: {pothole['area']:.0f}px, "
                          f"Confiança: {pothole['confidence_score']:.2f}")

                if len(result['potholes']) > 10:
                    print(f"  ... e mais {len(result['potholes']) - 10} buracos")

            # Criar visualização
            output_filename = f"pothole_{Path(image_path).stem}_{method}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            output_path = self.output_dir / output_filename

            self.pothole_detector.visualize_detections(image_path, result, str(output_path))

            print(f"\n💾 Visualização salva: {output_path}")
            print("="*60)

            # Perguntar se quer abrir
            if input("\nDeseja abrir a imagem? (s/n): ").strip().lower() == 's':
                import platform
                if platform.system() == 'Darwin':  # macOS
                    os.system(f'open "{output_path}"')
                elif platform.system() == 'Windows':
                    os.system(f'start "" "{output_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{output_path}"')

        except Exception as e:
            logger.error(f"Erro na análise: {str(e)}", exc_info=True)
            print(f"❌ Erro: {str(e)}")

    def analyze_potholes_batch(self) -> None:
        """Analisa buracos em lote."""
        print("\n🕳️  ANÁLISE EM LOTE DE BURACOS")

        folder_path = input("Digite o caminho da pasta: ").strip().strip('"')

        if not Path(folder_path).exists():
            print(f"❌ Pasta não encontrada: {folder_path}")
            return

        # Escolhe método
        print("\n🔍 MÉTODOS DE DETECÇÃO:")
        print("1. Contornos")
        print("2. Textura")
        print("3. Sombras")
        print("4. Combinado (recomendado)")

        method_map = {'1': 'contour', '2': 'texture', '3': 'shadow', '4': 'combined'}

        while True:
            choice = input("\nEscolha o método (1-4): ").strip()
            if choice in method_map:
                method = method_map[choice]
                break
            print("❌ Opção inválida.")

        # Buscar imagens
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
        image_files = []
        for ext in extensions:
            image_files.extend(Path(folder_path).glob(ext))
            image_files.extend(Path(folder_path).glob(ext.upper()))

        if not image_files:
            print("❌ Nenhuma imagem encontrada na pasta")
            return

        print(f"\n📁 Encontradas {len(image_files)} imagens")
        print(f"🔄 Processando com método: {method}...")

        results = []

        for i, image_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] Processando: {image_path.name}")

            try:
                result = self.pothole_detector.detect_image(str(image_path), method=method)

                # Salvar visualização
                output_filename = f"pothole_batch_{image_path.stem}.jpg"
                output_path = self.output_dir / output_filename
                self.pothole_detector.visualize_detections(str(image_path), result, str(output_path))

                results.append({
                    'image': image_path.name,
                    'num_potholes': result['num_potholes'],
                    'total_area': result['total_area'],
                    'coverage': result['coverage'],
                    'confidence': result['confidence'],
                    'confidence_level': result['confidence_level'],
                    'output': output_path.name
                })

                print(f"  ✅ {result['num_potholes']} buracos | Confiança: {result['confidence']:.2f}")

            except Exception as e:
                print(f"  ❌ Erro: {str(e)}")
                logger.error(f"Erro processando {image_path}: {str(e)}")

        # Relatório final
        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL - ANÁLISE EM LOTE")
        print("="*60)
        print(f"📁 Total de imagens: {len(image_files)}")
        print(f"✅ Processadas com sucesso: {len(results)}")

        if results:
            total_potholes = sum(r['num_potholes'] for r in results)
            avg_confidence = np.mean([r['confidence'] for r in results])

            print(f"🕳️  Total de buracos detectados: {total_potholes}")
            print(f"📊 Média de buracos por imagem: {total_potholes / len(results):.1f}")
            print(f"🎯 Confiança média: {avg_confidence:.2f}")

            # Salvar relatório JSON
            import json
            report_path = self.output_dir / f"pothole_batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Relatório salvo: {report_path}")

        print("="*60)

    def compare_pothole_methods(self) -> None:
        """Compara diferentes métodos de detecção de buracos."""
        print("\n🕳️  COMPARAÇÃO DE MÉTODOS - BURACOS")

        image_path = input("Digite o caminho da imagem: ").strip().strip('"')

        if not Path(image_path).exists():
            print(f"❌ Arquivo não encontrado: {image_path}")
            return

        methods = ['contour', 'texture', 'shadow', 'combined']
        results = {}

        print(f"\n🔄 Executando {len(methods)} métodos...")

        for method in methods:
            print(f"\n  🔍 Testando método: {method}")
            try:
                result = self.pothole_detector.detect_image(image_path, method=method)
                results[method] = result

                # Salvar visualização
                output_filename = f"pothole_compare_{method}_{Path(image_path).stem}.jpg"
                output_path = self.output_dir / output_filename
                self.pothole_detector.visualize_detections(image_path, result, str(output_path))

                print(f"    ✅ {result['num_potholes']} buracos | Confiança: {result['confidence']:.2f}")

            except Exception as e:
                print(f"    ❌ Erro: {str(e)}")
                logger.error(f"Erro no método {method}: {str(e)}")

        # Exibir comparação
        print("\n" + "="*60)
        print("📊 COMPARAÇÃO DE RESULTADOS")
        print("="*60)
        print(f"{'Método':<15} {'Buracos':<10} {'Área Total':<12} {'Confiança':<10} {'Nível':<10}")
        print("-"*60)

        for method, result in results.items():
            print(f"{method:<15} {result['num_potholes']:<10} "
                  f"{result['total_area']:<12.0f} "
                  f"{result['confidence']:<10.2f} {result['confidence_level']:<10}")

        print("="*60)

        # Recomendação
        best_method = max(results.items(), key=lambda x: x[1]['confidence'])
        print(f"\n💡 Recomendação: Método '{best_method[0]}' "
              f"(confiança: {best_method[1]['confidence']:.2f})")

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
                elif choice == '9':
                    self.analyze_potholes_single()
                elif choice == '10':
                    self.analyze_potholes_batch()
                elif choice == '11':
                    self.compare_pothole_methods()
                elif choice == '12':
                    self.process_video_with_overlay()
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
    parser.add_argument('--video', type=str, help='Caminho do vídeo para processar com overlay')
    parser.add_argument('--method', type=str, default='combined',
                       choices=['color', 'texture', 'combined', 'deeplearning'],
                       help='Método de detecção')
    parser.add_argument('--output', type=str, help='Diretório de saída personalizado')
    parser.add_argument('--batch', type=str, help='Pasta para análise em lote')
    parser.add_argument('--visual-mode', type=str, default='1',
                       choices=['1', '2', '3'],
                       help='Modo visual do overlay: 1=leve, 2=clássico, 3=dashboard')
    parser.add_argument('--quality', type=str, default='1',
                       choices=['1', '2'],
                       help='Qualidade de processamento: 1=rápido, 2=alta precisão')
    parser.add_argument('--preview', action='store_true',
                       help='Mostrar preview durante processamento de vídeo')

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

    elif args.video:
        # Processamento de vídeo com overlay via CLI
        video_path = args.video
        if not Path(video_path).exists():
            print(f"❌ Arquivo não encontrado: {video_path}")
            return

        video_ext = Path(video_path).suffix.lower()
        if video_ext not in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']:
            print(f"❌ Formato de vídeo não suportado: {video_ext}")
            return

        method = args.method
        visual_mode = args.visual_mode
        quality_mode = args.quality
        show_preview = args.preview

        if quality_mode == "2":
            system.detector.set_precision_mode(True)
            realtime_mode = False
            print("🎯 Modo alta precisão selecionado")
        else:
            system.detector.set_realtime_mode(True)
            realtime_mode = True
            print("🚀 Modo rápido selecionado")

        # Abre o vídeo de entrada
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("❌ Erro ao abrir o vídeo")
            return

        # Obtém propriedades do vídeo
        input_fps = cap.get(cv2.CAP_PROP_FPS)
        input_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        input_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / input_fps if input_fps > 0 else 0

        print(f"\n📊 INFORMAÇÕES DO VÍDEO:")
        print(f"   Resolução: {input_width}x{input_height}")
        print(f"   FPS: {input_fps:.2f}")
        print(f"   Total de frames: {total_frames}")
        print(f"   Duração: {duration:.1f}s ({duration/60:.1f}min)")

        # Define caminho de saída
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_name = Path(video_path).stem
        output_filename = f"{video_name}_overlay_{method}_{timestamp}.mp4"
        output_path = system.output_dir / output_filename

        # Determina o tamanho do frame de saída baseado no modo visual
        if visual_mode == "3":
            panel_width = int(input_width * 0.3)
            output_width = input_width + panel_width
            output_height = input_height
        else:
            output_width = input_width
            output_height = input_height

        # Configura o writer de vídeo de saída
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = cv2.VideoWriter(str(output_path), fourcc, input_fps, (output_width, output_height))

        if not out_writer.isOpened():
            print("❌ Erro ao criar arquivo de vídeo de saída")
            cap.release()
            return

        print(f"\n🔄 Processando vídeo... Saída: {output_path}")
        print(f"   Resolução de saída: {output_width}x{output_height}")

        if show_preview:
            window_name = 'Preview - Processamento de Vídeo'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, min(output_width, 1280), min(output_height, 720))

        frame_count = 0
        total_coverage = 0.0
        max_coverage = 0.0
        min_coverage = 100.0
        fps_timer = time.time()
        fps_frame_count = 0
        processing_fps = 0.0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                fps_frame_count += 1

                now = time.time()
                elapsed = now - fps_timer
                if elapsed >= 1.0:
                    processing_fps = fps_frame_count / elapsed
                    fps_frame_count = 0
                    fps_timer = now

                mask, stats = system.detector.detect_grass_areas(frame, method)
                coverage = stats.get('coverage_percentage', 0)
                total_coverage += coverage
                max_coverage = max(max_coverage, coverage)
                min_coverage = min(min_coverage, coverage)

                if visual_mode == "2":
                    viz = system.visualizer.create_overlay_visualization(frame, mask, stats)
                elif visual_mode == "3":
                    density_analysis = system.detector.analyze_grass_density(mask)
                    viz = system.visualizer.create_detailed_analysis_panel(
                        frame, mask, stats, density_analysis,
                        visualization_type='bounding_box')
                else:
                    # Overlay leve estilo webcam (padrão / modo "1")
                    viz = system._create_video_overlay(frame, mask, stats, processing_fps,
                                                       frame_count, total_frames)

                viz_h, viz_w = viz.shape[:2]
                if viz_w != output_width or viz_h != output_height:
                    viz = cv2.resize(viz, (output_width, output_height))

                out_writer.write(viz)

                progress = (frame_count / total_frames * 100) if total_frames > 0 else 0
                eta_seconds = ((total_frames - frame_count) / processing_fps) if processing_fps > 0 else 0
                eta_min = int(eta_seconds // 60)
                eta_sec = int(eta_seconds % 60)
                print(f"   Frame {frame_count}/{total_frames} ({progress:.1f}%) | "
                      f"Cobertura: {coverage:.1f}% | "
                      f"FPS: {processing_fps:.1f} | "
                      f"ETA: {eta_min}m{eta_sec:02d}s", end='\r')

                if show_preview:
                    cv2.imshow(window_name, viz)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or key == 27:
                        print("\n\n⚠️  Processamento cancelado pelo usuário")
                        break

            avg_coverage = total_coverage / frame_count if frame_count > 0 else 0

            print(f"\n\n✅ PROCESSAMENTO CONCLUÍDO!")
            print(f"="*60)
            print(f"   📁 Vídeo de saída: {output_path}")
            print(f"   🎞️  Frames processados: {frame_count}/{total_frames}")
            print(f"   📊 Cobertura média: {avg_coverage:.2f}%")
            print(f"   📈 Cobertura máxima: {max_coverage:.2f}%")
            print(f"   📉 Cobertura mínima: {min_coverage:.2f}%")
            print(f"   ⚡ FPS de processamento: {processing_fps:.1f}")
            print(f"="*60)

        except KeyboardInterrupt:
            print("\n\n⚠️  Processamento interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro no processamento do vídeo: {str(e)}")
            print(f"\n❌ Erro durante o processamento: {str(e)}")
        finally:
            cap.release()
            out_writer.release()
            if show_preview:
                cv2.destroyAllWindows()

    elif args.batch:
        print(f"Análise em lote: {args.batch}")
        # Implementar análise em lote via linha de comando
        system.batch_analysis()

    else:
        # Modo interativo
        system.run()


if __name__ == "__main__":
    main()
