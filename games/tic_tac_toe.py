GAME_KEY = "tic_tac_toe"
GAME_NAME = "Tic Tac Toe"

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
      background: #0f172a;
      color: #e2e8f0;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 16px;
    }}
    .wrap {{
      width: min(92vw, 420px);
    }}
    .card {{
      background: #111827;
      border: 1px solid #334155;
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 14px 40px rgba(0,0,0,.25);
      text-align: center;
    }}
    .board {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-top: 16px;
    }}
    .cell {{
      aspect-ratio: 1 / 1;
      border: 0;
      border-radius: 16px;
      background: #1f2937;
      color: white;
      font-size: 42px;
      font-weight: 700;
      cursor: pointer;
    }}
    .cell:disabled {{
      opacity: 0.92;
      cursor: not-allowed;
    }}
    .meta {{
      display: flex;
      justify-content: space-between;
      gap: 8px;
      margin-top: 14px;
      font-size: 14px;
      color: #cbd5e1;
      flex-wrap: wrap;
    }}
    .btn {{
      display: inline-block;
      margin-top: 14px;
      padding: 12px 16px;
      border-radius: 12px;
      background: #2563eb;
      color: white;
      text-decoration: none;
      font-weight: 700;
      margin-right: 8px;
    }}
    .status {{
      margin-top: 10px;
      font-size: 16px;
      min-height: 24px;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>{GAME_NAME}</h1>
      <div>Local 2-player browser game</div>

      <div id="status" class="status">X starts</div>
      <div class="board" id="board"></div>

      <div class="meta">
        <div>Tap a square to play.</div>
        <div>Share the link with your friend.</div>
      </div>

      <a class="btn" href="{base_url}/play">Back to games</a>
      <a class="btn" href="{base_url}/">Bot home</a>
    </div>
  </div>

  <script>
    const boardEl = document.getElementById("board");
    const statusEl = document.getElementById("status");
    let board = Array(9).fill("");
    let current = "X";
    let winner = "";

    function winnerLine(b) {{
      const lines = [
        [0,1,2],[3,4,5],[6,7,8],
        [0,3,6],[1,4,7],[2,5,8],
        [0,4,8],[2,4,6]
      ];
      for (const [a, b1, c] of lines) {{
        if (b[a] && b[a] === b[b1] && b[a] === b[c]) return b[a];
      }}
      return "";
    }}

    function render() {{
      boardEl.innerHTML = "";
      for (let i = 0; i < 9; i++) {{
        const btn = document.createElement("button");
        btn.className = "cell";
        btn.textContent = board[i];
        btn.disabled = Boolean(board[i]) || Boolean(winner);
        btn.onclick = () => move(i);
        boardEl.appendChild(btn);
      }}

      if (winner) {{
        statusEl.textContent = `${{winner}} wins!`;
      }} else if (board.every(Boolean)) {{
        statusEl.textContent = "Draw!";
      }} else {{
        statusEl.textContent = `${{current}} turn`;
      }}
    }}

    function move(i) {{
      if (board[i] || winner) return;
      board[i] = current;

      const w = winnerLine(board);
      if (w) {{
        winner = w;
      }} else {{
        current = current === "X" ? "O" : "X";
      }}
      render();
    }}

    render();
  </script>
</body>
</html>
"""
