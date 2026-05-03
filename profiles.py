
from html import escape
from urllib.parse import quote

import config
import db


def display_name(user_row: dict | None, fallback: str = "Unknown user") -> str:
    if not user_row:
        return fallback
    name = (user_row.get("full_name") or "").strip()
    if name:
        return name
    username = user_row.get("username") or ""
    if username:
        return f"@{username.lstrip('@')}"
    return fallback


def initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[1][0]).upper()


def file_url(file_path: str) -> str:
    return f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{quote(file_path)}"


def get_profile_photo_url(bot, user_id: int, user_row: dict | None = None) -> str | None:
    user_row = user_row or db.get_user(user_id)
    if user_row and user_row.get("photo_file_id"):
        try:
            f = bot.get_file(user_row["photo_file_id"])
            return file_url(f.file_path)
        except Exception:
            pass

    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count:
            photo = photos.photos[0][-1]
            db.set_user_photo(user_id, photo.file_id)
            f = bot.get_file(photo.file_id)
            return file_url(f.file_path)
    except Exception:
        pass
    return None


def avatar_html(user_row: dict | None, bot=None) -> str:
    user_row = user_row or {}
    name = display_name(user_row)
    photo_url = None
    if bot and user_row.get("user_id"):
        photo_url = get_profile_photo_url(bot, int(user_row["user_id"]), user_row)
    if photo_url:
        img = f'<img class="avatar" src="{escape(photo_url)}" alt="dp">'
    else:
        img = f'<div class="avatar fallback">{escape(initials(name))}</div>'
    uname = user_row.get("username") or ""
    uname_txt = f"@{escape(uname)}" if uname else "no username"
    return f"""
    <div class="usercard">
      {img}
      <div class="meta">
        <div class="name">{escape(name)}</div>
        <div class="uname">{uname_txt}</div>
      </div>
    </div>
    """
