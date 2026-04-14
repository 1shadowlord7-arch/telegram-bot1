GAME_KEY = "ludo"
GAME_NAME = "Ludo Mini"

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
      background: #111827;
      color: #e5e7eb;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      padding: 18px;
    }}
    .wrap {{
      width: min(96vw, 900px);
    }}
    .card {{
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 14px 40px rgba(0,0,0,.25);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 8px;
      margin-top: 16px;
    }}
    .cell {{
      aspect-ratio: 1 / 1;
      border-radius: 14px;
      background: #1e293b;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      min-height: 54px;
      position: relative;
      overflow: hidden;
    }}
    .chip {{
      font-size: 12px;
      background: rgba(255,255,255,.1);
      padding: 2px 6px;
      border-radius: 999px;
      margin: 2px;
      display: inline-block;
    }}
    .controls {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 14px;
      align-items: center;
    }}
    button, .btn {{
      padding: 12px 16px;
      border-radius: 12px;
      border: 0;
      background: #2563eb;
      color: white;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      display: inline-block;
    }}
    .secondary {{
      background: #334155;
    }}
    .status {{
      margin-top: 12px;
      font-size: 16px;
      color: #cbd5e1;
      min-height: 24px;
    }}
    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 12px;
      color: #cbd5e1;
      font-size: 14px;
    }}
    .dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      display: inline-block;
      margin-right: 6px;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>{GAME_NAME}</h1>
      <div>A simple browser race game inspired by Ludo</div>

      <div class="controls">
        <button onclick="rollDice()">Roll Dice</button>
        <button class="secondary" onclick="resetGame()">Reset</button>
        <a class="btn" href="{base_url}/play">Back to games</a>
        <a class="btn" href="{base_url}/">Bot home</a>
      </div>

      <div id="status" class="status">Red starts</div>
      <div id="dice" class="status">Dice: -</div>

      <div class="legend">
        <div><span class="dot" style="background:#ef4444"></span>Red</div>
        <div><span class="dot" style="background:#3b82f6"></span>Blue</div>
        <div><span class="dot" style="background:#22c55e"></span>Green</div>
        <div><span class="dot" style="background:#f59e0b"></span>Yellow</div>
      </div>

      <div id="grid" class="grid"></div>
    </div>
  </div>

  <script>
    const players = [
      {{ name: "Red", color: "#ef4444", pos: 0 }},
      {{ name: "Blue", color: "#3b82f6", pos: 0 }},
      {{ name: "Green", color: "#22c55e", pos: 0 }},
      {{ name: "Yellow", color: "#f59e0b", pos: 0 }},
    ];

    let turn = 0;
    let finished = false;

    const grid = document.getElementById("grid");
    const statusEl = document.getElementById("status");
    const diceEl = document.getElementById("dice");

    function render() {{
      grid.innerHTML = "";
      for (let i = 0; i <= 30; i++) {{
        const cell = document.createElement("div");
        cell.className = "cell";
        cell.textContent = i;

        const here = players.filter(p => p.pos === i);
        if (here.length) {{
          cell.innerHTML = here.map(p => `<span class="chip">${{p.name}}</span>`).join("");
        }}
        grid.appendChild(cell);
      }}
      statusEl.textContent = finished ? "Game finished." : `${{players[turn].name}} turn`;
    }}

    function rollDice() {{
      if (finished) return;
      const dice = Math.floor(Math.random() * 6) + 1;
      diceEl.textContent = "Dice: " + dice;

      const p = players[turn];
      p.pos = Math.min(30, p.pos + dice);

      if (p.pos >= 30) {{
        finished = true;
        statusEl.textContent = p.name + " wins!";
      }} else {{
        turn = (turn + 1) % players.length;
      }}

      render();
    }}

    function resetGame() {{
      players.forEach(p => p.pos = 0);
      turn = 0;
      finished = false;
      diceEl.textContent = "Dice: -";
      render();
    }}

    render();
  </script>
</body>
</html>
"""
