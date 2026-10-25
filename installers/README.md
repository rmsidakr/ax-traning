# 교육생 배포 설치파일

교육 전에 메일로 교육생에게 보낼 설치파일입니다. 교육생 PC는 Windows 11 64비트입니다.

| 파일 | 프로그램 | 받은 곳 | SHA-256 |
|---|---|---|---|
| `python-3.12.10-amd64.exe` | Python 3.12.10 (64비트) | https://www.python.org/ftp/python/3.12.10/ | `67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb` |
| `node-v24.22.1-x64.msi` | Node.js 24.22.1 LTS (64비트) | https://nodejs.org/dist/v24.22.1/ | `3bda4baf1ee709b33cf920dd633106ddb23951e322bff9c03ec9f64ab8981b01` |

- 두 파일 모두 공식 배포처에서 2026-10-25에 받았고, 배포자 디지털 서명(Python Software Foundation, OpenJS Foundation)이 유효합니다. Node.js는 공식 `SHASUMS256.txt`의 값과도 같습니다.
- Python 3.12는 3.12.10이 Windows 설치파일이 나온 마지막 버전입니다. 그 뒤 3.12.x는 소스 코드로만 나옵니다.
- 설치 방법은 교안 "1. 사전 안내 → Python과 Jupyter 확장 설치"에 있습니다. 설치 확인은 셋팅 노트북 1단계(Python)와 7단계(Node.js)에서 합니다.
