@echo off
rem 압축을 푼 폴더에서 더블클릭: 인터넷 없이 wheels 폴더의 파일로 Python 3.12에 ipykernel을 설치한다
chcp 65001 >nul
title ipykernel 설치

if not exist "%~dp0wheels\ipykernel-*.whl" (
  echo [X] 설치 파일을 찾지 못했습니다.
  echo     압축 파일을 마우스 오른쪽 버튼으로 눌러 [모두 압축 풀기]를 한 뒤,
  echo     풀린 폴더 안의 install_ipykernel.bat를 다시 더블클릭하세요.
  goto :end
)

rem Python 3.12 찾기: py 런처 → 사용자 설치 위치 → 모든 사용자 설치 위치
set "PYTHON="
for /f "delims=" %%p in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON=%%p"
if not defined PYTHON if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PYTHON if exist "%ProgramFiles%\Python312\python.exe" set "PYTHON=%ProgramFiles%\Python312\python.exe"
if not defined PYTHON (
  echo [X] Python 3.12을 찾지 못했습니다.
  echo     메일로 받은 python-3.12.10-amd64.exe를 먼저 설치하고 다시 더블클릭하세요.
  goto :end
)

echo Python 3.12: %PYTHON%
echo ipykernel을 설치합니다. 1분 정도 걸립니다 ...
echo.
"%PYTHON%" -m pip install --no-index --find-links "%~dp0wheels" --disable-pip-version-check ipykernel
if errorlevel 1 (
  echo.
  echo [X] 설치하지 못했습니다. 이 창을 그대로 두고 보조강사를 불러 주세요.
  goto :end
)
"%PYTHON%" -c "import ipykernel; print('[OK] ipykernel', ipykernel.__version__, '설치 완료. 이 창을 닫고 VS Code에서 노트북을 여세요.')"

:end
echo.
pause
