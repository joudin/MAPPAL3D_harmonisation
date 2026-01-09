from PyQt5.QtWidgets import  QPushButton, QComboBox
from PyQt5.QtGui import QFont

class ComboBoxState():
    def __init__(self,comboBox:QComboBox):
        self.comboBox = comboBox

    def change_color(self):
        pass

class ComboBoxOk(ComboBoxState):
    def __init__(self,comboBox:QComboBox):
        super().__init__(comboBox=comboBox)

    def change_color(self):
        self.comboBox.setStyleSheet("QComboBox { background-color: green; }")

class ComboBoxNok(ComboBoxState):
    def __init__(self,comboBox:QComboBox):
        super().__init__(comboBox=comboBox)

    def change_color(self):
        self.comboBox.setStyleSheet("QComboBox { background-color: red; }")


class ButtonState():
    def __init__(self, button:QPushButton):
        self.button = button

    def change_color(self):
        pass

class ButtonOk(ButtonState):
    def __init__(self,button:QPushButton):
        super().__init__(button=button)

    def change_color(self):
        self.button.setStyleSheet(("background-color: green;"))

class ButtonNok(ButtonState):
    def __init__(self,button:QPushButton):
        super().__init__(button=button)

    def change_color(self):
        self.button.setStyleSheet(("background-color: red;"))