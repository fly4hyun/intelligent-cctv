###################################################################################################
###################################################################################################

import re
import cv2
import time
from pathlib import Path


import requests

import subprocess

###################################################################################################

# ffmpeg_path = "C:/Program Files/ffmpeg/bin/ffmpeg.exe"
ffmpeg_path = "ffmpeg"
output_file = "full_record.mp4"

def check_stream(rtsp_url, transport_mode, test_duration=20):
    
    ffmpeg_check_cmd = [
        ffmpeg_path,
        "-loglevel", "debug",
        "-rtsp_transport", transport_mode,
        "-i", rtsp_url,
        "-c", "copy",
        "-t", str(test_duration),
        "-f", "null", "-"
        # "-y",
        # output_file
    ]
    
    # seconds 0
    # [tcp @ 0000027ab70b0fc0] Address 192.168.0.2 port 8554

    # seconds 0
    # [tcp @ 0000027ab70b0fc0] Starting connection attempt to 192.168.0.2 port 8554
    
    proc = subprocess.Popen(ffmpeg_check_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    frame_received = False
    start_time_check = time.time()
    
    # while True:
    #     if proc.poll() is not None:
    #         break
    #     line = proc.stderr.readline()
    #     print(line)
    #     if line:
    #         if 'H264/90000' in line:
    #             start_time = time.time() - 3
    #             print('start_time', start_time)
    #         seconds = 0
    #         if "time=" in line:
    #             match = re.search(r"time=\d{2}:\d{2}:(\d{2}\.\d+)", line)  # 소수점을 포함한 초 추출
    #             if match:
    #                 seconds = float(match.group(1))  # 초 값을 소수로 변환
    #             # else:
    #                 # print("time= 로그를 찾지 못했습니다.")
    #         # else:
    #             # print("line에 'time=' 문자열이 없습니다.")
    #         print('seconds', seconds)
    #         # start_time = time.time()# - seconds
    #         if "frame=" in line and not frame_received:
    #             frame_received = True
    #     if time.time() - start_time_check > test_duration:
    #         break
    #     time.sleep(0.01)
    
    seconds = 0
    while True:
        if proc.poll() is not None:
            break
        line = proc.stderr.readline()
        # print(line)
        if line:
            if 'H264/90000' in line:
                start_time = time.time()
                #print('start_time', start_time)
            
            if "start:" in line:
                match = re.search(r"start: (\d+.\d+)", line)  # 소수점을 포함한 초 추출
                # print(match)
                if match:
                    seconds = float(match.group(1))  # 초 값을 소수로 변환
                start_time = start_time - seconds # - 0.5
                # else:
                    # print("time= 로그를 찾지 못했습니다.")
            # else:
                # print("line에 'time=' 문자열이 없습니다.")
            # print('seconds', seconds)
            # start_time = time.time()# - seconds
            if "frame=" in line and not frame_received:
                frame_received = True
        if time.time() - start_time_check > test_duration:
            break
        time.sleep(0.01)
    
    

    proc.terminate()
    proc.wait(timeout=1)
    return frame_received, start_time

###################################################################################################

import socket

def is_rtsp_stream_ready(rtsp_url, timeout=0.01):
    # rtsp:// 형태에서 호스트와 포트를 파싱
    # rtsp://192.168.0.2:8554/ 형태 가정
    if rtsp_url.startswith("rtsp://"):
        temp = rtsp_url[7:]
    else:
        temp = rtsp_url
    host_port = temp.split('/')[0]
    if ':' in host_port:
        host, port_str = host_port.split(':')
        port = int(port_str)
    else:
        host = host_port
        port = 554  # 포트 명시 없을 경우 기본값 사용
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        request = f"OPTIONS {rtsp_url} RTSP/1.0\r\nCSeq: 1\r\n\r\n"
        s.sendall(request.encode('utf-8'))
        data = s.recv(1024)
        if b"RTSP/1.0 200" in data:
            return True
    except:
        pass
    finally:
        s.close()
    return False



###################################################################################################

def video_saver(test_video_path, 
                save_queue, 
                analysis_queue, 
                save_path, 
                video_test_mode, 
                skip_time, 
                streaming_check
                ):
    """
    분석할 동영상을 임시 폴더에 저장한 다음 분석 큐에 동영상 위치를 저장
    이 함수는 별도의 스레드에서 실행되어 비디오 파일을 지속적으로 처리

    Args:
        test_video_path (str): 분석할 스트리밍 주소 또는 폴더 주소
        save_queue (queue.Queue): 저장할 비디오 이름을 포함하는 큐
        analysis_queue (queue.Queue): 처리 완료된 비디오 파일 경로를 저장할 큐
        save_path (str): 비디오를 저장할 디렉토리 경로
        video_test_mode (bool): 테스트 모드의 활성화 상태, True일 경우 각 비디오 파일을 개별적으로 처리
        skip_time (int): 스트리밍에서 실제 저장을 시작하기 전에 건너뛸 시간(초)
    
    Returns:
        None: 결과는 analysis_queue를 통해 전달
    """
    
    ###
    save_directory = Path(save_path)
    save_directory.mkdir(exist_ok=True)
    
    ###
    while True:
        
        if streaming_check[1]:
            
            ######## 예열
            cap = cv2.VideoCapture('./temp_video_1.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            out = cv2.VideoWriter('./temp_video_2.mp4', fourcc, fps, (width, height), True)
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
            
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            
            Path('./temp_video_2.mp4').unlink()
            
            streaming_check[1] = False
            print('ready.')
        
        ###
        
        video_name = save_queue.get()
        if video_name is None:
            analysis_queue.put(None)
            break
        
        ###
        video_path = save_directory / f"{video_name}"
        print('puth the streaming button')
        print(f"Processing video: {video_path}")
        
        start_time = time.time()
        
        ### 첫번째 영상에 대한 시작 시간 측정
        # if streaming_check[0]:
        if not video_test_mode:
            #print(test_video_path)
            while True:
                # # TCP로 테스트
                # print("TCP 방식으로 스트림 테스트 중...")
                # aaa, bbb = check_stream(test_video_path, "tcp")
                # if aaa:
                #     chosen_transport = "tcp"
                #     print("스트림 시작 감지(TCP)!")
                #     break
                # UDP로 테스트
                print("UDP 방식으로 스트림 ...")
                print("Push The Video Load")
                check_stream_bool, start_time = check_stream(test_video_path, "udp")
                if check_stream_bool:
                    chosen_transport = "udp"
                    print("스트림 시작 감지(UDP)!")
                    break
                print("TCP/UDP 모두 프레임 없음. 1초 후 재시도.")
            print(time.time() - start_time)
            streaming_check[0] = False
        
        if video_test_mode:
            cap = cv2.VideoCapture(test_video_path + video_name)
        else:
            cap = cv2.VideoCapture(test_video_path)
        # print(2)
        # if cap.isOpened():
        #     print(3)
        #     streaming_check[0] = True
        # else:
        #     if streaming_check[0] == False:
        #         temp_list = []
        #         while not save_queue.empty():
        #             temp_list.append(save_queue.get())
        #         temp_list.insert(0, test_video_path)
                
        #         for item in temp_list:
        #             save_queue.put(item)
        #         print(1)
        #         continue
        
        ### 스트리밍 시 전송되는 동영상이 동영상 재생 시간과 동일하기 때문에, 로컬에 저장된 걸 로드할때는 다름
        
        if not video_test_mode:
            while time.time() - start_time < skip_time:
                ret, frame = cap.read()
                if not ret:
                    break
                
        ###
        fourcc = cv2.VideoWriter_fourcc(*'avc1')  # 코덱을 'avc1'로 변경
        # fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 또는 'mp4v' 사용 가능
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        ###
        out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height), True)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            
        ###
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        print(f"Processed video: {video_path}")
        
        analysis_queue.put(str(video_path))
        
###################################################################################################





###################################################################################################





###################################################################################################
###################################################################################################