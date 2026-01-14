
from view.widget_state import ButtonOk, ComboBoxOk, ComboBoxNok, ButtonNok, ButtonNoEmphasis
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QImage, QPixmap
from tools.singleton import SingletonMeta
from model.data_supplements import VERSION, XDIM, YDIM
from model.camera import  get_active_camera
from model.harmonisation_data import get_active_harmonisation_data
from view.camera_window import CameraWindowExtendedCenterEmission
import cv2
from model.calculations import get_gauss_fit_params, get_substracted_image
from controler.apd_position_controler import ApdPositionControler
import threading
import numpy as np

DELAY = 200

class CenterEmissionControler(metaclass=SingletonMeta):
    def __init__(self):       
        # Comportement de la GUI
        self.camera_window = CameraWindowExtendedCenterEmission()
        self.camera_window.show()
        self.camera_window.set_callback_timer(self.camera_window.timer, self.update_gui)
        self.camera_window.set_timer_timeout(self.camera_window.timer, DELAY)
        self.camera_window.set_callback_connect_button(self.camera_window.button_action, self.run_save_postion_spot_laser_on_new_thread)
        self.camera_window.set_button_label(self.camera_window.button_action, 'Enregistrer position spot laser')
        self.camera_window.set_callback_connect_button(self.camera_window.button_next, self.next_button_action)
        self.camera_window.set_callback_connect_button(self.camera_window.button_exit, self.exit_application_action)
        self.camera_window.button_action_extra_state = ButtonNok(self.camera_window.button_action)
        self.camera_window.set_callback_connect_button(self.camera_window.button_action_extra, self.capture_background_action)

        if get_active_camera().__class__.__name__ == "SimulationCamera":
            self.camera_window.set_callback_change_slider(self.camera_window.slider_x_centroid, self.x_centroid_change_slider_action)
            self.camera_window.set_callback_change_slider(self.camera_window.slider_y_centroid, self.y_centroid_change_slider_action)
            self.camera_window.set_callback_change_slider(self.camera_window.slider_width, self.width_change_slider_action)
            self.camera_window.set_callback_range_slider(self.camera_window.slider_x_centroid, 0, XDIM)
            self.camera_window.set_callback_range_slider(self.camera_window.slider_y_centroid, 0, YDIM)
            self.camera_window.set_callback_range_slider(self.camera_window.slider_width, 1, int(XDIM/2))
            self.camera_window.set_slider_value(self.camera_window.slider_x_centroid, int(XDIM/2))
            self.camera_window.set_slider_value(self.camera_window.slider_y_centroid, int(YDIM/2))
            self.camera_window.set_slider_value(self.camera_window.slider_width, int(XDIM/10))

############################ Callbacks #######################################

    def build_instructions_text(self):
        self.instruction_text = ""
        if type(self.camera_window.button_action_extra_state)== ButtonNok:
            self.instruction_text += "Veuillez enregistrer une image de fond avant de continuer."
        if type(self.camera_window.button_action_state) == ButtonNok:
            if(len(self.instruction_text) > 0):
                self.instruction_text += "\n"
            self.instruction_text += "Enregistrer la position du spot laser"
        
    def update_gui(self):
        # Mise à jour de la GUI en se basant sur les états des widgets
        self.camera_window.button_action_state.change_color()
        self.camera_window.button_action_extra_state.change_color()
        # On met à jour le tableau image en soustrayant le background
        self.raw_image = get_active_camera().snapshot('SPOT_LASER')
        self.np_image = get_substracted_image(self.raw_image, get_active_harmonisation_data().background_image) 
        # On met à jour l'image de la camera
        colored_image = cv2.applyColorMap(self.np_image, cv2.COLORMAP_TURBO)
        height, width = self.np_image.shape
        bytes_per_line = width
        # Convertir en QImage
        self.qimage = QImage(colored_image.data, width, height, bytes_per_line * 3, QImage.Format_RGB888)
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

    def capture_background_action(self):
        data = get_active_harmonisation_data()
        data.background_image = np.zeros((YDIM,XDIM), dtype=np.uint8)  # Reset background image
        self.np_image = get_active_camera().snapshot('SPOT_LASER') 
        # On enregistre l'image de fond dans les données
        data.background_image = self.np_image.copy() # Ajouter à harmonistation data
        self.qimage.save(f'{data.working_dir}/{data.read("SN")}_BACKGROUND.png', 'PNG')
        self.camera_window.button_action_extra_state = ButtonNoEmphasis(self.camera_window.button_action_extra)
        self.camera_window.log_text = "Image de fond enregistrée."

    def run_save_postion_spot_laser_on_new_thread(self):
        self.camera_window.log_text = "Enregistrement de la position du spot laser en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.position_spot_laser_action) 
        action_thread.start()

    def position_spot_laser_action(self):
        """
        faire un fit gaussien de l'image pour déterminer la position du spot laser
        enregistrer la position dans le json
        enregistrer l'image
        Mettre à jour le log
        Mettre à jour l'état du bouton
        """
        if type(self.camera_window.button_action_extra_state) == ButtonNok:
            self.camera_window.log_text = "Veuillez d'abord enregistrer une image de fond avant de continuer."
            return
        
        params = get_gauss_fit_params(self.np_image)
        data = get_active_harmonisation_data()
        data.laser_position_x = params['x_center']
        data.laser_position_y = params['y_center']
        data.write(f"LASER_POSITION_X_{data.step.upper()}", str(params['x_center']))
        data.write(f"LASER_POSITION_Y_{data.step.upper()}", str(params['y_center']))
        data.save()
        self.qimage.save(f'{data.working_dir}/{data.read("SN")}_LASER_POSITION_{data.step}.png', 'PNG')
        self.camera_window.log_text = f'Position du laser enregistrée : X={params["x_center"]:.2f}, Y={params["y_center"]:.2f}'
        self.camera_window.button_action_state = ButtonOk(self.camera_window.button_action)
   
    def next_button_action(self):
            if len(self.instruction_text) == 0:
                self.apd_position_controler = ApdPositionControler()
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