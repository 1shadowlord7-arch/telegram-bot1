GAME_KEY = "chess"
GAME_NAME = "Chess"

def render_page(base_url: str) -> str:
    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{GAME_NAME}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
  <style>
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      background: #0b1220;
      color: #e5e7eb;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      padding: 18px;
    }}
    .wrap {{
      width: min(96vw, 840px);
    }}
    .card {{
      background: #111827;
      border: 1px solid #334155;
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 14px 40px rgba(0,0,0,.25);
    }}
    #board {{
      width: min(88vw, 420px);
      margin-top: 14px;
    }}
    .top {{
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
    }}
    .status {{
      margin-top: 12px;
      font-size: 16px;
      color: #cbd5e1;
    }}
    .btn {{
      display: inline-block;
      margin-top: 14px;
      margin-right: 8px;
      padding: 12px 16px;
      border-radius: 12px;
      background: #2563eb;
      color: white;
      text-decoration: none;
      font-weight: 700;
    }}
    .note {{
      margin-top: 10px;
      font-size: 14px;
      color: #94a3b8;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="top">
        <div>
          <h1>{GAME_NAME}</h1>
          <div>Browser-based 2-player chess</div>
        </div>
        <div id="status" class="status">Loading...</div>
      </div>

      <div id="board"></div>

      <a class="btn" href="{base_url}/play">Back to games</a>
      <a class="btn" href="{base_url}/">Bot home</a>
      <a class="btn" href="https://t.me/share/url?url={base_url}/game/chess&text=Play%20Chess%20with%20me">Share link</a>

      <div class="note">
        Works best on a phone or desktop browser. This page is separate from the Telegram bot and opens through the game button.
      </div>
    </div>
  </div>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.13.4/chess.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
  <script>
    const game = new Chess();
    const statusEl = document.getElementById("status");

    function updateStatus() {{
      let status = "";
      const turn = game.turn() === "w" ? "White" : "Black";

      if (game.in_checkmate()) {{
        status = "Game over, " + turn + " is checkmated.";
      }} else if (game.in_draw()) {{
        status = "Game over, draw.";
      }} else {{
        status = turn + " to move";
        if (game.in_check()) status += ", check!";
      }}

      statusEl.textContent = status;
    }}

    function onDragStart(source, piece) {{
      if (game.game_over()) return false;
      if (game.turn() === "w" && piece.startsWith("b")) return false;
      if (game.turn() === "b" && piece.startsWith("w")) return false;
    }}

    function onDrop(source, target) {{
      const move = game.move({{ from: source, to: target, promotion: "q" }});
      if (move === null) return "snapback";
      updateStatus();
    }}

    function onSnapEnd() {{
      board.position(game.fen());
    }}

    const board = Chessboard("board", {{
      draggable: true,
      position: "start",
      onDragStart,
      onDrop,
      onSnapEnd,
      pieceTheme: "https://chessboardjs.com/img/chesspieces/wikipedia/{{piece}}.png"
    }});

    updateStatus();
  </script>
</body>
</html>
"""
