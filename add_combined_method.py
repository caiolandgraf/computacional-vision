#!/usr/bin/env python3
"""Adiciona o método webcam_combined_realtime ao main.py"""

combined_method = '''
    def analyze_potholes_single(self) -> None:
        """Analisa buracos em uma imagem."""
        print("\\n🕳️  ANÁLISE DE BURACOS - IMAGEM ÚNICA")
        
        image_path = input("Digite o caminho da imagem: ").strip().strip('"')
        
        if not Path(image_path).exists():
            print(f"❌ Arquivo não encontrado: {image_path}")
            return
        
        print("\\n🔍 Método: combined")
        
        try:
            result = self.pothole_detector.detect_image(image_path, method='combined')
            output_filename = f"pothole_{Path(image_path).stem}_result.jpg"
            output_path = self.output_dir / output_filename
            self.pothole_detector.visualize_detections(image_path, result, str(output_path))
            
            print(f"\\n✅ Buracos detectados: {result['num_potholes']}")
            print(f"💾 Resultado salvo em: {output_path}")
        except Exception as e:
            logger.error(f"Erro na detecção de buracos: {str(e)}")
            print(f"❌ Erro durante a detecção: {str(e)}")
    
    def analyze_potholes_batch(self) -> None:
        """Análise em lote de buracos."""
        print("\\n🕳️  ANÁLISE EM LOTE DE BURACOS")
        
        folder_path = input("Digite o caminho da pasta: ").strip().strip('"')
        
        if not Path(folder_path).exists():
            print(f"❌ Pasta não encontrada: {folder_path}")
            return
        
        print("\\n🔍 Método: contour (rápido)")
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(list(Path(folder_path).glob(f"*{ext}")))
        
        if not image_files:
            print(f"❌ Nenhuma imagem encontrada em: {folder_path}")
            return
        
        print(f"\\n🔍 Encontradas {len(image_files)} imagens")
        
        for i, image_path in enumerate(image_files, 1):
            print(f"  [{i}/{len(image_files)}] Processando: {image_path.name}")
            
            try:
                result = self.pothole_detector.detect_image(str(image_path), method='contour')
                output_filename = f"pothole_batch_{image_path.stem}.jpg"
                output_path = self.output_dir / output_filename
                self.pothole_detector.visualize_detections(str(image_path), result, str(output_path))
            except Exception as e:
                logger.error(f"Erro processando {image_path.name}: {str(e)}")
        
        print(f"\\n✅ Análise concluída!")
    
    def compare_pothole_methods(self) -> None:
        """Compara métodos de detecção de buracos."""
        print("\\n🕳️  COMPARAÇÃO DE MÉTODOS - BURACOS")
        
        image_path = input("Digite o caminho da imagem: ").strip().strip('"')
        
        if not Path(image_path).exists():
            print(f"❌ Arquivo não encontrado: {image_path}")
            return
        
        methods = ['contour', 'texture', 'shadow', 'combined']
        results = {}
        
        print(f"\\n🔄 Executando {len(methods)} métodos...")
        
        for method in methods:
            print(f"\\n  🔍 Testando método: {method}")
            try:
                result = self.pothole_detector.detect_image(image_path, method=method)
                results[method] = result
                
                output_filename = f"pothole_compare_{method}_{Path(image_path).stem}.jpg"
                output_path = self.output_dir / output_filename
                self.pothole_detector.visualize_detections(image_path, result, str(output_path))
                
                print(f"    ✅ {result['num_potholes']} buracos | Confiança: {result['confidence']:.2f}")
                
            except Exception as e:
                print(f"    ❌ Erro: {str(e)}")
                logger.error(f"Erro no método {method}: {str(e)}")
        
        print(f"\\n✅ Comparação concluída!")
    
    def webcam_combined_realtime(self) -> None:
        """Captura e análise em tempo real combinando detecção de mato e buracos."""
        print("\\n📹 CAPTURA COMBINADA EM TEMPO REAL - MATO + BURACOS")
        
        cameras = self.capture.get_available_cameras()
        if not cameras:
            print("❌ Nenhuma câmera encontrada")
            return
        
        print("Câmeras disponíveis:", cameras)
        camera_index = int(input(f"Escolha a câmera (padrão: {cameras[0]}): ") or cameras[0])
        
        print("\\n🌱 Método de detecção de MATO:")
        grass_method = self.display_detection_menu()
        
        print("\\n🕳️  Método de detecção de BURACOS:")
        print("1. Contornos (rápido)")
        print("2. Textura (médio)")
        print("3. Sombras (médio)")
        print("4. Combinado (lento, mais preciso)")
        pothole_choice = input("Escolha o método (1-4, padrão: 1): ").strip() or "1"
        pothole_methods_map = {'1': 'contour', '2': 'texture', '3': 'shadow', '4': 'combined'}
        pothole_method = pothole_methods_map.get(pothole_choice, 'contour')
        
        print("\\n🎯 MODO DE QUALIDADE:")
        print("1. Tempo real (rápido, precisão média)")
        print("2. Alta precisão (lento, qualidade máxima)")
        quality_mode = input("Escolha o modo (1-2, padrão: 1): ").strip() or "1"
        
        if quality_mode == "2":
            self.detector.set_precision_mode(True)
            realtime_mode = False
            print("🎯 Modo alta precisão selecionado")
        else:
            self.detector.set_realtime_mode(True)
            realtime_mode = True
            print("🚀 Modo tempo real selecionado")
        
        save_detections = input("Salvar detecções interessantes? (s/n): ").lower().startswith('s')
        min_coverage_to_save = 5.0
        
        print(f"\\n🔄 Iniciando captura combinada...")
        print("🎮 CONTROLES: 'Q'=sair, 'S'=salvar, 'M'=modo precisão, 'H'=ajuda")
        print("👁️  Mantenha a janela de vídeo em foco para usar os controles!")
        print("⏳ Aguarde alguns segundos para a webcam inicializar...")
        
        cv2.namedWindow('Detecção Combinada - Mato + Buracos', cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow('Detecção Combinada - Mato + Buracos', 100, 100)
        
        waiting_img = np.zeros((480, 640, 3), dtype=np.uint8)
        waiting_img[:] = (40, 40, 40)
        cv2.putText(waiting_img, "INICIANDO WEBCAM...", (180, 220), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2)
        cv2.putText(waiting_img, "Aguarde alguns segundos", (200, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)
        cv2.imshow('Detecção Combinada - Mato + Buracos', waiting_img)
        cv2.waitKey(2000)
        
        temp_path = self.output_dir / "temp_frame.jpg"
        
        try:
            saved_count = 0
            frame_count = 0
            
            for frame in self.capture.capture_from_webcam(camera_index, realtime_mode):
                frame_count += 1
                
                skip_factor = 2 if realtime_mode else 1
                if frame_count % skip_factor != 0:
                    cv2.imshow('Detecção Combinada - Mato + Buracos', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    continue
                
                grass_mask, grass_stats = self.detector.detect_grass_areas(frame, grass_method)
                grass_coverage = grass_stats['coverage_percentage']
                grass_confidence = self.detector.get_detection_confidence(grass_stats)
                
                cv2.imwrite(str(temp_path), frame)
                pothole_result = self.pothole_detector.detect_image(str(temp_path), method=pothole_method)
                num_potholes = pothole_result['num_potholes']
                pothole_confidence = pothole_result['confidence']
                
                viz_frame = frame.copy()
                h, w = viz_frame.shape[:2]
                
                grass_overlay = viz_frame.copy()
                grass_overlay[grass_mask > 0] = [0, 255, 0]
                cv2.addWeighted(grass_overlay, 0.3, viz_frame, 0.7, 0, viz_frame)
                
                grass_contours, _ = cv2.findContours(grass_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(viz_frame, grass_contours, -1, (0, 255, 0), 2)
                
                for pothole in pothole_result['potholes']:
                    x, y, w_box, h_box = pothole['bounding_box']
                    cv2.rectangle(viz_frame, (x, y), (x + w_box, y + h_box), (0, 0, 255), 2)
                    
                    label = f"Buraco {pothole['confidence_score']:.2f}"
                    (label_w, label_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(viz_frame, (x, y - label_h - 10), (x + label_w, y), (0, 0, 255), -1)
                    cv2.putText(viz_frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                panel_height = 120
                info_panel = np.zeros((panel_height, w, 3), dtype=np.uint8)
                info_panel[:] = (40, 40, 40)
                
                cv2.putText(info_panel, "DETECCAO COMBINADA", (10, 25),
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)
                
                grass_text = f"MATO: {grass_coverage:.1f}% | Conf: {grass_confidence:.2f}"
                grass_color = (0, 255, 0) if grass_coverage > 15 else (255, 255, 255)
                cv2.putText(info_panel, grass_text, (10, 55),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, grass_color, 2)
                
                pothole_text = f"BURACOS: {num_potholes} detectados | Conf: {pothole_confidence:.2f}"
                pothole_color = (0, 0, 255) if num_potholes > 0 else (255, 255, 255)
                cv2.putText(info_panel, pothole_text, (10, 85),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, pothole_color, 2)
                
                mode_text = "ALTA PRECISAO" if self.detector.precision_params['enabled'] else "TEMPO REAL"
                cv2.putText(info_panel, f"Modo: {mode_text} | Frame: {frame_count}",
                           (w - 350, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                
                alert_y = 110
                if grass_coverage > 20:
                    cv2.putText(info_panel, "! ALERTA: Muito mato detectado",
                               (10, alert_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                if num_potholes > 0:
                    cv2.putText(info_panel, "! ALERTA: Buraco(s) detectado(s)",
                               (w//2, alert_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
                
                combined_viz = np.vstack([viz_frame, info_panel])
                
                cv2.imshow('Detecção Combinada - Mato + Buracos', combined_viz)
                
                if save_detections and (grass_coverage > min_coverage_to_save or num_potholes > 0):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    save_path = self.output_dir / f"combined_detection_{timestamp}.jpg"
                    cv2.imwrite(str(save_path), combined_viz)
                    saved_count += 1
                    print(f"💾 Detecção salva: {save_path.name} (Mato: {grass_coverage:.1f}%, Buracos: {num_potholes})")
                
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q') or key == 27:
                    print("👋 Saindo da captura...")
                    break
                elif key == ord('s'):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = self.output_dir / f"combined_manual_{timestamp}.jpg"
                    cv2.imwrite(str(save_path), combined_viz)
                    print(f"📸 Frame salvo: {save_path.name}")
                elif key == ord('m'):
                    if self.detector.realtime_params['enabled']:
                        self.detector.set_precision_mode(True)
                        print("🎯 Alternado para modo alta precisão")
                    else:
                        self.detector.set_realtime_mode(True)
                        print("🚀 Alternado para modo tempo real")
                elif key == ord('h'):
                    print("\\n🎮 CONTROLES DISPONÍVEIS:")
                    print("  Q ou ESC = Sair")
                    print("  S = Salvar frame atual")
                    print("  M = Alternar modo precisão")
                    print("  H = Mostrar esta ajuda")
            
            if temp_path.exists():
                temp_path.unlink()
            
            print(f"\\n✅ Captura finalizada. {saved_count} imagens salvas.")
            
        except Exception as e:
            logger.error(f"Erro na captura combinada: {str(e)}", exc_info=True)
            print(f"❌ Erro durante a captura: {str(e)}")
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            cv2.destroyAllWindows()
'''

# Ler o arquivo atual
with open('src/main.py', 'r') as f:
    lines = f.readlines()

# Encontrar onde inserir (antes do método run)
insert_line = None
for i, line in enumerate(lines):
    if 'def run(self)' in line:
        insert_line = i
        break

if insert_line:
    # Inserir os novos métodos
    lines.insert(insert_line, combined_method)
    
    # Salvar
    with open('src/main.py', 'w') as f:
        f.writelines(lines)
    
    print("✅ Métodos de detecção combinada adicionados com sucesso!")
else:
    print("❌ Não foi possível encontrar onde inserir os métodos")

