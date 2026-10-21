"""교안(ax_training.html)을 localhost로 띄우고, 파일이 바뀌면 브라우저를 자동 새로고침한다(스크롤 위치 유지).

사용법: python tools/live_server.py [포트]   → http://127.0.0.1:8765/
새로고침 스크립트는 응답에만 끼워 넣고, 원본 HTML 파일은 바꾸지 않는다.
"""
import http.server, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "ax_training.html"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

RELOAD = b"""<script>
(function(){
  try { var y = sessionStorage.getItem('ax_scroll'); if (y) { history.scrollRestoration='manual'; window.scrollTo(0, +y); } } catch(e){}
  var last = null;
  setInterval(function(){
    fetch('/__mtime', {cache:'no-store'}).then(function(r){return r.text();}).then(function(t){
      if (last === null) last = t;
      else if (t !== last) { try { sessionStorage.setItem('ax_scroll', window.scrollY); } catch(e){} location.reload(); }
    }).catch(function(){});
  }, 800);
})();
</script></body>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/__mtime':
            body, ctype = str(os.path.getmtime(os.path.join(ROOT, PAGE))).encode(), 'text/plain'
        elif path in ('/', '/' + PAGE):
            with open(os.path.join(ROOT, PAGE), 'rb') as f:
                body = f.read().replace(b'</body>', RELOAD, 1)
            ctype = 'text/html; charset=utf-8'
        else:
            return super().do_GET()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

print(f"http://127.0.0.1:{PORT}/ 에서 {PAGE}를 보여 줍니다. 끝내려면 Ctrl + C")
http.server.ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
