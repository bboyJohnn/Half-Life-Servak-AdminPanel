#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Разбор строк живого лога Half-Life (logs/live.log).

Сервер шлёт каждую строку лога UDP-пакетом (logaddress), socat в контейнере
дописывает пакеты в live.log как есть: FF FF FF FF "log " + строка + "\n" + 00.
Строка: «L 10/03/2026 - 18:12:54: событие». Время — часы контейнера, то есть UTC.

Названия карты в логе WON-сервера НЕТ. Смена карты видна только по паре
«Log file closed» / «Log file started». Какая карта загрузилась, панель узнаёт
у сервера сама (запрос info) в момент, когда видит «Log file started», и пишет в
таблицу map_starts — по ней статистика подставляет карту в матчи. Steam-сервер
пишет карту сам («Loading map», «Started map») — тогда она берётся прямо из лога.

Игрок в строке: "Имя<userid><WONID><команда>". У ботов WONID = BOT (кроме строк
Kick, там 0). У живых игроков WON2 без авторизации — 4294967295.
"""

import calendar
import re
import time

PREFIX = b"\xff\xff\xff\xfflog "
LINE_RE = re.compile(r"^L (\d\d)/(\d\d)/(\d{4}) - (\d\d):(\d\d):(\d\d): (.*)$")
P = r'"(?P<{0}>.*?)<(?P<{0}_uid>-?\d+)><(?P<{0}_won>[^>]*)><(?P<{0}_team>[^>]*)>"'
PLAYER_RE = re.compile("^" + P.format("p"))
KILL_RE = re.compile("^" + P.format("k") + " killed " + P.format("v") + r' with "(?P<weapon>[^"]*)"')
SUICIDE_RE = re.compile("^" + P.format("p") + r' committed suicide with "(?P<weapon>[^"]*)"')
CONNECT_RE = re.compile("^" + P.format("p") + r' connected, address "(?P<addr>[^"]*)"')
ENTER_RE = re.compile("^" + P.format("p") + " entered the game")
DISCONNECT_RE = re.compile("^" + P.format("p") + " disconnected")
RENAME_RE = re.compile("^" + P.format("p") + r' changed name to "(?P<new>.*)"')
SAY_RE = re.compile("^" + P.format("p") + r' say(?:_team)? "(?P<text>.*)"')
KICK_RE = re.compile("^Kick: " + P.format("p") + r' was kicked by "(?P<by>[^"]*)"')
# Steam-сервер пишет название карты сам: «Loading map "crossfire"», «Started map "crossfire" (CRC …)»
MAP_RE = re.compile(r'^(?:Loading|Started) map "(?P<map>[^"]+)"')
RCON_RE = re.compile(r'(rcon \S+ ")[^"]*(")')


def decode(raw):
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1251", "replace")


def clean_line(raw):
    """Байты одной записи live.log → текст строки лога (без служебных байтов)."""
    raw = raw.replace(b"\x00", b"")
    if raw.startswith(PREFIX):
        raw = raw[len(PREFIX):]
    elif raw.startswith(b"\xff\xff\xff\xffRL "):     # так шлют лог движки поновее (S2A_LOGSTRING)
        raw = raw[5:]
    return decode(raw.rstrip(b"\r"))


def redact(text):
    """Пароль rcon движок пишет в лог открытым текстом — вырезаем."""
    return RCON_RE.sub(r"\1***\2", text)


def is_bot(won):
    return won == "BOT"


def parse(text):
    """Строка лога → (время UTC, событие, данные) или None.

    События: map_start, map_end, map_name, kill, suicide, connect, enter, disconnect,
    rename, say, kick, other.
    """
    m = LINE_RE.match(text)
    if not m:
        return None
    mo, d, y, hh, mi, ss, body = m.groups()
    ts = calendar.timegm((int(y), int(mo), int(d), int(hh), int(mi), int(ss), 0, 0, 0))
    if body.startswith("Log file started"):
        return ts, "map_start", {}
    if body.startswith("Log file closed"):
        return ts, "map_end", {}
    mp = MAP_RE.match(body)
    if mp:
        return ts, "map_name", {"map": mp.group("map").lower()}
    k = KILL_RE.match(body)
    if k:
        return ts, "kill", {"killer": k.group("k"), "killer_uid": int(k.group("k_uid")),
                            "killer_bot": is_bot(k.group("k_won")),
                            "victim": k.group("v"), "victim_uid": int(k.group("v_uid")),
                            "victim_bot": is_bot(k.group("v_won")), "weapon": k.group("weapon")}
    for kind, rx in (("suicide", SUICIDE_RE), ("connect", CONNECT_RE), ("enter", ENTER_RE),
                     ("disconnect", DISCONNECT_RE), ("rename", RENAME_RE), ("say", SAY_RE),
                     ("kick", KICK_RE)):
        mm = rx.match(body)
        if mm:
            data = {"name": mm.group("p"), "uid": int(mm.group("p_uid")),
                    "won": mm.group("p_won"), "bot": is_bot(mm.group("p_won"))}
            if kind == "suicide":
                data["weapon"] = mm.group("weapon")
            elif kind == "connect":
                data["address"] = mm.group("addr").split(":")[0]
                # у ботов адрес "localhost" или пустой
                data["bot"] = data["bot"] or data["address"] in ("", "localhost", "loopback")
            elif kind == "rename":
                data["new"] = mm.group("new")
            elif kind == "say":
                data["text"] = mm.group("text")
            return ts, kind, data
    return ts, "other", {"text": body}


def now():
    return int(time.time())
