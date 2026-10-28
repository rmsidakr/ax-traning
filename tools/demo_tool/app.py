"""보안정책 개선 검토 도우미 (예시 화면 · 가상 값)

교안 2교시 '완성 모습'에 넣을 화면을 찍기 위한 예시 도구입니다.
실제 조회·분석·발송은 하지 않습니다.

- 127.0.0.1에서만 엽니다. 외부 네트워크와 키 파일은 쓰지 않습니다.
- GET  /           → index.html
- GET  /api/run    → 미리 넣어 둔 가상 결과(JSON)
- POST /api/send   → 가짜 성공(아무 데도 보내지 않음)

실행: python tools/demo_tool/app.py [--port 8766]   (리눅스는 python3)
"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOST = "127.0.0.1"

# 모든 값은 가상 값입니다. 요청·정책·KM 번호, 부서, 도메인(example.com), IP(192.0.2.x),
# 받는 사람의 Knox ID(ax.user01)·메일 주소(ax.user01@example.com)는 실제와 겹치지 않게 지었습니다.
# 실제 사람 이름·사번·연락처는 넣지 않았습니다.
DAILY_FROM = "9/28"
DAILY = [22, 25, 24, 27, 23, 12, 10, 23, 26, 28, 24, 25, 11, 9, 22,          # 9/28 ~ 10/12
         88, 104, 112, 109, 62, 58, 97, 106, 115, 110, 108, 63, 59, 96, 111]  # 10/13 ~ 10/27

DEMO_RESULT = {
    "demo": True,
    "flow_file": "prompts\\내 업무 흐름.md",
    "ran_at": "10/28 08:40",
    "flow": {
        "query": "접수 요청, 매칭 정책·근거, 유사 사례, 30일 차단 이력",
        "analyze": "정책 특정, 근거·유효성, 개선 필요성·가능 여부, 영향도 분석",
        "receive": "의사결정 회부 메일 보고서 초안 · 사내 메일로 나에게",
        "apply": "결정 메일이 오면 이어서 (지금은 실행하지 않음)",
    },
    "target": {"id": "REQ-2610-018", "team": "B팀", "note": "새 요청 1건"},
    # 이 도구가 쓰는 데이터 출처마다 AI Ready 준비 상태. state: ok(준비됨) · part(일부) · no(안 됨)
    # part·no인 출처에서 나온 결과는 화면에 '짐작 · 사람 확인'으로 표시하고 보고서에도 '사람 확인'으로 넣습니다.
    "readiness": [
        {"name": "개선 요청 접수함", "state": "ok", "why": "요청이 항목별로 나뉨"},
        {"name": "정책문서", "state": "ok", "why": "조항 번호(§4.2)로 찾음"},
        {"name": "KM 결정 이력·유사 사례", "state": "part", "why": "결정은 항목, 옛 사례는 본문에만"},
        {"name": "Splunk 차단 이력", "state": "ok", "why": "부서·서버·날짜로 바로 셈"},
        {"name": "정책 간 관계", "state": "no", "why": "연결 정보 없음 → AI가 짐작"},
    ],
    "readiness_note": [
        "이 화면이 되려면 데이터가 AI가 읽을 수 있게 준비돼 있어야 합니다.",
        "△·✗인 곳은 AI가 짐작하므로 사람이 확인합니다.",
    ],
    # 사용자의 10단계. group: run(①+②, [실행] 한 번) · receive(③) · apply(④)
    "stages": [
        {"no": 1, "label": "요청 접수", "group": "run", "uses": ["q"]},
        {"no": 2, "label": "정책 특정", "group": "run", "uses": ["a"]},
        {"no": 3, "label": "근거 확인", "group": "run", "uses": ["q", "a"]},
        {"no": 4, "label": "유효성 확인", "group": "run", "uses": ["a"]},
        {"no": 5, "label": "유사 사례", "group": "run", "uses": ["q", "a"]},
        {"no": 6, "label": "개선 필요성", "group": "run", "uses": ["q", "a"]},
        {"no": 7, "label": "개선 가능 여부", "group": "run", "uses": ["a"]},
        {"no": 8, "label": "영향도 분석", "group": "run", "uses": ["a"]},
        {"no": 9, "label": "의사결정 회부", "group": "receive", "sub": "나에게 초안"},
        {"no": 10, "label": "결정사항 적용", "group": "apply", "sub": "다음 단계"},
    ],
    "steps": [
        {"id": "query", "status": "done", "seconds": 6.2},
        {"id": "analyze", "status": "done", "seconds": 48},
        {"id": "receive", "status": "ready"},
        {"id": "apply", "status": "next"},
    ],
    "query": {
        "request": {
            "id": "REQ-2610-018",
            "received": "10/27 14:20 접수",
            "team": "B팀 (개발)",
            "title": "공개 패키지 저장소 접속이 막혀 야간 빌드가 실패합니다",
            "ask": "빌드 서버에서 공개 패키지 저장소 3곳에 접속하게 해 주세요",
            "source": [{"name": "개선 요청 접수함", "ready": "ok"}],
        },
        "policy": {
            "id": "POL-NET-031",
            "name": "외부 소프트웨어 저장소 직접 접속 차단",
            "clause": "§4.2",
            "doc": "정책문서 v3.2 (25년 3월 개정)",
            "basis_id": "KM-0412",
            "basis": "24년 3월 · 공급망 공격 대응으로 제정",
            "source": [{"name": "정책문서", "ready": "ok"}, {"name": "KM", "ready": "part"}],
        },
        "cases": [
            {"id": "KM-0388", "text": "C팀 컨테이너 이미지 저장소 접속", "result": "승인", "cond": "사내 미러 경유 조건", "when": "25년 6월"},
            {"id": "KM-0451", "text": "D팀 개인 PC에서 공개 저장소 직접 접속", "result": "반려", "cond": "단말 직접 접속은 예외 불가", "when": "26년 2월"},
        ],
        "cases_source": [{"name": "KM", "ready": "part"}],
        "blocks": {
            "source": [{"name": "Splunk", "ready": "ok"}],
            "total": 1709,
            "domains": 3,
            "servers": 12,
            "daily_from": DAILY_FROM,
            "daily": DAILY,
            "mark_index": 15,
            "mark_label": "10/13 야간 빌드 전환",
            "by_team": [
                {"team": "B팀", "count": 1268, "mine": True},
                {"team": "A팀", "count": 214},
                {"team": "C팀", "count": 151},
                {"team": "기타", "count": 76},
            ],
        },
    },
    "analysis": {
        "target": {
            "need": "빌드 서버 12대 → 공개 패키지 저장소 3곳 접속 허용",
            "match": "POL-NET-031 §4.2",
            "match_note": "외부 저장소 직접 접속 차단 · 일치",
            "related": "POL-DEV-012 §2",
            "related_note": "빌드 서버 외부 통신 제한",
            "related_guess": "no",  # 정책 간 관계 데이터가 없어 AI가 문서를 읽고 짐작
        },
        "verdicts": [
            {"step": 3, "label": "근거 확인", "badge": "확인됨", "kind": "good",
             "text": "정책문서 v3.2 §4.2 · KM-0412 결정 이력"},
            {"step": 4, "label": "유효성 확인", "badge": "유효", "kind": "good",
             "text": "공급망 공격 대응 목적은 타당 · 빌드 서버 예외 기준은 없음"},
            {"step": 6, "label": "개선 필요성", "badge": "높음", "kind": "warn",
             "text": "30일 차단 1,709건, 74%가 B팀 · 10/13부터 하루 93건"},
            {"step": 7, "label": "개선 가능 여부", "badge": "조건부 가능", "kind": "info",
             "text": "사내 미러 경유면 가능(KM-0388) · 직접 접속은 불가(KM-0451)",
             "check": {"ready": "part", "text": "옛 사례는 KM 본문에만 있음"}},
        ],
        "impact": {
            "tiles": [
                {"label": "충돌 정책", "value": "1", "unit": "건", "guess": "no"},  # 어느 정책인지는 아래 충돌 줄에
                {"label": "바꿀 설정", "value": "7", "unit": "건", "sub": "약 3일 작업"},
                {"label": "영향 사용자", "value": "46", "unit": "명", "sub": "B팀 개발자"},
            ],
            "rows": [
                {"where": "정책 조항", "what": "POL-NET-031 §4.2에 '사내 미러 경유' 예외 추가", "n": "1건"},
                {"where": "사내 미러", "what": "공개 저장소 3곳 동기화 등록", "n": "3건"},
                {"where": "방화벽", "what": "빌드망 192.0.2.0/26 → 미러 192.0.2.80 443 허용", "n": "2건"},
                {"where": "프록시", "what": "허용 목록에 mirror.example.com 추가", "n": "1건"},
            ],
            "conflict": "직접 허용하면 POL-DEV-012 §2와 충돌 · 사내 미러 경유면 충돌 없음",
            "conflict_guess": "짐작 · 사람 확인",
            "conflict_why": "정책 간 관계 데이터가 없어 AI가 두 문서를 읽고 판단",
        },
        "summary": [
            {"text": "직접 허용 대신 사내 미러 경유 예외 권고 · 바꿀 설정 7건 · 영향 46명"},
            {"text": "✗ 정책 충돌 · △ 옛 유사 사례는 데이터가 덜 준비돼 짐작입니다", "guess": True},
        ],
    },
    "draft": {
        "channel": "사내 메일",
        "to": "나",
        # 받는 사람은 '나' 한 명으로 고정. Knox ID와 메일 주소는 가상 값(실제 계정 아님)
        "to_knox": "ax.user01",
        "to_mail": "ax.user01@example.com",
        "forward": "결재권자 전달은 내가 직접",  # 보내기 버튼 아래 안내 줄에 붙음
        "subject": "[의사결정 요청] POL-NET-031 사내 미러 경유 예외 추가 (REQ-2610-018)",
        "summary": [
            "B팀 빌드가 저장소 차단으로 30일간 1,709건 막힘",
            "현행 정책은 유효하나 빌드 서버 예외 기준이 없음",
            "사내 미러 경유 예외 권고 (설정 7건, 충돌은 사람 확인)",
        ],
        "basis": [
            "정책문서 v3.2 §4.2 · KM-0412 (24년 3월 결정)",
            "유사 사례 KM-0388 승인 · KM-0451 반려",
            "Splunk 차단 이력 30일 · 10/13부터 4배 넘게 늘어남",
        ],
        "recommend": "§4.2에 '사내 미러 경유' 예외 추가, 직접 접속은 계속 차단",
        "decide": "예외 추가 승인 여부 · 적용일(11/10 희망)",
        # 준비가 덜 된 데이터(△·✗)에서 나온 짐작 2곳. 보고서에 '사람 확인'으로 들어감
        "checks": [
            {"ready": "no", "text": "정책 충돌 여부"},
            {"ready": "part", "text": "옛 유사 사례"},
        ],
        "seen_label": "보고서와 “사람 확인” 2곳을 확인했습니다",
    },
    "apply": {
        "items": ["결정 메일 분석", "KM 히스토리 초안", "요청자 회신 초안"],
        "note": "KM 적재와 회신은 내가 확인한 뒤에",
    },
}


class Handler(BaseHTTPRequestHandler):
    server_version = "DemoTool/1.0"

    def _send(self, code, body, ctype):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            html = (HERE / "index.html").read_text(encoding="utf-8")
            self._send(200, html, "text/html; charset=utf-8")
        elif path == "/api/run":
            self._json(200, DEMO_RESULT)
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            length = max(0, int(self.headers.get("Content-Length") or 0))
        except ValueError:
            length = 0
        if length:
            self.rfile.read(min(length, 65536))  # 내용은 쓰지 않음
        if path == "/api/run":
            self._json(200, DEMO_RESULT)
        elif path == "/api/send":
            # 예시 화면이므로 실제로 보내지 않고 성공만 돌려줌
            d = DEMO_RESULT["draft"]
            self._json(200, {"ok": True, "demo": True, "to": d["to"], "to_knox": d["to_knox"],
                             "to_mail": d["to_mail"], "channel": d["channel"],
                             "message": "예시 화면이라 실제로 보내지 않았습니다."})
        else:
            self._json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print("[demo]", self.address_string(), fmt % args)


def main():
    ap = argparse.ArgumentParser(description="보안정책 개선 검토 도우미 (예시 화면 · 가상 값)")
    ap.add_argument("--port", type=int, default=8766)  # 8765는 tools/live_server.py가 씀
    args = ap.parse_args()
    httpd = ThreadingHTTPServer((HOST, args.port), Handler)
    print(f"열 주소: http://{HOST}:{args.port}/  (끄기: Ctrl+C)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
