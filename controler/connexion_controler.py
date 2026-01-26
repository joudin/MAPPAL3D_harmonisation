
from view.widget_state import ButtonOk, ComboBoxOk, ComboBoxNok
from PyQt5.QtWidgets import QApplication, QWidget
from view.connexion_window import ConnexionWindow
from tools.singleton import SingletonMeta
from model.data_supplements import VERSION, operator_names, sn, PIXEL_SIZE, FOCAL_LENGTH
from model.camera import create_camera, get_active_camera
from model.harmonisation_data import create_harmonisation_data
from controler.cube_position_controler import CubePositionControler
from datetime import datetime 

DELAY = 200

class ConnexionControler(metaclass=SingletonMeta):
    def __init__(self):       
        # Comportement de la GUI
        self.connexion_window = ConnexionWindow()
        self.connexion_window.set_callback_timer(self.connexion_window.timer, self.update_gui)
        self.connexion_window.set_timer_timeout(self.connexion_window.timer, DELAY)
        self.connexion_window.set_callback_connect_button(self.connexion_window.button_connect_camera, self.connexion_action)
        self.connexion_window.set_callback_connect_button(self.connexion_window.next_button, self.next_button_action)
        self.connexion_window.set_callback_connect_button(self.connexion_window.exit_button, self.exit_application_action)
        self.connexion_window.set_items_comboBox(self.connexion_window.comboBox_operator_name, operator_names)
        self.connexion_window.set_items_comboBox(self.connexion_window.comboBox_sn, sn)
        self.connexion_window.set_callback_change_comboBox(self.connexion_window.comboBox_operator_name, self.operator_name_change_comboBox)
        self.connexion_window.set_callback_change_comboBox(self.connexion_window.comboBox_sn, self.sn_change_comboBox)
        self.connexion_window.set_items_comboBox(self.connexion_window.comboBox_step, ["--","Emission", "Reception"])
        self.connexion_window.set_callback_change_comboBox(self.connexion_window.comboBox_step, self.step_change_comboBox)
############################ Callbacks #######################################

    def build_instructions_text(self):
         self.instruction_text = ""
         if type(self.connexion_window.comboBox_operator_name_state) == ComboBoxOk:
            pass
         else:
             self.instruction_text += "Sélectionner le nom"
         if type(self.connexion_window.comboBox_sn_state) == ComboBoxOk:
             pass
         else:
             if len(self.instruction_text) > 0:
                 self.instruction_text += "<br>"
             self.instruction_text += "Sélectionner le SN"

         if type(self.connexion_window.comboBox_step_state) == ComboBoxOk:
            pass
         else:
            if len(self.instruction_text) > 0:
                self.instruction_text += "<br>"
            self.instruction_text += "Sélectionner le étape de réglage"

         if type(self.connexion_window.button_connect_camera_state) == ButtonOk:
             pass
         else:
             if len(self.instruction_text) > 0:
                 self.instruction_text += "<br>"
             self.instruction_text += "Connecter la caméra"

    def update_gui(self):
        # Mise à jour de la GUI en se basant sur les états des widgets
        self.connexion_window.button_connect_camera_state.change_color()
        self.connexion_window.comboBox_operator_name_state.change_color()
        self.connexion_window.comboBox_sn_state.change_color()
        self.connexion_window.comboBox_step_state.change_color()
        # On construit le texte donnant les instructions restantes en fonction de l'état des widgets
        self.build_instructions_text()
        self.connexion_window.instruction_label.setText(self.instruction_text)
        # On affiche les logs
        self.connexion_window.log_label.setText(self.connexion_window.log_text)
   
    def connexion_action(self):
        # on crée un object camera et on tente de se connecter
        cam = create_camera("NIT","0000000000")
        connexion_status = False
        if cam is not None:
            connexion_status = cam.connect()
        if connexion_status:
            self.connexion_window.log_text = f'Camera connectée'
            self.connexion_window.button_connect_camera_state = ButtonOk(self.connexion_window.button_connect_camera)
        else:
            self.connexion_window.log_text = f'Echec de la connexion de la caméra'

    def operator_name_change_comboBox(self):
        self.connexion_window.value_comboBox_operator_name = self.connexion_window.comboBox_operator_name.currentText()
        if self.connexion_window.value_comboBox_operator_name != "--":
            self.connexion_window.comboBox_operator_name_state = ComboBoxOk(self.connexion_window.comboBox_operator_name)
        else:
            self.connexion_window.comboBox_operator_name_state = ComboBoxNok(self.connexion_window.comboBox_operator_name)

        self.connexion_window.log_text = f'Sélection du nom {self.connexion_window.value_comboBox_operator_name}'

    def sn_change_comboBox(self):
        self.connexion_window.value_comboBox_sn = self.connexion_window.comboBox_sn.currentText()
        if self.connexion_window.value_comboBox_sn != "0":
            self.connexion_window.comboBox_sn_state = ComboBoxOk(self.connexion_window.comboBox_sn)
        else:
            self.connexion_window.comboBox_sn_state = ComboBoxNok(self.connexion_window.comboBox_sn)

        self.connexion_window.log_text = f'Sélection du SN {self.connexion_window.value_comboBox_sn}'
       
    def step_change_comboBox(self):
        if self.connexion_window.comboBox_step.currentText() != "--":
            self.connexion_window.comboBox_step_state = ComboBoxOk(self.connexion_window.comboBox_step)
            self.connexion_window.value_comboBox_step = self.connexion_window.comboBox_step.currentText()
        else:
            self.connexion_window.comboBox_step_state = ComboBoxNok(self.connexion_window.comboBox_step)

        self.connexion_window.log_text = f'Sélection de l\'étape {self.connexion_window.value_comboBox_step}'

    def next_button_action(self):
        if len(self.instruction_text) == 0: # Si toutes les états sont OK
            data = create_harmonisation_data("JSON",str(self.connexion_window.value_comboBox_sn),str(self.connexion_window.value_comboBox_step).upper())
            data.write("SOFT_VERSION", VERSION)
            data.write("OPERATOR_NAME",str(self.connexion_window.value_comboBox_operator_name))
            data.write("SN",str(self.connexion_window.value_comboBox_sn))
            data.write("DATE",str(datetime.now().strftime("%d/%m/%Y")))
            data.write("PIXEL_SIZE_IN_M", str(PIXEL_SIZE))
            data.write("FOCAL_LENGTH_IN_M", str(FOCAL_LENGTH))
            data.save()
            self.cube_position_controler = CubePositionControler()
            QWidget.close(self.connexion_window)
            self.connexion_window.stop_timer(self.connexion_window.timer)
        else:
            self.connexion_window.log_text = "Veuillez compléter toutes les étapes avant de continuer"

    def exit_application_action(self):
        cam = get_active_camera()
        if cam is not None:
            try:
                cam.disconnect()
            except:
                pass
        QApplication.quit() 
        QWidget.close(self.connexion_window)