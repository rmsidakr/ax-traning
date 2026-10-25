"""tools/pc_setup_core.py를 pc_setup.ipynb에 넣는다.

- 점검 코드는 노트북 metadata["ax_setup_code"]에 들어가 교육생 화면에 보이지 않는다.
- 0단계 칸은 그 코드를 불러오고, 1~14단계 칸은 step(번호) 한 줄만 둔다.
사용법: python tools/build_notebook.py
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB = os.path.join(ROOT, "pc_setup.ipynb")
CORE = os.path.join(ROOT, "tools", "pc_setup_core.py")

LOADER = '''# 0단계: 점검 도구 불러오기 (코드는 읽지 않아도 됩니다)
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
    cell["source"] = lines(LOADER if n == 0 else f"step({n})")
    cell["metadata"] = {}
    cell["outputs"], cell["execution_count"] = [], None
    n += 1
assert n == 15, n

text = json.dumps(nb, ensure_ascii=False, indent=1) + "\n"
open(NB, "w", encoding="utf-8", newline="").write(text.replace("\n", "\r\n"))
print(f"노트북에 점검 코드를 넣었습니다: 단계 칸 {n}개")
