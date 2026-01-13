# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QPushButton,QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QFrame, QComboBox
from PyQt5.QtGui import QFont
from PyQt5 import QtCore
from model.data_supplements import VERSION
from view.widget_state import ButtonNok, ComboBoxNok

class ConnexionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(f'Utilitaire v{VERSION}')
        self.setGeometry(500, 100, 500, 400)

        # Timer pour définir le FPS de la GUI
        self.timer = QtCore.QTimer(self)   

        # Widget Présentation
        self.label_connexion = QLabel("<i><b>Connexion au banc d'harmo</i></b>", self)
        self.label_connexion.setFont(QFont("Roboto", 15))
        line_h1 = QFrame()
        line_h1.setFrameShape(QFrame.HLine)
        line_h1.setFrameShadow(QFrame.Sunken)

        # Widget nom operateur
        self.label_operator_name = QLabel('Sélectionner votre nom', self)
        self.comboBox_operator_name = QComboBox(self)
        self.value_comboBox_operator_name = ""

        # Widget SN de l'unité
        self.label_sn = QLabel("Séléctionner le SN de l'unité", self)
        self.comboBox_sn = QComboBox(self)
        self.value_comboBox_sn = ""

        # Widget connexion camera
        self.label_connect_camera = QLabel("Connecter la caméra", self)
        self.button_connect_camera = QPushButton('Connexion',self)

        # Widget Emission Reception
        self.step_label = QLabel("Séléctionner l'étape", self)
        self.comboBox_step = QComboBox(self)
        self.value_comboBox_step = ""
  
        # Bouton pour passer à la suite de la séquence de programmation
        self.next_button = QPushButton('Suivant', self)

        # Boutton de sortie pour quitter proprement l'application
        self.exit_button = QPushButton("Quitter", self)
                
        # Label pour informer l'utilisateur des logs 
        self.log_text = ""
        self.log_label = QLabel(self.log_text,self)
        self.log_label.setFont(QFont("Roboto", 8))

        # Label pour informer l'utilisateur des instructions à réaliser
        self.instruction_label_title = QLabel("<i><b>Instructions à réaliser</i></b>",self)
        self.instruction_label_title.setFont(QFont("Roboto", 15))
        self.instruction_label = QLabel("",self)
        self.instruction_label.setFont(QFont("Roboto", 10))
        self.instruction_label.setStyleSheet("border: 1px solid white;")

        # Mise en forme de la GUI
        main_layout_v = QVBoxLayout()
        main_layout_v.addWidget(self.instruction_label_title)
        main_layout_v.addWidget(self.instruction_label)
        main_layout_v.addWidget(self.label_connexion)
        main_layout_v.addWidget(line_h1)
        main_layout_v.addWidget(self.label_operator_name)
        main_layout_v.addWidget(self.comboBox_operator_name)
        main_layout_v.addWidget(self.label_sn)
        main_layout_v.addWidget(self.comboBox_sn)
        main_layout_v.addWidget(self.step_label)
        main_layout_v.addWidget(self.comboBox_step)

        layout_h1 = QHBoxLayout()
        layout_h1.addWidget(self.label_connect_camera)
        layout_h1.addStretch()
        layout_h1.addWidget(self.button_connect_camera)
        layout_h1.addStretch()
        main_layout_v.addLayout(layout_h1)

        main_layout_v.addWidget(self.next_button)
        main_layout_v.addWidget(self.exit_button)

        main_layout_v.addWidget(self.log_label)

        self.setLayout(main_layout_v)

        # Liste des widgets necessitant un suivi de leur etat
        self.comboBox_operator_name_state = ComboBoxNok(self.comboBox_operator_name)
        self.comboBox_sn_state = ComboBoxNok(self.comboBox_sn)
        self.button_connect_camera_state = ButtonNok(self.button_connect_camera)
        self.comboBox_step_state = ComboBoxNok(self.comboBox_step)

        self.show()
        
    def set_callback_connect_button(self, button:QPushButton, set_callback):
        button.clicked.connect(set_callback)

    def set_callback_timer(self,timer:QtCore.QTimer, set_callback):
        timer.timeout.connect(set_callback)

    def set_callback_change_comboBox(self,comboBox:QComboBox, set_callback):
        comboBox.currentIndexChanged.connect(set_callback)

    def set_items_comboBox(self,comboBox:QComboBox, list_of_items:list):
        comboBox.addItems(list_of_items)

    def set_timer_timeout(self, timer:QtCore.QTimer, delay:int):
        timer.start(delay)

    def stop_timer(self, timer:QtCore.QTimer):
        timer.stop()