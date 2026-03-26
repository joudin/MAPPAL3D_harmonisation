
from view.widget_state import ButtonOk, ComboBoxOk, ComboBoxNok, LineEditNoEmphasis, LineEditNok
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QImage, QPixmap
from tools.singleton import SingletonMeta
from model.data_supplements import VERSION, XDIM, YDIM
from model.camera import  get_active_camera
from model.harmonisation_data import get_active_harmonisation_data
from view.camera_window import CameraWindowExtendedFocusApd
from controler.center_emission_controler import CenterEmissionControler
import cv2
import threading
import numpy as np

DELAY = 200

class FocusApdControler(metaclass=SingletonMeta):
    def __init__(self):       
        # Comportement de la GUI
        self.camera_window = CameraWindowExtendedFocusApd()
        self.camera_window.show()
        self.camera_window.set_callback_timer(self.camera_window.timer, self.update_gui)
        self.camera_window.set_timer_timeout(self.camera_window.timer, DELAY)
        self.camera_window.set_callback_connect_button(self.camera_window.button_action, self.run_save_apd_image_new_thread)
        self.camera_window.set_button_label(self.camera_window.button_action, "Enregistrer image de l'APD au plan focal")
        self.camera_window.set_callback_connect_button(self.camera_window.button_next, self.next_button_action)
        self.camera_window.set_callback_connect_button(self.camera_window.button_exit, self.exit_application_action)
        self.camera_window.set_label_text(self.camera_window.extra_label, "Epaisseur cale pelable (mm):")
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
        if type(self.camera_window.button_action_state) == ButtonOk:
            pass
        else:
            self.instruction_text += "Enregistrer l'image de l'APD au plan focal"
        
    def update_gui(self):
        # Mise à jour de la GUI en se basant sur les états des widgets
        self.camera_window.button_action_state.change_color()
        self.camera_window.lineEdit_state.change_color()

        self.np_image = get_active_camera().snapshot('APD') 
        # On met à jour l'image de la camera
        colored_image = cv2.applyColorMap(self.np_image.astype(np.uint8), cv2.COLORMAP_TURBO)
        # Convertir BGR (OpenCV) vers RGB (QImage)
        colored_image = cv2.cvtColor(colored_image, cv2.COLOR_BGR2RGB)
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

    def amplitude_change_slider_action(self):
        cam = get_active_camera()
        if cam.__class__.__name__ == "SimulationCamera":
            cam.amplitude_simu = self.camera_window.slider_amplitude.value()

    def run_save_apd_image_new_thread(self):
        self.camera_window.log_text = "Enregistrement de l'image de l'APD au plan focal en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.apd_image_action) 
        action_thread.start()

    def apd_image_action(self):
        """
        Vérifier que le textField est rempli et valide
        Enregistrer l'epaisseur de la cale pelable dans le json
        Enregistrer l'image
        On met à jour l'etat du bouton d'action
        Mettre à jour le log
        """
        if self.camera_window.extra_lineEdit.text() != "":
            # On vérifie que la valeur numérique entrée est correcte
            try:
                reception_wedge_width_in_mm = float(self.camera_window.extra_lineEdit.text())
            except:
                self.camera_window.lineEdit_state = LineEditNok(self.camera_window.extra_lineEdit)
                self.camera_window.log_text = "Valeur d'épaisseur de cale pelable invalide."
                return
            # On met à jour l'état du champ de texte
            self.camera_window.lineEdit_state = LineEditNoEmphasis(self.camera_window.extra_lineEdit)
            data = get_active_harmonisation_data()
            data.write("RECEPTION_WEDGE_WIDTH_IN_MM", str(reception_wedge_width_in_mm))
            data.save()
            data.reception_final_wedge_width_in_mm = reception_wedge_width_in_mm
            self.qimage.save(f'{data.working_dir}/{data.read("SN")}_FOCUS_APD_{reception_wedge_width_in_mm}.png', 'PNG')
            # On vide le champ de texte
            self.camera_window.extra_lineEdit.clear()
            self.camera_window.log_text = "Image enregistrée"
            self.camera_window.button_action_state = ButtonOk(self.camera_window.button_action)
        else:
            self.camera_window.lineEdit_state = LineEditNok(self.camera_window.extra_lineEdit)
            self.camera_window.log_text = "Veuillez entrer une valeur pour l'épaisseur de la cale pelable."
     
    def next_button_action(self):
            if len(self.instruction_text) == 0:
                self.center_position_controler = CenterEmissionControler()
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