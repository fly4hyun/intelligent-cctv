@echo off
REM 1) conda 환경 활성화
call "%USERPROFILE%\anaconda3\Scripts\activate.bat" cctv_ai

REM 2) pythonw 로 gui_main.py 실행 (콘솔창 없이)
start "" pythonw "%~dp0gui_main.py"

REM 3) 배치파일은 종료해도 GUI는 계속 실행됩니다.
exit
