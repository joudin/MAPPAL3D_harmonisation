import os
import pandas as pd

# Version du logiciel major.minor.patch
VERSION = '1.0.0'

# On charge le fichier de config Excel
path = f'{os.getcwd()}\\assets\\config_app.xlsx'
config_df = pd.read_excel(path)

# Nom des operateurs
operator_names = config_df.OPERATOR_NAMES.dropna().tolist()

# Liste des SN
sn = [str(i) for i in config_df.SERIAL_NUMBER.dropna().tolist()]

# Seuil pass/fail
EUCLIDIAN_DISTANCE_CUBE_MIROR_THRESHOLD_IN_PX = config_df.EUCLIDIAN_DISTANCE_CUBE_MIROR_THRESHOLD_IN_PX[0]
DIVERGENCE_THRESHOLD_IN_MRAD = config_df.DIVERGENCE_THRESHOLD_IN_MRAD[0]
EUCLIDIAN_DISTANCE_CUBE_LASER_THRESHOLD_IN_PX = config_df.EUCLIDIAN_DISTANCE_CUBE_LASER_THRESHOLD_IN_PX[0]
APD_CENTERS_DISTANCE_THRESHOLD_IN_PX = config_df.APD_CENTERS_DISTANCE_THRESHOLD_IN_PX[0]

# On charge les variables utilisateur
params = {}
with open("assets\\user_var.txt", "r") as f:
    for line in f:
        if "=" in line:
            key, value = line.strip().split("=")
            params[key.strip()] = value.strip()         
for c in params:
    if "VAR1" in c.upper():
        VAR1 = params[c]
    elif "VAR2" in c.upper():
        VAR2 = params[c]
    else:
        print("Erreur dans le formalisme user_var.txt")

# Parametres caméra
XDIM = 256
YDIM = 320
PIXEL_SIZE = 25e-6

# Paramètres banc harmo
FOCAL_LENGTH = 1
