# Half-Life Web Panel

A web control panel for a **Half-Life 1 (1998) dedicated server** — the old **WON** HLDS 3.1.1.x as well as
the current **Steam / SteamCMD** HLDS. One small Python process on the same machine as the server; you open it in a
browser and manage the server without the console.

- **Overview** — server status, current map and time left, players with frags and time, machine load, memory,
  disk, match history; quick buttons: next map, restart map, restart server.
- **Players** — who is on the server (from the live log: user id, address, bot or human), kick, ban by IP,
  lift bans, message to everyone. With **jk_botti**: minimum bots, players with bots, skill, remove all bots.
- **Maps** — what is playing now (with a picture), load any map in a click (a window with its picture and what
  comes next), and **your own map order**: drag tiles to reorder, switch maps off — the server plays exactly
  that order, from the next map change, no restart.
- **Server settings** — every setting of `server.cfg` (and `jk_botti.cfg`) with the value in the file and the live
  value on the server; saved with a backup copy and applied at once. If the server only takes it after a map
  change or a restart, the panel asks whether to do it now or later and keeps a reminder.
- **Statistics** — matches, kills, weapons, maps, bots; **human players by IP address** (nicknames repeat):
  visits with exact times, countries with flags, a player card (visits, play time, K/D, favourite weapons and
  maps, best visits, when they come), records, top killers, new players, a calendar and a weekday × hour heat map.
- **Logs** — the live game log, the server's own `L*.log` and the console, with filter and auto-refresh; the rcon
  password that the engine writes into its log is cut out. **Console** — any rcon command with a command
  reference. **Audit log** — every action done in the panel.
- **9 languages** (Russian, English, German, French, Spanish, Portuguese, Polish, Japanese, Chinese) and three
  looks: **Half-Life** (the 1998 menu colours, orange on black, with a lab / HEV suit / current map background),
  **Steam 2003** (the olive Counter-Strike 1.6 menu) and a plain light/dark one. Background music (CC0) and,
  if you build them from your own game, map pictures, the old menu sounds and the menu logo.

> The panel needs **no Docker, no bots and no extra scripts** — only your HLDS and Python 3. It was written for
> a server that has Docker, jk_botti and watchdogs; all of that is optional here, and the matching buttons
> simply do not appear when it is not configured.

---

## Contents

1. [Requirements](#requirements)
2. [Installation, step by step](#installation-step-by-step)
3. [Where everything is configured](#where-everything-is-configured)
4. [Updating](#updating)
5. [How it works](#how-it-works)
6. [Security](#security)
7. [Troubleshooting](#troubleshooting)
8. [Translations](#translations)
9. [Project layout](#project-layout)
10. [Legal](#legal)

---

## Requirements

| What | Notes |
|---|---|
| **A Half-Life dedicated server that already works** | WON HLDS 3.1.1.x (protocol 46) or Steam HLDS (protocol 48), Half-Life Deathmatch (`valve`). The protocol is detected automatically. |
| **Linux** | The panel reads `/proc` for machine load and the server's uptime. Any distribution; the commands below are for Debian / Ubuntu. |
| **The same machine as the server** | The panel edits `server.cfg` and `mapcycle.txt`, reads the maps folder and the logs. |
| **Python 3.10+** | With `aiohttp` (and optionally `maxminddb` for countries), installed below into a virtual environment. |
| **rcon password** set on the server | The panel sends commands through rcon. |
| A Half-Life game client *(optional)* | Only to build map pictures, menu sounds and the menu logo (step 11). |

The examples below assume:

- the server runs as the Linux user **`hlds`**;
- it is installed in **`/home/hlds/hlds`** (with `hlds_linux` and the game folder `valve/` that holds `server.cfg`,
  `mapcycle.txt` and `maps/`);
- the panel goes to **`/opt/hl-panel`**.

Replace these with your own paths and user everywhere.

---

## Installation, step by step

### Step 1. Look at your server

```bash
ls /home/hlds/hlds/valve
```

You should see `server.cfg`, `mapcycle.txt` and the `maps` folder. This folder is `HL_DIR` in the settings.

```bash
grep -E '^\s*(rcon_password|log|logaddress)' /home/hlds/hlds/valve/server.cfg
```

### Step 2. Install Python and git

```bash
sudo apt update
```

```bash
sudo apt install -y git python3 python3-venv
```

Check the version — it must be 3.10 or newer:

```bash
python3 --version
```

### Step 3. Download the panel and install its packages

```bash
sudo git clone https://github.com/bboyJohnn/halflife-AdminPanel.git /opt/hl-panel
```

```bash
sudo chown -R hlds:hlds /opt/hl-panel
```

```bash
sudo -u hlds python3 -m venv /opt/hl-panel/venv
```

```bash
sudo -u hlds /opt/hl-panel/venv/bin/pip install -r /opt/hl-panel/requirements.txt
```

### Step 4. Turn on rcon and the live log in `server.cfg`

The panel learns who joins, leaves and kills whom from the **live log**: the server sends every log line over UDP
to the panel. Add to `/home/hlds/hlds/valve/server.cfg` (keep your own rcon password if you have one):

```
rcon_password "put-a-long-password-here"
log on
logaddress 127.0.0.1 27500
```

On a **Steam** server use `logaddress_add 127.0.0.1 27500` instead of `logaddress`.
Restart the game server once so it reads the file.

### Step 5. Write the settings file `.env`

All settings of the panel are in **one file**, `.env`, next to `app.py`:

```bash
cd /opt/hl-panel
```

```bash
sudo -u hlds cp .env.example .env
```

```bash
sudo -u hlds chmod 600 .env
```

```bash
sudo -u hlds nano .env
```

Usually only **one line** is needed — the game folder:

```
HL_DIR=/home/hlds/hlds/valve
```

Everything else (server.cfg, mapcycle.txt, maps, logs, the rcon password from server.cfg) is found from it. If the
server listens on another port, set `HL_PORT`; to show the address players connect to, set `PUBLIC_ADDRESS`.
The full list is in [Where everything is configured](#where-everything-is-configured).

### Step 6. Set the panel password

A random password (printed on the screen and saved to `data/panel-password.txt`):

```bash
sudo -u hlds venv/bin/python app.py --init
```

Or choose your own:

```bash
sudo -u hlds venv/bin/python tools/passwd.py
```

Both write only a hash of the password and a session key into `.env`.

### Step 7. Check the setup

Start the game server first, then:

```bash
sudo -u hlds venv/bin/python app.py --check
```

It prints what the panel found and what it can reach, for example:

```
[OK  ] .env
[OK  ] panel password           set
[OK  ] HL_DIR                   /home/hlds/hlds/valve
[OK  ] server.cfg               /home/hlds/hlds/valve/server.cfg
[OK  ] mapcycle.txt             /home/hlds/hlds/valve/mapcycle.txt
[OK  ] maps (*.bsp)             12 in /home/hlds/hlds/valve/maps
[ -  ] map order                /opt/hl-panel/data/mappool.txt (created on first save)
[OK  ] server 127.0.0.1:27015   My HL server, crossfire, 0/16 players, protocol 48 (steam)
[OK  ] rcon                     "mapcyclefile" is "mapcycle.txt"
[ -  ] live log                 the panel listens on 127.0.0.1:27500 and writes /opt/hl-panel/data/live.log ...
[ -  ] Docker                   no
[ -  ] server restart           not configured
[ -  ] jk_botti bots            no
[ -  ] countries (GeoLite2)     no database: countries are not shown
All good.
```

`FAIL` lines must be fixed; `-` lines are optional features that are off.

### Step 8. Run the panel as a service

```bash
sudo cp deploy/hl-panel.service /etc/systemd/system/
```

Edit `User`, `Group` and the paths in it if yours differ:

```bash
sudo nano /etc/systemd/system/hl-panel.service
```

```bash
sudo systemctl daemon-reload
```

```bash
sudo systemctl enable --now hl-panel
```

```bash
systemctl status hl-panel
```

### Step 9. Open the panel in your browser

By default the panel listens only on `127.0.0.1:8093` — nothing from the internet can reach it. The simplest
safe way in is an **SSH tunnel** from your computer:

```bash
ssh -L 8093:127.0.0.1:8093 hlds@your-server
```

and then open <http://127.0.0.1:8093> on your computer, while that SSH session is open.

Other ways:

- **Home network.** Set `PANEL_HOST=0.0.0.0` and allow your network:
  `PANEL_ALLOWED_PEERS=127.0.0.1,::1,192.168.0.0/24`. Open `http://<server-ip>:8093`.
- **Reverse proxy with HTTPS** (nginx, Caddy) on the same machine: keep `PANEL_HOST=127.0.0.1` and proxy to it.
  Do not open the plain-HTTP port to the internet.

### Step 10 (optional). The restart button

Without it the panel works the same, just without "Restart the server".

- **Server in Docker:** `CONTAINER=<container name>`. You also get the container card (CPU, memory, restarts),
  stop / start, and `docker logs` as the server console. The panel's user must be allowed to run `docker`.
- **Server without Docker:** run it so that something starts it again when it stops — `hlds_run` (it restarts
  the server after a crash) or systemd with `Restart=always` (see `deploy/hlds.service`). Then let the panel
  stop the process:

  ```
  RESTART_CMD=pkill -x hlds_linux
  ```

  With `deploy/hlds.service` the console output goes to a file; show it in the panel with
  `CONSOLE_LOG=/home/hlds/hlds/console.log`.

### Step 11 (optional). Map pictures, menu sounds and the menu logo from your game

These are Valve's files, so they are not in the repository. Build them from **your own** Half-Life copy (the game
folder with `valve/` inside — a client install or the server itself):

```bash
sudo -u hlds venv/bin/pip install numpy pillow
```

```bash
sudo -u hlds venv/bin/python tools/build_assets.py --game /path/to/Half-Life
```

- **Map pictures** — a rendered view of every map of your server (from `MAPS_DIRS`, the game's `valve/maps` and
  `valve/pak0.pak`), textures from the game's `.wad` files. Without them the panel shows "no picture".
  Popular maps have hand-picked views in `tools/map_cameras.txt`; others get an automatic view from a spawn point.
- **Menu sounds** — `valve/media/launch_*.wav` of the old WON menu: hover, click, error, window open/close.
- **Menu logo** — `valve/media/logo.avi` of the WON menu, shown on the login screen (needs `ffmpeg`).
- **Soundtrack** — if your game is the Steam version, `valve/media/Half-Life??.mp3` is added to the music player.

You can also run the script on your PC and copy `static/maps`, `static/hl` and `static/music` to the server.
Then reload the panel page.

### Step 12 (optional). Countries of IP addresses

Download the free **GeoLite2 Country** database from MaxMind (needs a free account), put
`GeoLite2-Country.mmdb` into `/opt/hl-panel/data/` (or set `GEOIP_DB`), and restart the panel. Lookups happen on
your server; addresses are not sent anywhere.

### Step 13 (optional). jk_botti bots

If the server runs the [jk_botti](https://github.com/Bots-United/jk_botti) bot, set `BOTS_CFG` to its
`jk_botti.cfg` — you get the bots card on the Players page and the bot settings on the Server settings page.

---

## Where everything is configured

Everything is in **`.env`** (see `.env.example` for comments). Paths may use `${KEY}` of a key above; relative
paths start at the folder of `.env`. Check with `python3 app.py --check`.

| Key | Default | What it is |
|---|---|---|
| `HL_DIR` | — (**required**) | The server's game folder (`valve`) with `server.cfg`, `mapcycle.txt`, `maps/`. |
| `PANEL_PASSWORD_HASH`, `PANEL_SECRET` | — (**required**) | Written by `app.py --init` / `tools/passwd.py`. |
| `HL_HOST`, `HL_PORT` | `127.0.0.1`, `27015` | Where the panel queries the server. |
| `PUBLIC_ADDRESS` | | Address players connect to, shown on the Overview. |
| `RCON_PASSWORD` | from `RCON_CFG` | The rcon password; empty = read `rcon_password` from `RCON_CFG`. |
| `RCON_CFG` | `${SERVER_CFG}` | File with `rcon_password` (if you keep it outside server.cfg). |
| `LOG_UDP` | `127.0.0.1:27500` | Where the panel receives the live log. Empty = do not listen. |
| `LIVE_LOG` | `${PANEL_DATA}/live.log` | The live log file (written by the panel, or by something else when `LOG_UDP` is empty). |
| `PANEL_HOST`, `PANEL_PORT` | `127.0.0.1`, `8093` | Where the panel listens. |
| `PANEL_ALLOWED_PEERS` | `127.0.0.1,::1` | Addresses / networks allowed to connect at all. |
| `PANEL_TITLE` | server's hostname | Name in the menu and on the login screen. |
| `PANEL_HUB` | | Optional "All panels" link: a URL or `:port` on the same host. |
| `SERVER_CFG` | `${HL_DIR}/server.cfg` | The settings page. Sections are lines `// 1. Name` (optional). |
| `MAPCYCLE` | `${HL_DIR}/mapcycle.txt` | The engine's map list (rewritten by the panel). |
| `MAPPOOL` | `${PANEL_DATA}/mappool.txt` | The panel's map order (first time taken from mapcycle.txt). |
| `MAPS_DIRS` | `${HL_DIR}/maps` | Folders with `.bsp` maps, comma separated. |
| `LISTIP_CFG` | `${HL_DIR}/listip.cfg` | IP bans (written by `writeip`). |
| `HLDS_LOGS` | `${HL_DIR}/logs` | The server's `L*.log` files. |
| `PANEL_DATA` | `./data` | Panel database, map order, live log, copies of edited files. |
| `PASSWORD_FILE` | `${PANEL_DATA}/panel-password.txt` | Where `--init` saves the new password. |
| `CONTAINER` | | Docker container of the server (restart / stop / start, container card, docker logs). |
| `RESTART_CMD` | | Without Docker: command that restarts the server, e.g. `pkill -x hlds_linux`. |
| `CONSOLE_LOG` | | File with the server's console output (Logs page, crash list). |
| `BOTS_CFG` | | `jk_botti.cfg` — bots card and bot settings. |
| `GEOIP_DB` | `${PANEL_DATA}/GeoLite2-Country.mmdb` | GeoLite2 country database, comma-separated list allowed. |

Settings of the **look** (language, style, background, music) are not on the server: each browser keeps its own,
on the **Panel settings** page (also reachable from the login screen).

---

## Updating

```bash
cd /opt/hl-panel
```

```bash
sudo -u hlds git pull
```

```bash
sudo -u hlds venv/bin/pip install -r requirements.txt
```

```bash
sudo systemctl restart hl-panel
```

`.env`, `data/` and the files built by `tools/build_assets.py` are not touched by `git pull`. Press F5 in the browser
— the page links carry the file versions, so the browser picks up the new panel.

---

## How it works

- **Queries.** Status, players and settings come from the public queries every server browser uses (`info`,
  `players`, `rules` on WON; `A2S_INFO`, `A2S_PLAYER`, `A2S_RULES` with the challenge on Steam). Actions go
  through **rcon** (`challenge rcon` + `rcon`). The panel figures out which protocol your server speaks by itself.
- **Live log.** The old engine writes every rcon command into its log together with the password, so the panel does
  *not* poll `rcon status`: who is on the server, their user id and address come from the live log (connect / enter
  / disconnect / kick lines), frags and time from the public `players` query. Visits of human players are stored with
  exact times; when the server restarts, open visits are closed at the last moment the player was seen.
- **Map names.** A WON server's log has no map names — the panel asks the server (`info`) when it sees
  "Log file started" and remembers which map was loaded at that moment.
- **Map order.** The game library reads `mapcycle.txt` once and re-reads it only when the name in the
  `mapcyclefile` setting changes. So after saving the order the panel writes `mapcycle.txt` rotated so that **the
  next map comes first** and switches `mapcyclefile` between `mapcycle.txt` and `./mapcycle.txt` (the same file):
  at the next map change the server takes the first map of the new list. If someone changes the map past the list
  (console, `changelevel`), the panel rotates the list again. Disabled maps are left out of `mapcycle.txt`. The
  file is written in place (same inode), so a server in a container with a single-file bind mount sees it too.
  Keep the list short: the WON 1.1.1.0 client reads only ~8 KB of the map list the server sends.
- **Settings.** `server.cfg` is changed line by line — comments, order and layout stay; a copy goes to
  `data/cfg-backups` before every write. The new value is sent by rcon at once; then the panel compares it with the
  live value from `rules` and tells you if the server only takes it after a map change or a restart.
- **Statistics.** Matches (one map from start to change), kills, weapons and maps are parsed from the live log once
  a minute into SQLite (`data/panel.db`). The live log is trimmed when it grows over 10 MB.

---

## Security

- Out of the box the panel accepts connections **only from the same machine** (`PANEL_HOST=127.0.0.1`,
  `PANEL_ALLOWED_PEERS=127.0.0.1,::1`). Reach it with an SSH tunnel or a reverse proxy with HTTPS.
- Login with one password, stored only as an scrypt hash; signed session cookie (`HttpOnly`, `SameSite=Strict`),
  CSRF token on every change; 5 wrong passwords lock the login for 5 minutes.
- Strict Content-Security-Policy (no inline scripts, nothing from other sites); everything from the server
  (player names, log lines) is shown as text, never as HTML.
- The rcon password never reaches the browser; it is cut out of every log line the panel shows.
- Every action (kick, ban, settings, maps, console commands, logins) goes to the audit log.
- `.env` and `data/` should be readable only by the panel's user (`chmod 600 .env`).

---

## Troubleshooting

| Problem | What to do |
|---|---|
| `--check`: **server … no answer** | Is the server running? Right `HL_HOST` / `HL_PORT`? On a machine with a firewall, the query goes to the server's UDP port from the same machine — nothing to open. |
| `--check`: **rcon … rejected the rcon password** | `rcon_password` in server.cfg (or `RCON_PASSWORD`) must match the running server; restart the server after changing it. |
| Nobody shows up on **Players**, statistics stay empty | The live log is not arriving: check `log on` and `logaddress 127.0.0.1 27500` (`logaddress_add` on Steam) in server.cfg, restart the server, and look at `data/live.log`. Only one program can listen on the port. |
| The map order does not change the next map | The server must allow the `mapcyclefile` change by rcon (it does by default). The order applies **from the next** map change; "Next map" applies it at once. |
| "Restart the server" is missing | Set `CONTAINER` or `RESTART_CMD` (step 10). |
| No pictures on Maps | Build them from your game (step 11), or put your own 640×360 JPEGs into `static/maps/` and 192×108 ones into `static/maps/thumb/`. |
| The page looks old after an update | Press F5. |
| Logs of the panel itself | `journalctl -u hl-panel -f` |

---

## Translations

The source language is Russian; the dictionaries are `static/i18n/<code>.js` (`en de fr es pt pl ja zh`). Every
text of the panel is wrapped in `L('…')` in `static/app.js` and that Russian text is the key; server messages are
translated with the same dictionary. To check or extend them:

```bash
python3 tools/i18n.py check
```

```bash
python3 tools/i18n.py keys > keys.txt
```

A missing translation just shows the Russian text — nothing breaks. Keys starting with `#` are plural forms
(an object with the language's plural categories, e.g. `{"one": "{0} visit", "other": "{0} visits"}`).

---

## Project layout

```
app.py            web server, API, background tasks, live-log receiver; --init and --check (cli.py)
config.py         reads .env, defaults, which optional features exist
hl.py             talking to HLDS: WON and Steam queries, rcon, command reference
live.py           live log -> who is online, visits of human players
stats.py          live log -> matches, kills, weapons, maps (SQLite)
humans.py         per-IP player summaries, player card, records
cfg.py            server.cfg / jk_botti.cfg editing with backups, map order
mapcycle.py       map order file and the engine's mapcycle.txt
sysinfo.py        machine, Docker or process uptime, restart, logs
geo.py            country by IP (GeoLite2)
logline.py        parsing of HL log lines, rcon password redaction
audit.py          audit log
passwords.py      password hash
static/           the web page: app.js, app.css, boot.js, i18n/, fonts/, music/, hl/, flags/
tools/            i18n.py, passwd.py, build_assets.py (+ bsp_render.py, map_cameras.txt)
deploy/           systemd units for the panel and (example) for HLDS
```

---

## Legal

Half-Life® is a trademark of Valve Corporation. This panel is not affiliated with or endorsed by Valve.
Map pictures, menu sounds, the menu logo and the soundtrack are Valve's and are **not** included — the panel builds
them from your own copy of the game (`tools/build_assets.py`).

Included third-party files: background music by Ruskerdax, yd, isaiah658 and vitalezzz from OpenGameArt under
**CC0** (`static/music/CREDITS.txt`); fonts Exo 2, Russo One (as "Panel Display") and Share Tech Mono (as "Panel
Mono") under the **SIL Open Font License 1.1** (`static/fonts/`); country flags from
[flag-icons](https://github.com/lipis/flag-icons) under the **MIT** license (`static/flags/LICENSE.txt`).
The backgrounds and the λ icon are drawn for this panel.
