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

from utils.utils_main import video_analyzer
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
    parser.add_argument('--yolo_model', type=str, default='yolo11x', help='model name')
    
    
    
    ### 평가 동영상 위치
    parser.add_argument('--test_mode', type=bool, default=False, help='test mode select')
    parser.add_argument('--stream_url', type=str, default='rtsp://192.168.0.2:8554/')
    parser.add_argument('--test_path', type=str, default='../KISAtest/')
    parser.add_argument('--test_save_path', type=str, default='../KISAtemp/')
    parser.add_argument('--video_list_path', type=str, default='../KISAlist/RTSP_streaming_list.xml')
    parser.add_argument('--video_mapping_path', type=str, default='../KISAmap/')

    ### 
    parser.add_argument('--target_fps', type=int, default=10)
    parser.add_argument('--target_fps_PeopleCounting', type=int, default=30)
    parser.add_argument('--skip_time', type=int, default=30)
     
     
     
     

    opt = parser.parse_args()
    opt.class_list = opt.class_list.split(",")
    
    return opt

###################################################################################################

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

###################################################################################################


###################################################################################################

if __name__ == "__main__":
    
    opt = parse_opt()
    

    #################
    
    ### streaming check
    streaming_check = {0: True, 1: True}
    
    #############################
    
    yolo_model_path = os.path.join('yolo_weight', opt.yolo_model + '.pt')
    
    yolo_model = YOLO(yolo_model_path)
    
    #############################
    
    if opt.test_mode:
        test_video_path = opt.test_path
    else:
        test_video_path = opt.stream_url
    
    ### 비디오 리스트 가져오기
    video_files = get_video_list(opt.video_list_path)
    total_len = len(video_files)
    now_index = 1
    
    #############################
    
    save_queue = Queue()    ### 임시 저장할 동영상 파일 이름 저장
    analysis_queue = Queue()    ### 분석할 동영상 파일 이름 저장

    #############################
    
    ### 동영상 저장 및 분석 스레드 정의 및 실행
    saver_thread = threading.Thread(target=video_saver, 
                                    args=(test_video_path, 
                                          save_queue, 
                                          analysis_queue, 
                                          opt.test_save_path, 
                                          opt.test_mode, 
                                          opt.skip_time, 
                                          streaming_check))
    analyzer_thread = threading.Thread(target=video_analyzer, 
                                       args=(analysis_queue, 
                                             opt.video_mapping_path, 
                                             opt.class_list, 
                                             opt.target_fps, 
                                             opt.target_fps_PeopleCounting, 
                                             yolo_model, 
                                             opt.test_mode, 
                                             opt.skip_time
                                             ))
    
    saver_thread.start()
    analyzer_thread.start()
    print('thread start.')
    
    #############################
    ### 동영상 리스트로부터 분석할 동영상 목록 리스트업
    
    for video_file in video_files:
        stream = test_video_path
        if opt.test_mode:
            stream = test_video_path + video_file
        
        save_queue.put(video_file)
    
    #############################
    
    save_queue.put(None)    ### saver_thread 스레드에 더 이상 처리할 동영상이 없음을 전달
    saver_thread.join() ### saver_thread 스레드 종료시까지 대기
    analysis_queue.put(None)
    analyzer_thread.join()
    
    now_index = now_index + 1
    
###################################################################################################






###################################################################################################
###################################################################################################









































