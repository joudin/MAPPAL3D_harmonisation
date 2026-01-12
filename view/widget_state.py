from PyQt5.QtWidgets import  QPushButton, QComboBox, QLineEdit
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

class ComboBoxNoEmphasis(ComboBoxState):
    def __init__(self,comboBox:QComboBox):
        super().__init__(comboBox=comboBox)

    def change_color(self):
        self.comboBox.setStyleSheet("")

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

class ButtonNoEmphasis(ButtonState):
    def __init__(self,button:QPushButton):
        super().__init__(button=button)

    def change_color(self):
        self.button.setStyleSheet((""))

class LineEditState():
    def __init__(self, line:QLineEdit):
        self.line = line

    def change_color(self):
        pass

class LineEditOK(LineEditState):
    def __init__(self,line:QLineEdit):
        super().__init__(line=line)

    def change_color(self):
        self.line.setStyleSheet(("background-color: green;"))

class LineEditNok(LineEditState):
    def __init__(self,line:QLineEdit):
        super().__init__(line=line)

    def change_color(self):
        self.line.setStyleSheet(("background-color: red;"))

class LineEditNoEmphasis(LineEditState):
    def __init__(self,line:QLineEdit):
        super().__init__(line=line)

    def change_color(self):
        self.line.setStyleSheet((""))

class CheckBoxState():
    def __init__(self, checkbox):
        self.checkbox = checkbox

    def change_color(self):
        pass

class CheckBoxOk(CheckBoxState):
    def __init__(self,checkbox):
        super().__init__(checkbox=checkbox)

    def change_color(self):
        self.checkbox.setStyleSheet("QCheckBox { background-color: green; }")

class CheckBoxNok(CheckBoxState):
    def __init__(self,checkbox):
        super().__init__(checkbox=checkbox)

    def change_color(self):
        self.checkbox.setStyleSheet("QCheckBox { background-color: red; }")

class CheckBoxNoEmphasis(CheckBoxState):
    def __init__(self,checkbox):
        super().__init__(checkbox=checkbox)

    def change_color(self):
        self.checkbox.setStyleSheet("")