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
    .board {{
      display: grid;
      grid-template-columns: repeat(8, 1fr);
      gap: 2px;
      width: min(88vw, 480px);
      margin-top: 16px;
      border: 2px solid #334155;
    }}
    .sq {{
      aspect-ratio: 1 / 1;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: clamp(16px, 4vw, 30px);
      user-select: none;
    }}
    .light {{ background: #e5e7eb; color: #111827; }}
    .dark {{ background: #64748b; color: white; }}
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
      margin-top: 12px;
      color: #cbd5e1;
      line-height: 1.5;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>{GAME_NAME}</h1>
      <div>Web page opened from Telegram</div>

      <div class="board" id="board"></div>

      <a class="btn" href="{base_url}/play">Back to games</a>
      <a class="btn" href="{base_url}/">Bot home</a>

      <div class="note">
        This is a clean starter page for chess. You can later replace it with a full chess engine without changing the bot.
      </div>
    </div>
  </div>

  <script>
    const pieces = [
      "♜","♞","♝","♛","♚","♝","♞","♜",
      "♟","♟","♟","♟","♟","♟","♟","♟",
      "","","","","","","","",
      "","","","","","","","",
      "","","","","","","","",
      "","","","","","","","",
      "♙","♙","♙","♙","♙","♙","♙","♙",
      "♖","♘","♗","♕","♔","♗","♘","♖"
    ];

    const board = document.getElementById("board");

    for (let i = 0; i < 64; i++) {{
      const sq = document.createElement("div");
      sq.className = "sq " + (((Math.floor(i / 8) + i) % 2 === 0) ? "light" : "dark");
      sq.textContent = pieces[i];
      board.appendChild(sq);
    }}
  </script>
</body>
</html>
"""
