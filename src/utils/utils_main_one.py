###################################################################################################
###################################################################################################

import cv2
from tqdm import tqdm
from datetime import datetime

from pathlib import Path

from utils.utils import frame_to_time
from utils.utils_xml_one import get_detection_areas, xml_from_alarm

from utils.utils_marketing_one import PeopleCounting, Queueing
from utils.utils_loitering import Loitering
from utils.utils_intrusion import Intrusion

###################################################################################################
###################################################################################################

def video_analyzer(video_file, 
                   video_mapping_path, 
                   class_list, 
                   target_fps, 
                   yolo_model, 
                   test_mode, 
                   skip_time):
    """
    aaa
    
    Args:
        analysis_queue (Queue): aaa
    
    Returns:
        None
    """


    while True:
        video_file
        print(f"Analyzing video: {video_file}")  # 로그 출력
        if video_file is None:
            break  # 종료 신호를 받으면 루프 종료
        
        stream_video_path = video_file
        video_file = video_file.split('\\')[-1]
        name, exe = video_file.rsplit('.', 1)
        
        ####################################################################
        ### mapping 파일 
        
        file_name_to_map = video_file.split("_")
        file_map = file_name_to_map[0] +  '_'+  file_name_to_map[1] + '.mp4'
        mapping_file = file_map.replace('.mp4', '.map')

        ### 영역 정보 가져오기
        areas = get_detection_areas(mapping_file, video_mapping_path, class_list)
        areas_keys_list = list(areas.keys())
        
        ####################################################################
        ### 비디오 객체 생성
        
        cap = cv2.VideoCapture(stream_video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 비디오 라이터 객체 생성
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if fps == 0:
            fps = 30    ### 스트리밍 시 영상 fps 정보를 못 읽을 시 디폴트 값인 30으로 초기화
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        ### 프레임 스킵
        if fps > target_fps:
            frame_skip = int(fps / target_fps)
        else:
            frame_skip = 1
        frame_count = 0
        
        ### frame 및 영상 시간 초기화
        current_frame = 0
        hours, minutes, seconds, milliseconds = frame_to_time(current_frame, fps)
        
        ####################################################################
        ####################################################################
        ### 각 클래스별 변수 초기화
        
        detections = []
        
        ### 마케팅 (카운트)
        if any('PeopleCounting' in area for area in areas_keys_list):    ### 마케팅
            people_counting = PeopleCounting(areas, 
                                  current_frame, 
                                  fps, 
                                  width, 
                                  height, 
                                  frame_skip)
            detections.append(people_counting)
        ### 마케팅 (큐)
        if 'Queueing' in areas_keys_list:   ### 마케팅
            queueing = Queueing(areas, 
                                  current_frame, 
                                  fps, 
                                  width, 
                                  height, 
                                  frame_skip)
            detections.append(queueing)
        ### 배회
        if 'Loitering' in areas_keys_list:   ### 배회
            loitering = Loitering(areas, 
                                  current_frame, 
                                  fps, 
                                  width, 
                                  height, 
                                  frame_skip)
            detections.append(loitering)
        ### 침입
        if 'Intrusion' in areas_keys_list:  ### 침입
            intrusion = Intrusion(areas, 
                                  current_frame, 
                                  fps, 
                                  width, 
                                  height, 
                                  frame_skip)
            detections.append(intrusion)
        
        
        
        
        # loitering = Loitering(start_time="00:00:00")
        # intrusion = Intrusion(start_time="00:00:00")
        # people_counting = PeopleCounting(start_time="00:00:00")
        
        # detections = [loitering, intrusion, people_counting]
        
        
        
        ####################################################################
        ####################################################################
        ### 영상 스트리밍
        
        first_check = True
        
        pbar = tqdm(total = total_frames, desc = f"Processing video ")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            if current_frame % frame_skip != 0:
                continue
            
            ### 첫 프레임 시작 시간
            if first_check:
                hours, minutes, seconds, milliseconds = frame_to_time(current_frame, fps)
                for detection in detections:
                    detection.start_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                first_check = False
                
            #########################################################
            ### YOLO 모델 사람 탐지 및 트레킹
            
            results = yolo_model.track(frame, 
                                classes = [0], 
                                verbose = False, 
                                stream = True, 
                                persist = True,
                                # conf = 0.2, 
                                # iou = 0.8
                                )
            
            results_list = list(results)
            
            #########################################################
            ### 각 클래스별 후처리
            
            for detection in detections:
                detection.process_results(results_list.copy(), 
                                          frame_count, 
                                          current_frame, 
                                          fps)
            
            
            
            pbar.update(frame_skip)
            frame_count += 1
            
            # cv2.imshow(video_file, frame)
            
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
            
        ####################################################################
        ####################################################################
        ### 결과 후처리
        test_mode = False
        for detection in detections:
            detection.postprocess(test_mode, 
                                  skip_time)
            
        ##################
        ### xml 저장
        
        all_alarms = sum([detection.alarm_prediction for detection in detections], [])
        sorted_alarms = sorted(all_alarms, key=lambda x: datetime.strptime(x['StartTime'], "%H:%M:%S"))
        xml_from_alarm(sorted_alarms, name)
        
        # for detection in detections:
        #     detection.process_frame(frame)  # 프레임 처리
        
        
        ############
        ############
        
        
        
        
        # for detection in detections:
        #     detection.post_process()  # 후처리
        
        cap.release()
        cv2.destroyAllWindows()
        # Path(stream_video_path).unlink()
        
        break


###################################################################################################



###################################################################################################
###################################################################################################