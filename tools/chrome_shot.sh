#!/bin/sh
# 교안의 특정 위치를 Chrome 헤드리스로 캡처해 화면을 검증한다 (Git Bash에서 실행)
# 사용법: sh tools/chrome_shot.sh <요소 id> <출력 png 경로> [창 높이]
#   예) sh tools/chrome_shot.sh pre-install /tmp/b1.png 2300
# 요소 앞의 내용을 숨긴 사본을 만들어 그 요소가 맨 위에 오게 한다.
# (헤드리스 Chrome은 #앵커 스크롤 후 캡처가 비어 나오는 경우가 있어 이 방식을 쓴다)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ID="$1"; OUT="$2"; H="${3:-1080}"
CHROME="${CHROME:-/c/Program Files/Google/Chrome/Application/chrome.exe}"
TMP="$(mktemp -d)"
JS="<script>(function(){var n=document.getElementById('$ID');if(!n)return;while(n.tagName!=='MAIN'){var p=n.previousElementSibling;while(p){p.style.display='none';p=p.previousElementSibling;}n=n.parentElement;}})();</script></body>"
sed -e "s#</body>#$JS#" "$ROOT/ax_training.html" > "$TMP/shot.html"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$TMP/prof" \
  --window-size=1920,"$H" --screenshot="$OUT" "file:///$(cygpath -m "$TMP/shot.html" 2>/dev/null || echo "$TMP/shot.html")" 2>&1 | grep -v updater | tail -1
