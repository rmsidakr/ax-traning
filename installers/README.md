# 교육생 배포 설치파일

교육 전에 메일로 교육생에게 보낼 설치파일입니다. 교육생 PC는 Windows 11 64비트입니다.

| 파일 | 프로그램 | 받은 곳 | SHA-256 |
|---|---|---|---|
| `python-3.12.10-amd64.exe` | Python 3.12.10 (64비트) | https://www.python.org/ftp/python/3.12.10/ | `67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb` |
| `node-v24.22.1-x64.msi` | Node.js 24.22.1 LTS (64비트) | https://nodejs.org/dist/v24.22.1/ | `3bda4baf1ee709b33cf920dd633106ddb23951e322bff9c03ec9f64ab8981b01` |
| `ipykernel-py312-win64.zip` | ipykernel 7.4.0과 딸린 부품 29개 (Python 3.12, 64비트), 설치 파일 `install_ipykernel.bat` | https://pypi.org/ (`tools/build_ipykernel_bundle.py`로 묶음) | `ed9806140f1379c7077b43a4b19f19117e3909fb20d610e10edc7aa991b429bc` |

- Python·Node.js 설치파일은 공식 배포처에서 2026-10-25에 받았고, 배포자 디지털 서명(Python Software Foundation, OpenJS Foundation)이 유효합니다. Node.js는 공식 `SHASUMS256.txt`의 값과도 같습니다.
- Python 3.12는 3.12.10이 Windows 설치파일이 나온 마지막 버전입니다. 그 뒤 3.12.x는 소스 코드로만 나옵니다.
- Python 3.12는 셋팅 노트북 1단계, Node.js는 5단계가 받은 설치파일을 찾아 자동으로 설치합니다(다운로드·바탕화면·노트북 폴더 → 없으면 공식 사이트, SHA-256이 위 값과 같을 때만). Python은 이 사용자에게만 설치하고(관리자 승인 없음) 3.12를 기본 Python으로 설정합니다. PC에 Python이 아예 없어 노트북을 열 수 없을 때만 교안 "1. 사전 안내 → VS Code 확장 설치 → ① Python"(접힌 칸)대로 직접 설치합니다.
- ipykernel 묶음은 노트북 0단계에서 VS Code의 ipykernel 설치가 실패할 때(사내망에서 pip 접속이 막힌 경우) 씁니다. 압축을 풀고 `install_ipykernel.bat`를 더블클릭하면 인터넷 없이 Python 3.12에 설치합니다. 사용법은 교안 "Jupyter 노트북이 실행되지 않을 때" 표에 있습니다.
- 묶음을 새로 만들 때: `py -3.12 tools/build_ipykernel_bundle.py` (교육생 PC와 같은 Windows 64비트 Python 3.12에서 실행)
- 메일 보안 필터가 압축 파일 안의 `.bat`를 막을 수 있습니다. 막히면 사내 공유 폴더 등 다른 경로로 전달합니다.
