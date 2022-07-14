# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 16:34:34 2022

@author: WangLab
"""

# pypylon 
import pypylon.pylon as py
# plotting for graphs and display of image
import pypylon.genicam as geni

import matplotlib.pyplot as plt
# linear algebra and basic math on image matrices
import numpy as np
# OpenCV for image processing functions
import time
from imageio import get_writer
import os
import sys
import threading, queue
from collections import deque
import multiprocessing as mp
from campy.cameras.basler import cam
from campy import CampyParams
from campy.writer import campipe
from campy.display import display
import argparse
import ast
import yaml
import copy
#%%
# Recording parameters
params = {}
params["videoFolder"] = "./Trap10_07112022_NaloxoneInject"
# camSettings: ["./videoSettings/Cylinder_front_acA640-750um_22636055.pfs", "./videoSettings/Cylinder_side_acA720-520um_40190567.pfs","./videoSettings/Cylinder_top_acA800-510um_23193015"

params["camSettings"] =  ["./videoSettings/Cylinder_front_acA640-750um_22636055.pfs", "./videoSettings/Cylinder_top_acA800-510um_23193015.pfs", "./videoSettings/Cylinder_side_acA720-520um_40190567.pfs"]
params["frameRate"]   = 50
params["recTimeInSec"] = 3600

# Camera parameters
params["cameraMake"] = "basler"
params["numCams"] = 3
params["cameraNames"]= ['Camera1','Camera2','Camera3']

# Compression parameters
params["ffmpeg_path"]=[]
params["gpus"] = [0,0,0]
params["pixelFormatInput"] = "gray"
params["pixelFormatOutput"] =  "rgb0"
params["quality"] = "21"

# Display parameters
params["chunkLengthInSec"] = 30
params["displayFrameRate"] = 10
params["displayDownsample"] =  2

print(params)
#%%
def create_cam_params(params, n_cam):
    # Insert camera-specific metadata from parameters into cam_params dictionary
    cam_params = copy.deepcopy(params)
    cam_params["camSettings"] = params["camSettings"][n_cam]
    cam_params["n_cam"] = n_cam
    cam_params["cameraName"] = params["cameraNames"][n_cam]
    cam_params["gpu"] = params["gpus"][n_cam]
    cam_params["baseFolder"] = os.getcwd()

    # Other metadata
    # date
    # time
    # hardware?
    # os?

    return cam_params

def acquire_one_camera(n_cam):
    # Initializes metadata dictionary for this camera stream
    # and inserts important configuration details

    # cam_params["cameraMake"] == "basler":
    #     from campy.cameras.basler import cam

    cam_params = create_cam_params(params, n_cam)

    # Open camera n_cam
    camera, cam_params = cam.Open(cam_params)

    # Initialize queues for display window and video writer
    writeQueue = deque()
    stopQueue = deque([], 1)

    # Start image window display ('consumer' thread)
    if sys.platform == 'win32' and cam_params["cameraMake"] == "basler":
        dispQueue = []
    else:
        dispQueue = deque([], 2)
        threading.Thread(
            target=display.DisplayFrames,
            daemon=True,
            args=(cam_params, dispQueue,),
        ).start()

    # Start grabbing frames ('producer' thread)
    threading.Thread(
        target = cam.GrabFrames,
        daemon=True,
        args = (cam_params,
                camera,
                writeQueue,
                dispQueue,
                stopQueue),
        ).start()

    # Start video file writer (main 'consumer' thread)
    campipe.WriteFrames(cam_params, writeQueue, stopQueue)
    

if __name__=='__main__':
    print('Starting Video recording')
    pool = mp.Pool(processes=params['numCams'])
    pool.map(acquire_one_camera, range(0,params['numCams']))
