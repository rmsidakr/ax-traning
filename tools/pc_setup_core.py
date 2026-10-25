"""AX 실습 PC 환경 셋팅 점검 코드.

pc_setup.ipynb의 metadata["ax_setup_code"]에 그대로 넣어 배포한다(교육생에게 코드가 보이지 않게).
노트북 0단계 칸이 이 코드를 불러오고, 각 단계 칸은 step(번호) 한 줄만 실행한다.
고친 뒤에는 python tools/build_notebook.py 로 노트북에 다시 넣는다.
"""
import os, sys, json, shutil, subprocess, platform
from pathlib import Path

# ── 강사가 채울 값 ─────────────────────────────────────────
PRACTICE_DIR = Path.home() / "ax-training"               # 실습 폴더
SKILL_NAME = "[확인 필요: Skill 이름]"
SKILL_SOURCE = r"[확인 필요: Skill 배포 위치]"           # 배포받은 Skill 폴더 경로
SKILL_INSTALL_DIR = Path.home() / ".claude" / "skills"  # Skill 설치 위치
REQUIRED_PACKAGES = []                                   # [확인 필요: Skill에 필요한 Python 패키지] 예: ["requests"]
NEED_NODE = None                                         # [확인 필요: Node.js 필요 여부] True 또는 False
ENV_URL_NAME = "[확인 필요: Gateway 주소 변수명]"
ENV_URL = "[확인 필요: Gateway 주소]"
ENV_KEY_NAME = "[확인 필요: Virtual Key 변수명]"
# ─────────────────────────────────────────────────────────

STEP_ORDER = ["준비", "Python", "VS Code 확장", "Windows 11", "VS Code", "Claude Code", "Bedrock 설정", "Python 패키지",
              "Node.js", "실습 폴더", "Skill", ".env", "Gateway 연결", "Splunk 조회", "일정 조회"]
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


# 1단계: Python(3.8 이상)과 VS Code 확장(Python, Jupyter) 확인
def _step1():
    ok = sys.version_info >= (3, 8)
    show("Python", ok, f"Python {platform.python_version()} — 위치: {sys.executable}",
         "Python 3.8 이상이 필요합니다. 배포받은 Python 설치파일로 다시 설치한 뒤 VS Code를 재시작하세요.")

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


# 2단계: Windows 11 확인 (빌드 번호 22000 이상이면 Windows 11)
def _step2():
    build = sys.getwindowsversion().build if sys.platform == "win32" else 0
    show("Windows 11", build >= 22000,
         f"Windows 11 (빌드 {build})" if build >= 22000 else f"Windows 11이 아닙니다 (빌드 {build or '확인 불가'})",
         "사전 배포 기준과 다릅니다. 보조강사에게 알리고 다음 단계로 넘어가세요.")


# 3단계: VS Code 확인
def _step3():
    path = shutil.which("code")
    if path:
        ok, out = run([path, "--version"])
        show("VS Code", ok, f"VS Code {out.splitlines()[0] if ok and out else '버전 확인 실패'}",
             "VS Code를 완전히 닫았다가 다시 열고 0단계부터 다시 ▶를 누르세요.")
    else:
        show("VS Code", False, "VS Code 명령(code)을 찾지 못했습니다.",
             "VS Code를 완전히 닫았다가 다시 열고 0단계부터 다시 ▶를 누르세요. 그래도 ❌이면 보조강사를 불러 주세요.")


# 4단계: Claude Code 확인
def _step4():
    path = shutil.which("claude")
    fallback = Path.home() / ".local" / "bin" / "claude.exe"
    if path:
        ok, out = run([path, "--version"])
        show("Claude Code", ok, f"Claude Code {out.splitlines()[0] if ok and out else '버전 확인 실패'}",
             "보조강사를 불러 주세요.")
    elif fallback.exists():
        show("Claude Code", False, f"Claude Code는 있지만 PATH(명령을 찾는 경로)에 등록되지 않았습니다: {fallback}",
             "보조강사를 불러 주세요. [확인 필요: Claude Code 설치 방식]")
    else:
        show("Claude Code", False, "Claude Code를 찾지 못했습니다(사전 배포 누락).",
             "보조강사를 불러 주세요. [확인 필요: Claude Code 설치 방법]")


# 5단계: Bedrock 연결 설정 확인 (환경변수 → Claude Code 설정 파일 순서로 찾는다)
def _step5():
    # [확인 필요: Bedrock 연결 확인 방법] 사내 표준 방식에 맞게 조정
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
             "사내 설정 방식이 다를 수 있습니다. 8단계에서 Claude Code가 대답하면 정상입니다.")


# 6단계: Python 패키지 확인 → 없으면 설치 → 다시 확인
def _step6():
    from importlib import metadata

    def missing_packages():
        miss = []
        for name in REQUIRED_PACKAGES:
            try:
                metadata.version(name)
            except metadata.PackageNotFoundError:
                miss.append(name)
        return miss

    if not REQUIRED_PACKAGES:
        show("Python 패키지", None, "설치할 패키지 목록이 아직 정해지지 않았습니다.", "강사 안내를 기다리세요.")
    else:
        miss = missing_packages()
        if miss:
            print(f"설치 중: {', '.join(miss)} ...")
            ok, out = run([sys.executable, "-m", "pip", "install", *miss], timeout=600)
            if not ok:
                print(out[-1500:])
        miss = missing_packages()
        show("Python 패키지", not miss,
             f"모든 패키지 설치됨: {', '.join(REQUIRED_PACKAGES)}" if not miss else f"설치되지 않은 패키지: {', '.join(miss)}",
             "위 오류를 보조강사에게 보여 주세요. [확인 필요: 사내 pip 저장소/프록시]")


# 7단계: Node.js 확인 → 없으면 설치(winget) → 다시 확인
def _step7():
    def node_version():
        for p in (shutil.which("node"), r"C:\Program Files\nodejs\node.exe"):
            if p and Path(p).exists():
                ok, out = run([p, "--version"])
                if ok:
                    return out
        return None

    if NEED_NODE is None:
        show("Node.js", None, "Node.js가 필요한지 아직 정해지지 않았습니다.", "강사 안내를 기다리세요.")
    elif NEED_NODE is False:
        show("Node.js", True, "Node.js는 이번 실습에 필요 없습니다(건너뜀).")
    else:
        ver = node_version()
        if not ver:
            winget = shutil.which("winget")
            if winget:
                print("Node.js 설치 중 (몇 분 걸릴 수 있습니다) ...")
                ok, out = run([winget, "install", "--id", "OpenJS.NodeJS.LTS", "-e", "--silent",
                               "--accept-package-agreements", "--accept-source-agreements"], timeout=900)
                print(out[-1500:])
            else:
                print("winget(윈도우 설치 도구)을 찾지 못했습니다.")
            ver = node_version()
        show("Node.js", bool(ver), f"Node.js {ver}" if ver else "Node.js가 아직 없습니다.",
             "VS Code를 완전히 닫았다 다시 열고 0단계부터 다시 ▶를 누르세요. 그래도 ❌이면 보조강사를 불러 주세요.")


# 8단계: 실습 폴더 확인 (폴더는 위 안내대로 터미널에서 직접 만든다)
def _step8():
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


# 9단계: Skill 확인 → 없으면 설치(배포 폴더 복사) → 다시 확인
def _step9():
    if is_placeholder(SKILL_NAME):
        show("Skill", None, "Skill 이름이 아직 정해지지 않았습니다.", "강사 안내를 기다리세요.")
    else:
        target = SKILL_INSTALL_DIR / SKILL_NAME
        if not (target / "SKILL.md").exists():
            source = Path(SKILL_SOURCE)
            if not is_placeholder(SKILL_SOURCE) and (source / "SKILL.md").exists():
                print(f"설치 중: {source} → {target}")
                shutil.copytree(source, target, dirs_exist_ok=True)
                print("설치했습니다. Claude Code를 /exit 로 끄고 다시 claude 로 켜 주세요.")
            else:
                print(f"Skill 배포 위치를 찾지 못했습니다: {SKILL_SOURCE}")
        ok = (target / "SKILL.md").exists()
        show("Skill", ok, f"Skill 설치됨: {target}" if ok else "Skill이 설치되지 않았습니다.",
             "보조강사를 불러 주세요. [확인 필요: Skill 설치 방법]")


# 10단계: .env 만들기·확인 (키 자리를 비운 파일은 노트북이 만들고, 키는 사람이 직접 넣는다. 키 값은 출력하지 않는다)
#         Claude Code는 8단계 설정 때문에 .env를 읽지도 쓰지도 못한다
def _step10():
    env_path = PRACTICE_DIR / ".env"
    if is_placeholder(ENV_KEY_NAME) or is_placeholder(ENV_URL_NAME) or is_placeholder(ENV_URL):
        show(".env", None, ".env 변수 이름이 아직 정해지지 않았습니다.", "강사 안내를 기다리세요.")
        return
    if not PRACTICE_DIR.is_dir():
        show(".env", False, f"실습 폴더가 없습니다: {PRACTICE_DIR}", "8단계를 먼저 ✅로 만드세요.")
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


# 11단계: Gateway 주소까지 네트워크가 닿는지 확인 (응답 코드와 상관없이 응답이 오면 정상)
def _step11():
    import urllib.request, urllib.error
    url = "" if is_placeholder(ENV_URL_NAME) else read_env(PRACTICE_DIR / ".env").get(ENV_URL_NAME, "")
    if not url:
        show("Gateway 연결", None, "Gateway 주소가 없어 확인을 건너뜁니다.", "10단계를 먼저 ✅로 만드세요.")
    else:
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                show("Gateway 연결", True, f"Gateway에 연결됨 (응답 코드 {r.status})")
        except urllib.error.HTTPError as e:
            show("Gateway 연결", True, f"Gateway에 연결됨 (응답 코드 {e.code}: 주소까지는 정상적으로 닿았습니다)")
        except urllib.error.URLError as e:
            reason = str(e.reason)
            hint = ("사내 인증서(SSL) 문제일 수 있습니다. 보조강사를 불러 주세요." if "CERTIFICATE" in reason.upper()
                    else "주소 오타, 사내망 연결, 프록시 설정을 확인하세요. [확인 필요: 사내 프록시]")
            show("Gateway 연결", False, f"Gateway에 연결하지 못했습니다: {reason}", hint)
        except Exception as e:
            show("Gateway 연결", False, f"Gateway 확인 중 오류: {e}", "보조강사를 불러 주세요.")


# 12단계: Splunk 조회 결과 확인 (직접 보고 y/n 입력)
def _step12():
    answer = input("Claude Code가 Splunk 조회 결과(건수)를 보여 주었나요? (y/n): ").strip().lower()
    show("Splunk 조회", answer.startswith("y"), "Splunk 조회 성공" if answer.startswith("y") else "Splunk 조회 실패",
         "Claude Code 화면의 오류를 그대로 두고 보조강사를 불러 주세요.")


# 13단계: 일정 조회 결과 확인 (직접 보고 y/n 입력)
def _step13():
    answer = input("Claude Code가 오늘 내 일정(또는 '일정 없음')을 보여 주었나요? (y/n): ").strip().lower()
    show("일정 조회", answer.startswith("y"), "일정 조회 성공" if answer.startswith("y") else "일정 조회 실패",
         "Claude Code 화면의 오류를 그대로 두고 보조강사를 불러 주세요.")


# 14단계: 최종 점검표
def _step14():
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


def step(n):
    # 노트북의 각 단계 칸에서 부른다
    globals()[f"_step{n}"]()
