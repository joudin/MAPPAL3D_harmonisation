# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 10:16:06 2024

@author: joudin
"""


from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QSlider, QHBoxLayout
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5 import QtCore
from view.widget_state import ButtonNok
from model.data_supplements import VERSION
from model.camera import get_active_camera

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
        self.slider_x_centroid_label = QLabel('X_centroid')
        self.slider_y_centroid_label = QLabel('Y_centroid')
        self.slider_width_label = QLabel('Width')

        # Label pour informer l'utilisateur des logs
        self.log_text = ""
        self.log_label = QLabel(self.log_text,self)
        self.log_label.setFont(QFont("Roboto", 8))

        # Bouton pour calculer la position du spot
        self.button_spot_position = QPushButton('Enregistrer position du spot', self)

        # Bouton pour passer à la suite de la séquence de programmation
        self.button_next = QPushButton('Suivant', self)
        
        # Boutton de sortie pour quitter proprement l'application
        self.button_exit = QPushButton("Exit", self)
        
        # Mise en forme de la GUI
        main_layout_v = QVBoxLayout()

        main_layout_v.addWidget(self.instruction_label_title)
        main_layout_v.addWidget(self.instruction_label)
        main_layout_v.addWidget(self.image_label)
        if get_active_camera().__class__.__name__ == "SimulationCamera":
            slider_layout_h_1 = QHBoxLayout()
            slider_layout_h_1.addWidget(self.slider_x_centroid_label)
            slider_layout_h_1.addWidget(self.slider_x_centroid)
            main_layout_v.addLayout(slider_layout_h_1)

            slider_layout_h_2 = QHBoxLayout()
            slider_layout_h_2.addWidget(self.slider_y_centroid_label)
            slider_layout_h_2.addWidget(self.slider_y_centroid)
            main_layout_v.addLayout(slider_layout_h_2)

            slider_layout_h_3 = QHBoxLayout()
            slider_layout_h_3.addWidget(self.slider_width_label)
            slider_layout_h_3.addWidget(self.slider_width)
            main_layout_v.addLayout(slider_layout_h_3)

        main_layout_v.addWidget(self.button_spot_position)
        main_layout_v.addWidget(self.button_next)
        main_layout_v.addWidget(self.button_exit)
        main_layout_v.addWidget(self.log_label)
        
        self.setLayout(main_layout_v)

        # Liste des widgets necessitant un suivi de leur etat
        self.button_spot_position_state = ButtonNok(self.button_spot_position)

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

    