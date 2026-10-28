"""AX 실습 PC 환경 셋팅 점검 코드.

pc_setup.ipynb의 metadata["ax_setup_code"]에 그대로 넣어 배포한다(교육생에게 코드가 보이지 않게).
노트북 0단계 칸이 이 코드를 불러오고, 각 단계 칸은 step(번호) 한 줄만 실행한다.
고친 뒤에는 python tools/build_notebook.py 로 노트북에 다시 넣는다.
"""
import os, sys, json, shutil, subprocess, platform
from pathlib import Path

# ── 강사가 채울 값 ─────────────────────────────────────────
PRACTICE_DIR = Path.home() / "ax-training"               # 실습 폴더
SKILL_BUNDLE = "ai-gateway-skills"                       # 배포 묶음(저장소) 이름
SKILL_ZIP_GLOB = "ai-gateway-skills*.zip"                # 메일로 받는 압축 파일 이름
SKILL_REPO_DIR = Path.home() / ".claude" / "ai-gateway-skills"   # 압축을 푸는 고정 위치(링크 대상이라 지우면 안 됨)
SKILL_NAME = "litellm-gateway"                           # 묶음 안에 들어 있는, 실제로 설치되는 Skill 이름
SKILL_INSTALL_DIR = Path.home() / ".claude" / "skills"  # Skill 설치 위치
PY_EXE = "python-3.12.10-amd64.exe"                      # 공식 사이트에서 받는 Python 3.12 설치파일
PY_EXE_SHA256 = "67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb"
PY_EXE_URL = "https://www.python.org/ftp/python/3.12.10/" + PY_EXE
NEED_NODE = True                                         # 실습에 Node.js가 필요함
NODE_MSI = "node-v24.22.1-x64.msi"                       # 공식 사이트에서 받는 Node.js 설치파일
NODE_MSI_SHA256 = "3bda4baf1ee709b33cf920dd633106ddb23951e322bff9c03ec9f64ab8981b01"
NODE_MSI_URL = "https://nodejs.org/dist/v24.22.1/" + NODE_MSI
KEY_FILE = Path.home() / ".claude" / "litellm-gateway.env"   # Skill이 키를 읽는 파일 (배포본 install.ps1이 만든다)
ENV_URL_NAME = "LITELLM_BASE_URL"
ENV_URL = "https://gateway.security.samsungds.net"
ENV_KEY_NAME = "LITELLM_API_KEY"
# ─────────────────────────────────────────────────────────

STEP_ORDER = ["준비", "Python", "VS Code 확장", "Python 3.12", "Claude Code", "사내 AI 연결",
              "Node.js", "실습 폴더", "Skill", "Virtual Key"]
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

def run_ps(script, timeout=60):
    # PowerShell 명령을 실행한다. 한글이 깨지지 않게 출력을 UTF-8로 맞추고, 그래도 깨지면 PC 기본 인코딩으로 읽는다
    import locale
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
           "[Console]::OutputEncoding=[Text.Encoding]::UTF8; " + script]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except FileNotFoundError:
        return False, "PowerShell을 찾을 수 없음"
    except subprocess.TimeoutExpired:
        return False, "시간 초과"
    raw = (p.stdout or b"") + (p.stderr or b"")
    try:
        out = raw.decode("utf-8")
    except UnicodeDecodeError:
        out = raw.decode(locale.getpreferredencoding(False), errors="replace")
    return p.returncode == 0, out.strip()

def find_installer(name, sha256, url):
    # 설치파일을 공식 사이트에서 받는다. 받지 못했을 때만 다운로드·바탕화면·노트북 폴더에 같은 파일이 있는지 본다.
    # 어느 쪽이든 SHA-256 지문이 확인한 버전과 같을 때만 돌려준다
    import hashlib, tempfile, urllib.request

    def same_file(path):
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest() == sha256
        except OSError:
            return False

    cached = Path(tempfile.gettempdir()) / name
    if cached.exists() and same_file(cached):   # 앞서 받아 둔 파일
        return cached
    print(f"공식 사이트에서 {name}을 받습니다 ... ({url})")
    try:
        urllib.request.urlretrieve(url, cached)
        if same_file(cached):
            return cached
        print("   받은 파일이 확인한 버전과 다릅니다. 받다가 끊겼을 수 있습니다.")
    except Exception as e:
        print(f"   받지 못했습니다: {e}")
    notebook_dir = Path(globals().get("__vsc_ipynb_file__", "pc_setup.ipynb")).resolve().parent
    for folder in (Path.home() / "Downloads", Path.home() / "Desktop", notebook_dir):
        path = folder / name
        if path.exists() and same_file(path):
            print(f"   대신 이미 가진 파일을 씁니다: {path}")
            return path
    return None

def read_env(path):
    # KEY=VALUE 형식 파일을 읽어 {변수명: 값} 으로 돌려준다 (값은 화면에 출력하지 않는다)
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
                "사내망 연결을 확인하고 같은 칸을 다시 ▶ 누르세요. 그래도 ❌이면 보조강사를 불러 주세요.")
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
    kernel = ensure_ipykernel(exe)
    if installer or changed:
        print("👉 기본 Python을 3.12로 설정했습니다. 터미널이 알아보도록 VS Code를 완전히 닫았다 다시 열고 0단계부터 다시 ▶를 누르세요.")
    show("Python 3.12", True, f"기본 Python: Python {ver} — 위치: {exe}"
         + ("" if kernel else " (노트북 커널 준비는 못 했습니다 — 커널을 3.12로 바꿀 때 VS Code 안내를 따르세요)"))


def ensure_ipykernel(exe):
    # 노트북을 3.12 커널로 열 수 있게 ipykernel을 넣어 둔다.
    # 사내 pip 저장소에는 ipykernel이 없어서 공식 PyPI를 지정해 받는다(그래서 --index-url을 쓴다).
    ok, _ = run([str(exe), "-c", "import ipykernel"], timeout=60)
    if ok:
        return True
    print("노트북 커널(ipykernel)을 공식 PyPI에서 받아 설치합니다 ...")
    base = [str(exe), "-m", "pip", "install", "--quiet", "--index-url", "https://pypi.org/simple", "ipykernel"]
    ok, out = run(base, timeout=600)
    if not ok:   # 관리자 권한이 필요한 위치에 깔린 Python이면 이 사용자에게만 설치한다
        ok, out = run(base + ["--user"], timeout=600)
    if not ok:
        for line in out.splitlines()[-3:]:
            if line.strip():
                print(f"   {line.strip()}")
    return run([str(exe), "-c", "import ipykernel"], timeout=60)[0]


# 2단계: Claude Code 확인
def _step2():
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


# 3단계: 사내 AI 연결 설정 확인. 사내 배포는 두 가지 방식이 쓰여서 둘 다 인정한다.
#        ① 사내 AI Gateway: ANTHROPIC_BASE_URL + 키를 공급하는 apiKeyHelper(GatewayCLI)
#        ② AWS Bedrock: CLAUDE_CODE_USE_BEDROCK=1
#        값은 환경변수 → Claude Code 설정 파일(~/.claude/settings.json) 순서로 찾는다. 키 값은 보지 않는다.
def _step3():
    settings_file = Path.home() / ".claude" / "settings.json"
    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8")) if settings_file.exists() else {}
    except Exception:
        settings = {}
    settings_env = settings.get("env", {}) if isinstance(settings.get("env"), dict) else {}

    def value(name):
        # (값, 어디서 찾았는지)
        if os.environ.get(name):
            return os.environ[name], "환경변수"
        if settings_env.get(name):
            return str(settings_env[name]), "settings.json"
        return "", ""

    base_url, base_where = value("ANTHROPIC_BASE_URL")
    use_bedrock, bedrock_where = value("CLAUDE_CODE_USE_BEDROCK")
    helper = str(settings.get("apiKeyHelper") or "").strip().strip('"')

    if base_url:
        host = base_url.split("//")[-1].split("/")[0]
        helper_ok = bool(helper) and Path(helper).exists()
        msg = f"사내 AI Gateway 연결 확인 ({base_where}): {host}"
        if helper:   # 키를 공급하는 프로그램까지 있으면 함께 확인
            msg += " / 키 공급 프로그램 " + ("확인" if helper_ok else "없음")
        show("사내 AI 연결", True if (not helper or helper_ok) else None, msg,
             "키 공급 프로그램이 설치돼 있지 않습니다. 5단계에서 Claude Code가 대답하면 정상입니다.")
    elif use_bedrock.lower() in ("1", "true"):
        region = value("AWS_REGION")[0] or "미확인"
        show("사내 AI 연결", True, f"AWS Bedrock 연결 확인 ({bedrock_where}), 리전: {region}")
    else:
        show("사내 AI 연결", None, "사내 AI 연결 설정을 찾지 못했습니다.",
             "사내 배포 방식이 다를 수 있습니다. 5단계에서 Claude Code가 대답하면 정상입니다.")


# 4단계: Node.js 확인 → 없으면 설치 → 다시 확인
#        설치파일은 find_installer로 공식 사이트에서 받는다(SHA-256 지문이 확인한 버전과 같을 때만 설치).
def _step4():
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
        hint = ("사내망 연결을 확인하고 같은 칸을 다시 ▶ 누르세요. "
                "그래도 ❌이면 보조강사를 불러 주세요.")
    show("Node.js", bool(ver), f"Node.js {ver}" if ver else "Node.js가 설치돼 있지 않습니다.", hint)


# 5단계: 실습 폴더 확인 (폴더는 위 안내대로 터미널에서 직접 만든다)
def _step5():
    #        + Claude Code가 키 파일을 읽지 못하게 실습 폴더 설정에 읽기 금지 규칙을 넣는다.
    #          키는 홈의 ~/.claude/litellm-gateway.env 에 들어가고(Skill이 읽는 파일), 실습 폴더의 .env 도 함께 막는다.
    #          규칙이 있으면 승인 창 없이 바로 막힌다(규칙이 없으면 승인 요청이 떠서 교육생이 승인할 수 있다)
    ENV_DENY = ["Read(~/.claude/litellm-gateway.env)", "Read(./.env)", "Read(./.env.*)"]

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
            show("실습 폴더", True, f"실습 폴더 확인: {PRACTICE_DIR} (키 파일 읽기 금지 설정됨)")
        except Exception as e:
            show("실습 폴더", False, f"실습 폴더는 있지만 키 파일 읽기 금지 설정을 만들지 못했습니다: {e}",
                 "화면을 그대로 두고 보조강사를 불러 주세요.")


# 6단계 앞부분: Skill 확인 → 없으면 배포 압축본(zip)을 찾아 고정 위치에 풀고 install.ps1 실행 → 다시 확인
def _skill():
    target = SKILL_INSTALL_DIR / SKILL_NAME
    if not (target / "SKILL.md").exists():
        repo = _skill_repo()
        if repo:
            _run_installer(repo)                      # 배포본 공식 설치 (링크 + 키 파일 자리)
            if not (target / "SKILL.md").exists():
                _copy_skills(repo)                    # 예비: 링크가 안 되면 복사해서 설치
    ok = (target / "SKILL.md").exists()
    show("Skill", ok, f"Skill 설치됨: {target}" if ok else f"Skill({SKILL_NAME})이 설치되지 않았습니다.",
         f"메일로 받은 {SKILL_BUNDLE} 압축 파일을 다운로드 폴더에 저장하고 이 칸의 ▶를 다시 누르세요. "
         "그래도 ❌이면 보조강사를 불러 주세요.")


def _installer_dir(root):
    # install.ps1 이 있는 폴더를 찾는다 (GitHub 압축본은 폴더가 한 겹 더 들어가 있다)
    if not root.is_dir():
        return None
    for path in [root] + sorted(p for p in root.iterdir() if p.is_dir()):
        if (path / "install.ps1").exists():
            return path
    return None


def _skill_repo():
    # 이미 풀어 둔 폴더가 있으면 그대로 쓰고, 없으면 배포 압축본을 찾아 고정 위치에 푼다.
    # (install.ps1 이 이 폴더를 링크 대상으로 삼으므로 지우거나 옮기면 Skill이 깨진다)
    repo = _installer_dir(SKILL_REPO_DIR)
    if repo:
        return repo
    zip_path = _find_skill_zip()
    if not zip_path:
        print(f"배포 압축 파일({SKILL_ZIP_GLOB})을 다운로드·바탕화면·노트북 폴더에서 찾지 못했습니다.")
        return None
    print(f"압축을 풉니다: {zip_path.name} → {SKILL_REPO_DIR}")
    try:
        import zipfile
        SKILL_REPO_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(SKILL_REPO_DIR)
    except Exception as e:
        print(f"   압축을 풀지 못했습니다: {e}")
        return None
    repo = _installer_dir(SKILL_REPO_DIR)
    if not repo:
        print(f"   압축 안에서 install.ps1 을 찾지 못했습니다: {SKILL_REPO_DIR}")
    return repo


def _find_skill_zip():
    # 메일로 받은 Skill 압축본을 다운로드·바탕화면·노트북 폴더에서 찾는다 (여러 개면 가장 최근 것)
    notebook_dir = Path(globals().get("__vsc_ipynb_file__", "pc_setup.ipynb")).resolve().parent
    found = []
    for folder in (Path.home() / "Downloads", Path.home() / "Desktop", notebook_dir):
        if folder.is_dir():
            found += [p for p in folder.glob(SKILL_ZIP_GLOB) if p.is_file()]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def _run_installer(repo):
    # 배포본의 설치 스크립트를 그대로 실행한다 (skills/* 를 ~/.claude/skills 에 링크하고 키 파일 자리를 만든다)
    print(f"설치 중: {repo / 'install.ps1'}")
    ok, out = run_ps(f"& '{repo / 'install.ps1'}'", timeout=180)
    for line in out.splitlines():
        if line.strip():
            print(f"   {line.strip()}")
    if not ok:
        print("   설치 스크립트가 끝나지 않았습니다. 노트북이 직접 설치해 봅니다.")


def _copy_skills(repo):
    # 예비 경로: 링크 설치가 안 되면 skills/* 를 ~/.claude/skills 로 복사한다
    src_root = repo / "skills"
    if not src_root.is_dir():
        print(f"   배포본에 skills 폴더가 없습니다: {src_root}")
        return
    for src in src_root.iterdir():
        if not (src / "SKILL.md").exists():
            continue
        dest = SKILL_INSTALL_DIR / src.name
        try:
            if dest.is_dir():
                shutil.rmtree(dest, ignore_errors=True)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dest, dirs_exist_ok=True)
            print(f"   복사해서 설치: {dest}")
        except Exception as e:
            print(f"   복사하지 못했습니다 ({dest}): {e}")


# 6단계 뒷부분: 키 파일 확인 (키 자리를 비운 파일은 설치 스크립트가 만들고, 키는 사람이 직접 넣는다. 키 값은 출력하지 않는다)
#         Skill은 이 파일에서만 키를 읽고, Claude Code는 5단계 설정 때문에 이 파일을 읽지 못한다
def _env():
    if not KEY_FILE.exists():
        try:
            KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
            KEY_FILE.write_text(f"# 본인 Virtual Key를 넣으세요 (이 파일은 Skill만 읽습니다)\n"
                                f"{ENV_KEY_NAME}=\n{ENV_URL_NAME}={ENV_URL}\n", encoding="utf-8")
            _lock_key_file()
            print("키 자리를 비워 둔 키 파일을 만들었습니다.")
        except Exception as e:
            show("Virtual Key", False, f"키 파일을 만들지 못했습니다: {e}", "보조강사를 불러 주세요.")
            return
    env = read_env(KEY_FILE)
    key, url = env.get(ENV_KEY_NAME, ""), env.get(ENV_URL_NAME, "")
    if not url:   # 주소가 빠져 있으면 채워 둔다 (Skill 기본값과 같은 주소)
        with KEY_FILE.open("a", encoding="utf-8") as f:
            f.write(f"{ENV_URL_NAME}={ENV_URL}\n")
        url = ENV_URL
    if not key or key.startswith("["):
        print(f"👉 아래 파란 경로를 Ctrl + 클릭해 키 파일을 열고, {ENV_KEY_NAME}= 바로 뒤에 Virtual Key를 붙여 넣고 Ctrl + S")
        print(f"   {KEY_FILE}")
        show("Virtual Key", False, "아직 Virtual Key가 비어 있습니다.", "키를 넣고 저장한 뒤 이 칸의 ▶를 다시 누르세요.")
    else:
        show("Virtual Key", True, f"Virtual Key 입력됨 (●●●● {len(key)}자) / Gateway 주소: {url}")


def _lock_key_file():
    # 배포본 install.ps1 과 같은 처리(chmod 600 에 해당) — 이 사용자만 키 파일을 열 수 있게 한다
    user = os.environ.get("USERNAME", "")
    if user:
        run(["icacls", str(KEY_FILE), "/inheritance:r", "/grant:r", f"{user}:(F)"])


# 6단계: Skill 설치와 Virtual Key 연결 → 둘 다 ✅이면 Claude Code를 한 번 다시 켜게 한다(새 Skill 적용)
def _step6():
    _skill()
    _env()
    if RESULTS.get("Skill", (None,))[0] is True and RESULTS.get("Virtual Key", (None,))[0] is True:
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


# 7단계: Splunk 조회 프롬프트 복사 (결과는 Claude Code 화면에서 확인)
def _step7():
    copy_prompt(SPLUNK_PROMPT)


# 8단계: 일정 조회 프롬프트 복사 (결과는 Claude Code 화면에서 확인)
def _step8():
    copy_prompt(CALENDAR_PROMPT)


# 9단계: 최종 점검표 (0~6단계. Splunk·일정 조회는 Claude Code 화면에서 확인한다)
def _step9():
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
        print("🎉 셋팅 완료!" + (" (⚠️ 항목은 5단계에서 Claude Code가 대답했으면 괜찮습니다)" if count[None] else ""))
    else:
        print("❌ 또는 ⬜ 항목의 단계로 돌아가 ▶를 다시 누르세요. 같은 ❌가 반복되면 보조강사를 불러 주세요.")
    print("Splunk·일정 조회(7·8단계)는 Claude Code 화면에 결과가 나왔으면 성공입니다.")


# 10단계: 교육 마무리 — 오늘 설치한 Skill과 키 파일을 지운다.
#         되돌릴 수 없으므로 한 번 ▶로 지울 목록만 보여 주고, 같은 칸을 다시 ▶ 눌렀을 때 지운다.
CLEANUP_LISTED = globals().get("CLEANUP_LISTED", False)


def _cleanup_items():
    # (설명, 경로, 링크인지) 목록. 있는 것만 돌려준다
    items = []
    skill = SKILL_INSTALL_DIR / SKILL_NAME
    if skill.exists() or skill.is_symlink():
        link = False
        try:
            link = bool(os.lstat(skill).st_file_attributes & 0x400)   # 링크(Junction)인지
        except OSError:
            pass
        items.append((f"Skill {'링크' if link else '폴더'}", skill, link))
    if SKILL_REPO_DIR.is_dir():
        items.append(("Skill 압축을 푼 폴더", SKILL_REPO_DIR, False))
    if KEY_FILE.exists():
        items.append(("Virtual Key 파일", KEY_FILE, False))
    practice_env = PRACTICE_DIR / ".env"
    if practice_env.exists():
        items.append(("실습 폴더의 .env", practice_env, False))
    return items


def _step10():
    global CLEANUP_LISTED
    items = _cleanup_items()
    if not items:
        show("마무리", True, "지울 것이 없습니다. 이미 정리됐습니다.")
        CLEANUP_LISTED = False
        return
    if not CLEANUP_LISTED:
        print("아래를 지웁니다. 되돌릴 수 없습니다.")
        for what, path, _ in items:
            print(f"   - {what}: {path}")
        print()
        print("👉 정말 지우려면 이 칸의 ▶를 한 번 더 누르세요. 그만두려면 다음 칸으로 넘어가면 됩니다.")
        CLEANUP_LISTED = True
        return

    failed = []
    for what, path, link in items:
        try:
            if link:
                os.rmdir(path)              # 링크만 지운다(가리키던 폴더는 건드리지 않는다)
            elif path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"🧹 지움 - {what}")
        except Exception as e:
            failed.append((what, e))
    CLEANUP_LISTED = False
    if failed:
        for what, e in failed:
            print(f"   {what}를 지우지 못했습니다: {e}")
        show("마무리", False, "일부를 지우지 못했습니다.",
             "VS Code와 Claude Code를 모두 닫고 이 칸의 ▶를 다시 누르세요. 그래도 남으면 보조강사를 불러 주세요.")
    else:
        show("마무리", True, "오늘 설치한 Skill과 Virtual Key를 지웠습니다.")
        print("실습 폴더와 저장한 프롬프트는 그대로 남아 있습니다. 다시 쓰려면 개인 Virtual Key를 받아 6단계를 다시 하면 됩니다.")


def step(n):
    # 노트북의 각 단계 칸에서 부른다
    globals()[f"_step{n}"]()
