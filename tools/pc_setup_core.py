"""AX 실습 PC 환경 셋팅 점검 코드.

pc_setup.ipynb의 metadata["ax_setup_code"]에 그대로 넣어 배포한다(교육생에게 코드가 보이지 않게).
노트북 0단계 칸이 이 코드를 불러오고, 각 단계 칸은 step(번호) 한 줄만 실행한다.
고친 뒤에는 python tools/build_notebook.py 로 노트북에 다시 넣는다.
"""
import os, sys, json, shutil, subprocess, platform
from pathlib import Path

# ── 강사가 채울 값 ─────────────────────────────────────────
PRACTICE_DIR = Path.home() / "ax-training"               # 실습 폴더
SKILL_NAME = "ai-gateway-skills"
SKILL_SOURCE = r"[확인 필요: Skill 배포 위치]"           # 배포받은 Skill 폴더 경로
SKILL_INSTALL_DIR = Path.home() / ".claude" / "skills"  # Skill 설치 위치
PY_EXE = "python-3.12.10-amd64.exe"                      # 메일로 배포하는 Python 3.12 설치파일
PY_EXE_SHA256 = "67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb"
PY_EXE_URL = "https://www.python.org/ftp/python/3.12.10/" + PY_EXE
NEED_NODE = True                                         # 실습에 Node.js가 필요함
NODE_MSI = "node-v24.22.1-x64.msi"                       # 메일로 배포하는 Node.js 설치파일
NODE_MSI_SHA256 = "3bda4baf1ee709b33cf920dd633106ddb23951e322bff9c03ec9f64ab8981b01"
NODE_MSI_URL = "https://nodejs.org/dist/v24.22.1/" + NODE_MSI
ENV_URL_NAME = "LITELLM_BASE_URL"
ENV_URL = "https://gateway.security.samsungds.net"
ENV_KEY_NAME = "LITELLM_API_KEY"
# ─────────────────────────────────────────────────────────

STEP_ORDER = ["준비", "Python", "VS Code 확장", "Python 3.12", "VS Code", "Claude Code", "Bedrock 설정",
              "Node.js", "실습 폴더", "Skill", ".env"]
MARK = {True: "✅", False: "❌", None: "⚠️"}
RESULTS = globals().get("RESULTS", {})

def show(step, ok, msg, hint=""):
    # 결과를 ✅/❌/⚠️ 로 보여주고 마지막 요약용으로 기록한다
    print(f"{MARK[ok]} {msg}")
    if hint and ok is not True:
        print(f"   👉 {hint}")
    RESULTS[step] = (ok, msg)

def run(cmd, timeout=60):
    # 명령을 실행하고 (성공 여부, 출력 내용)을 돌려준다
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
        return p.returncode == 0, ((p.stdout or "") + (p.stderr or "")).strip()
    except FileNotFoundError:
        return False, "명령을 찾을 수 없음"
    except subprocess.TimeoutExpired:
        return False, "시간 초과"

def find_installer(name, sha256, url):
    # 메일로 받은 설치파일을 다운로드·바탕화면·노트북 폴더에서 찾고, 없으면 공식 사이트에서 받는다.
    # 어느 쪽이든 SHA-256 지문이 배포 파일과 같을 때만 돌려준다
    import hashlib, tempfile, urllib.request

    def same_file(path):
        return hashlib.sha256(path.read_bytes()).hexdigest() == sha256

    notebook_dir = Path(globals().get("__vsc_ipynb_file__", "pc_setup.ipynb")).resolve().parent
    for folder in (Path.home() / "Downloads", Path.home() / "Desktop", notebook_dir):
        path = folder / name
        if path.exists() and same_file(path):
            return path
    print(f"받은 설치파일({name})을 찾지 못해 공식 사이트에서 받습니다 ...")
    path = Path(tempfile.gettempdir()) / name
    try:
        urllib.request.urlretrieve(url, path)
    except Exception as e:
        print(f"   받지 못했습니다: {e}")
        return None
    return path if same_file(path) else None

def is_placeholder(value):
    return isinstance(value, str) and value.startswith("[확인 필요")

def read_env(path):
    # .env 파일을 읽어 {변수명: 값} 으로 돌려준다 (값은 화면에 출력하지 않는다)
    values = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip().strip('"').strip("'")
    return values


def _step0():
    show("준비", True, f"준비 완료 (Python {platform.python_version()})")


# 1단계: Python(버전 무관)과 VS Code 확장(Python, Jupyter) 확인
#        → Python 3.12가 없으면 설치하고, 3.12를 기본 Python으로 설정한다(관리자 권한 없이 이 사용자에게만)
def _step1():
    import configparser, ctypes, winreg
    show("Python", True, f"Python {platform.python_version()} — 위치: {sys.executable}")

    NEED_EXTENSIONS = {"ms-python.python": "Python", "ms-toolsai.jupyter": "Jupyter"}

    def installed_extensions():
        # VS Code 확장 목록 {확장 id: 버전}. code 명령으로 먼저 보고, 없으면 확장 폴더의 목록 파일을 읽는다
        code_path = shutil.which("code")
        if code_path:
            ok, out = run([code_path, "--list-extensions", "--show-versions"])
            if ok:
                return dict(line.strip().lower().split("@", 1) for line in out.splitlines() if "@" in line)
        ext_file = Path.home() / ".vscode" / "extensions" / "extensions.json"
        try:
            return {e["identifier"]["id"].lower(): e.get("version", "?") for e in json.loads(ext_file.read_text(encoding="utf-8"))}
        except Exception:
            return None

    installed = installed_extensions()
    if installed is None:
        show("VS Code 확장", False, "VS Code 확장 목록을 확인하지 못했습니다.",
             "VS Code를 완전히 닫았다가 다시 열고 0단계부터 다시 ▶를 누르세요. 그래도 ❌이면 보조강사를 불러 주세요.")
    else:
        found = [f"{name} {installed[ext_id]}" for ext_id, name in NEED_EXTENSIONS.items() if ext_id in installed]
        missing = [name for ext_id, name in NEED_EXTENSIONS.items() if ext_id not in installed]
        show("VS Code 확장", not missing,
             f"VS Code 확장 확인: {', '.join(found)}" if not missing else f"VS Code 확장이 빠졌습니다: {', '.join(missing)}",
             "VS Code 왼쪽 확장 아이콘(Ctrl + Shift + X)에서 Microsoft의 확장을 설치하고 이 칸의 ▶를 다시 누르세요.")

    def find_py312():
        for p in (Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python" / "Python312" / "python.exe",
                  Path(r"C:\Program Files\Python312\python.exe")):
            if p.exists():
                ok, out = run([str(p), "--version"])
                if ok and out.startswith("Python 3.12"):
                    return p, out.split()[1]
        return None, None

    def same_dir(a, b):
        return os.path.normcase(os.path.expandvars(str(a)).rstrip("\\")) == os.path.normcase(str(b).rstrip("\\"))

    def set_default(exe):
        # 기본 Python = ① 사용자 PATH 맨 앞 ② py 명령의 기본값(py.ini) ③ VS Code의 기본 Python. 바꾼 게 있으면 True
        changed = False
        first = [str(exe.parent / "Scripts") + "\\", str(exe.parent) + "\\"]
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as k:
            try:
                old, kind = winreg.QueryValueEx(k, "Path")
            except FileNotFoundError:
                old, kind = "", winreg.REG_EXPAND_SZ
            parts = [x for x in old.split(";") if x]
            if not (len(parts) >= 2 and same_dir(parts[0], first[0]) and same_dir(parts[1], first[1])):
                rest = [x for x in parts if not any(same_dir(x, f) for f in first)]
                winreg.SetValueEx(k, "Path", 0, kind, ";".join(first + rest))
                ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, None)
                changed = True

        ini_path = Path(os.environ["LOCALAPPDATA"]) / "py.ini"
        ini = configparser.ConfigParser()
        ini.read(ini_path, encoding="utf-8")
        if ini.get("defaults", "python", fallback="") != "3.12":
            if not ini.has_section("defaults"):
                ini.add_section("defaults")
            ini.set("defaults", "python", "3.12")
            with open(ini_path, "w", encoding="utf-8") as f:
                ini.write(f)
            changed = True

        vs_path = Path(os.environ["APPDATA"]) / "Code" / "User" / "settings.json"
        try:
            vs = json.loads(vs_path.read_text(encoding="utf-8-sig")) if vs_path.exists() else {}
            if vs.get("python.defaultInterpreterPath") != str(exe):
                vs["python.defaultInterpreterPath"] = str(exe)
                vs_path.parent.mkdir(parents=True, exist_ok=True)
                vs_path.write_text(json.dumps(vs, ensure_ascii=False, indent=4), encoding="utf-8")
                changed = True
        except ValueError:   # 주석 등이 있어 읽지 못하면 VS Code 설정은 건드리지 않는다
            print("   (VS Code 설정 파일을 읽지 못해 VS Code의 기본 Python은 바꾸지 않았습니다)")
        return changed

    def path_python():
        # 새로 여는 터미널에서 python 명령이 가리킬 파일 (시스템 PATH → 사용자 PATH 순서)
        dirs = []
        for root, sub in ((winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                          (winreg.HKEY_CURRENT_USER, "Environment")):
            try:
                with winreg.OpenKey(root, sub) as k:
                    dirs += winreg.QueryValueEx(k, "Path")[0].split(";")
            except OSError:
                pass
        for d in filter(None, dirs):
            p = Path(os.path.expandvars(d)) / "python.exe"
            if p.exists():
                return p
        return None

    exe, ver = find_py312()
    installer = None
    if not exe:
        installer = find_installer(PY_EXE, PY_EXE_SHA256, PY_EXE_URL)
        if installer:
            print(f"Python 3.12를 설치합니다: {installer}")
            print("👉 설치 창이 저절로 닫힐 때까지 1~2분 기다립니다.")
            run([str(installer), "/passive", "InstallAllUsers=0", "PrependPath=1", "Include_launcher=1",
                 "InstallLauncherAllUsers=0", "Include_test=0"], timeout=900)
            exe, ver = find_py312()
    if not exe:
        hint = ("같은 칸을 다시 ▶ 누르세요. 그래도 ❌이면 보조강사를 불러 주세요." if installer else
                f"메일로 받은 {PY_EXE}를 다운로드 폴더에 저장하고 같은 칸을 다시 ▶ 누르세요. 그래도 ❌이면 보조강사를 불러 주세요.")
        show("Python 3.12", False, "Python 3.12가 설치돼 있지 않습니다.", hint)
        return
    try:
        changed = set_default(exe)
    except Exception as e:
        show("Python 3.12", False, f"Python 3.12는 있지만 기본 Python으로 설정하지 못했습니다: {e}",
             "화면을 그대로 두고 보조강사를 불러 주세요.")
        return
    first = path_python()
    if first and not same_dir(first.parent, exe.parent):
        show("Python 3.12", False, f"Python 3.12는 있지만 다른 Python이 먼저 잡힙니다: {first}",
             "PC 전체 설정(시스템 PATH)이라 관리자 권한이 필요합니다. 보조강사를 불러 주세요.")
        return
    if installer or changed:
        print("👉 기본 Python을 3.12로 설정했습니다. 터미널이 알아보도록 VS Code를 완전히 닫았다 다시 열고 0단계부터 다시 ▶를 누르세요.")
    show("Python 3.12", True, f"기본 Python: Python {ver} — 위치: {exe}")


# 2단계: VS Code 확인
def _step2():
    path = shutil.which("code")
    if path:
        ok, out = run([path, "--version"])
        show("VS Code", ok, f"VS Code {out.splitlines()[0] if ok and out else '버전 확인 실패'}",
             "VS Code를 완전히 닫았다가 다시 열고 0단계부터 다시 ▶를 누르세요.")
    else:
        show("VS Code", False, "VS Code 명령(code)을 찾지 못했습니다.",
             "VS Code를 완전히 닫았다가 다시 열고 0단계부터 다시 ▶를 누르세요. 그래도 ❌이면 보조강사를 불러 주세요.")


# 3단계: Claude Code 확인
def _step3():
    path = shutil.which("claude")
    fallback = Path.home() / ".local" / "bin" / "claude.exe"
    if path:
        ok, out = run([path, "--version"])
        show("Claude Code", ok, f"Claude Code {out.splitlines()[0] if ok and out else '버전 확인 실패'}",
             "보조강사를 불러 주세요.")
    elif fallback.exists():
        show("Claude Code", False, f"Claude Code는 있지만 PATH(명령을 찾는 경로)에 등록되지 않았습니다: {fallback}",
             "보조강사를 불러 주세요.")
    else:
        show("Claude Code", False, "Claude Code를 찾지 못했습니다(사전 배포 누락).",
             "보조강사를 불러 주세요.")


# 4단계: Bedrock 연결 설정 확인 (환경변수 → Claude Code 설정 파일 순서로 찾는다)
def _step4():
    keys = ("CLAUDE_CODE_USE_BEDROCK", "AWS_REGION")
    found = {k: (os.environ[k], "환경변수") for k in keys if os.environ.get(k)}
    settings_file = Path.home() / ".claude" / "settings.json"
    try:
        settings_env = json.loads(settings_file.read_text(encoding="utf-8")).get("env", {}) if settings_file.exists() else {}
    except Exception:
        settings_env = {}
    for k in keys:
        if k not in found and settings_env.get(k):
            found[k] = (str(settings_env[k]), "settings.json")

    use, where = found.get("CLAUDE_CODE_USE_BEDROCK", ("", ""))
    if use.lower() in ("1", "true"):
        region = found.get("AWS_REGION", ("미확인", ""))[0]
        show("Bedrock 설정", True, f"Bedrock 사용 설정 확인 ({where}), 리전: {region}")
    else:
        show("Bedrock 설정", None, "이 방법으로는 Bedrock 설정을 찾지 못했습니다.",
             "사내 설정 방식이 다를 수 있습니다. 6단계에서 Claude Code가 대답하면 정상입니다.")


# 5단계: Node.js 확인 → 없으면 설치 → 다시 확인
#        설치파일은 find_installer로 찾는다(SHA-256 지문이 배포 파일과 같을 때만 설치).
def _step5():
    def node_version():
        for p in (shutil.which("node"), r"C:\Program Files\nodejs\node.exe"):
            if p and Path(p).exists():
                ok, out = run([p, "--version"])
                if ok:
                    return out
        return None

    if NEED_NODE is None:
        show("Node.js", None, "Node.js가 필요한지 아직 정해지지 않았습니다.", "강사 안내를 기다리세요.")
        return
    if NEED_NODE is False:
        show("Node.js", True, "Node.js는 이번 실습에 필요 없습니다(건너뜀).")
        return

    ver = node_version()
    msi = None
    if not ver:
        msi = find_installer(NODE_MSI, NODE_MSI_SHA256, NODE_MSI_URL)
        if msi:
            print(f"Node.js를 설치합니다: {msi}")
            print("👉 관리자 승인 창이 뜨면 '예'를 누르세요. 설치 창이 닫힐 때까지 1~2분 기다립니다.")
            ok, out = run(["msiexec", "/i", str(msi), "/passive", "/norestart"], timeout=900)
            ver = node_version()
            if ver:
                print("👉 Node.js를 새로 설치했습니다. 터미널이 알아보도록 VS Code를 완전히 닫았다 다시 열고 0단계부터 다시 ▶를 누르세요.")
            elif not ok:
                print("   설치가 끝나지 않았습니다. 관리자 승인 창에서 '아니요'를 눌렀거나, 이 PC에서 설치가 막혀 있을 수 있습니다.")
    if msi:   # 설치파일은 있었는데 설치가 안 됨 → 다시 ▶하고 승인 창에서 '예'
        hint = "같은 칸을 다시 ▶ → 관리자 승인 창에서 '예'를 누르세요. 그래도 ❌이면 보조강사를 불러 주세요."
    else:     # 설치파일을 찾지도 받지도 못함
        hint = (f"메일로 받은 {NODE_MSI}를 다운로드 폴더에 저장하고 같은 칸을 다시 ▶ 누르세요. "
                "그래도 ❌이면 보조강사를 불러 주세요.")
    show("Node.js", bool(ver), f"Node.js {ver}" if ver else "Node.js가 설치돼 있지 않습니다.", hint)


# 6단계: 실습 폴더 확인 (폴더는 위 안내대로 터미널에서 직접 만든다)
def _step6():
    #        + Claude Code가 .env(키 파일)를 읽지 못하게 실습 폴더 설정에 읽기 금지 규칙을 넣는다
    ENV_DENY = ["Read(./.env)", "Read(./.env.*)"]

    if not PRACTICE_DIR.is_dir():
        show("실습 폴더", False, f"실습 폴더가 없습니다: {PRACTICE_DIR}",
             "위 할 일 2번의 명령을 VS Code 터미널에 입력한 뒤 이 칸의 ▶를 다시 누르세요.")
    else:
        settings_path = PRACTICE_DIR / ".claude" / "settings.json"
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
            deny = settings.setdefault("permissions", {}).setdefault("deny", [])
            deny += [rule for rule in ENV_DENY if rule not in deny]
            settings_path.parent.mkdir(exist_ok=True)
            settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
            show("실습 폴더", True, f"실습 폴더 확인: {PRACTICE_DIR} (.env 읽기 금지 설정됨)")
        except Exception as e:
            show("실습 폴더", False, f"실습 폴더는 있지만 .env 읽기 금지 설정을 만들지 못했습니다: {e}",
                 "화면을 그대로 두고 보조강사를 불러 주세요.")


# 7단계 앞부분: Skill 확인 → 없으면 설치(배포 폴더 복사) → 다시 확인
def _skill():
    if is_placeholder(SKILL_NAME):
        show("Skill", None, "Skill 이름이 아직 정해지지 않았습니다.", "강사 안내를 기다리세요.")
    else:
        target = SKILL_INSTALL_DIR / SKILL_NAME
        if not (target / "SKILL.md").exists():
            source = Path(SKILL_SOURCE)
            if not is_placeholder(SKILL_SOURCE) and (source / "SKILL.md").exists():
                print(f"설치 중: {source} → {target}")
                shutil.copytree(source, target, dirs_exist_ok=True)
            else:
                print(f"Skill 배포 위치를 찾지 못했습니다: {SKILL_SOURCE}")
        ok = (target / "SKILL.md").exists()
        show("Skill", ok, f"Skill 설치됨: {target}" if ok else "Skill이 설치되지 않았습니다.",
             "보조강사를 불러 주세요. [확인 필요: Skill 설치 방법]")


# 7단계 뒷부분: .env 만들기·확인 (키 자리를 비운 파일은 노트북이 만들고, 키는 사람이 직접 넣는다. 키 값은 출력하지 않는다)
#         Claude Code는 6단계 설정 때문에 .env를 읽지 못한다
def _env():
    env_path = PRACTICE_DIR / ".env"
    if is_placeholder(ENV_KEY_NAME) or is_placeholder(ENV_URL_NAME) or is_placeholder(ENV_URL):
        show(".env", None, ".env 변수 이름이 아직 정해지지 않았습니다.", "강사 안내를 기다리세요.")
        return
    if not PRACTICE_DIR.is_dir():
        show(".env", False, f"실습 폴더가 없습니다: {PRACTICE_DIR}", "6단계를 먼저 ✅로 만드세요.")
        return
    if not env_path.exists():
        env_path.write_text(f"{ENV_URL_NAME}={ENV_URL}\n{ENV_KEY_NAME}=\n", encoding="utf-8")
        print("키 자리를 비워 둔 .env 파일을 만들었습니다.")
    env = read_env(env_path)
    url, key = env.get(ENV_URL_NAME, ""), env.get(ENV_KEY_NAME, "")
    if not url:
        show(".env", False, f".env에 Gateway 주소({ENV_URL_NAME})가 없습니다.", "보조강사를 불러 주세요.")
    elif not key or key.startswith("["):
        print(f"👉 아래 파란 경로를 Ctrl + 클릭해 .env를 열고, {ENV_KEY_NAME}= 바로 뒤에 Virtual Key를 붙여 넣고 Ctrl + S")
        print(f"   {env_path}")
        show(".env", False, "아직 Virtual Key가 비어 있습니다.", "키를 넣고 저장한 뒤 이 칸의 ▶를 다시 누르세요.")
    else:
        show(".env", True, f"Virtual Key 입력됨 (●●●● {len(key)}자) / Gateway 주소: {url}")


# 7단계: Skill 설치와 Virtual Key 연결 → 둘 다 ✅이면 Claude Code를 한 번 다시 켜게 한다(새 Skill 적용)
def _step7():
    _skill()
    _env()
    if RESULTS.get("Skill", (None,))[0] is True and RESULTS.get(".env", (None,))[0] is True:
        print("👉 Claude Code 화면에 /exit 를 입력해 끄고, claude 를 입력해 다시 켜세요. 새 Skill은 다시 켜야 적용됩니다.")


SPLUNK_PROMPT = "Splunk에서 최근 15분 동안 들어온 이벤트 건수만 알려줘. 조회만 하고 다른 작업은 하지 마."
CALENDAR_PROMPT = "오늘 내 일정 목록만 조회해서 보여줘. 등록, 수정, 삭제는 하지 마."

def copy_prompt(text):
    # 프롬프트를 클립보드에 넣는다(Windows clip, UTF-16). 실패하면 직접 입력하도록 문장만 보여 준다
    try:
        subprocess.run(["clip"], input=text.encode("utf-16-le"), check=True, timeout=10)
        print("📋 프롬프트를 복사했습니다. 아래 터미널의 Claude Code 입력창을 누르고 Ctrl + V → Enter")
    except Exception:
        print("👉 복사하지 못했습니다. 아래 문장을 Claude Code 입력창에 직접 입력하고 Enter")
    print(f"   {text}")


# 8단계: Splunk 조회 프롬프트 복사 (결과는 Claude Code 화면에서 확인)
def _step8():
    copy_prompt(SPLUNK_PROMPT)


# 9단계: 일정 조회 프롬프트 복사 (결과는 Claude Code 화면에서 확인)
def _step9():
    copy_prompt(CALENDAR_PROMPT)


# 10단계: 최종 점검표 (0~7단계. Splunk·일정 조회는 Claude Code 화면에서 확인한다)
def _step10():
    print("=== 셋팅 결과 요약 ===")
    count = {True: 0, False: 0, None: 0}
    for step in STEP_ORDER:
        if step in RESULTS:
            ok, msg = RESULTS[step]
            count[ok] += 1
            print(f"{MARK[ok]} {step}: {msg}")
        else:
            print(f"⬜ {step}: 아직 실행하지 않음")
    print()
    if count[False] == 0 and all(s in RESULTS for s in STEP_ORDER):
        print("🎉 셋팅 완료!" + (" (⚠️ 항목은 강사 안내를 따르세요)" if count[None] else ""))
    else:
        print("❌ 또는 ⬜ 항목의 단계로 돌아가 ▶를 다시 누르세요. 같은 ❌가 반복되면 보조강사를 불러 주세요.")
    print("Splunk·일정 조회(8·9단계)는 Claude Code 화면에 결과가 나왔으면 성공입니다.")


def step(n):
    # 노트북의 각 단계 칸에서 부른다
    globals()[f"_step{n}"]()
