# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 10:16:06 2024

@author: joudin
"""


from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QLineEdit, QCheckBox, QGridLayout, QComboBox
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5 import QtCore
from view.widget_state import ButtonNoEmphasis, ButtonNok, LineEditNoEmphasis, CheckBoxNoEmphasis
from model.data_supplements import VERSION
from model.camera import get_active_camera
from view.mpl_canvas import MplCanvas

class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):        

        # On implémente la GUI
        self.setWindowTitle(f'Utilitaire v{VERSION}')
        self.setGeometry(100, 100, 500, 700)
        
        # Label pour informer l'utilisateur des instructions
        self.instruction_label_title = QLabel("<i><b>Instructions à réaliser</i></b>",self)
        self.instruction_label_title.setFont(QFont("Roboto", 15))
        self.instruction_label = QLabel("",self)
        self.instruction_label.setFont(QFont("Roboto", 10))
        self.instruction_label.setStyleSheet("border: 1px solid white;")

        # Image de la caméra
        self.camera_last_image = QImage()
        pixmap = QPixmap.fromImage(self.camera_last_image)
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        
        # Sliders utilisés en mode simulation pour régler la position du spot
        # Trois sliders horizontaux: x_centroid, y_centroid et width
        self.slider_x_centroid = QSlider(QtCore.Qt.Horizontal)
        self.slider_y_centroid = QSlider(QtCore.Qt.Horizontal)
        self.slider_width = QSlider(QtCore.Qt.Horizontal)
        self.slider_amplitude = QSlider(QtCore.Qt.Horizontal)
        self.slider_x_centroid_label = QLabel('X_centroid')
        self.slider_y_centroid_label = QLabel('Y_centroid')
        self.slider_width_label = QLabel('Width')
        self.slider_amplitude_label = QLabel('Amplitude')

        # Label pour informer l'utilisateur des logs
        self.log_text = ""
        self.log_label = QLabel(self.log_text,self)
        self.log_label.setFont(QFont("Roboto", 8))

        # Bouton pour calculer la position du spot
        self.button_action = QPushButton('Action', self)

        # Bouton pour passer à la suite de la séquence de programmation
        self.button_next = QPushButton('Suivant', self)
        
        # Boutton de sortie pour quitter proprement l'application
        self.button_exit = QPushButton("Exit", self)
        
        # Mise en forme de la GUI
        self.main_layout_v = QVBoxLayout()

        self.main_layout_v.addWidget(self.instruction_label_title)
        self.main_layout_v.addWidget(self.instruction_label)
        self.layout_h1 = QHBoxLayout()
        self.layout_h1.addStretch()
        self.layout_h1.addWidget(self.image_label)
        self.layout_h1.addStretch()
        # Reste une place sur layout_h1 pour ajouter un graphique si besoin
        self.main_layout_v.addLayout(self.layout_h1)

        if get_active_camera().__class__.__name__ == "SimulationCamera":
            self.slider_layout_h_1 = QHBoxLayout()
            self.slider_layout_h_1.addWidget(self.slider_x_centroid_label)
            self.slider_layout_h_1.addWidget(self.slider_x_centroid)
            self.main_layout_v.addLayout(self.slider_layout_h_1)

            self.slider_layout_h_2 = QHBoxLayout()
            self.slider_layout_h_2.addWidget(self.slider_y_centroid_label)
            self.slider_layout_h_2.addWidget(self.slider_y_centroid)
            self.main_layout_v.addLayout(self.slider_layout_h_2)

            self.slider_layout_h_3 = QHBoxLayout()
            self.slider_layout_h_3.addWidget(self.slider_width_label)
            self.slider_layout_h_3.addWidget(self.slider_width)
            self.main_layout_v.addLayout(self.slider_layout_h_3)

            self.slider_layout_h_4 = QHBoxLayout()
            self.slider_layout_h_4.addWidget(self.slider_amplitude_label)
            self.slider_layout_h_4.addWidget(self.slider_amplitude)
            self.main_layout_v.addLayout(self.slider_layout_h_4)

        self.extra_layout_h = QHBoxLayout()
        self.main_layout_v.addLayout(self.extra_layout_h)
        self.extra_layout_v = QVBoxLayout()
        self.main_layout_v.addLayout(self.extra_layout_v)

        self.main_layout_v.addWidget(self.button_action)
        self.main_layout_v.addWidget(self.button_next)
        self.main_layout_v.addWidget(self.button_exit)
        self.main_layout_v.addWidget(self.log_label)

        self.setLayout(self.main_layout_v)
        # Liste des widgets necessitant un suivi de leur etat
        self.button_action_state = ButtonNok(self.button_action)

        self.timer = QtCore.QTimer(self)

    def set_callback_connect_button(self, button:QPushButton, set_callback):
        button.clicked.connect(set_callback)

    def set_callback_timer(self,timer:QtCore.QTimer, set_callback):
        timer.timeout.connect(set_callback)
    
    def set_timer_timeout(self, timer:QtCore.QTimer, delay:int):
        timer.start(delay)

    def stop_timer(self, timer:QtCore.QTimer):
        timer.stop()

    def set_callback_change_slider(self, slider:QSlider, set_callback):
        slider.valueChanged.connect(set_callback)

    def set_callback_range_slider(self, slider:QSlider, min_value:int, max_value:int):
        slider.setMinimum(min_value)
        slider.setMaximum(max_value)

    def set_slider_value(self, slider:QSlider, value:int):
        slider.setValue(value)

    def set_button_label(self, button:QPushButton, label:str):
        button.setText(label)

    def set_label_text(self, label:QLabel, text:str):
        label.setText(text)

    def add_extra_widget(self):
        pass

    
class CameraWindowExtendedDivergence(CameraWindow):
    def __init__(self):
        super().__init__()
        self.add_extra_widget_divergence()
        self.setGeometry(100, 100, 900, 700)
    
    def add_extra_widget_divergence(self):
        # Widget to plot scatter plot
        self.canvas = MplCanvas(self, width=100, height=50, dpi=100)
        self.layout_h1.addWidget(self.canvas)
        self.layout_h1.addStretch()

        self.extra_label = QLabel("")
        self.extra_lineEdit = QLineEdit()
        self.extra_checkbox = QCheckBox('Cale pelable définitive')
        self.extra_checkbox.setChecked(False)
        self.extra_layout_h.addWidget(self.extra_label)
        self.extra_layout_h.addWidget(self.extra_lineEdit)
        self.extra_layout_h.addWidget(self.extra_checkbox)

        # Liste des widgets necessitant un suivi de leur etat
        self.lineEdit_state = LineEditNoEmphasis(self.extra_lineEdit)
        self.extra_checkbox_state = CheckBoxNoEmphasis(self.extra_checkbox)

class CameraWindowExtendedFocusApd(CameraWindow):
    def __init__(self):
        super().__init__()
        self.add_extra_widget_focus_apd()

    def add_extra_widget_focus_apd(self):
        self.extra_label = QLabel("")
        self.extra_lineEdit = QLineEdit()
        self.extra_checkbox = QCheckBox('Cale pelable définitive')
        self.extra_layout_h.addWidget(self.extra_label)
        self.extra_layout_h.addWidget(self.extra_lineEdit)

        # Liste des widgets necessitant un suivi de leur etat
        self.lineEdit_state = LineEditNoEmphasis(self.extra_lineEdit)

class CameraWindowExtendedCenterEmission(CameraWindow):
    def __init__(self):
        super().__init__()
        self.add_extra_widget_center_emission()

    def add_extra_widget_center_emission(self):
         # Bouton pour calculer la position du spot
        self.button_action_extra = QPushButton('Background', self)
        self.extra_layout_v.addWidget(self.button_action_extra)

        # Liste des widgets necessitant un suivi de leur etat
        self.button_action_extra_state = ButtonNoEmphasis(self.button_action_extra)    


class CameraWindowApdPosition(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):        

        # On implémente la GUI
        self.setWindowTitle(f'Utilitaire v{VERSION}')
        self.setGeometry(100, 100, 500, 700)
        
        # Label pour informer l'utilisateur des instructions
        self.instruction_label_title = QLabel("<i><b>Instructions à réaliser</i></b>",self)
        self.instruction_label_title.setFont(QFont("Roboto", 15))
        self.instruction_label = QLabel("",self)
        self.instruction_label.setFont(QFont("Roboto", 10))
        self.instruction_label.setStyleSheet("border: 1px solid white;")

        # Image de la caméra
        self.camera_last_image = QImage()
        pixmap = QPixmap.fromImage(self.camera_last_image)
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        
        # Sliders utilisés en mode simulation pour régler la position du spot
        # Trois sliders horizontaux: x_centroid, y_centroid et width
        self.slider_x_centroid = QSlider(QtCore.Qt.Horizontal)
        self.slider_y_centroid = QSlider(QtCore.Qt.Horizontal)
        self.slider_width = QSlider(QtCore.Qt.Horizontal)
        self.slider_amplitude = QSlider(QtCore.Qt.Horizontal)
        self.slider_x_centroid_label = QLabel('X_centroid')
        self.slider_y_centroid_label = QLabel('Y_centroid')
        self.slider_width_label = QLabel('Width')
        self.slider_amplitude_label = QLabel('Amplitude')

        # Label pour informer l'utilisateur des logs
        self.log_text = ""
        self.log_label = QLabel(self.log_text,self)
        self.log_label.setFont(QFont("Roboto", 8))

        # Bouton pour calculer la position up de l'anneau
        self.button_up_action = QPushButton('Haut', self)
        self.button_up_results_label = QLabel('X=--- , Y=---', self)

        # Bouton pour calculer la position down de l'anneau
        self.button_down_action = QPushButton('Bas', self)
        self.button_down_results_label = QLabel('X=--- , Y=---', self)

        # Bouton pour calculer la position left de l'anneau
        self.button_left_action = QPushButton('Gauche', self)
        self.button_left_results_label = QLabel('X=--- , Y=---', self)

        # Bouton pour calculer la position right de l'anneau
        self.button_right_action = QPushButton('Droite', self)
        self.button_right_results_label = QLabel('X=--- , Y=---', self)

        # Exposition réglable
        self.exposure_label = QLabel('Exposure (ms)', self)
        self.exposure_combobox = QComboBox(self)
        for value in [100, 500, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]:
            self.exposure_combobox.addItem(str(value), value)

        # Bouton pour capturer le background (APD)
        self.button_action_extra = QPushButton('Background', self)

        # Bouton pour calculer la position du spot
        self.button_action = QPushButton('Pass/Fail position APD', self)

        # Bouton pour passer à la suite de la séquence de programmation
        self.button_next = QPushButton('Suivant', self)
        
        # Boutton de sortie pour quitter proprement l'application
        self.button_exit = QPushButton("Exit", self)
        
        # Mise en forme de la GUI
        self.main_layout_v = QVBoxLayout()

        self.main_layout_v.addWidget(self.instruction_label_title)
        self.main_layout_v.addWidget(self.instruction_label)
        self.layout_h1 = QHBoxLayout()
        self.layout_h1.addStretch()
        self.layout_h1.addWidget(self.image_label)
        self.layout_h1.addStretch()
        # crée la grille de contrôles
        controls_grid = QGridLayout()
        controls_grid.addWidget(self.button_up_action,     0, 0)
        controls_grid.addWidget(self.button_up_results_label, 0, 1)
        controls_grid.addWidget(self.button_down_action,   1, 0)
        controls_grid.addWidget(self.button_down_results_label, 1, 1)
        controls_grid.addWidget(self.button_left_action,   2, 0)
        controls_grid.addWidget(self.button_left_results_label, 2, 1)
        controls_grid.addWidget(self.button_right_action,  3, 0)
        controls_grid.addWidget(self.button_right_results_label, 3, 1)
        controls_grid.addWidget(self.exposure_label, 4, 0)
        controls_grid.addWidget(self.exposure_combobox, 4, 1)

        # encapsule la grille dans un QWidget (pour la mettre dans un QHBoxLayout)
        controls_widget = QWidget()
        controls_widget.setLayout(controls_grid)
        self.layout_h1.addWidget(controls_widget)
        self.layout_h1.addStretch()
        # Reste une place sur layout_h1 pour ajouter un graphique si besoin
        self.main_layout_v.addLayout(self.layout_h1)

        if get_active_camera().__class__.__name__ == "SimulationCamera":
            self.slider_layout_h_1 = QHBoxLayout()
            self.slider_layout_h_1.addWidget(self.slider_x_centroid_label)
            self.slider_layout_h_1.addWidget(self.slider_x_centroid)
            self.main_layout_v.addLayout(self.slider_layout_h_1)

            self.slider_layout_h_2 = QHBoxLayout()
            self.slider_layout_h_2.addWidget(self.slider_y_centroid_label)
            self.slider_layout_h_2.addWidget(self.slider_y_centroid)
            self.main_layout_v.addLayout(self.slider_layout_h_2)

            self.slider_layout_h_3 = QHBoxLayout()
            self.slider_layout_h_3.addWidget(self.slider_width_label)
            self.slider_layout_h_3.addWidget(self.slider_width)
            self.main_layout_v.addLayout(self.slider_layout_h_3)

            self.slider_layout_h_4 = QHBoxLayout()
            self.slider_layout_h_4.addWidget(self.slider_amplitude_label)
            self.slider_layout_h_4.addWidget(self.slider_amplitude)
            self.main_layout_v.addLayout(self.slider_layout_h_4)

        self.main_layout_v.addWidget(self.button_action_extra)
        self.main_layout_v.addWidget(self.button_action)
        self.main_layout_v.addWidget(self.button_next)
        self.main_layout_v.addWidget(self.button_exit)
        self.main_layout_v.addWidget(self.log_label)

        self.setLayout(self.main_layout_v)
        # Liste des widgets necessitant un suivi de leur etat
        self.button_action_state = ButtonNok(self.button_action)
        self.button_action_extra_state = ButtonNok(self.button_action_extra)
        self.button_up_action_state = ButtonNok(self.button_up_action)
        self.button_down_action_state = ButtonNok(self.button_down_action)
        self.button_left_action_state = ButtonNok(self.button_left_action)
        self.button_right_action_state = ButtonNok(self.button_right_action)

        self.timer = QtCore.QTimer(self)

    def set_callback_connect_button(self, button:QPushButton, set_callback):
        button.clicked.connect(set_callback)

    def set_callback_timer(self,timer:QtCore.QTimer, set_callback):
        timer.timeout.connect(set_callback)
    
    def set_timer_timeout(self, timer:QtCore.QTimer, delay:int):
        timer.start(delay)

    def stop_timer(self, timer:QtCore.QTimer):
        timer.stop()

    def set_callback_change_slider(self, slider:QSlider, set_callback):
        slider.valueChanged.connect(set_callback)

    def set_callback_range_slider(self, slider:QSlider, min_value:int, max_value:int):
        slider.setMinimum(min_value)
        slider.setMaximum(max_value)

    def set_slider_value(self, slider:QSlider, value:int):
        slider.setValue(value)

    def set_button_label(self, button:QPushButton, label:str):
        button.setText(label)

    def set_label_text(self, label:QLabel, text:str):
        label.setText(text)