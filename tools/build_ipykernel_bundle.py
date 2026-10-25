"""교육생에게 메일로 보낼 ipykernel 설치파일 묶음(installers/ipykernel-py312-win64.zip)을 만든다.

- 교육생 PC와 같은 Python 3.12(Windows 64비트)의 pip로 공식 PyPI에서 ipykernel과 딸린 부품을 받는다.
- 묶음 안의 install_ipykernel.bat를 더블클릭하면 인터넷 없이 그 파일들로 설치한다.
사용법: py -3.12 tools/build_ipykernel_bundle.py
"""
import os, shutil, subprocess, sys, tempfile, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "ipykernel-py312-win64"
BAT = os.path.join(ROOT, "tools", "ipykernel_bundle", "install_ipykernel.bat")
OUT = os.path.join(ROOT, "installers", NAME + ".zip")

assert sys.version_info[:2] == (3, 12) and sys.platform == "win32", "Windows의 Python 3.12로 실행하세요: py -3.12"

with tempfile.TemporaryDirectory() as tmp:
    wheels = os.path.join(tmp, "wheels")
    subprocess.run([sys.executable, "-m", "pip", "download", "ipykernel", "--only-binary=:all:",
                    "--no-cache-dir", "--disable-pip-version-check", "-q", "-d", wheels], check=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(BAT, f"{NAME}/install_ipykernel.bat")
        for f in sorted(os.listdir(wheels)):
            z.write(os.path.join(wheels, f), f"{NAME}/wheels/{f}")
    print(f"만들었습니다: {OUT} (부품 {len(os.listdir(wheels))}개)")
