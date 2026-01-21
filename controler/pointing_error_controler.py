
from turtle import color
from view.widget_state import ButtonOk, ButtonNok
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
from tools.singleton import SingletonMeta
from model.data_supplements import VERSION, XDIM, YDIM, EUCLIDIAN_DISTANCE_CUBE_LASER_THRESHOLD_IN_PX
from model.camera import  get_active_camera
from model.harmonisation_data import get_active_harmonisation_data
from view.camera_window import CameraWindow
import cv2
from model.calculations import get_gauss_fit_params, get_euclidian_distance, get_substracted_image
import threading
import numpy as np

DELAY = 200

class PointingErrorControler(metaclass=SingletonMeta):
    def __init__(self):       
        # Comportement de la GUI
        self.camera_window = CameraWindow()
        self.camera_window.show()
        self.camera_window.set_callback_timer(self.camera_window.timer, self.update_gui)
        self.camera_window.set_timer_timeout(self.camera_window.timer, DELAY)
        self.camera_window.set_callback_connect_button(self.camera_window.button_action, self.run_pointing_error_on_new_thread)
        self.camera_window.set_button_label(self.camera_window.button_action, 'Enregistrer dépointé emission')
        self.camera_window.set_callback_connect_button(self.camera_window.button_next, self.next_button_action)
        self.camera_window.set_callback_connect_button(self.camera_window.button_exit, self.exit_application_action)
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
        
############################ Callbacks #######################################

    def build_instructions_text(self):
        self.instruction_text = ""
        if type(self.camera_window.button_action_state) == ButtonNok:
            self.instruction_text += "Enregistrer le dépointé de l'émission laser"
        
    def update_gui(self):
        # Mise à jour de la GUI en se basant sur les états des widgets
        self.camera_window.button_action_state.change_color()

         # On met à jour le tableau image en soustrayant le background
        self.raw_image = get_active_camera().snapshot('SPOT_LASER')
        self.np_image = get_substracted_image(self.raw_image, get_active_harmonisation_data().background_image)
        # On met à jour l'image de la camera
        colored_image = cv2.applyColorMap(self.np_image.astype(np.uint8), cv2.COLORMAP_TURBO)
        height, width = self.np_image.shape
        bytes_per_line = width
        # Convertir en QImage
        self.qimage = QImage(colored_image.data, width, height, bytes_per_line * 3, QImage.Format_RGB888)
        p = QPainter(self.qimage)
        p.setPen(QPen(QColor(255, 0, 0), 1))
        size = 10
        p.drawLine(int(get_active_harmonisation_data().cube_position_x) - size, int(get_active_harmonisation_data().cube_position_y) - size, int(get_active_harmonisation_data().cube_position_x) + size, int(get_active_harmonisation_data().cube_position_y) + size)  # diagonale \
        p.drawLine(int(get_active_harmonisation_data().cube_position_x) - size, int(get_active_harmonisation_data().cube_position_y) + size, int(get_active_harmonisation_data().cube_position_x) + size, int(get_active_harmonisation_data().cube_position_y) - size)  # diagonale /
        p.end()
        self.qimage.setPixel(int(get_active_harmonisation_data().cube_position_x), int(get_active_harmonisation_data().cube_position_y), 0xFF0000)  # Marquer la position du miroir en rouge
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

    def run_pointing_error_on_new_thread(self):
        self.camera_window.log_text = "Calcul du dépointé de l'émission laser en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.pointing_error_action) 
        action_thread.start()

    def pointing_error_action(self):
        """
        faire un fit gaussien de l'image pour déterminer la position du spot laser d'emission
        enregistrer la position du spot laser dans les data
        enregistrer l'image
        Mettre à jour le log
        Mettre à jour l'état du bouton
        """
        params = get_gauss_fit_params(self.np_image)
        data = get_active_harmonisation_data()
        data.laser_position_x = params['x_center']
        data.laser_position_y = params['y_center']
        data.write(f"LASER_POSITION_X_{data.step.upper()}", str(params['x_center']))
        data.write(f"LASER_POSITION_Y_{data.step.upper()}", str(params['y_center']))
        self.qimage.save(f'{data.working_dir}/{data.read("SN")}_LASER_POSITION_{data.step.upper()}.png', 'PNG')
        data.distance_cube_laser_in_px = get_euclidian_distance((data.cube_position_x, data.cube_position_y), (data.laser_position_x, data.laser_position_y))['euclidian']
        data.write(f"DISTANCE_CUBE_LASER_IN_PX_{data.step.upper()}", str(data.distance_cube_laser_in_px))
        data.save()
        if data.distance_cube_laser_in_px <= EUCLIDIAN_DISTANCE_CUBE_LASER_THRESHOLD_IN_PX:
            self.camera_window.button_action_state = ButtonOk(self.camera_window.button_action)
            self.camera_window.log_text = f'Position du spot laser enregistrée : X={params["x_center"]:.2f}, Y={params["y_center"]:.2f}\nDistance cube-spot laser = {data.distance_cube_laser_in_px:.2f} px (OK max = {EUCLIDIAN_DISTANCE_CUBE_LASER_THRESHOLD_IN_PX} px)'
        else:
            self.camera_window.button_action_state = ButtonNok(self.camera_window.button_action)
            self.camera_window.log_text = f'Position du spot laser enregistrée : X={params["x_center"]:.2f}, Y={params["y_center"]:.2f}\nDistance cube-spot laser = {data.distance_cube_laser_in_px:.2f} px (NOK max = {EUCLIDIAN_DISTANCE_CUBE_LASER_THRESHOLD_IN_PX} px)'

    def next_button_action(self):
            if len(self.instruction_text) == 0:
                self.exit_application_action()
            else:
                self.camera_window.log_text = "Veuillez compléter les instructions avant de continuer."

    def exit_application_action(self):
        cam = get_active_camera()
        if cam is not None:
            cam.disconnect()
        QApplication.quit() 
        QWidget.close(self.camera_window)