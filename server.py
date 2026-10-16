#!/usr/bin/env python3
"""Mini Arcade 서버 — 정적 파일 + SQLite 리더보드 API (표준 라이브러리만 사용)

실행: python3 server.py
- http://127.0.0.1:8137/  정적 게임 파일 서빙
- POST /api/score         게임 결과 기록 {game, player, cpu, result, score}
- GET  /api/leaderboard   기록 조회 (?game=키 로 필터)
- GET  /api/stats         전체 통계
"""
import json
import os
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "arcade.db")
PORT = 8137

GAMES = {
    "battle", "connect4", "othello", "memory",
    "tictactoe", "rps", "reaction", "mole", "baseball",
}


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT NOT NULL,
                player TEXT NOT NULL,
                cpu TEXT NOT NULL,
                result TEXT NOT NULL CHECK(result IN ('win','lose','draw')),
                score INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    # ── 공통 ──
    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # 콘솔을 조용히 유지 (API 로그만 짧게)

    # ── GET ──
    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/leaderboard":
            qs = parse_qs(u.query)
            game = (qs.get("game") or [None])[0]
            if game and game not in GAMES:
                self._json({"error": "unknown game"}, 400)
                return
            with db() as conn:
                if game:
                    rows = conn.execute(
                        "SELECT * FROM scores WHERE game=? ORDER BY id DESC LIMIT 500",
                        (game,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM scores ORDER BY id DESC LIMIT 500"
                    ).fetchall()
            self._json([dict(r) for r in rows])
            return
        if u.path == "/api/stats":
            with db() as conn:
                total = conn.execute("SELECT COUNT(*) c FROM scores").fetchone()["c"]
                wins = conn.execute(
                    "SELECT COUNT(*) c FROM scores WHERE result='win'"
                ).fetchone()["c"]
                players = conn.execute(
                    "SELECT COUNT(DISTINCT player) c FROM scores"
                ).fetchone()["c"]
            self._json({"total": total, "wins": wins, "players": players})
            return
        super().do_GET()

    # ── POST ──
    def do_POST(self):
        if urlparse(self.path).path != "/api/score":
            self._json({"error": "not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json({"error": "invalid json"}, 400)
            return
        game = str(data.get("game", ""))[:32]
        player = str(data.get("player", "익명")).strip()[:24] or "익명"
        cpu = str(data.get("cpu", "?")).strip()[:32]
        result = str(data.get("result", "")).lower()
        try:
            score = int(data.get("score"))
        except (TypeError, ValueError):
            score = None
        if game not in GAMES or result not in ("win", "lose", "draw") or score is None:
            self._json({"error": "invalid payload"}, 400)
            return
        with db() as conn:
            cur = conn.execute(
                "INSERT INTO scores (game, player, cpu, result, score) VALUES (?,?,?,?,?)",
                (game, player, cpu, result, score),
            )
        self._json({"ok": True, "id": cur.lastrowid})


if __name__ == "__main__":
    init_db()
    print(f"Mini Arcade server on http://127.0.0.1:{PORT}/ (DB: {DB_PATH})")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
