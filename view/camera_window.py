# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 10:16:06 2024

@author: joudin
"""


from PyQt5.QtWidgets import QSpinBox, QWidget, QPushButton, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QLineEdit, QCheckBox, QGridLayout, QComboBox
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5 import QtCore
from view.widget_state import ButtonNoEmphasis, ButtonNok, LineEditNoEmphasis, CheckBoxNoEmphasis
from model.data_supplements import VERSION,XDIM, YDIM
from model.camera import get_active_camera
from view.mpl_canvas import MplCanvas
import numpy as np

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

        # Images des différentes positions
        self.apd_up_image = QImage(XDIM, YDIM, QImage.Format_RGB888)
        pixmap_up = QPixmap.fromImage(self.apd_up_image)
        self.apd_up_image_label = QLabel()
        self.apd_up_image_label.setPixmap(pixmap_up)

        self.apd_down_image = QImage(XDIM, YDIM, QImage.Format_RGB888)
        pixmap_down = QPixmap.fromImage(self.apd_down_image)
        self.apd_down_image_label = QLabel()
        self.apd_down_image_label.setPixmap(pixmap_down)

        self.apd_right_image = QImage(XDIM, YDIM, QImage.Format_RGB888)
        pixmap_right = QPixmap.fromImage(self.apd_right_image)
        self.apd_right_image_label = QLabel()
        self.apd_right_image_label.setPixmap(pixmap_right)

        self.apd_left_image = QImage(XDIM, YDIM, QImage.Format_RGB888)
        pixmap_left = QPixmap.fromImage(self.apd_left_image)
        self.apd_left_image_label = QLabel()
        self.apd_left_image_label.setPixmap(pixmap_left)

       
        # Ajout des QSpinBox pour xcentroid et ycentroid
        self.xcentroid_up_label = QLabel("xcentroid", self)
        self.xcentroid_up_spinbox = QSpinBox(self)
        self.xcentroid_up_spinbox.setRange(0, 256)

        self.xcentroid_down_label = QLabel("xcentroid", self)
        self.xcentroid_down_spinbox = QSpinBox(self)
        self.xcentroid_down_spinbox.setRange(0, 256)

        self.xcentroid_left_label = QLabel("xcentroid", self)
        self.xcentroid_left_spinbox = QSpinBox(self)
        self.xcentroid_left_spinbox.setRange(0, 256)

        self.xcentroid_right_label = QLabel("xcentroid", self)
        self.xcentroid_right_spinbox = QSpinBox(self)
        self.xcentroid_right_spinbox.setRange(0, 256)

        self.ycentroid_up_label = QLabel("ycentroid", self)
        self.ycentroid_up_spinbox = QSpinBox(self)
        self.ycentroid_up_spinbox.setRange(0, 320)

        self.ycentroid_down_label = QLabel("ycentroid", self)
        self.ycentroid_down_spinbox = QSpinBox(self)
        self.ycentroid_down_spinbox.setRange(0, 320)

        self.ycentroid_left_label = QLabel("ycentroid", self)
        self.ycentroid_left_spinbox = QSpinBox(self)
        self.ycentroid_left_spinbox.setRange(0, 320)

        self.ycentroid_right_label = QLabel("ycentroid", self)
        self.ycentroid_right_spinbox = QSpinBox(self)
        self.ycentroid_right_spinbox.setRange(0, 320)

        self.radius_up_label = QLabel("Rayon", self)
        self.radius_up_spinbox = QSpinBox(self)
        self.radius_up_spinbox.setRange(80, 120)

        self.radius_down_label = QLabel("Rayon", self)
        self.radius_down_spinbox = QSpinBox(self)
        self.radius_down_spinbox.setRange(80, 120)

        self.radius_left_label = QLabel("Rayon", self)
        self.radius_left_spinbox = QSpinBox(self)
        self.radius_left_spinbox.setRange(80, 120)

        self.radius_right_label = QLabel("Rayon", self)
        self.radius_right_spinbox = QSpinBox(self)
        self.radius_right_spinbox.setRange(80, 120)

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

        # Bouton pour calculer la position down de l'anneau
        self.button_down_action = QPushButton('Bas', self)

        # Bouton pour calculer la position left de l'anneau
        self.button_left_action = QPushButton('Gauche', self)

        # Bouton pour calculer la position right de l'anneau
        self.button_right_action = QPushButton('Droite', self)

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
        save_layout = QVBoxLayout()
        save_layout.addWidget(self.button_up_action)
        save_layout.addWidget(self.button_down_action)
        save_layout.addWidget(self.button_left_action)
        save_layout.addWidget(self.button_right_action)
        save_layout.addWidget(self.exposure_label)
        save_layout.addWidget(self.exposure_combobox)

        # Grille de spinBox pour les coordonnées et le rayon
        spin_box_grid_up = QGridLayout()
        spin_box_grid_up.addWidget(self.xcentroid_up_label, 0,0)
        spin_box_grid_up.addWidget(self.xcentroid_up_spinbox, 0,1)
        spin_box_grid_up.addWidget(self.ycentroid_up_label, 1,0)
        spin_box_grid_up.addWidget(self.ycentroid_up_spinbox, 1,1)
        spin_box_grid_up.addWidget(self.radius_up_label, 2,0)
        spin_box_grid_up.addWidget(self.radius_up_spinbox, 2,1)

        spin_box_grid_down = QGridLayout()
        spin_box_grid_down.addWidget(self.xcentroid_down_label, 0,0)
        spin_box_grid_down.addWidget(self.xcentroid_down_spinbox, 0,1)
        spin_box_grid_down.addWidget(self.ycentroid_down_label, 1,0)
        spin_box_grid_down.addWidget(self.ycentroid_down_spinbox, 1,1)
        spin_box_grid_down.addWidget(self.radius_down_label, 2,0)
        spin_box_grid_down.addWidget(self.radius_down_spinbox, 2,1)

        spin_box_grid_left = QGridLayout()
        spin_box_grid_left.addWidget(self.xcentroid_left_label, 0,0)
        spin_box_grid_left.addWidget(self.xcentroid_left_spinbox, 0,1)
        spin_box_grid_left.addWidget(self.ycentroid_left_label, 1,0)
        spin_box_grid_left.addWidget(self.ycentroid_left_spinbox, 1,1)
        spin_box_grid_left.addWidget(self.radius_left_label, 2,0)
        spin_box_grid_left.addWidget(self.radius_left_spinbox, 2,1)

        spin_box_grid_right = QGridLayout()
        spin_box_grid_right.addWidget(self.xcentroid_right_label, 0,0)
        spin_box_grid_right.addWidget(self.xcentroid_right_spinbox, 0,1)
        spin_box_grid_right.addWidget(self.ycentroid_right_label, 1,0)
        spin_box_grid_right.addWidget(self.ycentroid_right_spinbox, 1,1)
        spin_box_grid_right.addWidget(self.radius_right_label, 2,0)
        spin_box_grid_right.addWidget(self.radius_right_spinbox, 2,1)


        # crée la grille de contrôles
        controls_grid = QGridLayout()
        controls_grid.addWidget(self.apd_up_image_label, 0,0) #(Y,X)
        controls_grid.addLayout(spin_box_grid_up, 0,1)
        controls_grid.addWidget(self.apd_down_image_label, 1,0)
        controls_grid.addLayout(spin_box_grid_down, 1,1)
        controls_grid.addWidget(self.apd_right_image_label, 0,2)
        controls_grid.addLayout(spin_box_grid_right, 0,3)
        controls_grid.addWidget(self.apd_left_image_label, 1,2)
        controls_grid.addLayout(spin_box_grid_left, 1,3)
     
        # encapsule la grille dans un QWidget (pour la mettre dans un QHBoxLayout)
        controls_grid_widget = QWidget()
        controls_grid_widget.setLayout(controls_grid)

        self.layout_h1.addLayout(save_layout)
        self.layout_h1.addStretch()
        self.layout_h1.addWidget(controls_grid_widget)
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

    def set_callback_change_spin_box(self, spin_box:QSpinBox, set_callback):
        spin_box.valueChanged.connect(set_callback)

    def set_spin_box_value(self, spin_box:QSpinBox, value:int):
        spin_box.setValue(value)