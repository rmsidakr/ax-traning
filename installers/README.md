# 설치파일

Python·Node.js는 **노트북이 공식 사이트에서 직접 받아** 설치합니다(2026-10-27 결정). 메일로 보내는 것은 Skill 압축본(`ai-gateway-skills…zip`)과 Virtual Key뿐입니다. 교육생 PC는 Windows 11 64비트입니다.

## 노트북이 받는 파일 (저장소에 두지 않음)

| 프로그램 | 받는 곳 | SHA-256 |
|---|---|---|
| Python 3.12.10 (64비트) `python-3.12.10-amd64.exe` | https://www.python.org/ftp/python/3.12.10/ | `67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb` |
| Node.js 24.22.1 LTS (64비트) `node-v24.22.1-x64.msi` | https://nodejs.org/dist/v24.22.1/ | `3bda4baf1ee709b33cf920dd633106ddb23951e322bff9c03ec9f64ab8981b01` |

- 노트북은 공식 사이트에서 받은 뒤 **SHA-256 지문이 위 값과 같을 때만** 설치합니다. 받지 못하면(사내망 차단 등) 다운로드·바탕화면·노트북 폴더에 같은 파일이 있는지 보고, 지문이 맞으면 그것을 씁니다 — 다운로드가 막힌 교육장에서는 보조강사가 이 경로로 넘길 수 있습니다.
- Python 3.12는 1단계, Node.js는 4단계가 설치합니다. Python은 이 사용자에게만 설치하고(관리자 승인 없음) 3.12를 기본 Python으로 설정합니다.
- 두 파일의 지문은 2026-10-25에 공식 배포처에서 받아 확인한 값입니다(배포자 디지털 서명 유효, Node.js는 공식 `SHASUMS256.txt`와 일치). 사내망에서 받아지는 것은 2026-10-27에 다시 확인했습니다.
- Python 3.12는 3.12.10이 Windows 설치파일이 나온 마지막 버전입니다. 그 뒤 3.12.x는 소스 코드로만 나옵니다.
- PC에 Python이 아예 없어 노트북을 열 수조차 없을 때만 교안 "1. 사전 안내 → VS Code 확장 설치 → ① Python"(접힌 칸)대로 직접 설치합니다.

## 저장소에 두는 파일

| 파일 | 내용 | SHA-256 |
|---|---|---|
| `ipykernel-py312-win64.zip` | ipykernel 7.4.0과 딸린 부품 29개 (Python 3.12, 64비트), 설치 파일 `install_ipykernel.bat` | `ed9806140f1379c7077b43a4b19f19117e3909fb20d610e10edc7aa991b429bc` |

- 노트북 1단계가 Python 3.12에 ipykernel을 **공식 PyPI에서 받아** 설치합니다(사내 pip 저장소에는 ipykernel이 없어 `--index-url https://pypi.org/simple`을 지정합니다).
- 이 묶음은 그 설치까지 막혔을 때 쓰는 **보조강사용 비상 수단**입니다. 압축을 풀고 `install_ipykernel.bat`를 더블클릭하면 인터넷 없이 설치합니다.
- 묶음을 새로 만들 때: `py -3.12 tools/build_ipykernel_bundle.py` (교육생 PC와 같은 Windows 64비트 Python 3.12에서 실행)
