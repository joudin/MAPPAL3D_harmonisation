
from view.widget_state import ButtonOk,ButtonNok, ComboBoxOk, ComboBoxNok, ButtonNoEmphasis
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QImage, QPixmap
from tools.singleton import SingletonMeta
from model.data_supplements import VERSION, XDIM, YDIM
from model.camera import  get_active_camera
from model.harmonisation_data import get_active_harmonisation_data
from view.camera_window import CameraWindowExtendedCenterEmission
import cv2
from model.calculations import get_gauss_fit_params
import threading
from controler.miror_position_controler import MirorPositionControler
import numpy as np
DELAY = 200

class CubePositionControler(metaclass=SingletonMeta):
    def __init__(self):       
        # Comportement de la GUI
        self.camera_window = CameraWindowExtendedCenterEmission()
        self.camera_window.show()
        self.camera_window.set_callback_timer(self.camera_window.timer, self.update_gui)
        self.camera_window.set_timer_timeout(self.camera_window.timer, DELAY)
        self.camera_window.set_callback_connect_button(self.camera_window.button_action, self.run_position_cube_on_new_thread)
        self.camera_window.set_button_label(self.camera_window.button_action, 'Enregistrer position du cube')
        self.camera_window.set_callback_connect_button(self.camera_window.button_next, self.next_button_action)
        self.camera_window.set_callback_connect_button(self.camera_window.button_exit, self.exit_application_action)
        self.camera_window.set_callback_connect_button(self.camera_window.button_action_extra, self.capture_background_action)
        if get_active_camera().__class__.__name__ == "SimulationCamera":
            self.camera_window.set_callback_change_slider(self.camera_window.slider_x_centroid, self.x_centroid_change_slider_action)
            self.camera_window.set_callback_change_slider(self.camera_window.slider_y_centroid, self.y_centroid_change_slider_action)
            self.camera_window.set_callback_change_slider(self.camera_window.slider_width, self.width_change_slider_action)
            self.camera_window.set_callback_change_slider(self.camera_window.slider_amplitude, self.amplitude_change_slider_action)
            self.camera_window.set_callback_range_slider(self.camera_window.slider_x_centroid, 0, XDIM)
            self.camera_window.set_callback_range_slider(self.camera_window.slider_y_centroid, 0, YDIM)
            self.camera_window.set_callback_range_slider(self.camera_window.slider_width, 1, int(XDIM/2))
            self.camera_window.set_callback_range_slider(self.camera_window.slider_amplitude, 0, 256)
            self.camera_window.set_slider_value(self.camera_window.slider_x_centroid, int(XDIM/2))
            self.camera_window.set_slider_value(self.camera_window.slider_y_centroid, int(YDIM/2))
            self.camera_window.set_slider_value(self.camera_window.slider_width, int(XDIM/10))
            self.camera_window.set_slider_value(self.camera_window.slider_amplitude, get_active_camera().amplitude_simu)

        self.camera_window.button_action_state = ButtonNok(self.camera_window.button_action)
        self.camera_window.button_action_extra_state = ButtonNoEmphasis(self.camera_window.button_action_extra)

############################ Callbacks #######################################

    def build_instructions_text(self):
        self.instruction_text = ""
        data = get_active_harmonisation_data()
        if not hasattr(data, 'background_image') or data.background_image is None:
            self.instruction_text += "Enregistrer une image de fond avant de continuer."
        if type(self.camera_window.button_action_state) == ButtonOk:
            pass
        else:
            if len(self.instruction_text) > 0:
                self.instruction_text += "\n"
            self.instruction_text += "Enregistrer la position du cube"
        
    def update_gui(self):
        # Mise à jour de la GUI en se basant sur les états des widgets
        self.camera_window.button_action_state.change_color()
        self.camera_window.button_action_extra_state.change_color()

        self.raw_image = get_active_camera().snapshot('SPOT_LASER')
        # On met à jour l'image de la camera en soustrayant le background si disponible
        data = get_active_harmonisation_data()
        if hasattr(data, 'background_image') and data.background_image is not None:
            from model.calculations import get_substracted_image
            self.np_image = get_substracted_image(self.raw_image, data.background_image)
        else:
            self.np_image = self.raw_image
        # On met à jour l'image de la camera en normalisant sur toute la plage de valeurs
        normalized_image = cv2.normalize(self.np_image.astype(np.float32), None, 0, 255, cv2.NORM_MINMAX)
        normalized_image = np.clip(normalized_image, 0, 255).astype(np.uint8)
        colored_image = cv2.applyColorMap(normalized_image, cv2.COLORMAP_BONE)
        # Convertir BGR (OpenCV) vers RGB (QImage)
        colored_image = cv2.cvtColor(colored_image, cv2.COLOR_BGR2RGB)
        height, width = self.np_image.shape
        bytes_per_line = width
        # Convertir en QImage
        self.qimage = QImage(colored_image.data, width, height, bytes_per_line * 3, QImage.Format_RGB888)
        #scale_factor = 0.2  # réduire à 20%
        #scaled_qimage = self.qimage.scaled(int(self.qimage.width() * scale_factor), int(self.qimage.height() * scale_factor))
        pixmap = QPixmap.fromImage(self.qimage)
        self.camera_window.image_label.setPixmap(pixmap)

        # On construit le texte donnant les instructions restantes en fonction de l'état des widgets
        self.build_instructions_text()
        self.camera_window.instruction_label.setText(self.instruction_text)
        # On affiche les logs
        self.camera_window.log_label.setText(self.camera_window.log_text)

    def x_centroid_change_slider_action(self):
        cam = get_active_camera()
        if cam.__class__.__name__ == "SimulationCamera":
            cam.x_centroid_simu = self.camera_window.slider_x_centroid.value()
    
    def y_centroid_change_slider_action(self):
        cam = get_active_camera()
        if cam.__class__.__name__ == "SimulationCamera":
            cam.y_centroid_simu = self.camera_window.slider_y_centroid.value()

    def width_change_slider_action(self):
        cam = get_active_camera()
        if cam.__class__.__name__ == "SimulationCamera":
            cam.width_simu = self.camera_window.slider_width.value()

    def amplitude_change_slider_action(self):
        cam = get_active_camera()
        if cam.__class__.__name__ == "SimulationCamera":
            cam.amplitude_simu = self.camera_window.slider_amplitude.value()

    def run_position_cube_on_new_thread(self):
        self.camera_window.log_text = "Calcul de la position du cube en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.position_cube_action) 
        action_thread.start()

    def capture_background_action(self):
        data = get_active_harmonisation_data()
        data.background_image = np.zeros((YDIM,XDIM), dtype=np.uint8)  # Reset background image
        
        # Capturer 10 frames et faire la moyenne
        num_frames = 10
        accumulated_image = np.zeros((YDIM, XDIM), dtype=np.float32)
        
        self.camera_window.log_text = "Capture d'images de fond en cours..."
        for i in range(num_frames):
            frame = get_active_camera().snapshot('SPOT_LASER')
            accumulated_image += frame.astype(np.float32)
            self.camera_window.log_text = f"Capture {i+1}/{num_frames}..."
            # Petite pause si nécessaire, mais snapshot devrait suffire
        
        # Calculer la moyenne (input déjà normalisé 0..255)
        averaged_image = (accumulated_image / num_frames).astype(np.uint8)
        
        # On enregistre l'image de fond moyennée dans les données
        data.background_image = averaged_image.copy()
        self.qimage = self.qimage  # Garder la dernière pour sauvegarde PNG, ou utiliser averaged_image
        # Créer QImage à partir de averaged_image pour sauvegarde
        colored_image = cv2.applyColorMap(averaged_image, cv2.COLORMAP_RAINBOW)
        # Convertir BGR (OpenCV) vers RGB (QImage)
        colored_image = cv2.cvtColor(colored_image, cv2.COLOR_BGR2RGB)
        height, width = averaged_image.shape
        bytes_per_line = width
        qimage_averaged = QImage(colored_image.data, width, height, bytes_per_line * 3, QImage.Format_RGB888)
        qimage_averaged.save(f'{data.working_dir}/{data.read("SN")}_BACKGROUND.png', 'PNG')
        
        self.camera_window.button_action_extra_state = ButtonNoEmphasis(self.camera_window.button_action_extra)
        self.camera_window.log_text = "Image de fond moyennée enregistrée."

    def position_cube_action(self):
        """
        faire un fit gaussien de l'image pour déterminer la position du cube
        enregistrer la position dans les data supplements
        enregistrer l'image
        Mettre à jour le log
        Mettre à jour l'état du bouton
        """
        data = get_active_harmonisation_data()
        if not hasattr(data, 'background_image') or data.background_image is None:
            self.camera_window.log_text = "Veuillez d'abord enregistrer une image de fond avant de continuer."
            return
        
        params = get_gauss_fit_params(self.np_image)
        data.cube_position_x = params['x_center']
        data.cube_position_y = params['y_center']
        data.write(f"CUBE_POSITION_X_{data.step.upper()}", str(params['x_center']))
        data.write(f"CUBE_POSITION_Y_{data.step.upper()}", str(params['y_center']))
        data.save()
        self.qimage.save(f'{data.working_dir}/{data.read("SN")}_CUBE_POSITION_{data.step}.png', 'PNG')
        self.camera_window.log_text = f'Position du cube enregistrée : X={params["x_center"]:.2f}, Y={params["y_center"]:.2f}'
        self.camera_window.button_action_state = ButtonOk(self.camera_window.button_action)
   
    def next_button_action(self):
            if len(self.instruction_text) == 0:
                self.miror_position_controler = MirorPositionControler()
                QWidget.close(self.camera_window)
                self.camera_window.stop_timer(self.camera_window.timer)
            else:
                self.camera_window.log_text = "Veuillez compléter les instructions avant de continuer."

    def exit_application_action(self):
        cam = get_active_camera()
        if cam is not None:
            cam.disconnect()
        QApplication.quit() 
        QWidget.close(self.camera_window)