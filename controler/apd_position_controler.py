
from view.widget_state import ButtonOk, ButtonNok, ComboBoxNok, LineEditNoEmphasis, LineEditNok
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
from tools.singleton import SingletonMeta
from model.data_supplements import VERSION, XDIM, YDIM
from model.camera import  get_active_camera
from model.harmonisation_data import get_active_harmonisation_data
from view.camera_window import CameraWindowApdPosition
from model.calculations import get_circle_fit_params
import cv2
import threading
import numpy as np

DELAY = 200

class ApdPositionControler(metaclass=SingletonMeta):
    def __init__(self):       
        # Comportement de la GUI
        self.camera_window = CameraWindowApdPosition()
        self.camera_window.show()
        self.camera_window.set_callback_timer(self.camera_window.timer, self.update_gui)
        self.camera_window.set_timer_timeout(self.camera_window.timer, DELAY)
        self.camera_window.set_callback_connect_button(self.camera_window.button_action, self.run_pass_fail_action_on_new_thread)
        self.camera_window.set_callback_connect_button(self.camera_window.button_next, self.next_button_action)
        self.camera_window.set_callback_connect_button(self.camera_window.button_exit, self.exit_application_action)
        self.camera_window.set_callback_connect_button(self.camera_window.button_up_action, self.run_apd_position_up_on_new_thread)
        self.camera_window.set_callback_connect_button(self.camera_window.button_down_action, self.run_apd_position_down_on_new_thread)
        self.camera_window.set_callback_connect_button(self.camera_window.button_left_action, self.run_apd_position_left_on_new_thread)
        self.camera_window.set_callback_connect_button(self.camera_window.button_right_action, self.run_apd_position_right_on_new_thread)
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
        # PAramètres pour fit circulaires
        DELTA_CENTER = 50#30
        LIM_DELTA_CENTER = 200


        # For circle fitting
        I_MIN = 75 
        I_STD = 100
        I_MAX = 255 

        APD_R_MIN = 93
        APD_R_STD = 103
        APD_R_MAX = 113 

        DECAY_MIN = 100
        DECAY_STD = 300
        DECAY_MAX = 600

        pulse_center_x = int(YDIM/2)
        pulse_center_y = int(XDIM/2)

        self.bounds=([I_MIN,  pulse_center_x-LIM_DELTA_CENTER, pulse_center_y-LIM_DELTA_CENTER, APD_R_MIN, DECAY_MIN],   # bornes inf
                [I_MAX, pulse_center_x+LIM_DELTA_CENTER, pulse_center_y+LIM_DELTA_CENTER, APD_R_MAX, DECAY_MAX])   # bornes sup
        
        self.p0_init_up = (I_STD, pulse_center_x+DELTA_CENTER, pulse_center_y, APD_R_STD, DECAY_STD)
        self.p0_init_down = (I_STD, pulse_center_x-DELTA_CENTER, pulse_center_y, APD_R_STD, DECAY_STD)
        self.p0_init_left = (I_STD, pulse_center_x, pulse_center_y+DELTA_CENTER, APD_R_STD, DECAY_STD)
        self.p0_init_right = (I_STD, pulse_center_x, pulse_center_y-DELTA_CENTER, APD_R_STD, DECAY_STD)
############################ Callbacks #######################################

    def build_instructions_text(self):
        self.instruction_text = ""
        if type(self.camera_window.button_up_action_state) == ButtonNok:
            self.instruction_text += "Enregistrer la position APD haute"
        if type(self.camera_window.button_down_action_state) == ButtonNok:
            if len(self.instruction_text) > 0:
                self.instruction_text += '\n'
            self.instruction_text += "Enregistrer la position APD basse"
        if type(self.camera_window.button_left_action_state) == ButtonNok:
            if len(self.instruction_text) > 0:
                self.instruction_text += '\n'
            self.instruction_text += "Enregistrer la position APD gauche"
        if type(self.camera_window.button_right_action_state) == ButtonNok:
            if len(self.instruction_text) > 0:
                self.instruction_text += '\n'
            self.instruction_text += "Enregistrer la position APD droite"
        if type(self.camera_window.button_action_state) == ButtonNok:
            if len(self.instruction_text) > 0:
                self.instruction_text += '\n'
            self.instruction_text += "Appliquer le critere pass/fail"
        
        
    def update_gui(self):
        # Mise à jour de la GUI en se basant sur les états des widgets
        self.camera_window.button_action_state.change_color()
        self.camera_window.button_up_action_state.change_color()
        self.camera_window.button_down_action_state.change_color()
        self.camera_window.button_left_action_state.change_color()
        self.camera_window.button_right_action_state.change_color()

        self.np_image = get_active_camera().snapshot('APD') 
        # On met à jour l'image de la camera
        colored_image = cv2.applyColorMap(self.np_image.astype(np.uint8), cv2.COLORMAP_TURBO)
        height, width = self.np_image.shape
        bytes_per_line = width
        # Convertir en QImage
        self.qimage = QImage(colored_image.data, width, height, bytes_per_line * 3, QImage.Format_RGB888)
        
       
        if get_active_harmonisation_data().apd_position_up_x is not None and get_active_harmonisation_data().apd_position_up_y is not None:
            p = QPainter(self.qimage)
            p.setPen(QPen(QColor(255, 0, 0), 1))
            size = 10
            p.drawLine(int(get_active_harmonisation_data().apd_position_up_x) - size, int(get_active_harmonisation_data().apd_position_up_y) - size, int(get_active_harmonisation_data().apd_position_up_x) + size, int(get_active_harmonisation_data().apd_position_up_y) + size)  # diagonale \
            p.drawLine(int(get_active_harmonisation_data().apd_position_up_x) - size, int(get_active_harmonisation_data().apd_position_up_y) + size, int(get_active_harmonisation_data().apd_position_up_x) + size, int(get_active_harmonisation_data().apd_position_up_y) - size)  # diagonale /
            p.end()
        pixmap = QPixmap.fromImage(self.qimage)
        self.camera_window.image_label.setPixmap(pixmap)

        # On construit le texte donnant les instructions restantes en fonction de l'état des widgets
        self.build_instructions_text()
        self.camera_window.instruction_label.setText(self.instruction_text)
        # On affiche les logs
        self.camera_window.log_label.setText(self.camera_window.log_text)

    def run_pass_fail_action_on_new_thread(self):
        self.camera_window.log_text = "Enregistrement de l'image de l'APD au plan focal en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.pass_fail_action) 
        action_thread.start()

    def pass_fail_action(self):
        # Enregistrement du resultat 
        # Evaluation du critere pass/fail
        # Gestion de l'etat du bouton
        self.camera_window.button_action_state = ButtonOk(self.camera_window.button_action)

    def run_apd_position_up_on_new_thread(self):
        self.camera_window.log_text = "Enregistrement de l'image de l'APD et calcule de la position APD up en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.apd_position_up) 
        action_thread.start()

    def apd_position_up(self):
        # 1 - Evaluer la position APD
        # 2 - Enregistrer la position dans data
        # 3 - Enregistrer la position dans le JSON
        # 4 - Enregistrer l'image
        # 5 - Mettre à jour le label résultat
        # 6 - Mettre à jour le log
        # 7 - Mettre à jour le statut bouton
        # 8 - Afficher la position du centre sur l'image
        # Si donnee dans position_up et position_down alors supprimer les deux données et passer au rouge le bouton down
        data = get_active_harmonisation_data()
        if data.apd_position_up_x is not None and data.apd_position_up_y is not None:
            data.apd_position_up_x = None
            data.apd_position_up_y = None
            self.camera_window.button_down_action_state = ButtonNok(self.camera_window.button_down_action)
        
        params = get_circle_fit_params(self.np_image,p0=self.p0_init_up, bounds=self.bounds)
        data.apd_position_up_x = params['x_center']
        data.apd_position_up_y = params['y_center']
        data.write(f"APD_POSITION_UP_X{data.step.upper()}", str(data.apd_position_up_x))
        data.write(f"APD_POSITION_UP_Y{data.step.upper()}", str(data.apd_position_up_y))
        data.save()
        self.qimage.save(f'{data.working_dir}/{data.read("SN")}APD_POSITION_UP_{data.step}.png', 'PNG')
        self.camera_window.set_label_text(self.camera_window.button_up_results_label,f'X = {data.apd_position_up_x:.1f} Y = {data.apd_position_up_y:.1f}')
        print(f'params = {params}')
        self.camera_window.log_text = "Position APD haut enregistrée."
        self.camera_window.button_up_action_state = ButtonOk(self.camera_window.button_up_action)
        
    def run_apd_position_down_on_new_thread(self):
        self.camera_window.log_text = "Enregistrement de l'image de l'APD et calcule de la position APD down en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.apd_position_down) 
        action_thread.start()
    
    def apd_position_down(self):
        # On enregistre la position
        # On enregistre l'image
        # On met à jour le log
        # On met à jour le label affichant le résulat
        # Si donnee dans position_up et position_down alors supprimer les deux données et passer au rouge le bouton up
        self.camera_window.button_down_action_state = ButtonOk(self.camera_window.button_down_action)
        self.camera_window.log_text = "Position APD bas enregistrée."

    def run_apd_position_left_on_new_thread(self):
        self.camera_window.log_text = "Enregistrement de l'image de l'APD et calcule de la position APD left en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.apd_position_left) 
        action_thread.start()

    def apd_position_left(self):
        # On enregistre la position
        # On enregistre l'image
        # On met à jour le log
        # On met à jour le label affichant le résulat
        # Si donnee dans position_left et position_right alors supprimer les deux données et passer au rouge le bouton right
        self.camera_window.button_left_action_state = ButtonOk(self.camera_window.button_left_action)
        self.camera_window.log_text = "Position APD gauche enregistrée."
      
    def run_apd_position_right_on_new_thread(self):
        self.camera_window.log_text = "Enregistrement de l'image de l'APD et calcule de la position APD right en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.apd_position_right) 
        action_thread.start()

    def apd_position_right(self):
        # On enregistre la position
        # On enregistre l'image
        # On met à jour le log
        # On met à jour le label affichant le résulat
        # Si donnee dans position_left et position_right alors supprimer les deux données et passer au rouge le bouton left
        self.camera_window.button_right_action_state = ButtonOk(self.camera_window.button_right_action)
        self.camera_window.log_text = "Position APD droite enregistrée."

    def next_button_action(self):
            if len(self.instruction_text) == 0:
                self.exit_application_action()
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