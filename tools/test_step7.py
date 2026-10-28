"""7단계(Skill 설치·Virtual Key) 검증. 가짜 홈 폴더에서만 돌리므로 실제 ~/.claude 는 건드리지 않는다.

사용법: python tools/_test_step7.py <실제 배포 zip 경로>
"""
import os, shutil, sys, tempfile
from pathlib import Path

ZIP = Path(sys.argv[1])
ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "tools" / "pc_setup_core.py"


def fresh_home(with_zip=True):
    home = Path(tempfile.mkdtemp(prefix="ax_home_"))
    (home / "Downloads").mkdir()
    (home / "Desktop").mkdir()
    (home / "ax-training").mkdir()
    if with_zip:
        shutil.copy(ZIP, home / "Downloads" / ZIP.name)
    for k in ("USERPROFILE", "HOME", "HOMEPATH"):
        os.environ[k] = str(home)
    return home


def load():
    # 환경변수를 바꾼 뒤에 코드를 새로 실행해야 Path.home() 이 가짜 홈을 가리킨다
    ns = {"__name__": "ax_core"}
    exec(compile(CORE.read_text(encoding="utf-8"), str(CORE), "exec"), ns)
    return ns


def case(title):
    print("\n" + "=" * 70)
    print("■", title)
    print("=" * 70)


# ── 시험 1: zip 있음, 설치 안 됨 → 설치되고 키는 비어 있어야 함 ──
case("시험 1. 배포 zip만 있는 새 PC → 7단계 ▶")
home = fresh_home()
ns = load()
ns["step"](7)
key_file = home / ".claude" / "litellm-gateway.env"
skill = home / ".claude" / "skills" / "litellm-gateway"
print("\n[확인]")
print(" 키 파일 존재:", key_file.exists())
print(" 키 파일 내용:", repr(key_file.read_text(encoding="utf-8")) if key_file.exists() else "-")
print(" Skill 경로 존재:", skill.exists(), "/ SKILL.md:", (skill / "SKILL.md").exists())
print(" Skill이 링크(Junction)인가:", os.path.isdir(skill) and bool(os.lstat(skill).st_file_attributes & 0x400))
print(" 해제 위치 유지:", (home / ".claude" / "ai-gateway-skills").is_dir())

# ── 시험 2: 키를 넣고 다시 ▶ → ✅ 두 줄 ──
case("시험 2. 키를 넣고 같은 칸을 다시 ▶")
key_file.write_text(key_file.read_text(encoding="utf-8").replace(
    "LITELLM_API_KEY=", "LITELLM_API_KEY=sk-FAKE-TEST-ONLY-123456"), encoding="utf-8")
ns = load()
ns["step"](7)

# ── 시험 3: 이미 설치된 상태에서 다시 ▶ (압축 다시 풀지 않아야 함) ──
case("시험 3. 이미 설치된 PC에서 다시 ▶")
ns = load()
ns["step"](7)

# ── 시험 4: 6단계 읽기 금지 규칙 ──
case("시험 4. 6단계 → 실습 폴더 설정 파일")
ns = load()
ns["step"](6)
settings = home / "ax-training" / ".claude" / "settings.json"
print("\n[확인] settings.json:")
print(settings.read_text(encoding="utf-8"))

# ── 시험 5: zip 을 못 찾는 경우 ──
case("시험 5. 배포 zip 이 없는 PC → 7단계 ▶")
home2 = fresh_home(with_zip=False)
ns = load()
ns["step"](7)

# ── 시험 6: 10단계 요약 (라벨 바뀐 것 반영됐는지) ──
case("시험 6. 10단계 요약표")
ns["step"](10)

for h in (home, home2):
    shutil.rmtree(h, ignore_errors=True)
print("\n가짜 홈 폴더 정리 완료")
