###################################################################################################
###################################################################################################


from datetime import datetime, timedelta

from collections import defaultdict

from utils.utils import frame_to_time, overlap_check, increase_time, box_iou, is_in_center_area

###################################################################################################
###################################################################################################

### 사전 정의 할 변수들
### 나중에 yaml 파일로 뺄거임

###################################################################################################
###################################################################################################
### 함수 정의

def box_track_LI(results, 
                 track_boxes, 
                 track_mapping_ids, 
                 track_frame, 
                 frame_count, 
                 track_in_check, 
                 remind_boxes, 
                 target_area, 
                 overlap_target_score, 
                 width, 
                 height):
    
    ###############################################################################################

    for result in results:
        for bbox in result.boxes:
            if bbox.cls == 0:  # 사람 클래스
                x, y, w, h = map(int, bbox.xywh[0])
                track_id = int(bbox.id) if bbox.id else -1
                if track_id == -1:
                    continue
                
                box_id_check = None
                    
                ###################################################################################
                # 기존 박스랑 겹치는 지 확인

                if track_id in list(track_boxes.keys()):
                    if track_frame[track_id][-1] == frame_count - 1:
                        overlap_score = box_iou(track_boxes[track_id][-1], 
                                                        (float(x), float(y), float(w), float(h)))
                        
                        ### 겹침
                        if overlap_score > overlap_target_score:
                            track_box = track_boxes[track_id]
                            track_box.append((float(x), float(y), float(w), float(h)))
                            track_frame[track_id].append(frame_count)
                            track_in_check[track_id] = track_in_check[track_id]
                            box_id_check = True
                            
                if box_id_check == None:
                    remind_boxes.append((track_id, float(x), float(y), float(w), float(h)))
    
    ###############################################################################################
    
    for box_info in remind_boxes:
        track_id, x, y, w, h = box_info
        
        ###########################################################################################
        ### 남은 박스 중에 번호는 같으나 다른 박스
        
        max_overlap_score = 0
        max_track_ed_id = None

        for track_ed_id in list(track_boxes.keys()):
            if track_frame[track_ed_id][-1] == frame_count - 1:
                overlap_score = box_iou(track_boxes[track_ed_id][-1], 
                                                        (float(x), float(y), float(w), float(h)))
                
                if overlap_score > overlap_target_score and overlap_score > max_overlap_score:
                    max_overlap_score = overlap_score
                    max_track_ed_id = track_ed_id
                    
        if max_track_ed_id != None:
            track_box = track_boxes[track_id]
            track_box.append((float(x), float(y), float(w), float(h)))
            track_frame[track_id].append(frame_count)
            track_in_check[track_id] = track_in_check[max_track_ed_id]
            continue
        
        ###########################################################################################
        ### 남은 박스 중에 새로운 박스
        
        temp_list = []
        id_num_check = None
        for new_id_temp in list(track_boxes.keys()):
            if track_frame[new_id_temp][-1] == frame_count:
                temp_list.append(new_id_temp)
            if track_frame[new_id_temp][-1] == frame_count - 1:
                temp_list.append(new_id_temp)
        
        for id_num in range(len(temp_list)):
            if id_num not in temp_list:
                id_num_check = id_num
                track_box = track_boxes[id_num_check]
                track_box.append((float(x), float(y), float(w), float(h)))
                track_frame[id_num_check].append(frame_count)
                overlap_status_now = overlap_check(target_area, [float(x), float(y), float(w), float(h)])
                if overlap_status_now < 0.9:
                    overlap_status_now = 0
                else:
                    overlap_status_now = 1
                track_in_check[id_num_check] = [overlap_status_now]
                
                break
        
        ### 박스 번호가 다 차서 새로운 번호를 부여
        if id_num_check == None:
            id_num_check = len(temp_list)
            track_box = track_boxes[id_num_check]
            track_box.append((float(x), float(y), float(w), float(h)))
            track_frame[id_num_check].append(frame_count)
            overlap_status_now = overlap_check(target_area, [float(x), float(y), float(w), float(h)])
            if overlap_status_now >= 0.9:
                overlap_status_now = 1
            track_in_check[id_num_check] = [overlap_status_now]
            
    ###############################################################################################
    ### 남은 박스 중에 이전에는 있으나 지금은 없는 사람
    
    for track_ed_id in list(track_boxes.keys()):
        end_check_1 = None
    
        ### 이전 박스 중에 확인
        
        if track_frame[track_ed_id][-1] == frame_count - 1:
            x, y, w, h = track_boxes[track_ed_id][-1]
            
            ### 지금 박스랑 겹치는게 있는지 확인
            for track_now_id in list(track_boxes.keys()):
                if track_frame[track_now_id][-1] == frame_count:
                    overlap_score = box_iou(track_boxes[track_now_id][-1], 
                                                    (float(x), float(y), float(w), float(h)))
                
                    if overlap_score > overlap_target_score:
                        end_check_1 = True
                        break
                    
            if end_check_1 == True:
                return True
            
            ### 겹치지 않고 영역 안에 있는 박스중에서
            if is_in_center_area(x, y, w, h, width, height, 0.05):
                track_box = track_boxes[track_ed_id]
                track_box.append((float(x), float(y), float(w), float(h)))
                track_frame[track_ed_id].append(frame_count)
                track_in_check[track_ed_id] = track_in_check[track_ed_id]
            
    ###############################################################################################
    ### 이전 박스 중에 현재랑 같은 번호인 것들
    
    for track_ed_id in list(track_boxes.keys()):
        end_check_2 = None
        
        if len(track_frame[track_ed_id]) > 1:
            if track_frame[track_ed_id][-2] == frame_count - 1:
                x, y, w, h = track_boxes[track_ed_id][-2]
                
                ### 지금 박스들 중에 겹치는 번호 확인
                for track_now_id in list(track_boxes.keys()):
                    if track_frame[track_now_id][-1] == frame_count:
                        overlap_score = box_iou(track_boxes[track_now_id][-1], 
                                                        (float(x), float(y), float(w), float(h))) 
                        
                        if overlap_score > overlap_target_score:
                            end_check_2 = True
                            break
            
                if end_check_2 == True:
                    continue
                
                ### 새로운 번호 부여
                if is_in_center_area(x, y, w, h, width, height, 0.05):
                    
                    temp_list = []
                    id_num_check = None
                    for new_id_temp in list(track_boxes.keys()):
                        if track_frame[new_id_temp][-1] == frame_count:
                            temp_list.append(new_id_temp)
                        if track_frame[new_id_temp][-1] == frame_count - 1:
                            temp_list.append(new_id_temp)
                    for id_num in range(len(temp_list)):
                        if id_num not in temp_list:
                            id_num_check = id_num
                            break
                    if id_num_check == None:
                        id_num_check = len(temp_list)
                            
                    track_box = track_boxes[id_num_check]
                    track_box.append((float(x), float(y), float(w), float(h)))
                    track_frame[id_num_check].append(frame_count)
                    track_in_check[id_num_check] = track_in_check[track_ed_id]

    ###############################################################################################
    ### 일정 프레임 지난 데이터 삭제

    for track_id in list(track_frame.keys()):
        if frame_count - track_frame[track_id][-1] > 3:
            if track_id in list(track_boxes.keys()):
                del track_boxes[track_id]
            if track_id in list(track_mapping_ids.keys()):
                del track_mapping_ids[track_id]
            if track_id in list(track_frame.keys()):
                del track_frame[track_id]
            if track_id in list(track_in_check.keys()):
                del track_in_check[track_id]

    return False

###################################################################################################

def alarm_LI(alarm_prediction, 
             area_type, 
             track_frame, 
             track_boxes, 
             track_in_check, 
             frame_count, 
             current_frame, 
             target_area, 
             frame_skip, 
             target_sec, 
             target_mil, 
             fps, 
             params
             ):
             
    non_count, duration, start_time, duration_frame = params
    LI_check = [0, 0, 0, 0]
    time_format = "%H:%M:%S"
    for track_id in list(track_frame.keys()):
        if track_frame[track_id][-1] == frame_count:
            x, y, w, h = track_boxes[track_id][-1]
            old_overlap_status = track_in_check[track_id][-1]
            ### 해당 영역 안에 있는지 확인
            if area_type == 'Intrusion':
                overlap_status = overlap_check(target_area, [float(x), float(y), float(w), float(h)], 0.99)
            else:
                overlap_status = overlap_check(target_area, [float(x), float(y), float(w), float(h)])

            if old_overlap_status == 0 and overlap_status != 0 and overlap_status != 1:
                overlap_status = 0
            elif old_overlap_status == 1 and overlap_status != 0 and overlap_status != 1:
                overlap_status = 1
                
            ### 확인
            if old_overlap_status == 0 and overlap_status == 0:
                LI_check[0] += 1
            elif old_overlap_status == 0 and overlap_status == 1:
                LI_check[1] += 1
            elif old_overlap_status == 1 and overlap_status == 0:
                LI_check[2] += 1
            elif old_overlap_status == 1 and overlap_status == 1:
                LI_check[3] += 1
                
            track_in_check[track_id] = [overlap_status]
    
    ###############################################################################################
    ### 영역 안에 사람이 없음
    if LI_check[1] == 0 and LI_check[3] == 0:
        if non_count < 2 and duration != None:
            
            duration_frame = duration_frame + frame_skip
            hours, minutes, seconds, milliseconds = frame_to_time(duration_frame, fps)
            if area_type == 'Intrusion':
                duration = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}:{int(milliseconds):03d}"
            else:
                duration = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                
            non_count = non_count + 1
        
        else:
            
            if area_type == 'Intrusion':
                if duration != None:
                    hours, minutes, seconds, milliseconds = duration.split(":")
                    hours, minutes, seconds, milliseconds = int(hours), int(minutes), int(seconds), int(milliseconds)
                    if hours > 0 or minutes > 0 or seconds > target_sec or milliseconds > target_mil:
                        
                        start_time_obj = datetime.strptime(start_time, time_format)
                        new_time_obj = start_time_obj + timedelta(seconds=target_sec)
                        new_time = new_time_obj.strftime(time_format)
                        
                        duration_obj = datetime.strptime(duration[:-4], time_format)
                        new_duration_obj = duration_obj - timedelta(seconds=target_sec)
                        new_duration = new_duration_obj.strftime(time_format)
                        
                        description = area_type
                        alarm_prediction.append({'StartTime': new_time, 
                                                'AlarmDescription': description, 
                                                'AlarmDuration': new_duration
                                                })
            else:
                if duration != None:
                    hours, minutes, seconds = duration.split(":")
                    hours, minutes, seconds = int(hours), int(minutes), int(seconds)
                    if hours > 0 or minutes > 0 or seconds > 10:
                        
                        start_time_obj = datetime.strptime(start_time, time_format)
                        new_time_obj = start_time_obj + timedelta(seconds=10)
                        new_time = new_time_obj.strftime(time_format)
                        
                        duration_obj = datetime.strptime(duration, time_format)
                        new_duration_obj = duration_obj - timedelta(seconds=10)
                        new_duration = new_duration_obj.strftime(time_format)
                        
                        description = area_type
                        alarm_prediction.append({'StartTime': new_time, 
                                                'AlarmDescription': description, 
                                                'AlarmDuration': new_duration
                                                })


            duration_frame = 0
            duration = None
            non_count = 0
        if duration == None:
            duration_frame = 0
            non_count = 0
    
    ### 영역안에 사람이 들어온 순간
    elif duration_frame == 0 or LI_check[1] != 0:
        non_count = 0
        hours, minutes, seconds, milliseconds = frame_to_time(current_frame, fps)
        start_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
        duration_frame = frame_skip
        hours, minutes, seconds, milliseconds = frame_to_time(duration_frame, fps)
        if area_type == 'Intrusion':
            duration = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}:{int(milliseconds):03d}"
        else:
            duration = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            
    ### 계속 안에 사람 있음
    else:
        non_count = 0
        duration_frame = duration_frame + frame_skip
        hours, minutes, seconds, milliseconds = frame_to_time(duration_frame, fps)
        if area_type == 'Intrusion':
            duration = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}:{int(milliseconds):03d}"
        else:
            duration = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    params = [non_count, duration, start_time, duration_frame]
    
    return LI_check, start_time, params


###################################################################################################
###################################################################################################

class Intrusion:
    
    def __init__(self, 
                 areas, 
                 current_frame, 
                 fps, 
                 width, 
                 height, 
                 frame_skip):
        
        hours, minutes, seconds, milliseconds = frame_to_time(current_frame, fps)
        self.start_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
        self.Intrusion_area = areas['Intrusion']
        
        self.alarm_prediction = []

        self.Intrusion_track_boxes = defaultdict(lambda: [])
        self.Intrusion_track_mapping_ids = defaultdict(lambda: -1)
        self.Intrusion_track_frame = defaultdict(lambda: [])
        self.Intrusion_track_in_check = defaultdict(lambda: [])
        self.intrusion_check = [0, 0, 0, 0]
        self.Intrusion_non_count = 0
        self.Intrusion_duration = None
        self.Intrusion_duration_frame = 0
        
        self.width = width
        self.height = height
        self.frame_skip = frame_skip
        
        ### 가변 변수
        self.overlap_target_score = 0.05
        self.target_sec = 0
        self.target_mil = 110
        
    def process_results(self, 
                        results, 
                        frame_count, 
                        current_frame, 
                        fps):
        
        Intrusion_remind_boxes = []
        box_track_LI(results, 
                    self.Intrusion_track_boxes, 
                    self.Intrusion_track_mapping_ids, 
                    self.Intrusion_track_frame, 
                    frame_count, 
                    self.Intrusion_track_in_check, 
                    Intrusion_remind_boxes, 
                    self.Intrusion_area, 
                    self.overlap_target_score, 
                    self.width, 
                    self.height)
        
        Intrusion_params = [self.Intrusion_non_count, 
                            self.Intrusion_duration, 
                            self.start_time, 
                            self.Intrusion_duration_frame]
        
        self.intrusion_check, self.start_time, Intrusion_params = alarm_LI(
            self.alarm_prediction, 
            'Intrusion', 
            self.Intrusion_track_frame, 
            self.Intrusion_track_boxes, 
            self.Intrusion_track_in_check, 
            frame_count, 
            current_frame, 
            self.Intrusion_area, 
            self.frame_skip, 
            self.target_sec, 
            self.target_mil, 
            fps, 
            Intrusion_params
            )
        
        self.Intrusion_non_count, self.Intrusion_duration, self.start_time, self.Intrusion_duration_frame = Intrusion_params
        
    def postprocess(self, 
                    video_test_mode, 
                    skip_time):
        
        time_format = "%H:%M:%S"
            
        if self.intrusion_check[1] != 0 or self.intrusion_check[3] != 0:
                
            if self.Intrusion_duration != None:
                hours, minutes, seconds, milliseconds = self.Intrusion_duration.split(":")
                hours, minutes, seconds, milliseconds = int(hours), int(minutes), int(seconds), int(milliseconds)
                if hours > 0 or minutes > 0 or seconds > self.target_sec or milliseconds > self.target_mil:
                    
                    start_time_obj = datetime.strptime(self.start_time, time_format)
                    new_time_obj = start_time_obj + timedelta(seconds=self.target_sec)
                    new_time = new_time_obj.strftime(time_format)
                    
                    duration_obj = datetime.strptime(self.Intrusion_duration[:-4], time_format)
                    new_duration_obj = duration_obj - timedelta(seconds=self.target_sec)
                    new_duration = new_duration_obj.strftime(time_format)
                    
                    description = 'Intrusion'
                    self.alarm_prediction.append({'StartTime': new_time, 
                                            'AlarmDescription': description, 
                                            'AlarmDuration': new_duration
                                            })
                    
        if len(self.alarm_prediction) > 1:
            self.alarm_prediction = [self.alarm_prediction[-1]]
            
        if not video_test_mode:
            increase_time(self.alarm_prediction, skip_time)
        
        
        
        
###################################################################################################


###################################################################################################
###################################################################################################