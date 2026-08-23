from flask import Flask, request, render_template_string, redirect, session, Response
import requests
import time
import os
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = os.environ.get("CLIENT_ID", "YOUR_CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "YOUR_CLIENT_SECRET")
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
</html>
"""

DASHBOARD_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spidey Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background: #050505; color: #e0e0e0; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: #0b0b0e; padding: 25px; border-radius: 12px; border: 1px solid #8b0000; }
        h2 { font-family: 'Orbitron', sans-serif; color: #ff1e1e; text-align: center; }
        .nav { display: flex; gap: 10px; margin-bottom: 20px; }
        .nav a { flex: 1; text-align: center; padding: 10px; background: #121218; color: #ff1e1e; text-decoration: none; font-family: 'Orbitron', sans-serif; font-size: 12px; border-radius: 6px; border: 1px solid #331a1a; }
        .nav a.active { background: #8b0000; color: #fff; border-color: #ff1e1e; }
        input[type="text"], input[type="password"] { width: 100%; padding: 12px; margin-top: 6px; margin-bottom: 12px; background: #08080a; color: #fff; border: 1px solid #262636; border-radius: 8px; box-sizing: border-box; }
        .checkbox-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; background: #050507; padding: 12px; border-radius: 8px; border: 1px solid #1f1f2e; font-size: 13px; }
        .checkbox-grid label { display: flex; align-items: center; gap: 8px; cursor: pointer; }
        button { width: 100%; padding: 14px; margin-top: 15px; background: #8b0000; color: white; font-family: 'Orbitron', sans-serif; font-weight: 700; border-radius: 8px; border: 1px solid #ff1e1e; cursor: pointer; }
        button:hover { background: #a30000; }
        .success { color: #00ffcc; font-size: 13px; text-align: center; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🕷️ SPIDEY HUB</h2>
        <p style="text-align:center; font-size:13px; color:#888;">Logged in as: <b>{{ username }}</b></p>
        
        <div class="nav">
            <a href="/" class="{% if tab == 'cloner' %}active{% endif %}">SERVER CLONER</a>
            {% if username == 'aaravg7820133.exe' %}
            <a href="/mass-join-panel" class="{% if tab == 'admin' %}active{% endif %}">MASS JOIN PANEL</a>
            {% endif %}
        </div>

        {% if tab == 'cloner' %}
        <h3>Advanced Server Cloner</h3>
        <form method="POST" action="/clone" target="_blank">
            <label>Discord Token (User or Bot)</label>
            <input type="password" name="token" required placeholder="Enter token...">
            
            <label>Source Server ID</label>
            <input type="text" name="source_id" required placeholder="Source ID...">
            
            <label>Target Server ID</label>
            <input type="text" name="target_id" required placeholder="Target ID...">
            
            <div class="checkbox-grid">
                <label><input type="checkbox" name="delete_channels" checked> Delete Target Channels</label>
                <label><input type="checkbox" name="delete_roles" checked> Delete Target Roles</label>
                <label><input type="checkbox" name="clone_channels" checked> Clone Channels/Cats</label>
                <label><input type="checkbox" name="clone_roles" checked> Clone Roles & Order</label>
                <label><input type="checkbox" name="clone_emojis" checked> Clone Emojis</label>
                <label><input type="checkbox" name="clone_settings" checked> Clone Server Settings</label>
            </div>

            <button type="submit">EXECUTE CLONING PROTOCOL</button>
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
</html>
"""

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
    return render_template_string(DASHBOARD_PAGE, username=session.get("username", "Agent"), tab="cloner")

@app.route("/mass-join-panel")
def mass_join_panel():
    if "user_token" not in session or session.get("username") != "aaravg7820133.exe":
        return redirect("/")
    return render_template_string(DASHBOARD_PAGE, username=session.get("username"), tab="admin", msg=request.args.get("msg", ""))

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
    token = request.form.get("token")
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
        yield "<html><head><title>Cloning Logs</title><link href='https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap' rel='stylesheet'><style>body{background:#050505;color:#00ffcc;font-family:'Inter',sans-serif;padding:20px;}pre{background:#0b0b0e;padding:15px;border:1px solid #8b0000;border-radius:8px;max-height:80vh;overflow-y:auto;font-size:12px;}</style></head><body>"
        yield "<h2>⚡ SPIDEY CLONER EXECUTION LOGS</h2><pre>" + (" " * 1024) + "\n"
        
        # 1. Delete Channels
        if del_channels:
            yield "[+] Fetching existing target channels for deletion...\n"
            r_tc = requests.get(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers)
            if r_tc.status_code == 200:
                for ch in r_tc.json():
                    requests.delete(f"https://discord.com/api/v10/channels/{ch['id']}", headers=headers)
                    yield f"[-] Deleted channel: {ch['name']}\n"
                    time.sleep(0.1)

        # 2. Delete Roles
        if del_roles:
            yield "[+] Clearing target roles...\n"
            r_tr = requests.get(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers)
            if r_tr.status_code == 200:
                for role in sorted(r_tr.json(), key=lambda x: x['position'], reverse=True):
                    if role['name'] != "@everyone" and not role.get('managed') and not role.get('bot_id'):
                        del_res = requests.delete(f"https://discord.com/api/v10/guilds/{target_id}/roles/{role['id']}", headers=headers)
                        if del_res.status_code in [200, 204]:
                            yield f"[-] Deleted role: {role['name']}\n"
                        else:
                            yield f"[!] Could not delete role {role['name']} (Skipped)\n"
                        time.sleep(0.2)

        # 3. Clone Roles in Correct Hierarchical Order
        role_map = {}
        if c_roles:
            yield "[+] Fetching and creating roles in proper order...\n"
            r_roles = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/roles", headers=headers)
            if r_roles.status_code == 200:
                # Sort from lowest position to highest position so hierarchy builds correctly
                source_roles = sorted([r for r in r_roles.json() if not r.get("managed")], key=lambda x: x['position'])
                for role in source_roles:
                    if role['name'] == "@everyone":
                        # Update default @everyone permissions directly
                        requests.patch(f"https://discord.com/api/v10/guilds/{target_id}/roles/{target_id}", headers=headers, json={"permissions": str(role['permissions'])})
                        continue
                        
                    payload = {
                        "name": role['name'],
                        "permissions": str(role['permissions']),
                        "color": int(role.get('color', 0)),
                        "hoist": bool(role.get('hoist', False)),
                        "mentionable": bool(role.get('mentionable', False))
                    }
                    cr = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers, json=payload)
                    if cr.status_code == 429:
                        yield "[!] Rate limited, waiting 5s...\n"
                        time.sleep(5)
                        cr = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers, json=payload)
                        
                    if cr.status_code in [200, 201]:
                        new_role = cr.json()
                        role_map[role['id']] = new_role['id']
                        yield f"[V] Created role: {role['name']}\n"
                    else:
                        yield f"[X] Failed Role {role['name']} (Code: {cr.status_code})\n"
                    time.sleep(0.2)

        # 4. Clone Channels & Categories
        if c_channels:
            yield "[+] Cloning categories and channels...\n"
            r_channels = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/channels", headers=headers)
            if r_channels.status_code == 200:
                channels = r_channels.json()
                categories = [c for c in channels if c['type'] == 4]
                other_channels = [c for c in channels if c['type'] != 4]
                
                cat_map = {}
                for cat in sorted(categories, key=lambda x: x.get('position', 0)):
                    payload = {"name": cat['name'], "type": 4}
                    cc = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers, json=payload)
                    if cc.status_code in [200, 201]:
                        new_cat = cc.json()
                        cat_map[cat['id']] = new_cat['id']
                        yield f"[V] Created Category: {cat['name']}\n"
                    time.sleep(0.2)
                    
                for ch in sorted(other_channels, key=lambda x: x.get('position', 0)):
                    payload = {
                        "name": ch['name'],
                        "type": ch['type'],
                        "topic": ch.get('topic'),
                        "nsfw": ch.get('nsfw', False),
                        "bitrate": ch.get('bitrate'),
                        "user_limit": ch.get('user_limit')
                    }
                    if ch.get('parent_id') in cat_map:
                        payload['parent_id'] = cat_map[ch['parent_id']]
                        
                    ch_create = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers, json=payload)
                    if ch_create.status_code in [200, 201]:
                        yield f"[V] Created Channel: {ch['name']}\n"
                    time.sleep(0.2)

        # 5. Clone Emojis
        if c_emojis:
            yield "[+] Cloning emojis...\n"
            r_emo = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/emojis", headers=headers)
            if r_emo.status_code == 200:
                for emo in r_emo.json():
                    img_res = requests.get(f"https://cdn.discordapp.com/emojis/{emo['id']}.png")
                    if img_res.status_code == 200:
                        b64_img = f"data:image/png;base64,{base64.b64encode(img_res.content).decode('utf-8')}"
                        payload = {"name": emo['name'], "image": b64_img}
                        ce = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/emojis", headers=headers, json=payload)
                        if ce.status_code in [200, 201]:
                            yield f"[V] Cloned Emoji: {emo['name']}\n"
                        time.sleep(0.3)

        # 6. Clone Settings
        if c_settings:
            yield "[+] Cloning server settings...\n"
            r_src = requests.get(f"https://discord.com/api/v10/guilds/{source_id}", headers=headers)
            if r_src.status_code == 200:
                s_data = r_src.json()
                patch_payload = {
                    "name": s_data.get("name"),
                    "verification_level": s_data.get("verification_level"),
                    "default_message_notifications": s_data.get("default_message_notifications"),
                    "explicit_content_filter": s_data.get("explicit_content_filter")
                }
                requests.patch(f"https://discord.com/api/v10/guilds/{target_id}", headers=headers, json=patch_payload)
                yield "[V] Server settings updated successfully!\n"

        yield "\n[+] CLONING PROTOCOL COMPLETED SUCCESSFULLY!</pre><br><a href='/' style='color:#ff1e1e; font-weight:bold;'>← Return to Hub</a></body></html>"

    return Response(generate_stream(), mimetype='text/html')

@app.route("/mass-join", methods=["POST"])
def mass_join():
    if session.get("username") != "aaravg7820133.exe":
        return redirect("/")
    
    guild_id = request.form.get("guild_id")
    bot_token = os.environ.get("BOT_TOKEN", "")
    
    success_count = 0
    for u in AUTHORIZED_USERS:
        url = f"https://discord.com/api/v10/guilds/{guild_id}/members/{u['id']}"
        headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}
        payload = {"access_token": u['token']}
        
        r = requests.put(url, headers=headers, json=payload)
        if r.status_code in [201, 204]:
            success_count += 1
        time.sleep(0.3)
        
    return redirect(f"/mass-join-panel?msg=Successfully forced {success_count} authorized players into server!")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
