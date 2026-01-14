
from view.widget_state import ButtonOk, ComboBoxOk, ComboBoxNok, LineEditNoEmphasis, LineEditNok
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QImage, QPixmap
from tools.singleton import SingletonMeta
from model.data_supplements import VERSION, XDIM, YDIM
from model.camera import  get_active_camera
from model.harmonisation_data import get_active_harmonisation_data
from view.camera_window import CameraWindowApdPosition
import cv2
import threading

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
            self.camera_window.set_callback_range_slider(self.camera_window.slider_x_centroid, 0, XDIM)
            self.camera_window.set_callback_range_slider(self.camera_window.slider_y_centroid, 0, YDIM)
            self.camera_window.set_callback_range_slider(self.camera_window.slider_width, 1, int(XDIM/2))
            self.camera_window.set_slider_value(self.camera_window.slider_x_centroid, int(XDIM/2))
            self.camera_window.set_slider_value(self.camera_window.slider_y_centroid, int(YDIM/2))
            self.camera_window.set_slider_value(self.camera_window.slider_width, int(XDIM/10))

############################ Callbacks #######################################

    def build_instructions_text(self):
        self.instruction_text = ""
        
        
    def update_gui(self):
        # Mise à jour de la GUI en se basant sur les états des widgets
        self.camera_window.button_action_state.change_color()

        self.np_image = get_active_camera().snapshot('APD') 
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
        # On enregistre la position
        # On enregistre l'image
        # On met à jour le log
        # On met à jour le label affichant le résulat
        # Si donnee dans position_up et position_down alors supprimer les deux données et passer au rouge le bouton down
        self.camera_window.button_up_action_state = ButtonOk(self.camera_window.button_up_action)
        self.camera_window.log_text = "Position APD haut enregistrée."
        
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