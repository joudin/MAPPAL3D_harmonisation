# -*- coding: utf-8 -*-
"""
Created on Fri Oct  4 08:58:09 2024

@author: joudin
"""

import numpy as np
import scipy.optimize as optimize
from math import sqrt, atan

def gaussian1D(amplitude: int,
             x_center: int,
             x_width: int,
             x: np.array(int))-> np.array(float):
    """ 
    f(x) = amplitude * exp(-2(x-x_center)**2/x_width**2)
    diameter 4 sigma along x axis = 2*x_width
    """
    return amplitude*np.exp(-2*(x-x_center)**2/x_width**2)

def gaussian2D(amplitude: int,
             x_centroid: int,
             x_width: int,
             x_axis: np.array(int),
             y_centroid: int,
             y_width: int,
             y_axis:np.array(int))-> np.array(float):
  
    y_axis = y_axis[:,np.newaxis]
    return amplitude*np.exp(-2*((x_axis-x_centroid)**2/x_width**2 + (y_axis-y_centroid)**2/y_width**2))

def ring_sigmoid(coord, A, x0, y0, r, w, k=30.0):
    """
    Anneau avec bords lissés (sigmoïdes)
    Meilleur compromis top-hat / gaussienne

    Parameters
    ----------
    r : rayon central
    w : épaisseur totale
    k : raideur du bord (20–100 typique)
    """
    t = np.hypot(coord[:, 0] - x0, coord[:, 1] - y0)

    r_in  = r - w / 2.0
    r_out = r + w / 2.0

    s_in  = 1.0 / (1.0 + np.exp(-k * (t - r_in)))
    s_out = 1.0 / (1.0 + np.exp(-k * (r_out - t)))

    return A * s_in * s_out

def ring_gaussian(coord, A, x0, y0, r, s):
    t = np.sqrt(np.power(coord[:, 0] - x0, 2) + np.power(coord[:, 1] - y0, 2))
    return A * np.exp(-(np.power(t - r, 2) / s))

def build_fake_spot_laser_image(dim:tuple(),
                    x_centroid: int,
                    y_centroid: int,
                    d4sigma_x: int,
                    d4sigma_y: int,
                    a0: int) -> np.array(int):
    
    x_axis = np.arange(0,dim[1],1)
    y_axis = np.arange(0,dim[0],1)
    x_width = int(d4sigma_x/2)
    y_width = int(d4sigma_y/2)

    return gaussian2D(a0,x_centroid,x_width,x_axis,y_centroid,y_width,y_axis)

def make_random_noise(dim:tuple()):
    return np.random.random(dim)

def build_fake_apd_image(dim:tuple(),
                         x_centroid:int,
                         y_centroid:int,
                         radius: int,
                         width: int,
                         a0: int
                         ) ->np.array(int):
    coord = []
    for x in range(dim[1]):
        for y in range(dim[0]):
            coord.append((x, y))
    fit = ring_gaussian(np.array(coord),a0 , x_centroid, y_centroid, radius, width)
    fit = fit.reshape(dim[1],dim[0])#.astype(np.uint8)
    return fit

def get_centroid_position(image:np.array(float)) -> tuple():
    """
    On remplace le centroid par la position du max suivant les intégrations d'image, plus robuste au bruit que le centroid
    width, height = image.shape # Dimension y en premier et x en second
    y = np.arange(width)
    x = np.arange(height)
    p = np.sum(image)
    moment_x = np.sum(image * x)
    moment_y = np.sum(image.T * y)
    x_centroid = round(moment_x/p)
    y_centroid = round(moment_y/p)
    """

    x_centroid = int(np.argmax(np.sum(image,axis=0))) # Du bruit sur les 100 premiers points, pourquoi ?
    y_centroid = int(np.argmax(np.sum(image,axis=1)[1:])+1) # Le premier point diverge, pourquoi ?
    return (x_centroid,y_centroid)


def func_gauss3D(coord, A, x0, y0, s1, s2):
    return A * np.exp(-(np.power(coord[:,0]-x0,2)/s1 + np.power(coord[:,1]-y0,2)/s2))

def func_circle3D(coord, A, x0, y0, r, s):
    t = np.sqrt(np.power(coord[:, 0] - x0, 2) + np.power(coord[:, 1] - y0, 2))
    return A * np.exp(-(np.power(t - r, 2) / s))
  
def get_gauss_fit_params(image:np.array(np.float32)) -> dict:
    coord = []
    val = []
    max_ = 0
    x_max = -1
    y_max = -1
    for x in range(np.shape(image)[1]):
        for y in range(np.shape(image)[0]):
            if (image[y,x]>max_):
                max_ = image[y,x]
                y_max = y
                x_max = x
            coord.append((x, y))
            val.append(image[y, x])

    params, pcov = optimize.curve_fit(func_gauss3D, coord, val, (max_,x_max,y_max, 20., 20.))
    data = {'amplitude': params[0], 'x_center' : params[1], 'y_center' : params[2], 'x_sigma' : np.sqrt(params[3]/2), 'y_sigma' : np.sqrt(params[4]/2)}
    return data

def get_circle_fit_params(image:np.array(np.float32), p0:tuple(), bounds:tuple()) -> dict:
    coord = []
    val = []
    for x in range(np.shape(image)[1]):
        for y in range(np.shape(image)[0]):
            coord.append((x, y))
            val.append(image[y, x])

    params, pcov = optimize.curve_fit(
        ring_gaussian,           # f : fonction
        coord,                   # xdata : coordonnées d'entrée
        val,                     # ydata : valeurs mesurées correspondantes
        p0=p0,                   # initiales guess
        #bounds=bounds            # bornes
        #TODO remettre les bornes active
    )
    data = {'amplitude': params[0], 'x_center' : params[1], 'y_center' : params[2], 'r' : params[3], 's' : params[4]}
    return data

def get_euclidian_distance(position_1:tuple(), position_2:tuple()) -> dict:
    horizontal_distance = position_1[1] - position_2[1]
    vertical_distance = position_1[0] - position_2[0]
    euclidian_distance = np.sqrt(horizontal_distance**2 + vertical_distance**2)
    data = {'horizontal' : horizontal_distance, 'vertical' : vertical_distance, 'euclidian' : euclidian_distance}
    return data
    
def get_gaussian_divergence_and_diameter(gauss_data:dict, focal_length:float, pixel_size:float) -> dict:
    x_waist_radius = np.sqrt(2) * gauss_data['x_sigma'] # [pixels]
    y_waist_radius = np.sqrt(2) * gauss_data['y_sigma'] # [pixels]
    mean_waist_radius = 0.5 * (x_waist_radius + y_waist_radius) # [pixels]
    divergence = 2 * atan(mean_waist_radius * pixel_size / focal_length) # [rad]
    data = {'x_waist_radius' : x_waist_radius, 'y_waist_radius' : y_waist_radius, 'mean_waist_radius': mean_waist_radius, 'divergence' : divergence}
    return data

def get_center_position(position_1:tuple(), position_2:tuple()) -> dict:
    x_center_position = (position_1[0] + position_2[0]) * 0.5
    y_center_position = (position_1[1] + position_2[1]) * 0.5 
    data = {'x_value' : x_center_position, 'y_value' : y_center_position}
    return data

def get_substracted_image(image:np.array(float), background_image:np.array(float)) -> np.array(float):
    if image.shape != background_image.shape:
        raise ValueError(f"Image shapes do not match: image {image.shape}, background {background_image.shape}")
    
    shape = image.shape
    substracted_image = np.zeros(shape, dtype=np.uint8)
    for i in range(shape[0]):
        for j in range(shape[1]):
            if image[i,j] < background_image[i,j]:
                substracted_image[i,j] = 0
            else:
                substracted_image[i,j] = image[i,j] - background_image[i,j]
   
    return substracted_image


def filter_intensity_range(np_image: np.ndarray, drop_top_n: int = 200) -> np.ndarray:
    """Masque les 'drop_top_n' pixels d'intensité les plus élevées.

    - garde les autres valeurs inchangées
    - met à 0 les pixels éliminés
    """
    image = np.asarray(np_image)
    if image.ndim not in (2, 3):
        raise ValueError("filter_intensity_range attend une image 2D ou 3D")

    flat = image.flatten()
    if drop_top_n <= 0:
        return image.copy()

    n_pixels = flat.size
    if drop_top_n >= n_pixels:
        return np.zeros_like(image)

    # seuil d'intensité du pixel (drop_top_n)-ème plus élevé
    sorted_vals = np.partition(flat, -drop_top_n)
    threshold = sorted_vals[-drop_top_n]

    # on élimine les plus forts
    filtered = np.array(image, copy=True)
    filtered[filtered > threshold] = 0

    # si plusieurs pixels ont exactement la valeur seuil, on garde max n_pixels-drop_top_n
    # on peut affiner pour éliminer précisément le bon nombre en passant par un masque.
    if np.count_nonzero(image > threshold) < drop_top_n:
        extras = drop_top_n - np.count_nonzero(image > threshold)
        if extras > 0:
            threshold_mask = (image == threshold)
            inds = np.flatnonzero(threshold_mask)
            if extras < len(inds):
                remove_inds = inds[:extras]
                filtered_flat = filtered.flatten()
                filtered_flat[remove_inds] = 0
                filtered = filtered_flat.reshape(image.shape)

    return filtered