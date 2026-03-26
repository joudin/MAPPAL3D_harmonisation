
from turtle import color

import numpy as np
from view.widget_state import LineEditNok, LineEditNoEmphasis, ButtonNoEmphasis, CheckBoxNoEmphasis, ButtonNok
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QImage, QPixmap
from tools.singleton import SingletonMeta
from model.data_supplements import XDIM, YDIM, DIVERGENCE_THRESHOLD_IN_MRAD, FOCAL_LENGTH, PIXEL_SIZE
from model.camera import  get_active_camera
from model.harmonisation_data import get_active_harmonisation_data
from view.camera_window import CameraWindowExtendedDivergence
from controler.pointing_error_controler import PointingErrorControler
import cv2
from model.calculations import get_gauss_fit_params, get_gaussian_divergence_and_diameter, get_substracted_image
import threading

DELAY = 200

class DivergenceControler(metaclass=SingletonMeta):
    def __init__(self):       
        # Comportement de la GUI
        self.camera_window = CameraWindowExtendedDivergence()
        self.camera_window.show()
        self.camera_window.set_callback_timer(self.camera_window.timer, self.update_gui)
        self.camera_window.set_timer_timeout(self.camera_window.timer, DELAY)
        self.camera_window.set_callback_connect_button(self.camera_window.button_action, self.run_divergence_on_new_thread)
        self.camera_window.set_button_label(self.camera_window.button_action, 'Enregistrer Divergence')
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
        
        self.camera_window.button_action_state = ButtonNoEmphasis(self.camera_window.button_action)
############################ Callbacks #######################################

    def build_instructions_text(self):
        self.instruction_text = ""
        if get_active_harmonisation_data().emission_final_wedge_width_in_mm is None:
            self.instruction_text += "Pour plusieurs épaisseurs de cale pelable, mesurer la divergence jusqu'à observer un minimum.\nPuis enregistrer la divergence finale avec l'épaisseur de cale pelable définitive."
        
    def update_gui(self):
        # Mise à jour de la GUI en se basant sur les états des widgets
        self.camera_window.lineEdit_state.change_color()
        # On met à jour le tableau image en soustrayant le background
        self.raw_image = get_active_camera().snapshot('SPOT_LASER')
        data = get_active_harmonisation_data()
        if hasattr(data, 'background_image') and data.background_image is not None:
            self.np_image = get_substracted_image(self.raw_image.astype(np.uint8), data.background_image)
        else:
            self.np_image = self.raw_image
        # On met à jour l'image de la camera
        colored_image = cv2.applyColorMap(self.np_image, cv2.COLORMAP_JET)
        # Convertir BGR (OpenCV) vers RGB (QImage)
        colored_image = cv2.cvtColor(colored_image, cv2.COLOR_BGR2RGB)
        height, width = self.np_image.shape
        bytes_per_line = width
        # Convertir en QImage
        self.qimage = QImage(colored_image.data, width, height, bytes_per_line * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(self.qimage)
        self.camera_window.image_label.setPixmap(pixmap)

        # On met à jour le scatter plot
        data = get_active_harmonisation_data()
        try:
            if  len(data.wedge_width_list_in_mm) == len(data.divergence_list_in_mrad) and len(data.divergence_list_in_mrad) != 0:
                self.camera_window.canvas.axes.cla()
                self.camera_window.canvas.axes.scatter(data.wedge_width_list_in_mm, data.divergence_list_in_mrad)
                if data.emission_final_wedge_width_in_mm is not None:
                    self.camera_window.canvas.axes.scatter(data.emission_final_wedge_width_in_mm, data.divergence_list_in_mrad[-1], color='green', s=100, label='Cale pelable définitive')
                self.camera_window.canvas.axes.plot([min(data.wedge_width_list_in_mm)-0.1,max(data.wedge_width_list_in_mm)+0.1],[DIVERGENCE_THRESHOLD_IN_MRAD,DIVERGENCE_THRESHOLD_IN_MRAD],color='red', label='Seuil de divergence')
                self.camera_window.canvas.axes.set_xlabel("Epaisseur cale pelable (mm)")
                self.camera_window.canvas.axes.set_ylabel("divergence (mrad)")
                self.camera_window.canvas.axes.set_title("Divergence en fonction de l'épaisseur de cale pelable")
                self.camera_window.canvas.draw()
        except:
            print("X et Y n'ont pas les memes dimentions")

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

    def run_divergence_on_new_thread(self):
        self.camera_window.log_text = "Calcul de la divergence en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.divergence_action) 
        action_thread.start()

    def divergence_action(self):
        """
        Vérifier que le textField est rempli et valide
        Faire un fit gaussien de l'image pour déterminer la divergence
        Enregistrer la divergence dans le json
        Enregistrer l'image
        Mettre à jour les listes pour le scatter plot
        Mettre à jour le log
    
        """
        if self.camera_window.extra_lineEdit.text() != "":
            # On vérifie que la valeur numérique entrée est correcte
            try:
                wedge_width_in_mm = float(self.camera_window.extra_lineEdit.text())
            except:
                self.camera_window.lineEdit_state = LineEditNok(self.camera_window.extra_lineEdit)
                self.camera_window.log_text = "Valeur d'épaisseur de cale pelable invalide."
                return
            # On met à jour l'état du champ de texte
            self.camera_window.lineEdit_state = LineEditNoEmphasis(self.camera_window.extra_lineEdit)
            # On calcule la divergence et on enregistre les résultats
            params = get_gauss_fit_params(self.np_image)
            data = get_active_harmonisation_data()
            dict_results = get_gaussian_divergence_and_diameter(params, FOCAL_LENGTH, PIXEL_SIZE)
            data.divergence_in_mrad = dict_results['divergence']*1000  # conversion en mrad
            data.write("DIVERGENCE_IN_MRAD", str(data.divergence_in_mrad))
            if self.camera_window.extra_checkbox.isChecked():
                data.emission_final_wedge_width_in_mm = wedge_width_in_mm
                data.write("EMISSION_WEDGE_WIDTH_IN_MM", str(wedge_width_in_mm))
            data.save()
            self.qimage.save(f'{data.working_dir}/{data.read("SN")}_DIVERGENCE.png', 'PNG')
            
            # On ajoute les valeurs dans les listes pour tracer le scatter plot
            data.wedge_width_list_in_mm.append(wedge_width_in_mm)
            data.divergence_list_in_mrad.append(data.divergence_in_mrad)

            if data.divergence_in_mrad <= DIVERGENCE_THRESHOLD_IN_MRAD:
                self.camera_window.log_text = f'Divergence enregistrée : {data.divergence_in_mrad:.2f}\n (OK max ={DIVERGENCE_THRESHOLD_IN_MRAD} mrad)'
            else:
                self.camera_window.log_text = f'Divergence enregistrée : {data.divergence_in_mrad:.2f}\n (NOK max ={DIVERGENCE_THRESHOLD_IN_MRAD} mrad)'
            
            # On vide le champ de texte
            self.camera_window.extra_lineEdit.clear()
        else:
            self.camera_window.lineEdit_state = LineEditNok(self.camera_window.extra_lineEdit)
            self.camera_window.log_text = "Veuillez entrer une valeur pour l'épaisseur de la cale pelable."

    def next_button_action(self):
            if len(self.instruction_text) == 0:
                self.divergence_controler = PointingErrorControler()
                self.camera_window.close()
                self.camera_window.stop_timer(self.camera_window.timer)
            else:
                self.camera_window.log_text = "Veuillez compléter les instructions avant de continuer."

    def exit_application_action(self):
        cam = get_active_camera()
        if cam is not None:
            cam.disconnect()
        QApplication.quit() 
        QWidget.close(self.camera_window)
