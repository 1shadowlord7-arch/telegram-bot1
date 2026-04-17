import base64
import hashlib
import hmac
import json
import os
import re
import threading
import time
import uuid
from collections import defaultdict, deque
from html import escape
from urllib.parse import parse_qsl
from flask import Flask, abort, jsonify, redirect, render_template_string, request
import telebot
from telebot import types
import config
import db
import games
import profiles
db.init_db()
bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)
SPAM_CACHE = defaultdict(lambda: deque(maxlen=30))
BOT_USERNAME = config.BOT_USERNAME
# -------------------------
# auth helpers
# -------------------------
def sign_payload(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    b64 = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    sig = hmac.new(config.SECRET_KEY.encode(), b64.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{b64}.{sig}"
def verify_payload(token: str) -> dict | None:
    try:
        b64, sig = token.rsplit(".", 1)
        expect = hmac.new(config.SECRET_KEY.encode(), b64.encode(), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(sig, expect):
            return None
        raw = base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4))
        return json.loads(raw.decode())
    except Exception:
        return None
def verify_webapp_init_data(init_data: str) -> dict | None:
    if not init_data:
        return None
    try:
        data = dict(parse_qsl(init_data, keep_blank_values=True))
        hash_value = data.pop("hash", None)
        if not hash_value:
            return None
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
        secret_key = hmac.new(b"WebAppData", config.BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, hash_value):
            return None
        if "user" in data:
            data["user"] = json.loads(data["user"])
        return data
    except Exception:
        return None
def webapp_user():
    init_data = request.headers.get("X-Telegram-WebApp-InitData", "") or request.args.get("initData", "")
    data = verify_webapp_init_data(init_data)
    if not data or not isinstance(data.get("user"), dict):
        return None
    u = data["user"]
    user_id = int(u["id"])
    username = u.get("username") or ""
    full_name = (u.get("first_name") or "") + (" " + u.get("last_name") if u.get("last_name") else "")
    db.upsert_web_user(user_id, username, full_name)
    return {"user_id": user_id, "username": username, "full_name": full_name}
# -------------------------
# telegram helpers
# -------------------------
def fullname(user):
    return (user.first_name or "") + (" " + user.last_name if getattr(user, "last_name", None) else "")
def ensure_user(user):
    db.upsert_user(user)
def ensure_group(chat):
    db.upsert_group(chat.id, chat.title or chat.username or str(chat.id))
def is_chat_admin(chat_id: int, user_id: int) -> bool:
    try:
        cm = bot.get_chat_member(chat_id, user_id)
        return cm.status in ("administrator", "creator")
    except Exception:
        return False
def is_bot_admin(chat_id: int) -> bool:
    try:
        me = bot.get_me()
        cm = bot.get_chat_member(chat_id, me.id)
        return cm.status in ("administrator", "creator")
    except Exception:
        return False
def bot_username() -> str:
    return BOT_USERNAME or bot.get_me().username or "bot"
def profile_token(user_id: int) -> str:
    return f"https://t.me/{bot_username()}?start=friend_{user_id}"
def request_status_token(uid: int) -> str:
    return sign_payload({"scope": "status", "uid": uid})
def admin_token(uid: int, group_id: int) -> str:
    return sign_payload({"scope": "admin", "uid": uid, "group_id": group_id})
def game_token(game_type: str, game_id: str) -> str:
    return sign_payload({"scope": "game", "game_type": game_type, "game_id": game_id})
def player_row(user_id: int):
    row = db.get_user(user_id)
    if not row:
        return {"user_id": user_id, "full_name": f"User {user_id}", "username": "", "photo_file_id": ""}
    return row
def bot_file_url(file_id: str) -> str | None:
    if not file_id:
        return None
    try:
        f = bot.get_file(file_id)
        return f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{f.file_path}"
    except Exception:
        return None
def ensure_photo_cached(user_id: int):
    row = db.get_user(user_id)
    if row and row.get("photo_file_id"):
        return row["photo_file_id"]
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count:
            fid = photos.photos[0][-1].file_id
            db.set_user_photo(user_id, fid)
            return fid
    except Exception:
        pass
    return None
def user_photo_url(user_id: int):
    row = db.get_user(user_id) or {"user_id": user_id}
    fid = row.get("photo_file_id") or ensure_photo_cached(user_id)
    if fid:
        return bot_file_url(fid)
    return None
def user_card_html(user_id: int, label: str = ""):
    row = player_row(user_id)
    name = profiles.display_name(row)
    uname = row.get("username") or ""
    photo_url = user_photo_url(user_id)
    if photo_url:
        avatar = f'<img class="avatar" src="{escape(photo_url)}" alt="dp">'
    else:
        avatar = f'<div class="avatar fallback">{escape(profiles.initials(name))}</div>'
    friend_link = profile_token(user_id)
    return f"""
    <div class="usercard">
      {avatar}
      <div class="meta">
        <div class="name">{escape(label + name if label else name)}</div>
        <div class="uname">{escape('@' + uname) if uname else 'no username'}</div>
        <a class="friend" href="{escape(friend_link)}">Send friend request</a>
      </div>
    </div>
    """
def friend_state(viewer_id: int | None, target_id: int) -> str:
    if not viewer_id or viewer_id == target_id:
        return "self"
    if db.are_friends(viewer_id, target_id):
        return "friends"
    if db.friend_request_exists(viewer_id, target_id):
        return "pending"
    return "none"
# -------------------------
# keyboards
# -------------------------
def back_markup(callback: str):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Back", callback_data=callback))
    return kb
def menu_markup():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("➕️ add to group", url=f"https://t.me/{bot_username()}?startgroup=add"),
        types.InlineKeyboardButton("group settings", callback_data="menu:groups"),
    )
    kb.row(types.InlineKeyboardButton("🕹 play games", web_app=types.WebAppInfo(url=f"{config.BASE_URL}/games")))
    kb.row(types.InlineKeyboardButton("linked files", callback_data="menu:files"))
    kb.row(types.InlineKeyboardButton("Market", callback_data="menu:market"))
    kb.row(
        types.InlineKeyboardButton("owner", url=config.OWNER_URL),
        types.InlineKeyboardButton("join updates channel", url=config.UPDATES_CHANNEL_URL),
    )
    return kb
def group_settings_markup(chat_id: int):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("🔗 connect group and channel", callback_data=f"gs:connect:{chat_id}"),
        types.InlineKeyboardButton("⚙️ Request settings", callback_data=f"gs:req:{chat_id}"),
    )
    kb.row(
        types.InlineKeyboardButton("🧹 Basic word filter", callback_data=f"gs:filter:{chat_id}"),
        types.InlineKeyboardButton("⚠️ Warning", callback_data=f"gs:warn:{chat_id}"),
    )
    kb.row(
        types.InlineKeyboardButton("🛡️ Spam detection", callback_data=f"gs:spam:{chat_id}"),
        types.InlineKeyboardButton("📋 Admin request dashboard", callback_data=f"gs:dash:{chat_id}"),
    )
    kb.row(types.InlineKeyboardButton("⬅️ Back", callback_data="menu:back"))
    return kb
def request_limit_markup(chat_id: int):
    kb = types.InlineKeyboardMarkup(row_width=5)
    for n in [1, 2, 3, 5, 10]:
        kb.add(types.InlineKeyboardButton(str(n), callback_data=f"reqlimit:{chat_id}:{n}"))
    kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"gs:open:{chat_id}"))
    return kb
def warning_limit_markup(chat_id: int):
    kb = types.InlineKeyboardMarkup(row_width=3)
    for n in [1, 3, 5]:
        kb.add(types.InlineKeyboardButton(str(n), callback_data=f"warnlimit:{chat_id}:{n}"))
    kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"gs:open:{chat_id}"))
    return kb
def spam_markup(chat_id: int):
    kb = types.InlineKeyboardMarkup(row_width=4)
    kb.row(
        types.InlineKeyboardButton("✅ on", callback_data=f"spam:{chat_id}:on"),
        types.InlineKeyboardButton("❌ off", callback_data=f"spam:{chat_id}:off"),
    )
    kb.row(
        types.InlineKeyboardButton("3", callback_data=f"spamlimit:{chat_id}:3"),
        types.InlineKeyboardButton("5", callback_data=f"spamlimit:{chat_id}:5"),
        types.InlineKeyboardButton("7", callback_data=f"spamlimit:{chat_id}:7"),
        types.InlineKeyboardButton("10", callback_data=f"spamlimit:{chat_id}:10"),
    )
    kb.row(types.InlineKeyboardButton("⬅️ Back", callback_data=f"gs:open:{chat_id}"))
    return kb
def challenge_markup(challenge_id: str):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("❎ Tic Tac Toe", callback_data=f"ch:ttt:{challenge_id}"),
        types.InlineKeyboardButton("✊ Rock Paper Scissors", callback_data=f"ch:rps:{challenge_id}"),
    )
    kb.row(types.InlineKeyboardButton("✖️ Cancel", callback_data=f"ch:cancel:{challenge_id}"))
    return kb
def room_markup(game_type: str, game_id: str, player_ids: list[int]):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.row(types.InlineKeyboardButton("Open game room", web_app=types.WebAppInfo(url=f"{config.BASE_URL}/game/{game_token(game_type, game_id)}")))
    if len(player_ids) >= 2:
        kb.row(
            types.InlineKeyboardButton("Add challenger", url=profile_token(player_ids[0])),
            types.InlineKeyboardButton("Add opponent", url=profile_token(player_ids[1])),
        )
    return kb
def friend_action_markup(req_id: int):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("✅ Accept", callback_data=f"friend:accept:{req_id}"),
        types.InlineKeyboardButton("❌ Decline", callback_data=f"friend:decline:{req_id}"),
    )
    return kb
def friends_list_markup(friend_ids):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for fid in friend_ids[:100]:
        row = player_row(fid)
        name = profiles.display_name(row)
        kb.add(types.InlineKeyboardButton(f"Remove {name}", callback_data=f"friend:remove:{fid}"))
    return kb
def game_invite_markup(game_type: str, game_id: str):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎮 Open game room", web_app=types.WebAppInfo(url=f"{config.BASE_URL}/game/{game_token(game_type, game_id)}")))
    return kb
def send_game_invites(game_type: str, game_id: str, players: list[int]):
    url = f"{config.BASE_URL}/game/{game_token(game_type, game_id)}"
    title = games.game_title(game_type)
    for pid in players[:2]:
        try:
            bot.send_message(pid, f"🎮 <b>{escape(title)}</b> match is ready. Open the room below.", reply_markup=game_invite_markup(game_type, game_id))
        except Exception:
            try:
                bot.send_message(pid, f"🎮 {title} match is ready: {url}")
            except Exception:
                pass
def warning_event_text(user, count: int, limit: int, reason: str = ""):
    name = escape(user.first_name or user.username or str(user.id))
    lines = [
        "⚠️ <b>Warn Event</b>",
        f"• User: {name}",
        f"• User ID: {user.id}",
        f"• Count: {count}/{limit}",
    ]
    if reason:
        lines.append(f"• Reason: {escape(reason)}")
    return "\n".join(lines)
# -------------------------
# web ui templates
# -------------------------
def render_games_hub():
    return render_template_string("""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="https://telegram.org/js/telegram-web-app.js"></script>
      <style>
        body{font-family:Arial,sans-serif;background:#0f0f12;color:#fff;margin:0;padding:14px}
        .wrap{max-width:760px;margin:0 auto}
        .hero{background:#181821;border-radius:18px;padding:16px;margin-bottom:12px}
        .title{font-size:22px;font-weight:800;margin:0 0 6px 0}
        .sub{opacity:.75;font-size:13px;line-height:1.5}
        .panel{background:#1b1b22;padding:12px;border-radius:16px;margin-top:12px}
        .row{display:flex;gap:10px;flex-wrap:wrap}
        .btn{border:0;border-radius:12px;padding:12px 14px;background:#2f7cf6;color:#fff;font-weight:700;cursor:pointer;text-decoration:none;display:inline-block}
        .btn.secondary{background:#30313d}
        .friendrow{display:flex;gap:10px;align-items:center;justify-content:space-between;background:#1b1b22;padding:10px;border-radius:14px;margin-bottom:8px}
        .avatar{width:42px;height:42px;border-radius:50%;object-fit:cover;background:#2e2e3a;display:flex;align-items:center;justify-content:center;font-weight:700;flex:0 0 42px}
        .fallback{background:#2f3545}
        .small{font-size:13px;opacity:.78}
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <div class="title">Play games</div>
          <div class="sub">Open a challenge in a group, then the match will appear here as a Telegram Mini App.</div>
        </div>
        <div id="profile" class="panel">Loading profile...</div>
        <div class="panel">
          <div class="title" style="font-size:18px">Available games</div>
          <div class="row" style="margin-top:10px">
            <a class="btn" href="#" onclick="alert('Use /challenge @username in a group to start Tic Tac Toe.');return false;">Tic Tac Toe</a>
            <a class="btn secondary" href="#" onclick="alert('Use /challenge @username in a group to start Rock Paper Scissors.');return false;">Rock Paper Scissors</a>
          </div>
        </div>
        <div class="panel">
          <div class="title" style="font-size:18px">Friend list</div>
          <div id="friends" style="margin-top:10px">Loading friends...</div>
        </div>
      </div>
      <script>
        const tg = window.Telegram?.WebApp;
        if (tg) tg.ready();
        function initials(name){
          const parts = (name || '').trim().split(/\s+/).filter(Boolean);
          if (!parts.length) return '?';
          if (parts.length === 1) return parts[0][0].toUpperCase();
          return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        async function fetchJson(url, opts){
          const headers = (opts && opts.headers) ? opts.headers : {};
          if (tg?.initData) headers['X-Telegram-WebApp-InitData'] = tg.initData;
          const res = await fetch(url, {...opts, headers});
          return await res.json();
        }
        async function load(){
          const data = await fetchJson('/api/friends/list');
          const profile = document.getElementById('profile');
          if (data.viewer){
            const p = data.viewer;
            profile.innerHTML = `<b>You are signed in.</b><div class="small">${p.full_name || ''} ${p.username ? '@'+p.username : ''}</div>`;
          } else {
            profile.innerHTML = 'Open this inside Telegram to see your profile and friends.';
          }
          const friends = document.getElementById('friends');
          if (!data.friends || !data.friends.length){
            friends.innerHTML = '<div class="small">No friends yet.</div>';
            return;
          }
          friends.innerHTML = data.friends.map(f => `
            <div class="friendrow">
              <div style="display:flex;gap:10px;align-items:center">
                ${f.photo_url ? `<img class="avatar" src="${f.photo_url}" alt="dp">` : `<div class="avatar fallback">${initials(f.name)}</div>`}
                <div>
                  <div><b>${f.name}</b></div>
                  <div class="small">${f.username ? '@'+f.username : 'no username'}</div>
                </div>
              </div>
              <button class="btn secondary" onclick="removeFriend(${f.id})">Remove</button>
            </div>`).join('');
        }
        async function removeFriend(id){
          await fetchJson('/api/friends/remove', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({target_id:id})});
          load();
        }
        load();
      </script>
    </body>
    </html>
    """)
def render_game_page(game_type: str, game_id: str):
    token = game_token(game_type, game_id)
    title = games.game_title(game_type)
    html = """
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="https://telegram.org/js/telegram-web-app.js"></script>
      <style>
        body{{font-family:Arial,sans-serif;background:#0f0f12;color:#fff;margin:0;padding:14px}}
        .wrap{{max-width:760px;margin:0 auto}}
        .hero{{background:#181821;border-radius:18px;padding:16px;margin-bottom:12px}}
        .title{{font-size:22px;font-weight:800;margin:0 0 6px 0}}
        .sub{{opacity:.75;font-size:13px;line-height:1.5}}
        .usercard{{display:flex;gap:12px;align-items:center;background:#1b1b22;padding:12px;border-radius:16px;margin-bottom:12px}}
        .avatar{{width:64px;height:64px;border-radius:50%;object-fit:cover;background:#2e2e3a;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:22px;overflow:hidden;flex:0 0 64px}}
        .fallback{{background:#2f3545}}
        .meta .name{{font-size:17px;font-weight:700}}
        .meta .uname{{font-size:12px;opacity:.72;margin:4px 0}}
        .friend{{display:inline-block;margin-top:4px;text-decoration:none;background:#2f7cf6;color:white;padding:8px 10px;border-radius:10px}}
        .panel{{background:#1b1b22;padding:12px;border-radius:16px;margin-top:12px}}
        .row{{display:flex;gap:10px;flex-wrap:wrap}}
        .btn{{border:0;border-radius:12px;padding:12px 14px;background:#2f7cf6;color:#fff;font-weight:700;cursor:pointer}}
        .btn.secondary{{background:#30313d}}
        .btn.ghost{{background:#21222b}}
        .board{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}}
        .cell{{aspect-ratio:1;background:#22232d;border:0;border-radius:16px;color:#fff;font-size:32px;font-weight:800;cursor:pointer}}
        .cell:disabled{{opacity:.7;cursor:not-allowed}}
        .pill{{display:inline-block;padding:7px 10px;border-radius:999px;background:#262735;margin:0 8px 8px 0}}
        .small{{font-size:13px;opacity:.78}}
        .friends{{display:grid;gap:10px}}
        .friendrow{{display:flex;gap:10px;align-items:center;justify-content:space-between;background:#1b1b22;padding:10px;border-radius:14px}}
        .friendrow img,.friendrow .mini{{width:42px;height:42px;border-radius:50%;object-fit:cover;background:#2e2e3a;display:flex;align-items:center;justify-content:center;font-weight:700;flex:0 0 42px}}
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <div class="title">__TITLE__ Mini App</div>
          <div class="sub">Tap a move in the app, see both players with profile photos and names, and use the friend controls below the cards.</div>
        </div>
        <div id="app">
          <div class="panel">Loading game...</div>
        </div>
      </div>
      <script>
        const GAME_TYPE = __GAME_TYPE__;
        const GAME_TOKEN = __TOKEN__;
        const tg = window.Telegram?.WebApp;
        if (tg) tg.ready();
        function initials(name) {{
          const parts = (name || '').trim().split(/\s+/).filter(Boolean);
          if (!parts.length) return '?';
          if (parts.length === 1) return parts[0][0].toUpperCase();
          return (parts[0][0] + parts[1][0]).toUpperCase();
        }}
        function card(player, viewerId) {{
          const isMe = viewerId && player.id === viewerId;
          const friendBtn = !isMe ? `
            <div class="row" style="margin-top:6px">
              ${{player.friend_state === 'friends' ? `<button class="btn secondary" data-action="remove-friend" data-target="${{player.id}}">Remove friend</button>` : `<button class="btn" data-action="add-friend" data-target="${{player.id}}">Add friend</button>`}}
            </div>` : '';
          return `
            <div class="usercard">
              ${{player.photo_url ? `<img class="avatar" src="${{player.photo_url}}" alt="dp">` : `<div class="avatar fallback">${{initials(player.name)}}</div>`}}
              <div class="meta">
                <div class="name">${{player.label || ''}}${{player.name}}</div>
                <div class="uname">${{player.username ? '@' + player.username : 'no username'}}</div>
                <div class="small">${{isMe ? 'You' : (player.friend_state === 'friends' ? 'Already friends' : player.friend_state === 'pending' ? 'Request pending' : 'Not friends yet')}}</div>
                ${{friendBtn}}
              </div>
            </div>`;
        }}
        async function api(path, body) {{
          const headers = {{'Content-Type': 'application/json'}};
          if (tg?.initData) headers['X-Telegram-WebApp-InitData'] = tg.initData;
          const res = await fetch(path, {{method:'POST', headers, body: JSON.stringify(body || {{}})}});
          return await res.json();
        }}
        async function loadState() {{
          const headers = {{}};
          if (tg?.initData) headers['X-Telegram-WebApp-InitData'] = tg.initData;
          const res = await fetch(`/api/game/${{GAME_TOKEN}}/state`, {{headers}});
          const data = await res.json();
          render(data);
        }}
        function render(data) {{
          if (!data.ok) {{
            document.getElementById('app').innerHTML = `<div class="panel">${{data.error || 'Unable to load game.'}}</div>`;
            return;
          }}
          const g = data.game;
          const viewerId = data.viewer ? data.viewer.user_id : null;
          let html = '';
          html += `<div class="panel"><b>Game ID:</b> <span class="pill">${{g.game_id}}</span> <b>Status:</b> <span class="pill">${{g.status}}</span></div>`;
          html += `<div class="panel">${{g.players.map(p => card(p, viewerId)).join('')}}</div>`;
          if (g.type === 'ttt') {{
            html += `<div class="panel"><div class="small">Tap a square to play.</div><div class="board">`;
            for (let i = 0; i < 9; i++) {{
              const cell = g.board[i] || ' ';
              const disabled = g.ended || cell !== ' ';
              html += `<button class="cell" data-cell="${{i}}" ${{disabled ? 'disabled' : ''}}>${{cell === ' ' ? '·' : cell}}</button>`;
            }}
            html += `</div></div>`;
          }} else if (g.type === 'rps') {{
            html += `<div class="panel"><div class="small">Each player picks once. The result appears after both choose.</div><div class="row" style="margin-top:10px">`;
            for (const c of ['rock','paper','scissors']) {{
              html += `<button class="btn" data-choice="${{c}}">${{c[0].toUpperCase() + c.slice(1)}}</button>`;
            }}
            html += `</div><div style="margin-top:12px"><b>Choices:</b> ${{g.choices_text || 'Waiting'}}</div></div>`;
          }}
          html += `<div class="panel"><b>Friend list</b><div class="friends" style="margin-top:10px">`;
          if (data.friends && data.friends.length) {{
            for (const f of data.friends) {{
              html += `<div class="friendrow">`;
              html += `<div style="display:flex;gap:10px;align-items:center">${{f.photo_url ? `<img src="${{f.photo_url}}" alt="dp">` : `<div class="mini">${{initials(f.name)}}</div>`}}<div><div><b>${{f.name}}</b></div><div class="small">${{f.username ? '@'+f.username : 'no username'}}</div></div></div>`;
              html += `<button class="btn ghost" data-action="remove-friend" data-target="${{f.id}}">Remove</button>`;
              html += `</div>`;
            }}
          }} else {{
            html += `<div class="small">No friends yet.</div>`;
          }}
          html += `</div></div>`;
          document.getElementById('app').innerHTML = html;
          document.querySelectorAll('[data-cell]').forEach(btn => btn.addEventListener('click', onCell));
          document.querySelectorAll('[data-choice]').forEach(btn => btn.addEventListener('click', onChoice));
          document.querySelectorAll('[data-action]').forEach(btn => btn.addEventListener('click', onAction));
        }}
        async function onCell(ev) {{
          const cell = parseInt(ev.currentTarget.dataset.cell, 10);
          const data = await api(`/api/game/${{GAME_TOKEN}}/move`, {{cell}});
          render(data);
        }}
        async function onChoice(ev) {{
          const choice = ev.currentTarget.dataset.choice;
          const data = await api(`/api/game/${{GAME_TOKEN}}/move`, {{choice}});
          render(data);
        }}
        async function onAction(ev) {{
          const action = ev.currentTarget.dataset.action;
          const target = parseInt(ev.currentTarget.dataset.target, 10);
          const route = action === 'add-friend' ? '/api/friends/request' : '/api/friends/remove';
          const data = await api(route, {{target_id: target}});
          render(data.state || data);
        }}
        loadState();
      </script>
    </body>
    </html>
    """
    html = html.replace("__TITLE__", escape(title))
    html = html.replace("__GAME_TYPE__", json.dumps(game_type))
    html = html.replace("__TOKEN__", json.dumps(token))
    return render_template_string(html)
# -------------------------
# startup / commands
# -------------------------
@bot.message_handler(commands=["start"])
def cmd_start(message):
    ensure_user(message.from_user)
    db.mark_started(message.from_user.id)
    if message.chat.type != "private":
        if message.chat.type in ("group", "supergroup"):
            ensure_group(message.chat)
        bot.reply_to(message, "Open me in DM for the full menu.")
        return
    payload = message.text.split(maxsplit=1)
    if len(payload) > 1:
        arg = payload[1].strip()
        if arg.startswith("friend_"):
            target_id = int(arg.split("_", 1)[1])
            handle_friend_request_start(message, target_id)
            return
    bot.send_message(message.chat.id, "Main menu:", reply_markup=menu_markup())
def handle_friend_request_start(message, target_id: int):
    sender = message.from_user.id
    ensure_user(message.from_user)
    if sender == target_id:
        bot.send_message(message.chat.id, "You cannot add yourself.")
        return
    target = db.get_user(target_id)
    if not target:
        bot.send_message(message.chat.id, "That user is not in the bot database yet. They need to start the bot first.")
        return
    if db.are_friends(sender, target_id):
        bot.send_message(message.chat.id, "You are already friends.")
        return
    if db.friend_count(sender) >= 100:
        bot.send_message(message.chat.id, "You already have the maximum of 100 friends.")
        return
    if db.friend_request_exists(sender, target_id):
        bot.send_message(message.chat.id, "A friend request already exists.")
        return
    req_id = db.create_friend_request(sender, target_id)
    note = (
        f"🤝 <b>Friend request</b>\n\n"
        f"{escape(fullname(message.from_user))} wants to add you as a friend."
    )
    kb = friend_action_markup(req_id)
    try:
        bot.send_message(target_id, note, reply_markup=kb)
        bot.send_message(message.chat.id, "Friend request sent.")
    except Exception:
        bot.send_message(message.chat.id, "Could not deliver the friend request. Ask them to start the bot first.")
@bot.message_handler(commands=["request_status", "my_request_status"])
def cmd_request_status(message):
    ensure_user(message.from_user)
    token = request_status_token(message.from_user.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📊 Open my request status", url=f"{config.BASE_URL}/status/{token}"))
    bot.send_message(message.chat.id, "Your request status:", reply_markup=kb)
@bot.message_handler(commands=["request_dashboard"])
def cmd_request_dashboard(message):
    if message.chat.type not in ("group", "supergroup", "private"):
        return
    ensure_user(message.from_user)
    if message.chat.type in ("group", "supergroup"):
        ensure_group(message.chat)
        if not is_chat_admin(message.chat.id, message.from_user.id) or not is_bot_admin(message.chat.id):
            bot.reply_to(message, "Admins only.")
            return
        group_id = message.chat.id
    else:
        bot.reply_to(message, "Use this inside an admin group to open its dashboard.")
        return
    token = admin_token(message.from_user.id, group_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📋 Open admin request dashboard", url=f"{config.BASE_URL}/admin/{token}"))
    bot.send_message(message.chat.id, "Open the request dashboard here:", reply_markup=kb)
@bot.message_handler(commands=["unban"])
def cmd_unban(message):
    if message.chat.type not in ("group", "supergroup"):
        bot.reply_to(message, "Use this in a group.")
        return
    if not is_chat_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "Admins only.")
        return
    target = None
    parts = message.text.split(maxsplit=1)
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(parts) > 1:
        username = parts[1].strip().lstrip("@")
        target = db.user_by_username(username)
    if not target:
        bot.reply_to(message, "Reply to a user or use /unban @username")
        return
    if hasattr(target, "id"):
        uid = target.id
        tname = target.first_name or target.username or str(uid)
    else:
        uid = int(target.get("user_id"))
        tname = target.get("full_name") or target.get("username") or str(uid)
    try:
        bot.unban_chat_member(message.chat.id, uid)
    except Exception:
        pass
    db.reset_warnings(message.chat.id, uid)
    bot.send_message(message.chat.id, f"✅ Unbanned <b>{escape(tname)}</b>.")
@bot.message_handler(commands=["menu", "settings"])
def cmd_menu(message):
    if message.chat.type != "private":
        bot.reply_to(message, "Open this in DM.")
        return
    ensure_user(message.from_user)
    bot.send_message(message.chat.id, "Main menu:", reply_markup=menu_markup())
@bot.message_handler(commands=["search"])
def cmd_search(message):
    if message.chat.type not in ("group", "supergroup"):
        bot.reply_to(message, "Use /search inside the connected group.")
        return
    ensure_group(message.chat)
    g = db.get_group(message.chat.id)
    if not g or not g.get("connected_channel_id"):
        bot.reply_to(message, "No channel is connected yet.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Use: /search jujutsu kaisen")
        return
    result = db.search_channel_posts(g["connected_channel_id"], parts[1].strip())
    if result:
        try:
            bot.copy_message(message.chat.id, result["channel_id"], result["message_id"], reply_to_message_id=message.message_id)
        except Exception:
            bot.reply_to(message, "Found a match, but I could not copy it.")
    else:
        bot.reply_to(message, "No match found in the connected channel.")
@bot.message_handler(commands=["request"])
def cmd_request(message):
    if message.chat.type not in ("group", "supergroup"):
        bot.reply_to(message, "Use /request inside the group.")
        return
    ensure_group(message.chat)
    g = db.get_group(message.chat.id)
    parts = message.text.split(maxsplit=1)
    text = parts[1].strip() if len(parts) > 1 else ""
    if not text:
        bot.reply_to(message, "Use: /request jujutsu kaisen")
        return
    if g and g.get("connected_channel_id"):
        result = db.search_channel_posts(g["connected_channel_id"], text)
        if result:
            bot.copy_message(message.chat.id, result["channel_id"], result["message_id"], reply_to_message_id=message.message_id)
            return
    limit = int(g.get("request_limit", config.DEFAULT_REQUEST_LIMIT))
    if db.count_open_requests(message.chat.id, message.from_user.id) >= limit:
        bot.reply_to(message, f"You already have {limit} active request(s).")
        return
    db.add_request(message.chat.id, message.from_user, text)
    bot.reply_to(message, "✅ Request added.")
@bot.message_handler(commands=["challenge"])
def cmd_challenge(message):
    if message.chat.type not in ("group", "supergroup"):
        bot.reply_to(message, "Use this in a group.")
        return
    ensure_group(message.chat)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Use: /challenge @username")
        return
    username = parts[1].strip().lstrip("@")
    target = db.user_by_username(username)
    if not target:
        bot.reply_to(message, "I do not know that username yet. Ask them to start the bot once or send a message in the group.")
        return
    challenge_id = uuid.uuid4().hex[:10]
    db.add_challenge(challenge_id, "choose", message.chat.id, message.from_user.id, target["user_id"])
    bot.send_message(message.chat.id, f"{message.from_user.first_name} challenged @{username}. Choose a game:", reply_markup=challenge_markup(challenge_id))
@bot.message_handler(commands=["warn", "warning"])
def cmd_warn(message):
    if message.chat.type not in ("group", "supergroup"):
        bot.reply_to(message, "Use this in a group.")
        return
    if not is_chat_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "Admins only.")
        return
    ensure_group(message.chat)
    parts = message.text.split(maxsplit=1)
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(parts) > 1:
        username = parts[1].strip().lstrip("@")
        target = db.user_by_username(username)
    if not target:
        bot.reply_to(message, "Reply to a member's message with /warn or use /warn @username.")
        return
    if not hasattr(target, 'id'):
        uid = int(target.get('user_id'))
        target = type('U', (), {'id': uid, 'first_name': target.get('full_name') or target.get('username') or str(uid), 'username': target.get('username')})()
    ensure_user(target)
    g = db.get_group(message.chat.id) or {}
    count = db.inc_warning(message.chat.id, target.id, "manual warn")
    limit = int(g.get("warn_limit", config.DEFAULT_WARN_LIMIT))
    if count >= limit:
        try:
            bot.ban_chat_member(message.chat.id, target.id)
        except Exception:
            pass
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧽 Remove warn", callback_data=f"warn:remove:{message.chat.id}:{target.id}"))
    bot.send_message(message.chat.id, warning_event_text(target, count, limit, "manual warn"), reply_markup=kb)
@bot.message_handler(commands=["friend", "addfriend"])
def cmd_friend(message):
    if message.chat.type != "private":
        bot.reply_to(message, "Open this command in DM.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Use: /friend @username")
        return
    username = parts[1].strip().lstrip("@")
    target = db.user_by_username(username)
    if not target:
        bot.reply_to(message, "User not found. They must start the bot or appear in a group first.")
        return
    if db.are_friends(message.from_user.id, target["user_id"]):
        bot.reply_to(message, "Already friends.")
        return
    if db.friend_count(message.from_user.id) >= 100:
        bot.reply_to(message, "You already have 100 friends.")
        return
    req_id = db.create_friend_request(message.from_user.id, target["user_id"])
    try:
        bot.send_message(target["user_id"], f"🤝 Friend request from <b>{escape(fullname(message.from_user))}</b>", reply_markup=friend_action_markup(req_id))
        bot.reply_to(message, "Friend request sent.")
    except Exception:
        bot.reply_to(message, "I could not message that user.")
@bot.message_handler(commands=["friends"])
def cmd_friends(message):
    if message.chat.type != "private":
        bot.reply_to(message, "Open this command in DM.")
        return
    ensure_user(message.from_user)
    friend_ids = db.friends_of(message.from_user.id)
    lines = []
    for fid in friend_ids:
        row = player_row(fid)
        lines.append(f"• {profiles.display_name(row)}")
    text = "<b>Your friends</b>\n\n" + ("\n".join(lines) if lines else "No friends yet.")
    if len(friend_ids) >= 100:
        text += "\n\nMaximum friends reached: 100."
    kb = friends_list_markup(friend_ids) if friend_ids else None
    bot.send_message(message.chat.id, text, reply_markup=kb)
@bot.message_handler(commands=["friendrequests", "requests"])
def cmd_friend_requests(message):
    if message.chat.type != "private":
        bot.reply_to(message, "Open this command in DM.")
        return
    rows = db.pending_friend_requests_for_user(message.from_user.id)
    if not rows:
        bot.reply_to(message, "No pending friend requests.")
        return
    for r in rows:
        sender = player_row(r["from_user_id"])
        txt = f"🤝 Friend request from <b>{escape(profiles.display_name(sender))}</b>"
        bot.send_message(message.chat.id, txt, reply_markup=friend_action_markup(r["id"]))
@bot.message_handler(commands=["removefriend"])
def cmd_removefriend(message):
    if message.chat.type != "private":
        bot.reply_to(message, "Open this command in DM.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Use: /removefriend @username")
        return
    username = parts[1].strip().lstrip("@")
    target = db.user_by_username(username)
    if not target:
        bot.reply_to(message, "User not found.")
        return
    if not db.are_friends(message.from_user.id, target["user_id"]):
        bot.reply_to(message, "You are not friends yet.")
        return
    db.remove_friend(message.from_user.id, target["user_id"])
    bot.reply_to(message, "Friend removed.")
@bot.message_handler(content_types=["new_chat_members"])
def on_new_chat_members(message):
    ensure_group(message.chat)
    for member in message.new_chat_members:
        ensure_user(member)
        if member.id == bot.get_me().id:
            bot.send_message(message.chat.id, "Thanks for adding me. Use /settings to configure the group.")
            return
@bot.channel_post_handler(content_types=["text", "photo", "video", "document", "audio", "voice", "animation"])
def channel_post(message):
    if message.chat.type != "channel":
        return
    text = message.text or message.caption or ""
    if getattr(message, "document", None) and getattr(message.document, "file_name", None):
        text += " " + message.document.file_name
    if getattr(message, "audio", None) and getattr(message.audio, "title", None):
        text += " " + message.audio.title
    if getattr(message, "video", None) and getattr(message.video, "file_name", None):
        text += " " + message.video.file_name
    db.index_channel_post(message.chat.id, message.message_id, text)
# -------------------------
# text handler / flows / moderation
# -------------------------
@bot.message_handler(content_types=["text"])
def on_text(message):
    ensure_user(message.from_user)
    if message.chat.type in ("group", "supergroup"):
        ensure_group(message.chat)
    st = db.get_state(message.from_user.id, message.chat.id)
    if st:
        if st["action"] == "bad_words":
            words = st["data"].get("words", [])
            if message.text.strip() == "/done":
                db.add_bad_words(message.chat.id, words)
                db.clear_state(message.from_user.id, message.chat.id)
                bot.reply_to(message, f"Saved {len(words)} bad word(s).")
                return
            parts = re.split(r"[_\n]+", message.text.strip())
            parts = [p.strip().lower() for p in parts if p.strip()]
            words.extend(parts)
            db.set_state(message.from_user.id, message.chat.id, "bad_words", {"words": words})
            bot.reply_to(message, f"Added {len(parts)} word(s). Send more or /done.")
            return
        if st["action"] == "connect_channel":
            text = (message.text or "").strip()
            channel_id = None
            if message.forward_from_chat and message.forward_from_chat.type == "channel":
                channel_id = message.forward_from_chat.id
            else:
                try:
                    channel_id = int(text)
                except Exception:
                    channel_id = None
            if channel_id is None:
                bot.reply_to(message, "Forward a post from the channel or send the numeric channel id.")
                return
            db.set_group_value(message.chat.id, "connected_channel_id", channel_id)
            db.clear_state(message.from_user.id, message.chat.id)
            bot.reply_to(message, f"Connected channel set to <code>{channel_id}</code>.")
            return
    if message.chat.type in ("group", "supergroup"):
        g = db.get_group(message.chat.id) or {}
        text = (message.text or "").lower()
        if not text or text.startswith("/"):
            return
        if g.get("spam_on"):
            key = (message.chat.id, message.from_user.id)
            now = time.time()
            SPAM_CACHE[key].append((text, now))
            recent = [t for t, ts in SPAM_CACHE[key] if now - ts <= 300]
            repeat_count = sum(1 for t in recent if t == text)
            if repeat_count >= int(g.get("spam_limit", config.DEFAULT_SPAM_LIMIT)):
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                except Exception:
                    pass
                try:
                    bot.ban_chat_member(message.chat.id, message.from_user.id)
                except Exception:
                    pass
                bot.reply_to(message, f"🚫 {message.from_user.first_name} banned for spam.")
                return
        bad_words = db.get_bad_words(message.chat.id)
        if bad_words and not is_chat_admin(message.chat.id, message.from_user.id):
            hit = next((w for w in bad_words if w in text), None)
            if hit:
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                except Exception:
                    pass
                count = db.inc_warning(message.chat.id, message.from_user.id, f"bad word: {hit}")
                warn_limit = int(g.get("warn_limit", config.DEFAULT_WARN_LIMIT))
                if count >= warn_limit:
                    try:
                        bot.ban_chat_member(message.chat.id, message.from_user.id)
                    except Exception:
                        pass
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("🧽 Remove warn", callback_data=f"warn:remove:{message.chat.id}:{message.from_user.id}"))
                bot.send_message(message.chat.id, warning_event_text(message.from_user, count, warn_limit, f"bad word: {hit}"), reply_markup=kb)
                return
# -------------------------
# callbacks
# -------------------------
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    try:
        data = call.data or ""
        if data.startswith("menu:"):
            page = data.split(":", 1)[1]
            if page == "back":
                bot.edit_message_text("Main menu:", call.message.chat.id, call.message.message_id, reply_markup=menu_markup())
            elif page == "groups":
                groups = db.list_groups()
                kb = types.InlineKeyboardMarkup(row_width=1)
                for g in groups[:20]:
                    kb.add(types.InlineKeyboardButton(g["title"] or str(g["chat_id"]), callback_data=f"gs:open:{g['chat_id']}"))
                kb.add(types.InlineKeyboardButton("Back", callback_data="menu:back"))
                bot.edit_message_text("Choose a group:", call.message.chat.id, call.message.message_id, reply_markup=kb)
            elif page == "files":
                bot.edit_message_text("Linked files is under construction.", call.message.chat.id, call.message.message_id, reply_markup=back_markup("menu:back"))
            elif page == "market":
                bot.edit_message_text("Market is under construction.", call.message.chat.id, call.message.message_id, reply_markup=back_markup("menu:back"))
            return
        if data.startswith("gs:open:"):
            chat_id = int(data.split(":")[-1])
            if not is_chat_admin(chat_id, call.from_user.id):
                bot.answer_callback_query(call.id, "Only admins can use this.", show_alert=True)
                return
            if not is_bot_admin(chat_id):
                bot.answer_callback_query(call.id, "I must be admin in that group first.", show_alert=True)
                return
            bot.edit_message_text(f"Settings for <code>{chat_id}</code>:", call.message.chat.id, call.message.message_id, reply_markup=group_settings_markup(chat_id))
            bot.answer_callback_query(call.id)
            return
        if data.startswith("gs:connect:"):
            chat_id = int(data.split(":")[-1])
            if not is_chat_admin(chat_id, call.from_user.id) or not is_bot_admin(chat_id):
                bot.answer_callback_query(call.id, "Admin rights required.", show_alert=True)
                return
            db.set_state(call.from_user.id, call.message.chat.id, "connect_channel", {"group_id": chat_id})
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, f"Send the channel numeric id or forward a post from the channel to connect to group <code>{chat_id}</code>.")
            return
        if data.startswith("gs:req:"):
            chat_id = int(data.split(":")[-1])
            if not is_chat_admin(chat_id, call.from_user.id) or not is_bot_admin(chat_id):
                bot.answer_callback_query(call.id, "Admin rights required.", show_alert=True)
                return
            bot.edit_message_text("Choose request limit:", call.message.chat.id, call.message.message_id, reply_markup=request_limit_markup(chat_id))
            bot.answer_callback_query(call.id)
            return
        if data.startswith("gs:filter:"):
            chat_id = int(data.split(":")[-1])
            if not is_chat_admin(chat_id, call.from_user.id) or not is_bot_admin(chat_id):
                bot.answer_callback_query(call.id, "Admin rights required.", show_alert=True)
                return
            current = db.get_bad_words(chat_id)
            db.set_state(call.from_user.id, call.message.chat.id, "bad_words", {"group_id": chat_id, "words": current})
            bot.answer_callback_query(call.id)
            current_txt = ", ".join(current) if current else "No words added yet."
            bot.send_message(call.message.chat.id, f"Current filtered words for <code>{chat_id}</code>:\n<b>{escape(current_txt)}</b>\nSend one word per message, or use underscores like word1_word2_word3. Send /done when finished.")
            return
        if data.startswith("gs:warn:"):
            chat_id = int(data.split(":")[-1])
            if not is_chat_admin(chat_id, call.from_user.id) or not is_bot_admin(chat_id):
                bot.answer_callback_query(call.id, "Admin rights required.", show_alert=True)
                return
            bot.edit_message_text("Choose warning limit:", call.message.chat.id, call.message.message_id, reply_markup=warning_limit_markup(chat_id))
            bot.answer_callback_query(call.id)
            return
        if data.startswith("gs:spam:"):
            chat_id = int(data.split(":")[-1])
            if not is_chat_admin(chat_id, call.from_user.id) or not is_bot_admin(chat_id):
                bot.answer_callback_query(call.id, "Admin rights required.", show_alert=True)
                return
            bot.edit_message_text("Spam detection:", call.message.chat.id, call.message.message_id, reply_markup=spam_markup(chat_id))
            bot.answer_callback_query(call.id)
            return
        if data.startswith("gs:dash:"):
            chat_id = int(data.split(":")[-1])
            if not is_chat_admin(chat_id, call.from_user.id) or not is_bot_admin(chat_id):
                bot.answer_callback_query(call.id, "Admin rights required.", show_alert=True)
                return
            token = admin_token(call.from_user.id, chat_id)
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("📋 Open admin dashboard", url=f"{config.BASE_URL}/admin/{token}"))
            bot.send_message(call.message.chat.id, "Open the request dashboard here:", reply_markup=kb)
            bot.answer_callback_query(call.id)
            return
        if data.startswith("reqlimit:"):
            _, chat_id, n = data.split(":")
            chat_id, n = int(chat_id), int(n)
            if not is_chat_admin(chat_id, call.from_user.id) or not is_bot_admin(chat_id):
                bot.answer_callback_query(call.id, "Admin rights required.", show_alert=True)
                return
            db.set_group_value(chat_id, "request_limit", n)
            bot.edit_message_text(f"Request limit set to {n}.", call.message.chat.id, call.message.message_id, reply_markup=group_settings_markup(chat_id))
            bot.answer_callback_query(call.id)
            return
        if data.startswith("warnlimit:"):
            _, chat_id, n = data.split(":")
            chat_id, n = int(chat_id), int(n)
            if not is_chat_admin(chat_id, call.from_user.id) or not is_bot_admin(chat_id):
                bot.answer_callback_query(call.id, "Admin rights required.", show_alert=True)
                return
            db.set_group_value(chat_id, "warn_limit", n)
            bot.edit_message_text(f"Warning limit set to {n}.", call.message.chat.id, call.message.message_id, reply_markup=group_settings_markup(chat_id))
            bot.answer_callback_query(call.id)
            return
        if data.startswith("spam:"):
            _, chat_id, state = data.split(":")
            chat_id = int(chat_id)
            if not is_chat_admin(chat_id, call.from_user.id) or not is_bot_admin(chat_id):
                bot.answer_callback_query(call.id, "Admin rights required.", show_alert=True)
                return
            db.set_group_value(chat_id, "spam_on", 1 if state == "on" else 0)
            bot.edit_message_text(f"Spam detection turned {state}.", call.message.chat.id, call.message.message_id, reply_markup=spam_markup(chat_id))
            bot.answer_callback_query(call.id)
            return
        if data.startswith("spamlimit:"):
            _, chat_id, n = data.split(":")
            chat_id, n = int(chat_id), int(n)
            if not is_chat_admin(chat_id, call.from_user.id) or not is_bot_admin(chat_id):
                bot.answer_callback_query(call.id, "Admin rights required.", show_alert=True)
                return
            db.set_group_value(chat_id, "spam_limit", n)
            bot.edit_message_text(f"Spam limit set to {n}.", call.message.chat.id, call.message.message_id, reply_markup=spam_markup(chat_id))
            bot.answer_callback_query(call.id)
            return
        if data.startswith("ch:"):
            _, game_type, ch_id = data.split(":")
            ch = db.get_challenge(ch_id)
            if not ch:
                bot.answer_callback_query(call.id, "Challenge not found.", show_alert=True)
                return
            if call.from_user.id != ch["target_id"]:
                bot.answer_callback_query(call.id, "Only the challenged user can accept this.", show_alert=True)
                return
            if game_type == "cancel":
                db.update_challenge(ch_id, "cancelled")
                bot.edit_message_text("Challenge cancelled.", call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id)
                return
            if game_type in ("ttt", "rps"):
                db.update_challenge(ch_id, "accepted")
                game_id = games.new_game(game_type, ch["challenger_id"], ch["target_id"], ch["group_id"])
                db.update_challenge(ch_id, f"{game_type}:{game_id}")
                try:
                    bot.edit_message_text(f"✅ {games.game_title(game_type)} match started. Players will get the room in DM.", call.message.chat.id, call.message.message_id)
                except Exception:
                    pass
                send_game_invites(game_type, game_id, [ch["challenger_id"], ch["target_id"]])
                try:
                    bot.send_message(ch["group_id"], f"🎮 {games.game_title(game_type)} room opened for the two players.")
                except Exception:
                    pass
                bot.answer_callback_query(call.id)
                return
        if data.startswith("warn:remove:"):
            _, _, group_id, user_id = data.split(":")
            group_id = int(group_id)
            user_id = int(user_id)
            if not is_chat_admin(group_id, call.from_user.id):
                bot.answer_callback_query(call.id, "Admins only.", show_alert=True)
                return
            count = db.dec_warning(group_id, user_id)
            try:
                bot.edit_message_text(f"🧽 Warn removed for user <code>{user_id}</code>. Remaining warnings: {count}.", call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            bot.answer_callback_query(call.id, "Warn removed.")
            return
        if data.startswith("friend:"):
            _, action, arg = data.split(":")
            if action in ("accept", "decline"):
                req = db.get_friend_request(int(arg))
                if not req:
                    bot.answer_callback_query(call.id, "Friend request not found.", show_alert=True)
                    return
                if call.from_user.id != req["to_user_id"]:
                    bot.answer_callback_query(call.id, "Only the recipient can do this.", show_alert=True)
                    return
                if action == "decline":
                    db.update_friend_request(int(arg), "declined")
                    bot.edit_message_text("Friend request declined.", call.message.chat.id, call.message.message_id)
                    try:
                        bot.send_message(req["from_user_id"], f"{profiles.display_name(player_row(req['to_user_id']))} declined your friend request.")
                    except Exception:
                        pass
                    bot.answer_callback_query(call.id)
                    return
                if db.friend_count(req["from_user_id"]) >= 100 or db.friend_count(req["to_user_id"]) >= 100:
                    bot.answer_callback_query(call.id, "One of the users already has 100 friends.", show_alert=True)
                    return
                db.add_friend(req["from_user_id"], req["to_user_id"])
                db.update_friend_request(int(arg), "accepted")
                bot.edit_message_text("Friend request accepted.", call.message.chat.id, call.message.message_id)
                try:
                    bot.send_message(req["from_user_id"], f"You are now friends with {profiles.display_name(player_row(req['to_user_id']))}.")
                except Exception:
                    pass
                bot.answer_callback_query(call.id)
                return
            if action == "remove":
                friend_id = int(arg)
                if not db.are_friends(call.from_user.id, friend_id):
                    bot.answer_callback_query(call.id, "Not in your friend list.", show_alert=True)
                    return
                db.remove_friend(call.from_user.id, friend_id)
                bot.answer_callback_query(call.id, "Friend removed.", show_alert=True)
                try:
                    bot.send_message(call.from_user.id, f"Removed {profiles.display_name(player_row(friend_id))} from your friends list.")
                except Exception:
                    pass
                return
        if data.startswith("room:"):
            _, game_type, game_id = data.split(":")
            url = f"{config.BASE_URL}/game/{game_token(game_type, game_id)}"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Open game room", web_app=types.WebAppInfo(url=url)))
            bot.send_message(call.message.chat.id, "Open the live game room:", reply_markup=kb)
            bot.answer_callback_query(call.id)
            return
    except Exception as e:
        try:
            bot.answer_callback_query(call.id, f"Error: {e}", show_alert=True)
        except Exception:
            pass
# -------------------------
# web pages
# -------------------------
@app.route("/")
def home():
    return "Bot is running"
@app.route("/games")
def games_page():
    return render_games_hub()
@app.route("/status/<token>")
def status_page(token):
    payload = verify_payload(token)
    if not payload or payload.get("scope") != "status":
        abort(403)
    uid = int(payload["uid"])
    rows = db.requests_for_user(uid)
    rows = sorted(rows, key=lambda r: (r["status"] != "pending", r["created_at"]))
    items = []
    for r in rows:
        items.append(f"""
        <div class="card">
          <div class="title">#{r['id']} — {escape(r['status'])}</div>
          <div class="meta">Group: {r['group_id']} • {time.strftime('%Y-%m-%d %H:%M', time.localtime(r['created_at']))}</div>
          <div class="body">{escape(r['text'])}</div>
          <div class="note">{escape(r['note'] or '')}</div>
        </div>
        """)
    html = f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body{{font-family:Arial,sans-serif;background:#0f0f12;color:#fff;padding:14px}}
    .card{{background:#1b1b22;padding:12px;border-radius:14px;margin-bottom:10px}}
    .title{{font-weight:700;margin-bottom:4px}}
    .meta{{opacity:.72;font-size:12px}}
    .body{{margin:8px 0}}
    .note{{opacity:.9;font-size:13px}}
    </style>
    </head>
    <body>
      <h3>Your request status</h3>
      {''.join(items) if items else '<p>No requests yet.</p>'}
    </body>
    </html>
    """
    return render_template_string(html)
@app.route("/admin/<token>")
def admin_page(token):
    payload = verify_payload(token)
    if not payload or payload.get("scope") != "admin":
        abort(403)
    uid = int(payload["uid"])
    group_id = int(payload["group_id"])
    if not is_chat_admin(group_id, uid):
        return "Admin rights required.", 403
    rows = db.requests_for_group(group_id)
    row_html = []
    for r in rows:
        row_html.append(f"""
        <form class="card" method="post" action="/api/request/{r['id']}/update">
          <input type="hidden" name="token" value="{escape(token)}">
          <div class="top">#{r['id']} • <b>{escape(r['status'])}</b> • <span>{escape(r['full_name'] or '')}</span></div>
          <div class="text">{escape(r['text'] or '')}</div>
          <input class="msg" name="note" placeholder="This message will be send to member" value="{escape(r['note'] or '')}">
          <div class="btns">
            <button name="action" value="working">Working</button>
            <button name="action" value="done">✅ Done</button>
            <button name="action" value="cancel">❌ Cancel</button>
          </div>
        </form>
        """)
    html = f"""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
      body{{font-family:Arial,sans-serif;background:#0f0f12;color:#fff;padding:12px}}
      .card{{background:#1b1b22;padding:12px;border-radius:14px;margin:12px 0}}
      .top{{font-size:13px;opacity:.95}}
      .text{{margin:8px 0 10px 0;white-space:pre-wrap}}
      .msg{{width:100%;box-sizing:border-box;padding:10px;border-radius:10px;border:0;margin-bottom:8px}}
      .btns{{display:flex;gap:8px;flex-wrap:wrap}}
      button{{padding:9px 12px;border-radius:10px;border:0;cursor:pointer}}
      </style>
    </head>
    <body>
      <h3>Request dashboard</h3>
      {''.join(row_html) if row_html else '<p>No requests yet.</p>'}
    </body>
    </html>
    """
    return render_template_string(html)
@app.route("/api/request/<int:req_id>/update", methods=["POST"])
def update_request(req_id):
    token = request.form.get("token", "")
    action = request.form.get("action", "")
    note = request.form.get("note", "").strip()
    payload = verify_payload(token)
    if not payload or payload.get("scope") != "admin":
        abort(403)
    uid = int(payload["uid"])
    group_id = int(payload["group_id"])
    if not is_chat_admin(group_id, uid):
        abort(403)
    r = db.get_request(req_id)
    if not r or int(r["group_id"]) != group_id:
        abort(404)
    if action == "working":
        db.update_request_status(req_id, "working", note)
        msg = f"🟡 Your request is being worked on.\n\nRequest: {r['text']}"
    elif action == "done":
        db.update_request_status(req_id, "done", note)
        msg = f"✅ Your request is completed.\n\nRequest: {r['text']}"
    elif action == "cancel":
        db.update_request_status(req_id, "cancelled", note)
        msg = f"❌ Your request was cancelled.\n\nRequest: {r['text']}"
    else:
        abort(400)
    if note:
        msg += f"\n\nAdmin note: {note}"
    try:
        bot.send_message(r["user_id"], msg)
    except Exception:
        pass
    return redirect(f"/admin/{token}")
@app.route("/game/<token>")
def game_page(token):
    payload = verify_payload(token)
    if not payload or payload.get("scope") != "game":
        abort(403)
    game_type = payload.get("game_type")
    game_id = payload.get("game_id")
    if game_type not in ("ttt", "rps"):
        abort(403)
    return render_game_page(game_type, game_id)
@app.route("/api/game/<token>/state")
def api_game_state(token):
    payload = verify_payload(token)
    if not payload or payload.get("scope") != "game":
        abort(403)
    game_type = payload.get("game_type")
    game_id = payload.get("game_id")
    state = games.room_state(game_type, game_id)
    if not state:
        return jsonify({"ok": False, "error": "Game not found."})
    viewer = webapp_user()
    viewer_id = viewer["user_id"] if viewer else None
    players = []
    for idx, pid in enumerate(state["players"], start=1):
        row = player_row(pid)
        players.append({
            "id": pid,
            "label": f"Player {idx}: ",
            "name": profiles.display_name(row),
            "username": row.get("username") or "",
            "photo_url": user_photo_url(pid),
            "friend_state": friend_state(viewer_id, pid),
        })
    game = {
        "game_id": game_id,
        "type": game_type,
        "players": players,
        "ended": state.get("ended", False),
        "winner": state.get("winner"),
        "status": "Finished" if state.get("ended") else "Live",
    }
    if game_type == "ttt":
        game["board"] = state.get("board", [" "] * 9)
        turn = state.get("turn")
        game["status"] = "Finished" if state.get("ended") else f"Turn: {profiles.display_name(player_row(turn)) if turn else '—'}"
    else:
        game["choices"] = state.get("choices", {})
        game["choices_text"] = ", ".join(f"{profiles.display_name(player_row(pid))}: {state.get('choices', {}).get(pid, '—')}" for pid in state["players"])
        game["status"] = "Finished" if state.get("ended") else "Waiting for choices"
        game["result"] = state.get("result", "")
    friends = []
    if viewer_id:
        for fid in db.friends_of(viewer_id):
            row = player_row(fid)
            friends.append({
                "id": fid,
                "name": profiles.display_name(row),
                "username": row.get("username") or "",
                "photo_url": user_photo_url(fid),
            })
    return jsonify({"ok": True, "viewer": viewer, "game": game, "friends": friends})
@app.route("/api/game/<token>/move", methods=["POST"])
def api_game_move(token):
    payload = verify_payload(token)
    if not payload or payload.get("scope") != "game":
        abort(403)
    game_type = payload.get("game_type")
    game_id = payload.get("game_id")
    viewer = webapp_user()
    if not viewer:
        return jsonify({"ok": False, "error": "Open this inside Telegram."}), 401
    data = request.get_json(force=True, silent=True) or {}
    if game_type == "ttt":
        if "cell" not in data:
            return jsonify({"ok": False, "error": "Missing cell."}), 400
        game, note = games.handle_move("ttt", game_id, viewer["user_id"], int(data["cell"]))
    elif game_type == "rps":
        if "choice" not in data:
            return jsonify({"ok": False, "error": "Missing choice."}), 400
        game, note = games.handle_move("rps", game_id, viewer["user_id"], data["choice"])
    else:
        return jsonify({"ok": False, "error": "Unknown game type."}), 400
    if not game:
        return jsonify({"ok": False, "error": note})
    return api_game_state(token)
@app.route("/api/friends/list")
def api_friends_list():
    viewer = webapp_user()
    if not viewer:
        return jsonify({"viewer": None, "friends": []})
    friend_ids = db.friends_of(viewer["user_id"])
    friends = []
    for fid in friend_ids:
        row = player_row(fid)
        friends.append({
            "id": fid,
            "name": profiles.display_name(row),
            "username": row.get("username") or "",
            "photo_url": user_photo_url(fid),
        })
    return jsonify({"viewer": viewer, "friends": friends})
@app.route("/api/friends/request", methods=["POST"])
def api_friends_request():
    viewer = webapp_user()
    if not viewer:
        return jsonify({"ok": False, "error": "Open this inside Telegram."}), 401
    data = request.get_json(force=True, silent=True) or {}
    target_id = int(data.get("target_id", 0))
    if not target_id:
        return jsonify({"ok": False, "error": "Missing target."}), 400
    if viewer["user_id"] == target_id:
        return jsonify({"ok": False, "error": "You cannot add yourself."}), 400
    if db.are_friends(viewer["user_id"], target_id):
        return jsonify({"ok": True, "state": {"ok": True, "message": "Already friends."}})
    if db.friend_count(viewer["user_id"]) >= 100:
        return jsonify({"ok": False, "error": "You already have 100 friends."}), 400
    if db.friend_request_exists(viewer["user_id"], target_id):
        return jsonify({"ok": True, "state": {"ok": True, "message": "Request already pending."}})
    req_id = db.create_friend_request(viewer["user_id"], target_id)
    try:
        bot.send_message(target_id, f"🤝 Friend request from <b>{escape(viewer['full_name'] or 'A user')}</b>", reply_markup=friend_action_markup(req_id))
    except Exception:
        pass
    return jsonify({"ok": True, "state": {"ok": True, "message": "Friend request sent."}})
@app.route("/api/friends/remove", methods=["POST"])
def api_friends_remove():
    viewer = webapp_user()
    if not viewer:
        return jsonify({"ok": False, "error": "Open this inside Telegram."}), 401
    data = request.get_json(force=True, silent=True) or {}
    target_id = int(data.get("target_id", 0))
    if not target_id:
        return jsonify({"ok": False, "error": "Missing target."}), 400
    if not db.are_friends(viewer["user_id"], target_id):
        return jsonify({"ok": False, "error": "Not in your friend list."}), 400
    db.remove_friend(viewer["user_id"], target_id)
    return jsonify({"ok": True, "state": {"ok": True, "message": "Friend removed."}})
# -------------------------
# main
# -------------------------
def run_bot():
    global BOT_USERNAME
    try:
        BOT_USERNAME = bot.get_me().username
    except Exception:
        pass
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
