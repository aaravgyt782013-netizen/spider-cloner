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
<head><meta charset="UTF-8"><title>Login</title></head>
<body style="background:#050505;color:#fff;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;">
<a href="https://discord.com/api/oauth2/authorize?client_id={{ client_id }}&redirect_uri={{ redirect_uri }}&response_type=code&scope=identify%20guilds.join" style="padding:15px;background:#8b0000;color:#fff;text-decoration:none;border-radius:8px;font-weight:bold;">LOGIN WITH DISCORD</a>
</body></html>"""

DASHBOARD_PAGE = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Spidey Hub</title></head>
<body style="background:#050505;color:#fff;font-family:sans-serif;padding:30px;">
<h2>Spidey Hub - Logged in as {{ username }}</h2>
<form method="POST" action="/clone" target="_blank">
    <label>Token:</label><br><input type="password" name="token" required style="width:100%;padding:10px;margin:5px 0;"><br>
    <label>Source ID:</label><br><input type="text" name="source_id" required style="width:100%;padding:10px;margin:5px 0;"><br>
    <label>Target ID:</label><br><input type="text" name="target_id" required style="width:100%;padding:10px;margin:5px 0;"><br>
    <input type="hidden" name="delete_channels" value="on">
    <input type="hidden" name="delete_roles" value="on">
    <input type="hidden" name="clone_channels" value="on">
    <input type="hidden" name="clone_roles" value="on">
    <input type="hidden" name="clone_emojis" value="on">
    <input type="hidden" name="clone_settings" value="on">
    <button type="submit" style="padding:15px;background:#8b0000;color:#fff;width:100%;margin-top:15px;font-weight:bold;cursor:pointer;">START CLONING</button>
</form>
</body></html>"""

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
    return render_template_string(DASHBOARD_PAGE, username=session.get("username", "Agent"))

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code: return redirect("/")
    res = requests.post("https://discord.com/api/oauth2/token", data={
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code", "code": code, "redirect_uri": get_redirect_uri()
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if res.status_code == 200:
        t_data = res.json()
        session["user_token"] = t_data.get("access_token")
        u_res = requests.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {t_data.get('access_token')}"})
        if u_res.status_code == 200:
            session["username"] = u_res.json().get("username")
    return redirect("/")

@app.route("/clone", methods=["POST"])
def clone_server():
    token = request.form.get("token")
    source_id = request.form.get("source_id")
    target_id = request.form.get("target_id")
    headers = {"Authorization": token, "Content-Type": "application/json"}
    
    def generate():
        yield "<html><body style='background:#050505;color:#00ffcc;font-family:monospace;padding:20px;'><pre>"
        
        # Delete Channels
        yield "[+] Deleting channels...\n"
        r = requests.get(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers)
        if r.status_code == 200:
            for ch in r.json():
                requests.delete(f"https://discord.com/api/v10/channels/{ch['id']}", headers=headers)
                time.sleep(0.05)

        # Delete Roles (Top-down deletion to prevent hierarchy locks)
        yield "[+] Deleting roles...\n"
        r = requests.get(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers)
        if r.status_code == 200:
            for role in sorted(r.json(), key=lambda x: x['position'], reverse=True):
                if role['name'] != "@everyone" and not role.get('managed') and not role.get('bot_id'):
                    requests.delete(f"https://discord.com/api/v10/guilds/{target_id}/roles/{role['id']}", headers=headers)
                    time.sleep(0.05)

        # Clone Roles
        yield "[+] Cloning roles...\n"
        r = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/roles", headers=headers)
        if r.status_code == 200:
            for role in sorted([x for x in r.json() if not x.get("managed")], key=lambda x: x['position']):
                if role['name'] == "@everyone":
                    requests.patch(f"https://discord.com/api/v10/guilds/{target_id}/roles/{target_id}", headers=headers, json={"permissions": str(role['permissions'])})
                    continue
                payload = {
                    "name": role['name'], "permissions": str(role['permissions']),
                    "color": int(role.get('color', 0)), "hoist": bool(role.get('hoist', False)),
                    "mentionable": bool(role.get('mentionable', False))
                }
                requests.post(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers, json=payload)
                time.sleep(0.1)

        # Clone Channels
        yield "[+] Cloning channels...\n"
        r = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/channels", headers=headers)
        if r.status_code == 200:
            channels = r.json()
            cat_map = {}
            for cat in sorted([c for c in channels if c['type'] == 4], key=lambda x: x.get('position', 0)):
                res = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers, json={"name": cat['name'], "type": 4})
                if res.status_code in [200, 201]:
                    cat_map[cat['id']] = res.json()['id']
                time.sleep(0.1)
            for ch in sorted([c for c in channels if c['type'] != 4], key=lambda x: x.get('position', 0)):
                payload = {"name": ch['name'], "type": ch['type'], "topic": ch.get('topic'), "nsfw": ch.get('nsfw', False)}
                if ch.get('parent_id') in cat_map:
                    payload['parent_id'] = cat_map[ch['parent_id']]
                requests.post(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers, json=payload)
                time.sleep(0.1)

        yield "\n[+] CLONING COMPLETE!</pre></body></html>"

    return Response(generate(), mimetype='text/html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
