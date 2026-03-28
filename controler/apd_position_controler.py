
from view.widget_state import ButtonOk, ButtonNok, ButtonNoEmphasis, ComboBoxNok, LineEditNoEmphasis, LineEditNok
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
from tools.singleton import SingletonMeta
from model.data_supplements import VERSION, XDIM, YDIM, APD_CENTERS_DISTANCE_THRESHOLD_IN_PX
from model.camera import  get_active_camera
from model.harmonisation_data import get_active_harmonisation_data
from view.camera_window import CameraWindowApdPosition
from model.calculations import get_circle_fit_params, get_euclidian_distance, get_substracted_image
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
        self.camera_window.set_callback_connect_button(self.camera_window.button_action_extra, self.capture_background_action)
        self.camera_window.set_callback_connect_button(self.camera_window.button_next, self.next_button_action)
        self.camera_window.set_callback_connect_button(self.camera_window.button_exit, self.exit_application_action)
        self.camera_window.set_callback_connect_button(self.camera_window.button_up_action, self.run_apd_position_up_on_new_thread)
        self.camera_window.set_callback_connect_button(self.camera_window.button_down_action, self.run_apd_position_down_on_new_thread)
        self.camera_window.set_callback_connect_button(self.camera_window.button_left_action, self.run_apd_position_left_on_new_thread)
        self.camera_window.set_callback_connect_button(self.camera_window.button_right_action, self.run_apd_position_right_on_new_thread)
        self.camera_window.exposure_combobox.currentIndexChanged.connect(self.set_exposure_time_action)
        self.camera_window.button_action_extra_state = ButtonNok(self.camera_window.button_action_extra)
        # applique l'exposition initiale
        self.set_exposure_time_action()
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
        DELTA_CENTER = 70
        LIM_DELTA_CENTER = 200


        # For circle fitting
        I_MIN = 10 
        I_STD = 100
        I_MAX = 255 

        APD_R_MIN = 93
        APD_R_STD = 103
        APD_R_MAX = 113 

        DECAY_MIN = 100
        DECAY_STD = 300
        DECAY_MAX = 600

        pulse_center_x = int(YDIM/2) #160
        pulse_center_y = int(XDIM/2) #128

        self.bounds=([I_MIN,  pulse_center_x-LIM_DELTA_CENTER, pulse_center_y-LIM_DELTA_CENTER, APD_R_MIN, DECAY_MIN],   # bornes inf
                [I_MAX, pulse_center_x+LIM_DELTA_CENTER, pulse_center_y+LIM_DELTA_CENTER, APD_R_MAX, DECAY_MAX])   # bornes sup
     
        self.p0_init = (I_STD, XDIM/2, YDIM/2, APD_R_STD, DECAY_STD)

############################ Callbacks #######################################

    def set_exposure_time_action(self):
        selected_value = int(self.camera_window.exposure_combobox.currentText())
        camera = get_active_camera()
        success = camera.set_exposure_time(selected_value)
        if success:
            self.camera_window.log_text = f"Exposure réglée sur {selected_value} ms"
        else:
            self.camera_window.log_text = f"Échec du réglage exposure {selected_value} ms"

    def build_instructions_text(self):
        self.instruction_text = ""
        if type(self.camera_window.button_action_extra_state) == ButtonNok:
            self.instruction_text += "Veuillez enregistrer une image de fond avant de continuer."
        if type(self.camera_window.button_up_action_state) == ButtonNok:
            if len(self.instruction_text) > 0:
                self.instruction_text += '\n'
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

        self.raw_image = get_active_camera().snapshot('APD')
        data = get_active_harmonisation_data()
        if hasattr(data, 'background_image') and data.background_image is not None:
            self.np_image = get_substracted_image(self.raw_image, data.background_image)
        else:
            self.np_image = self.raw_image 
        # On met à jour l'image de la camera
        colored_image = cv2.applyColorMap(self.np_image.astype(np.uint8), cv2.COLORMAP_TURBO)
        # Convertir BGR (OpenCV) vers RGB (QImage)
        colored_image = cv2.cvtColor(colored_image, cv2.COLOR_BGR2RGB)
        height, width = self.np_image.shape
        bytes_per_line = width
        # Convertir en QImage
        self.qimage = QImage(colored_image.data, width, height, bytes_per_line * 3, QImage.Format_RGB888)
        # On dessine un croix pour la position de référence du laser
        if get_active_harmonisation_data().laser_position_x is not None and get_active_harmonisation_data().laser_position_y is not None:
            p = QPainter(self.qimage)
            p.setPen(QPen(QColor(255, 222, 33), 1))
            size = 10
            p.drawLine(int(get_active_harmonisation_data().laser_position_x) - size, int(get_active_harmonisation_data().laser_position_y) - size, int(get_active_harmonisation_data().laser_position_x) + size, int(get_active_harmonisation_data().laser_position_y) + size)  # diagonale \
            p.drawLine(int(get_active_harmonisation_data().laser_position_x) - size, int(get_active_harmonisation_data().laser_position_y) + size, int(get_active_harmonisation_data().laser_position_x) + size, int(get_active_harmonisation_data().laser_position_y) - size)  # diagonale /
            p.end()
        # On dessine les croix aux positions enregistrées
        if get_active_harmonisation_data().apd_position_up_x is not None and get_active_harmonisation_data().apd_position_up_y is not None:
            p = QPainter(self.qimage)
            p.setPen(QPen(QColor(255, 0, 0), 1))
            size = 10
            p.drawLine(int(get_active_harmonisation_data().apd_position_up_x) - size, int(get_active_harmonisation_data().apd_position_up_y) - size, int(get_active_harmonisation_data().apd_position_up_x) + size, int(get_active_harmonisation_data().apd_position_up_y) + size)  # diagonale \
            p.drawLine(int(get_active_harmonisation_data().apd_position_up_x) - size, int(get_active_harmonisation_data().apd_position_up_y) + size, int(get_active_harmonisation_data().apd_position_up_x) + size, int(get_active_harmonisation_data().apd_position_up_y) - size)  # diagonale /
            p.end()
        if get_active_harmonisation_data().apd_position_down_x is not None and get_active_harmonisation_data().apd_position_down_y is not None:
            p = QPainter(self.qimage)
            p.setPen(QPen(QColor(255, 0, 0), 1))
            size = 10
            p.drawLine(int(get_active_harmonisation_data().apd_position_down_x) - size, int(get_active_harmonisation_data().apd_position_down_y) - size, int(get_active_harmonisation_data().apd_position_down_x) + size, int(get_active_harmonisation_data().apd_position_down_y) + size)  # diagonale \
            p.drawLine(int(get_active_harmonisation_data().apd_position_down_x) - size, int(get_active_harmonisation_data().apd_position_down_y) + size, int(get_active_harmonisation_data().apd_position_down_x) + size, int(get_active_harmonisation_data().apd_position_down_y) - size)  # diagonale /
            p.end()
        if get_active_harmonisation_data().apd_position_left_x is not None and get_active_harmonisation_data().apd_position_left_y is not None:
            p = QPainter(self.qimage)
            p.setPen(QPen(QColor(0, 255, 0), 1))
            size = 10
            p.drawLine(int(get_active_harmonisation_data().apd_position_left_x) - size, int(get_active_harmonisation_data().apd_position_left_y) - size, int(get_active_harmonisation_data().apd_position_left_x) + size, int(get_active_harmonisation_data().apd_position_left_y) + size)  # diagonale \
            p.drawLine(int(get_active_harmonisation_data().apd_position_left_x) - size, int(get_active_harmonisation_data().apd_position_left_y) + size, int(get_active_harmonisation_data().apd_position_left_x) + size, int(get_active_harmonisation_data().apd_position_left_y) - size)  # diagonale /
            p.end()
        if get_active_harmonisation_data().apd_position_right_x is not None and get_active_harmonisation_data().apd_position_right_y is not None:
            p = QPainter(self.qimage)
            p.setPen(QPen(QColor(0, 255, 0), 1))
            size = 10
            p.drawLine(int(get_active_harmonisation_data().apd_position_right_x) - size, int(get_active_harmonisation_data().apd_position_right_y) - size, int(get_active_harmonisation_data().apd_position_right_x) + size, int(get_active_harmonisation_data().apd_position_right_y) + size)  # diagonale \
            p.drawLine(int(get_active_harmonisation_data().apd_position_right_x) - size, int(get_active_harmonisation_data().apd_position_right_y) + size, int(get_active_harmonisation_data().apd_position_right_x) + size, int(get_active_harmonisation_data().apd_position_right_y) - size)  # diagonale /
            p.end()

        pixmap = QPixmap.fromImage(self.qimage)
        self.camera_window.image_label.setPixmap(pixmap)

        # On construit le texte donnant les instructions restantes en fonction de l'état des widgets
        self.build_instructions_text()
        self.camera_window.instruction_label.setText(self.instruction_text)
        # On affiche les logs
        self.camera_window.log_label.setText(self.camera_window.log_text)

    def run_pass_fail_action_on_new_thread(self):
        data = get_active_harmonisation_data()
        if data.apd_position_up_x is not None and data.apd_position_up_y is not None and data.apd_position_down_x is not None and data.apd_position_down_y is not None and data.apd_position_left_x is not None and data.apd_position_left_y is not None and data.apd_position_right_x is not None and data.apd_position_right_y is not None:
            self.camera_window.log_text = "Pass fail centrage APD cours..."
            # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
            action_thread = threading.Thread(target=self.pass_fail_action) 
            action_thread.start()
        else:
            self.camera_window.log_text = "Veuillez enregistrer l'ensemble des positions APD avant d'appliquer le critere pass/fail."

    def capture_background_action(self):
        data = get_active_harmonisation_data()
        data.background_image = np.zeros((YDIM, XDIM), dtype=np.uint8)

        num_frames = 10
        accumulated_image = np.zeros((YDIM, XDIM), dtype=np.float32)

        self.camera_window.log_text = "Capture d'images de fond en cours..."
        for i in range(num_frames):
            frame = get_active_camera().snapshot('SPOT_LASER')
            accumulated_image += frame.astype(np.float32)
            self.camera_window.log_text = f"Capture {i+1}/{num_frames}..."

        averaged_image = (accumulated_image / num_frames).astype(np.uint8)
        data.background_image = averaged_image.copy()

        colored_image = cv2.applyColorMap(averaged_image, cv2.COLORMAP_TURBO)
        colored_image = cv2.cvtColor(colored_image, cv2.COLOR_BGR2RGB)
        height, width = averaged_image.shape
        bytes_per_line = width
        qimage_averaged = QImage(colored_image.data, width, height, bytes_per_line * 3, QImage.Format_RGB888)
        qimage_averaged.save(f'{data.working_dir}/{data.read("SN")}_BACKGROUND.png', 'PNG')

        self.camera_window.button_action_extra_state = ButtonNoEmphasis(self.camera_window.button_action_extra)
        self.camera_window.log_text = "Image de fond moyennée enregistrée."

    def pass_fail_action(self):
        # Evaluation du critere pass/fail
        # Enregistrement du resultat 
        # Gestion de l'etat du bouton
        data = get_active_harmonisation_data()
        centers_x = [data.apd_position_up_x, data.apd_position_down_x, data.apd_position_left_x, data.apd_position_right_x]
        centers_y = [data.apd_position_up_y, data.apd_position_down_y, data.apd_position_left_y, data.apd_position_right_y]
        apd_center_x = np.mean(centers_x)
        apd_center_y = np.mean(centers_y)
        data_distances = get_euclidian_distance((apd_center_x, apd_center_y), (data.laser_position_x, data.laser_position_y))
        if data_distances['euclidian'] <= APD_CENTERS_DISTANCE_THRESHOLD_IN_PX:
            self.camera_window.log_text = f"Critere PASS : distance entre centre APD et laser = {data_distances['euclidian']:.1f} px <= {APD_CENTERS_DISTANCE_THRESHOLD_IN_PX} px"
            data.distance_laser_apd_in_px = data_distances['euclidian']
            data.write("DISTANCE_LASER_APD_IN_PX", str(data.distance_laser_apd_in_px))
            data.save()
            self.camera_window.button_action_state = ButtonOk(self.camera_window.button_action)
        else:
            self.camera_window.log_text = f"Critere FAIL : distance entre centre APD et laser = {data_distances['euclidian']:.1f} px > {APD_CENTERS_DISTANCE_THRESHOLD_IN_PX} px"
            self.camera_window.button_action_state = ButtonNok(self.camera_window.button_action)

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
        image_to_process = self.np_image
        # On met à jour l'image de la camera
        colored_image = cv2.applyColorMap(image_to_process.astype(np.uint8), cv2.COLORMAP_TURBO)
        # Convertir BGR (OpenCV) vers RGB (QImage)
        colored_image = cv2.cvtColor(colored_image, cv2.COLOR_BGR2RGB)
        height, width = image_to_process.shape
        bytes_per_line = width
        # Convertir en QImage
        self.qimage_to_save = QImage(colored_image.data, width, height, bytes_per_line * 3, QImage.Format_RGB888)
        self.qimage_to_save.save(f'{data.working_dir}/{data.read("SN")}APD_POSITION_UP.png', 'PNG')
       
        params = get_circle_fit_params(image_to_process,p0=self.p0_init, bounds=self.bounds)
        data.apd_position_up_x = params['x_center']
        data.apd_position_up_y = params['y_center']
        data.write(f"APD_POSITION_UP_X", str(data.apd_position_up_x))
        data.write(f"APD_POSITION_UP_Y", str(data.apd_position_up_y))
        data.save()
        
        self.camera_window.set_label_text(self.camera_window.button_up_results_label,f'X = {data.apd_position_up_x:.1f} Y = {data.apd_position_up_y:.1f}')
        self.camera_window.log_text = "Position APD haut enregistrée."
        self.camera_window.button_up_action_state = ButtonOk(self.camera_window.button_up_action)
        
    def run_apd_position_down_on_new_thread(self):
        self.camera_window.log_text = "Enregistrement de l'image de l'APD et calcule de la position APD down en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.apd_position_down) 
        action_thread.start()
    
    def apd_position_down(self):
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
        image_to_process = self.np_image
        # On met à jour l'image de la camera
        colored_image = cv2.applyColorMap(image_to_process.astype(np.uint8), cv2.COLORMAP_TURBO)
        # Convertir BGR (OpenCV) vers RGB (QImage)
        colored_image = cv2.cvtColor(colored_image, cv2.COLOR_BGR2RGB)
        height, width = image_to_process.shape
        bytes_per_line = width
        # Convertir en QImage
        self.qimage_to_save = QImage(colored_image.data, width, height, bytes_per_line * 3, QImage.Format_RGB888)
        self.qimage_to_save.save(f'{data.working_dir}/{data.read("SN")}APD_POSITION_DOWN.png', 'PNG')
       
        params = get_circle_fit_params(image_to_process,p0=self.p0_init, bounds=self.bounds)
        data.apd_position_down_x = params['x_center']
        data.apd_position_down_y = params['y_center']
        data.write(f"APD_POSITION_DOWN_X", str(data.apd_position_down_x))
        data.write(f"APD_POSITION_DOWN_Y", str(data.apd_position_down_y))
        data.save()
        self.camera_window.set_label_text(self.camera_window.button_down_results_label,f'X = {data.apd_position_down_x:.1f} Y = {data.apd_position_down_y:.1f}')
        self.camera_window.log_text = "Position APD bas enregistrée."
        self.camera_window.button_down_action_state = ButtonOk(self.camera_window.button_down_action)

    def run_apd_position_left_on_new_thread(self):
        self.camera_window.log_text = "Enregistrement de l'image de l'APD et calcule de la position APD left en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.apd_position_left) 
        action_thread.start()

    def apd_position_left(self):
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
        image_to_process = self.np_image
        # On met à jour l'image de la camera
        colored_image = cv2.applyColorMap(image_to_process.astype(np.uint8), cv2.COLORMAP_TURBO)
        # Convertir BGR (OpenCV) vers RGB (QImage)
        colored_image = cv2.cvtColor(colored_image, cv2.COLOR_BGR2RGB)
        height, width = image_to_process.shape
        bytes_per_line = width
        # Convertir en QImage
        self.qimage_to_save = QImage(colored_image.data, width, height, bytes_per_line * 3, QImage.Format_RGB888)
        self.qimage_to_save.save(f'{data.working_dir}/{data.read("SN")}APD_POSITION_LEFT.png', 'PNG')
       
        params = get_circle_fit_params(image_to_process,p0=self.p0_init, bounds=self.bounds)
        data.apd_position_left_x = params['x_center']
        data.apd_position_left_y = params['y_center']
        data.write(f"APD_POSITION_LEFT_X", str(data.apd_position_left_x))
        data.write(f"APD_POSITION_LEFT_Y", str(data.apd_position_left_y))
        data.save()
        self.camera_window.set_label_text(self.camera_window.button_left_results_label,f'X = {data.apd_position_left_x:.1f} Y = {data.apd_position_left_y:.1f}')
        self.camera_window.log_text = "Position APD gauche enregistrée."
        self.camera_window.button_left_action_state = ButtonOk(self.camera_window.button_left_action)

    def run_apd_position_right_on_new_thread(self):
        self.camera_window.log_text = "Enregistrement de l'image de l'APD et calcule de la position APD right en cours..."
        # On lance le calcul sur un autre thread pour ne pas bloquer la GUI
        action_thread = threading.Thread(target=self.apd_position_right) 
        action_thread.start()

    def apd_position_right(self):
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
        image_to_process = self.np_image
        # On met à jour l'image de la camera
        colored_image = cv2.applyColorMap(image_to_process.astype(np.uint8), cv2.COLORMAP_TURBO)
        # Convertir BGR (OpenCV) vers RGB (QImage)
        colored_image = cv2.cvtColor(colored_image, cv2.COLOR_BGR2RGB)
        height, width = image_to_process.shape
        bytes_per_line = width
        # Convertir en QImage
        self.qimage_to_save = QImage(colored_image.data, width, height, bytes_per_line * 3, QImage.Format_RGB888)
        self.qimage_to_save.save(f'{data.working_dir}/{data.read("SN")}APD_POSITION_RIGHT.png', 'PNG')
       
        params = get_circle_fit_params(image_to_process,p0=self.p0_init, bounds=self.bounds)
        data.apd_position_right_x = params['x_center']
        data.apd_position_right_y = params['y_center']
        data.write(f"APD_POSITION_RIGHT_X", str(data.apd_position_right_x))
        data.write(f"APD_POSITION_RIGHT_Y", str(data.apd_position_right_y))
        data.save()
        
        self.camera_window.set_label_text(self.camera_window.button_right_results_label,f'X = {data.apd_position_right_x:.1f} Y = {data.apd_position_right_y:.1f}')
        self.camera_window.log_text = "Position APD droit enregistrée."
        self.camera_window.button_right_action_state = ButtonOk(self.camera_window.button_right_action)

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