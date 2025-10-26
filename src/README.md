# CCTV AI – Intelligent Event Detection Demo

YOLO v11/12 가중치를 이용해 **배회(Loitering) · 침입(Intrusion) · 마케팅(피플카운팅 / 큐 대기)** 이벤트를
실시간 **RTSP 스트림** 또는 로컬 MP4에서 탐지하고  
**KISA 인증 XML** 포맷으로 결과를 생성하는 데모입니다.

```
main.py           # 스트림 전체 파이프라인
main_one.py       # 단일 영상 테스트 (디버그용)
score.py          # 예측 XML ↔ 정답 XML 비교 스크립트
utils/            # 후처리 · XML · 스레드 I/O 모듈
yolo_weight/      # YOLOv11·12 사전학습 가중치(.pt)
temp_video_1.mp4  # 스트림 예열용 더미 영상
```

---

## 1. 환경 구축 (Windows / CUDA 11.8 GPU 기준)

```bash
# 1) 파이썬 3.12 가상환경
conda create --name cctv_ai python=3.12.7 -y
conda activate cctv_ai

# 2) YOLO + PyTorch CUDA 11.8
pip install ultralytics==8.3.39
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118
pip uninstall -y torchvision && pip install torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu118

# 3) 추가 파이썬 패키지
pip install -r requirements.txt

# 4) H.264 디코더 DLL 복사
#   (FFmpeg가 OpenH264 DLL을 찾도록 System32로 복사)
copy openh264-1.8.0-win64.dll C:\Windows\System32

# 5) FFmpeg 설치 (영상 저장 · 스트림 체크용)
#   예: ffmpeg‑6.x full build → C:/Program Files/ffmpeg
setx PATH "%PATH%;C:\Program Files\ffmpeg\bin"
```

> GPU가 없으면 PyTorch CPU 빌드로 교체하고 `ultralytics`를 `--no-deps`로 설치한 뒤
> `torchvision`도 CPU 빌드로 재설치하세요.

---

## 2. 실행 방법

### 2‑1. RTSP 실시간 스트림

```bash
python main.py ^
  --class_list 배회,마케팅,침입 ^
  --yolo_model yolo12x ^
  --stream_url rtsp://192.168.0.2:8554/ ^
  --video_list_path ..\KISAlist\RTSP_streaming_list.xml ^
  --video_mapping_path ..\KISAmap\ ^
  --target_fps 10 ^
  --skip_time 30
```

- **video_saver** 스레드가 스트림을 mp4로 저장 →  
  **video_analyzer** 스레드가 YOLO 추론 및 후처리를 수행합니다.  
- 결과 XML은 `..\KISAresult\<영상이름>.xml` 에 저장됩니다.

### 2‑2. 단일 MP4 테스트

```bash
python main_one.py ^
  --test_mode True ^
  --test_path .\ ^
  --test_save_path .\temp\ ^
  --yolo_model yolo11x
```

---

## 3. 주요 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--class_list` | 활성화할 이벤트 클래스(콤마 구분) | `배회,마케팅,침입` |
| `--yolo_model` | `yolo_weight/<name>.pt` 선택 | `yolo11x` |
| `--test_mode` | True 시 로컬 MP4 사용, False 시 RTSP 스트림 | False |
| `--target_fps` | 분석 FPS (원본 FPS가 더 높으면 프레임 스킵) | 30 |
| `--skip_time` | 스트림 수신 후 분석 지연(초) | 30 |

---

## 4. 결과 XML 구조 (요약)

```xml
<KisaLibraryIndex>
  <Library>
    <Clip>
      <Header>
        <AlarmEvents>3</AlarmEvents>
        <Filename>sample.mp4</Filename>
      </Header>
      <Alarms>
        <Alarm>
          <AlarmDescription>Loitering</AlarmDescription>
          <StartTime>00:00:12</StartTime>
          <AlarmDuration>8</AlarmDuration>
        </Alarm>
        <Alarm>
          <AlarmDescription>PeopleCounting</AlarmDescription>
          <StartTime>00:02:05</StartTime>
          <OutCount>8</OutCount>
        </Alarm>
        …
      </Alarms>
    </Clip>
  </Library>
</KisaLibraryIndex>
```

- **PeopleCounting / Queueing** : `InCount`, `OutCount`, `Ingress`, `Egress` 태그 사용  
- **Loitering / Intrusion** : `AlarmDuration` 태그 포함

---

## 5. 참고 / 트러블슈팅

1. ❗ **FFmpeg not found** – `ffmpeg ‑version` 으로 설치·PATH 설정을 확인하세요.  
2. **“openh264 dll missing” 오류** – DLL이 `C:\Windows\System32` 에 존재하는지 확인합니다.  
3. **RTSP 프레임을 못 받음** – `utils_save_video_temp.py` 의 `check_stream()` 함수가
   UDP/TCP 모두 실패하는 경우 네트워크/카메라 방화벽 설정을 점검하세요.  
4. YOLO 추론 파라미터(`conf`, `iou`)는 `utils_main.py` 내부 `yolo_model.track()` 호출부에서 조정 가능합니다.
