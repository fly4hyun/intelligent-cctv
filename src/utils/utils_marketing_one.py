###################################################################################################
###################################################################################################




from collections import defaultdict

from utils.utils_one import frame_to_time, overlap_check, increase_time

###################################################################################################
###################################################################################################

### 사전 정의 할 변수들
### 나중에 yaml 파일로 뺄거임

###################################################################################################
###################################################################################################
### 함수 정의

def box_track(results, 
              track_history, 
              in_out_check, 
              last_update_frame, 
              frame_count
              ):
    """
    주어진 결과에서 각 객체의 트랙 ID를 추출하고, 해당 ID에 대한 위치 정보를 추적 기록에 업데이트합니다.
    또한, 지정된 시간 이상 업데이트 되지 않은 트랙 정보를 정리합니다.

    Args:
        results: 분석 결과 객체 리스트, 각 객체는 위치 박스와 트랙 ID를 포함해야 함
        track_history (dict): 트랙 ID별로 위치 정보를 저장하는 딕셔너리
        in_out_check (dict): 트랙 ID별 입출구 카운팅 정보를 저장하는 딕셔너리
        last_update_frame (dict): 트랙 ID별 마지막 업데이트 프레임 번호를 저장하는 딕셔너리
        frame_count (int): 현재 처리 중인 프레임 번호

    Returns:
        list: 처리된 프레임에서 추출된 모든 트랙 ID의 리스트

    Note:
        이 함수는 프레임마다 호출되어야 하며, 각 호출 시 `results`에는 최신 프레임의 분석 결과가 전달되어야 합니다.
    """
    
    track_ids = []
    
    ###############################################################################################
    
    if hasattr(results[0].boxes, 'id') and results[0].boxes.id is not None:
        
        bbox = results[0].boxes.xywh.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()

        for box, track_id in zip(bbox, track_ids):
            x, y, w, h = box
            in_out_check[track_id]
            track = track_history[track_id]
            track.append([float(x), float(y), float(w), float(h)])
            if len(track) > 30:
                track.pop(0)
            last_update_frame[track_id] = frame_count
        
        for track_id in list(last_update_frame.keys()):
            if frame_count - last_update_frame[track_id] > 300:
                del track_history[track_id]
                del last_update_frame[track_id]
                del in_out_check[track_id]
    
        ###########################################################################################
        
    return track_ids

###################################################################################################

def alarm_C(track_ids, 
            in_out_check, 
            track_history, 
            area_type, 
            target_area_A, 
            target_area_B, 
            alarm_prediction, 
            start_time, 
            PeopleCounting_params
            ):
    """
    주어진 트랙 ID들에 대하여 특정 영역과의 겹침을 확인하고, 해당 정보를 기반으로 입출구 카운팅 및 알람을 생성

    Args:
        track_ids (list): 처리할 트랙 ID 목록
        in_out_check (dict): 각 트랙 ID에 대한 현재 겹침 상태
        track_history (dict): 각 트랙 ID별 위치 정보 기록
        area_type (str): 처리할 영역의 종류 (예: 'Main Entrance')
        target_area_A (list): 첫 번째 타겟 영역의 좌표 리스트
        target_area_B (list): 두 번째 타겟 영역의 좌표 리스트
        alarm_prediction (list): 알람 기록을 저장할 리스트
        start_time (str): 감지 시작 시간
        PeopleCounting_params (list): 초기 입구 및 출구 카운트 [in_count, out_count]

    Returns:
        list: 업데이트된 입구 및 출구 카운트 [in_count, out_count]

    Notes:
        - 함수는 각 트랙 ID에 대해 target_area_A와 target_area_B와의 겹침을 계산
        - 겹침 상태에 따라 입구 또는 출구 카운트를 증가시키고, 해당하는 알람을 alarm_prediction에 추가
        - alarm_prediction 리스트에는 사전형 데이터가 추가되며, 각 사전은 알람 유형, 시작 시간, 알람 설명, 전체 카운트를 포함
    """
    
    in_count, out_count = PeopleCounting_params
    
    ###############################################################################################
    
    for track_id in track_ids:
        
        overlap_status_A_now, overlap_status_B_now = in_out_check[track_id]
        overlap_status_B_new = 0
        b_box = track_history[track_id][-1]
        
        ###########################################################################################
    
        overlap_status_A = overlap_check(target_area_A, b_box)
        overlap_status_B = overlap_check(target_area_B, b_box)
        
        if overlap_status_A != 0 and overlap_status_A != 1:
            overlap_status_A = 0.5
        if overlap_status_B != 0 and overlap_status_B != 1:
            overlap_status_B = 0.5
            
        if overlap_status_A_now == 0 and overlap_status_A == 0.5:
            overlap_status_A_new = 0
        elif overlap_status_A_now == 1 and overlap_status_A == 0.5:
            overlap_status_A_new = 1
        else:
            overlap_status_A_new = overlap_status_A
            if overlap_status_B == 0.5:
                overlap_status_A_new = overlap_status_A_now
                    
        ###########################################################################################
        
        if overlap_status_B_now == 0 and overlap_status_B == 0.5:
            overlap_status_B_new = 0
        elif overlap_status_B_now == 1 and overlap_status_B == 0.5:
            overlap_status_B_new = 1
        else:
            overlap_status_B_new = overlap_status_B
            if overlap_status_A == 0.5:
                overlap_status_B_new = overlap_status_B_now
        
        ###########################################################################################
        
        overlap_status_now = [overlap_status_A_now, overlap_status_B_now]
        overlap_status_new = [overlap_status_A_new, overlap_status_B_new]
        
        ###########################################################################################
        
        if len(track_history[track_id]) != 1:

            if overlap_status_now == [1, 0] and overlap_status_new == [0, 1]:
                in_count = in_count + 1
                alarm_type = 'InCount'
                description = area_type
                total_count = in_count
                alarm_prediction.append({'AlarmType': alarm_type, 
                                        'StartTime': start_time, 
                                        'AlarmDescription': description, 
                                        'TotalCount': total_count
                                        })
            if overlap_status_now == [0, 1] and overlap_status_new == [1, 0]:
                out_count = out_count + 1
                alarm_type = 'OutCount'
                description = area_type
                total_count = out_count
                alarm_prediction.append({'AlarmType': alarm_type, 
                                        'StartTime': start_time, 
                                        'AlarmDescription': description, 
                                        'TotalCount': total_count
                                        })
                
        in_out_check[track_id] = overlap_status_new
        
    PeopleCounting_params = [in_count, out_count]
    
    return PeopleCounting_params

###################################################################################################

def alarm_Q(track_ids, 
            in_out_check, 
            track_history, 
            area_type, 
            target_area, 
            alarm_prediction, 
            start_time, 
            Queueing_params
            ):
    """
    주어진 트랙 ID들에 대하여 특정 영역과의 겹침을 확인하고, 해당 정보를 기반으로 입출구 카운팅 및 알람을 생성

    Args:
        track_ids (list): 처리할 트랙 ID 목록
        in_out_check (dict): 각 트랙 ID에 대한 현재 겹침 상태
        track_history (dict): 각 트랙 ID별 위치 정보 기록
        area_type (str): 처리할 영역의 종류 (예: 'Main Entrance')
        target_area (list): 타겟 영역의 좌표 리스트
        alarm_prediction (list): 알람 기록을 저장할 리스트
        start_time (str): 감지 시작 시간
        Queueing_params (list): 초기 입구 및 출구 카운트 [ingress, egress]

    Returns:
        list: 업데이트된 입구 및 출구 카운트 [ingress, egress]

    Notes:
        - 함수는 각 트랙 ID에 대해 target_area와의 겹침을 계산
        - 겹침 상태에 따라 입구 또는 출구 카운트를 증가시키고, 해당하는 알람을 alarm_prediction에 추가
        - alarm_prediction 리스트에는 사전형 데이터가 추가되며, 각 사전은 알람 유형, 시작 시간, 알람 설명, 전체 카운트를 포함
    """
    
    ingress, egress = Queueing_params
    
    ###############################################################################################
    
    for track_id in track_ids:
        
        overlap_status_A_now, overlap_status_B_now = in_out_check[track_id]
        overlap_status_B_new = 0
        b_box = track_history[track_id][-1]
        
        ###########################################################################################
    
        overlap_status_A = overlap_check(target_area, b_box)
        
        if overlap_status_A != 0 and overlap_status_A != 1:
            overlap_status_A = 0.5
            
        if overlap_status_A_now == 0 and overlap_status_A == 0.5:
            overlap_status_A_new = 0
        elif overlap_status_A_now == 1 and overlap_status_A == 0.5:
            overlap_status_A_new = 1
        else:
            overlap_status_A_new = overlap_status_A
        
        ###########################################################################################
        
        overlap_status_now = [overlap_status_A_now, overlap_status_B_now]
        overlap_status_new = [overlap_status_A_new, overlap_status_B_new]
        
        ###########################################################################################

        if len(track_history[track_id]) != 1:

            if overlap_status_now == [0, 0] and overlap_status_new == [1, 0]:
                ingress = ingress + 1
                alarm_type = 'Ingress'
                description = area_type
                total_count = ingress
                alarm_prediction.append({'AlarmType': alarm_type, 
                                        'StartTime': start_time, 
                                        'AlarmDescription': description, 
                                        'TotalCount': total_count
                                        })
            if overlap_status_now == [1, 0] and overlap_status_new == [0, 0]:
                egress = egress + 1
                alarm_type = 'Egress'
                description = area_type
                total_count = egress
                alarm_prediction.append({'AlarmType': alarm_type, 
                                        'StartTime': start_time, 
                                        'AlarmDescription': description, 
                                        'TotalCount': total_count
                                        })

        in_out_check[track_id] = overlap_status_new

    Queueing_params = [ingress, egress]
    
    return Queueing_params

###################################################################################################
###################################################################################################

class PeopleCounting:
    """
    사람 수 세기를 위한 클래스로, 두 개의 구역(PeopleCounting A와 B)에서의 인원 수를 추적
    각 구역은 입출구 카운팅 및 알람 예측을 수행
    """
    
    def __init__(self, 
                 areas, 
                 current_frame, 
                 fps, 
                 width, 
                 height, 
                 frame_skip):
        """
        PeopleCounting 클래스의 인스턴스를 초기화
        각 구역에 대한 카운팅과 알람, 추적 기록을 초기화
        
        Args:
            areas (list): 탐지 영역에 대한 좌표
        """
        
        hours, minutes, seconds, milliseconds = frame_to_time(current_frame, fps)
        self.start_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
        ### PeopleCounting 확인
        self.PeopleCounting_A_area = areas['PeopleCountingA']
        self.PeopleCounting_B_area = areas['PeopleCountingB']
        
        ### 영역 변수
        self.alarm_prediction = []
        
        self.Counting_track_history = defaultdict(lambda: [])
        self.Counting_last_update_frame = defaultdict(lambda: [])
        self.Counting_in_out_check = defaultdict(lambda: [0, 0])
        
        self.in_count = 0
        self.out_count = 0
        

        
    def process_results(self, 
                        results, 
                        frame_count, 
                        current_frame, 
                        fps):
        """
        비디오 분석 결과를 받아서 사람 수 카운팅 및 관련 데이터를 업데이트

        Args:
            results: 비디오 분석 결과 데이터

        Returns:
            None: 이 메서드는 결과를 반환하지 않고 내부 상태를 업데이트
        """
        
        ### 초기 시간
        hours, minutes, seconds, _ = frame_to_time(current_frame, fps)
        marketing_start_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
        Counting_track_ids = box_track(results, 
                    self.Counting_track_history, 
                    self.Counting_in_out_check, 
                    self.Counting_last_update_frame, 
                    frame_count)
        
        PeopleCounting_params = [self.in_count, self.out_count]
        
        PeopleCounting_params = alarm_C(Counting_track_ids, 
                self.Counting_in_out_check, 
                self.Counting_track_history, 
                'PeopleCounting', 
                self.PeopleCounting_A_area, 
                self.PeopleCounting_B_area, 
                self.alarm_prediction, 
                marketing_start_time, 
                PeopleCounting_params
                )
        
        self.in_count, self.out_count = PeopleCounting_params
        
    def postprocess(self, 
                    video_test_mode, 
                    skip_time):
        
        if not video_test_mode:
            increase_time(self.alarm_prediction, skip_time)
    
###################################################################################################

class Queueing:
    """
    사람 수 세기를 위한 클래스로, 하나의 구역에서의 인원 수를 추적
    구역내 입출입 카운팅 및 알람 예측을 수행
    """
    
    def __init__(self, 
                 areas, 
                 current_frame, 
                 fps, 
                 width, 
                 height, 
                 frame_skip):
        """
        PeopleCounting 클래스의 인스턴스를 초기화
        각 구역에 대한 카운팅과 알람, 추적 기록을 초기화
        
        Args:
            areas (list): 탐지 영역에 대한 좌표
        """
        
        hours, minutes, seconds, milliseconds = frame_to_time(current_frame, fps)
        self.start_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
        ### Queueing 확인
        self.Queueing_area = areas['Queueing']
        
        ### 영역 변수
        self.alarm_prediction = []
        
        self.Queueing_track_history = defaultdict(lambda: [])
        self.Queueing_last_update_frame = defaultdict(lambda: [])
        self.Queueing_in_out_check = defaultdict(lambda: [0, 0])
        
        self.ingress = 0
        self.egress = 0
        

        
    def process_results(self, 
                        results, 
                        frame_count, 
                        current_frame, 
                        fps):
        """
        비디오 분석 결과를 받아서 사람 수 카운팅 및 관련 데이터를 업데이트

        Args:
            results: 비디오 분석 결과 데이터

        Returns:
            None: 이 메서드는 결과를 반환하지 않고 내부 상태를 업데이트
        """
        
        ### 초기 시간
        hours, minutes, seconds, _ = frame_to_time(current_frame, fps)
        marketing_start_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
        Queueing_track_ids = box_track(results, 
                    self.Queueing_track_history, 
                    self.Queueing_in_out_check, 
                    self.Queueing_last_update_frame, 
                    frame_count)
        
        Queueing_params = [self.ingress, self.egress]
        
        Queueing_params = alarm_Q(Queueing_track_ids, 
                self.Queueing_in_out_check, 
                self.Queueing_track_history, 
                'Queueing', 
                self.Queueing_area, 
                self.alarm_prediction, 
                marketing_start_time, 
                Queueing_params
                )
        
        self.ingress, self.egress = Queueing_params
        
    def postprocess(self, 
                    video_test_mode, 
                    skip_time):
        
        if not video_test_mode:
            increase_time(self.alarm_prediction, skip_time)
        
        pass

###################################################################################################



###################################################################################################






###################################################################################################
###################################################################################################