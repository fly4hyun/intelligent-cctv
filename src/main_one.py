###################################################################################################
###################################################################################################

import os
import argparse
import time
import cv2

from pathlib import Path

from ultralytics import YOLO

import threading
from queue import Queue

from utils.utils_main_one import video_analyzer
from utils.utils_xml import get_video_list
from utils.utils_save_video_temp import video_saver

###################################################################################################
###################################################################################################

###################################################################################################

def parse_opt():
    parser = argparse.ArgumentParser()

    ###
    parser.add_argument('--class_list', type=str, default='배회,마케팅,침입')
    
    
    ###
    parser.add_argument('--yolo_model', type=str, default='yolo12x', help='model name')
    
    
    
    ### 평가 동영상 위치
    parser.add_argument('--test_mode', type=bool, default=True, help='test mode select')
    parser.add_argument('--stream_url', type=str, default='rtsp://192.168.0.2:8554/')
    parser.add_argument('--test_path', type=str, default='../KISAtest/')
    parser.add_argument('--test_save_path', type=str, default='../KISAtemp/')
    parser.add_argument('--video_list_path', type=str, default='../KISAlist/RTSP_streaming_list.xml')
    parser.add_argument('--video_mapping_path', type=str, default='../KISAmap/')

    ### 
    parser.add_argument('--target_fps', type=int, default=30)
    parser.add_argument('--skip_time', type=int, default=30)
     
     
     
     

    opt = parser.parse_args()
    opt.class_list = opt.class_list.split(",")
    
    return opt

###################################################################################################


###################################################################################################


###################################################################################################

if __name__ == "__main__":
    
    opt = parse_opt()
    
    video_file = '..\KISAtemp\C00_094_0001.mp4'
    #################
    
    ### streaming check
    streaming_check = {0: True, 1: True}
    
    #############################
    
    yolo_model_path = os.path.join('yolo_weight', opt.yolo_model + '.pt')
    
    yolo_model = YOLO(yolo_model_path)
    
    #############################
    
    video_analyzer(video_file, 
                   opt.video_mapping_path,  
                   opt.class_list,  
                   opt.target_fps,  
                   yolo_model,  
                   opt.test_mode,  
                   opt.skip_time 
                   )
    
    #############################

    

    

    #############################
    ### 동영상 리스트로부터 분석할 동영상 목록 리스트업

    
###################################################################################################






###################################################################################################
###################################################################################################









































