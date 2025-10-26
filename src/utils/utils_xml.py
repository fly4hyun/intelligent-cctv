###################################################################################################
###################################################################################################

import os

import xml.etree.ElementTree as ET
from xml.dom import minidom

###################################################################################################
###################################################################################################

area_mapping_class = {
    '마케팅': ['PeopleCountingA', 'PeopleCountingB', 'Queueing'], 
    '방화': [], 
    '배회': ['Loitering'], 
    '싸움': [], 
    '쓰러짐': [], 
    '유기': [], 
    '침입': ['Intrusion'], 
}

###################################################################################################
###################################################################################################
### xml 읽어오기

def parse_xml(file_path):
    """
    xml 파일을 읽어와서 반환
    
    Args:
        file_path (str): xml 파일 경로
    
    Returns:
        root (xml.etree.ElementTree.Element): xml 문서의 루트 요소
    """
    
    tree = ET.parse(file_path)
    root = tree.getroot()
    return root

###################################################################################################
### 비디오 리스트 가져오기

def get_video_list(xml_path):
    """
    RTSP_streaming_list.xml 파일을 읽어와서 동영상 리스트를 반환
    
    Args:
        xml_path (str): xml 파일 경로
        
    Returns:
        List[str]: 동영상 파일 이름의 리스트
    """
    
    root = parse_xml(xml_path)
    file_elements = root.findall(".//File/Name")
    
    return [file_elem.text for file_elem in file_elements]

###################################################################################################
### 영상 내 영역 및 탐지 목표 정보 가져오기

def get_detection_areas(mapping_file, folder_path, class_list):
    """
    해당 동영상의 mapping 파일로부터 탐지 영역과 탐지 클래스 정보 반환
    
    Args:
        mapping_file (str): XML 매핑 파일의 이름
        folder_path (str): 매핑 파일이 위치한 폴더 경로
        class_list (List[str]): 탐지 클래스 목록

    Returns:
        Dict[str, List[Tuple[int, int]]]: 탐지 영역의 타입을 키로 하고, 각 타입에 해당하는 점의 좌표 리스트를 값으로 하는 딕셔너리
    """
    
    area_type_list = ['DetectArea']
    for cls in class_list:
        area_type_list += area_mapping_class[cls]
    area_type_list = list(set(area_type_list))
    
    xml_path = os.path.join(folder_path, mapping_file)
    if not os.path.exists(xml_path):
        return {}
    
    root = parse_xml(xml_path)
    areas = {}
    for area_type in area_type_list:
        points = []
        for point in root.findall(f".//{area_type}/Point"):
            x, y = map(int, point.text.split(','))
            points.append((x, y))
        if points:
            areas[area_type] = points
    return areas





###################################################################################################

def xml_from_alarm(alarm_prediction, name):
    
    kisa_library_index = ET.Element('KisaLibraryIndex')
    library = ET.SubElement(kisa_library_index, 'Library')
    clip = ET.SubElement(library, 'Clip')
    header = ET.SubElement(clip, 'Header')
    
    ###############################################################################################
    
    ET.SubElement(header, 'AlarmEvents').text = str(len(alarm_prediction))
    ET.SubElement(header, 'Filename').text = name + '.mp4'
    
    ###############################################################################################
    
    none_check = 0
    for alarm in alarm_prediction:
        if none_check == 0:
            alarms = ET.SubElement(clip, 'Alarms')
            none_check = 1
        alarm_elem = ET.SubElement(alarms, 'Alarm')
        ET.SubElement(alarm_elem, 'AlarmDescription').text = alarm['AlarmDescription']
        ET.SubElement(alarm_elem, 'StartTime').text = alarm['StartTime']
        if 'AlarmType' in list(alarm.keys()):
            if alarm['AlarmType'] == 'InCount':
                ET.SubElement(alarm_elem, 'InCount').text = str(alarm['TotalCount'])
            elif alarm['AlarmType'] == 'OutCount':
                    ET.SubElement(alarm_elem, 'OutCount').text = str(alarm['TotalCount'])
            elif alarm['AlarmType'] == 'Ingress':
                    ET.SubElement(alarm_elem, 'Ingress').text = str(alarm['TotalCount'])
            elif alarm['AlarmType'] == 'Egress':
                    ET.SubElement(alarm_elem, 'Egress').text = str(alarm['TotalCount'])
        if 'AlarmDescription' in list(alarm.keys()):
            if alarm['AlarmDescription'] == 'Loitering':
                ET.SubElement(alarm_elem, 'AlarmDuration').text = str(alarm['AlarmDuration'])
            if alarm['AlarmDescription'] == 'Intrusion':
                ET.SubElement(alarm_elem, 'AlarmDuration').text = str(alarm['AlarmDuration'])
    
    ###############################################################################################

    xml_str = ET.tostring(kisa_library_index, encoding='utf-8', method='xml')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml_str = parsed_xml.toprettyxml(indent="  ")

    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    pretty_xml_str = '\n'.join(pretty_xml_str.split('\n')[1:])

    with open('../KISAresult/' + name + '.xml', 'w', encoding='utf-8') as f:
        f.write(xml_declaration + pretty_xml_str)
        
###################################################################################################








###################################################################################################
###################################################################################################