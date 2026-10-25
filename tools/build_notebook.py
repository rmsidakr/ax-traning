"""tools/pc_setup_core.py를 pc_setup.ipynb에 넣는다.

- 점검 코드는 노트북 metadata["ax_setup_code"]에 들어가 교육생 화면에 보이지 않는다.
- 0단계 칸은 그 코드를 불러오고, 1~13단계 칸은 step(번호) 한 줄만 둔다.
사용법: python tools/build_notebook.py
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB = os.path.join(ROOT, "pc_setup.ipynb")
CORE = os.path.join(ROOT, "tools", "pc_setup_core.py")

# 단계 칸에 보일 설명(무엇을 확인하는지). 점검 코드는 pc_setup_core.py의 _step번호 함수
STEP_NOTES = {
    1: "Python이 3.12인지, VS Code에 Python·Jupyter 확장이 설치돼 있는지 확인합니다",
    2: "VS Code가 설치돼 있는지, 버전이 무엇인지 확인합니다",
    3: "Claude Code가 설치돼 있는지, 버전이 무엇인지 확인합니다",
    4: "Claude Code가 사내 AI(AWS Bedrock)를 쓰도록 설정돼 있는지 확인합니다",
    5: "실습에 필요한 Python 패키지가 있는지 확인하고, 없으면 설치합니다",
    6: "Node.js가 설치돼 있는지 확인하고, 없으면 설치합니다",
    7: "실습 폴더(ax-training)가 있는지 확인하고, Claude Code가 .env를 읽지 못하게 막는 설정을 만듭니다",
    8: "실습용 Skill이 설치돼 있는지 확인하고, 없으면 설치합니다",
    9: ".env가 없으면 키 자리를 비운 파일을 만들고, Virtual Key가 들어갔는지 확인합니다 (키 내용은 화면에 나오지 않습니다)",
    10: "내 PC에서 사내 Gateway 주소까지 연결되는지 확인합니다",
    11: "Claude Code에서 Splunk 조회가 됐는지 묻습니다 (위쪽 입력창에 y 또는 n)",
    12: "Claude Code에서 내 일정 조회가 됐는지 묻습니다 (위쪽 입력창에 y 또는 n)",
    13: "지금까지의 결과를 한 표로 모아 보여 줍니다",
}

LOADER = '''# 0단계: 점검 도구를 불러오고, 노트북이 실행되는지 확인합니다 (아래 코드는 읽지 않아도 됩니다)
import json
exec(json.load(open(globals().get("__vsc_ipynb_file__", "pc_setup.ipynb"), encoding="utf-8"))["metadata"]["ax_setup_code"])
step(0)'''

def lines(text):
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + [parts[-1]]

nb = json.load(open(NB, encoding="utf-8"))
core = open(CORE, encoding="utf-8").read()
compile(core, CORE, "exec")
nb["metadata"]["ax_setup_code"] = core

n = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    cell["source"] = lines(LOADER if n == 0 else f"# {n}단계: {STEP_NOTES[n]}\nstep({n})")
    cell["metadata"] = {}
    cell["outputs"], cell["execution_count"] = [], None
    n += 1
assert n == 14, n

text = json.dumps(nb, ensure_ascii=False, indent=1) + "\n"
open(NB, "w", encoding="utf-8", newline="").write(text.replace("\n", "\r\n"))
print(f"노트북에 점검 코드를 넣었습니다: 단계 칸 {n}개")
