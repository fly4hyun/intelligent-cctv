###################################################################################################
###################################################################################################

import os

import xml.etree.ElementTree as ET
from shapely.geometry import Polygon, box

from datetime import datetime, timedelta

###################################################################################################
###################################################################################################



###################################################################################################
### 시간 변환

def frame_to_time(frame_number, fps):
    """
    주어진 프레임 번호와 비디오의 프레임 속도(fps)를 기반으로 시간 정보를 계산
    
    Args:
        frame_number (int): 비디오의 프레임 번호
        fps (float): 비디오의 프레임 속도 (초당 프레임 수)
    
    Returns:
        tuple: 계산된 시간 정보 (시, 분, 초, 밀리초)를 포함하는 튜플
    """
    seconds_total = frame_number / fps
    hours = int(seconds_total // 3600)
    minutes = int((seconds_total % 3600) // 60)
    seconds = int(seconds_total % 60)
    milliseconds = int((seconds_total - int(seconds_total)) * 1000)  # 소수점 이하를 밀리초로 변환

    return hours, minutes, seconds, milliseconds

###################################################################################################

def increase_time(alarm_list, seconds):
    """
    주어진 알람 목록에서 각 알람의 시작 시간을 지정된 초 만큼 증가

    Args:
        alarm_list (list of dict): 알람 데이터를 담고 있는 사전의 리스트. 각 사전은 'StartTime' 키를 포함해야 하며,
                                   해당 키의 값은 "%H:%M:%S" 형식의 문자열
        seconds (int): 시작 시간에 추가할 초의 수.

    Returns:
        None: 이 함수는 알람 목록을 직접 수정하며 반환 값은 없dma

    Example:
        alarm_list = [{'StartTime': '12:34:56'}, {'StartTime': '01:23:45'}]
        increase_time(alarm_list, 60)  # 각 알람의 시작 시간을 1분 증가
    """
    
    for alarm in alarm_list:
        start_time = datetime.strptime(alarm['StartTime'], "%H:%M:%S")
        new_time = start_time + timedelta(seconds=seconds)
        alarm['StartTime'] = new_time.strftime("%H:%M:%S")




###################################################################################################
###################################################################################################

def overlap_check(detection_area, bbox, overlap_score = 0.9):
    """
    주어진 감지 영역과 바운딩 박스 사이의 겹침 비율을 계산하고, 설정된 임계값에 따라 겹침 결과를 반환

    Args:
        detection_area (list of tuples): 감지 영역의 좌표 목록. 각 튜플은 (x, y) 형태
        bbox (tuple): 바운딩 박스의 좌표 (x, y, w, h). 여기서 (x, y)는 중심점, w는 너비, h는 높이
        overlap_score (float): 겹침을 '1' (완전 겹침)으로 판정하는 최소 비율. 기본값은 0.9

    Returns:
        int or float: 
            - 1: 겹침 비율이 overlap_score 이상일 경우
            - 0: 겹침 비율이 1 - overlap_score 이하일 경우
            - float: 위 두 조건에 해당하지 않는 경우, 실제 겹침 비율을 반환

    Notes:
        - 겹침 비율은 바운딩 박스의 면적에 대한 감지 영역과의 교차 면적의 비율로 계산
        - 함수는 Shapely 라이브러리의 Polygon과 box 객체를 사용하여 공간적 계산을 수행
        - 감지 영역의 다각형이 유효하지 않은 경우, `buffer(0)`을 사용하여 보정
    """
    detection_polygon = Polygon(detection_area)
    x, y, w, h = bbox
    bbox_poly = box(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    
    if not detection_polygon.is_valid:
        detection_polygon = detection_polygon.buffer(0)

    intersection_area = detection_polygon.intersection(bbox_poly).area
    bbox_area = bbox_poly.area
    
    overlap_ratio = intersection_area / bbox_area
    
    if overlap_ratio >= overlap_score:
        return 1
    elif overlap_ratio <= 1 - overlap_score:
        return 0
    else:
        return overlap_ratio

###################################################################################################
### 겹치는 정도 측정

def box_iou(bbox1, bbox2):
    # bbox1과 bbox2는 (x, y, w, h) 형식입니다. x, y는 박스의 중심 좌표입니다.
    
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2

    # 각 박스의 좌측 상단과 우측 하단 좌표를 계산
    xmin1 = x1 - w1 / 2
    ymin1 = y1 - h1 / 2
    xmax1 = x1 + w1 / 2
    ymax1 = y1 + h1 / 2

    xmin2 = x2 - w2 / 2
    ymin2 = y2 - h2 / 2
    xmax2 = x2 + w2 / 2
    ymax2 = y2 + h2 / 2

    # 교집합의 좌표
    inter_xmin = max(xmin1, xmin2)
    inter_ymin = max(ymin1, ymin2)
    inter_xmax = min(xmax1, xmax2)
    inter_ymax = min(ymax1, ymax2)

    # 교집합의 넓이와 높이
    inter_width = max(0, inter_xmax - inter_xmin)
    inter_height = max(0, inter_ymax - inter_ymin)
    
    # 교집합의 면적
    intersection_area = inter_width * inter_height
    
    # 각 박스의 면적
    area1 = w1 * h1
    area2 = w2 * h2
    
    # 합집합의 면적
    union_area = area1 + area2 - intersection_area
    
    # IOU 계산
    iou = intersection_area / union_area if union_area != 0 else 0
    
    return iou

###################################################################################################
# 중앙 영역을 정의하는 함수

def is_in_center_area(x, y, w, h, frame_width, frame_height, margin_ratio=0.1):
    margin_x = frame_width * margin_ratio
    margin_y = frame_height * margin_ratio

    center_x_min = margin_x
    center_y_min = margin_y
    center_x_max = frame_width - margin_x
    center_y_max = frame_height - margin_y

    box_x_min = x - w / 2
    box_y_min = y - h / 2
    box_x_max = x + w / 2
    box_y_max = y + h / 2

    if (box_x_min >= center_x_min and box_x_max <= center_x_max and
        box_y_min >= center_y_min and box_y_max <= center_y_max):
        return True
    return False

###################################################################################################
###################################################################################################