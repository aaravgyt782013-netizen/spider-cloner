from flask import Flask, request, render_template_string, jsonify
import requests
import time
import threading

app = Flask(__name__)

current_logs = ["System idle. Standing by for command..."]
is_cloning = False

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spidey Cloner v2 | Symbiote Edition</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #050505;
            --panel-bg: #0b0b0e;
            --crimson-red: #8b0000;
            --bright-red: #ff1e1e;
            --glow-red: rgba(255, 30, 30, 0.4);
            --text-main: #e0e0e0;
            --text-muted: #888888;
            --border-dark: #1f1f2e;
        }
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-deep);
            background-image: radial-gradient(circle at 50% 10%, rgba(139, 0, 0, 0.15) 0%, transparent 60%);
            color: var(--text-main);
            margin: 0; padding: 10px; box-sizing: border-box;
        }
        *, *:before, *:after { box-sizing: inherit; }
        .container {
            width: 100%; max-width: 600px; margin: 20px auto;
            background: var(--panel-bg); padding: 20px; border-radius: 12px;
            border: 1px solid var(--crimson-red);
            box-shadow: 0 0 25px rgba(139, 0, 0, 0.25);
        }
        h2 {
            font-family: 'Orbitron', sans-serif; text-align: center;
            color: var(--bright-red); text-shadow: 0 0 10px var(--glow-red);
            font-size: clamp(1.2rem, 4vw, 1.5rem); margin-bottom: 20px;
        }
        label {
            display: block; margin-top: 14px; font-size: 12px;
            font-weight: 600; color: #b3b3b3; text-transform: uppercase;
        }
        input[type="password"], input[type="text"] {
            width: 100%; padding: 12px; margin-top: 6px;
            background: #08080a; color: #fff; border: 1px solid #262636;
            border-radius: 8px; font-size: 14px;
        }
        input:focus { border-color: var(--bright-red); outline: none; }
        .grid-section {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 10px; background: #070709; padding: 12px; border-radius: 8px;
            margin-top: 8px; border: 1px solid var(--border-dark);
        }
        .grid-section label { color: var(--text-main); font-weight: 400; text-transform: none; margin: 0; display: flex; align-items: center; gap: 8px; cursor: pointer; }
        input[type="checkbox"] { accent-color: var(--bright-red); width: 16px; height: 16px; cursor: pointer; }
        button {
            width: 100%; padding: 14px; margin-top: 20px;
            background: linear-gradient(135deg, var(--crimson-red), #5c0000);
            color: white; font-family: 'Orbitron', sans-serif; font-size: 13px;
            font-weight: 700; border-radius: 8px; border: 1px solid var(--bright-red); cursor: pointer;
        }
        button:hover { background: linear-gradient(135deg, #a30000, var(--crimson-red)); box-shadow: 0 0 20px var(--bright-red); }
        .logs-title { font-family: 'Orbitron', sans-serif; font-size: 11px; color: var(--text-muted); margin-top: 20px; }
        pre {
            background: #030304; padding: 12px; border-radius: 8px; height: 180px;
            overflow-y: scroll; color: #ff4d4d; font-family: monospace; font-size: 12px;
            border: 1px solid #1a0000; margin-top: 6px; white-space: pre-wrap; word-break: break-all;
        }
    </style>
    <script>
        function startPolling() {
            setInterval(async () => {
                try {
                    let res = await fetch('/logs');
                    let data = await res.json();
                    let logBox = document.getElementById('log-box');
                    logBox.innerText = data.logs.join('\\n');
                    logBox.scrollTop = logBox.scrollHeight;
                } catch (e) {
                    console.error(e);
                }
            }, 1000);
        }
        window.onload = startPolling;
    </script>
</head>
<body>
    <div class="container">
        <h2>🕷️ SPIDEY CLONER 🕸️</h2>
        <form method="POST" action="/clone">
            <label>User Token</label>
            <input type="password" name="token" required placeholder="Paste your user token...">
            
            <label>Source Guild ID (Copy From)</label>
            <input type="text" name="source_id" required placeholder="Source ID">
            
            <label>Target Guild ID (Paste To)</label>
            <input type="text" name="target_id" required placeholder="Target ID">
            
            <label>Target Destruction (What to Delete First)</label>
            <div class="grid-section">
                <label><input type="checkbox" name="del_channels" checked> Channels</label>
                <label><input type="checkbox" name="del_categories" checked> Categories</label>
                <label><input type="checkbox" name="del_roles"> Roles</label>
            </div>

            <label>Replication Protocol (What to Clone)</label>
            <div class="grid-section">
                <label><input type="checkbox" name="clone_channels" checked> Channels</label>
                <label><input type="checkbox" name="clone_categories" checked> Categories</label>
                <label><input type="checkbox" name="clone_roles"> Roles</label>
                <label><input type="checkbox" name="clone_perms" checked> Overwrites</label>
            </div>
            
            <button type="submit">INITIATE WEB-CLONE</button>
        </form>
        
        <div class="logs-title">SYSTEM OUTPUT LOGS</div>
        <pre id="log-box">Initializing web interface...</pre>
    </div>
</body>
</html>
"""

def log_message(msg):
    global current_logs
    current_logs.append(msg)
    print(msg)

def run_cloning_task(token, source_id, target_id, form_data):
    global is_cloning, current_logs
    is_cloning = True
    current_logs = ["🕸️ Connecting to Discord API..."]

    headers = {"Authorization": token, "Content-Type": "application/json"}
    src_res = requests.get(f"https://discord.com/api/v10/guilds/{source_id}", headers=headers)
    
    if src_res.status_code != 200:
        log_message(f"❌ Error accessing source server: {src_res.text}")
        is_cloning = False
        return
    
    log_message(f"✅ Target Source Acquired: {src_res.json().get('name')}")
    log_message("🧹 Cleaning target server safely...")

    if form_data.get("del_channels") or form_data.get("del_categories"):
        tgt_chan_res = requests.get(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers)
        if tgt_chan_res.status_code == 200:
            for c in tgt_chan_res.json():
                is_cat = (c['type'] == 4)
                if (is_cat and form_data.get("del_categories")) or (not is_cat and form_data.get("del_channels")):
                    requests.delete(f"https://discord.com/api/v10/channels/{c['id']}", headers=headers)
                    log_message(f"🗑️ Deleted {'Category' if is_cat else 'Channel'}: {c['name']}")
                    time.sleep(0.3)

    if form_data.get("del_roles"):
        tgt_roles_res = requests.get(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers)
        if tgt_roles_res.status_code == 200:
            for r in tgt_roles_res.json():
                if r['name'] != "@everyone" and not r.get("managed"):
                    requests.delete(f"https://discord.com/api/v10/guilds/{target_id}/roles/{r['id']}", headers=headers)
                    log_message(f"🗑️ Deleted Role: {r['name']}")
                    time.sleep(0.3)

    role_map = {} # Maps source role ID -> new target role ID
    if form_data.get("clone_roles"):
        log_message("🎭 Cloning Roles in Order...")
        src_roles_res = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/roles", headers=headers)
        if src_roles_res.status_code == 200:
            # Sort roles by position ascending so we create bottom-up or top-down accurately
            roles = sorted(src_roles_res.json(), key=lambda x: x.get('position', 0))
            
            # Find target @everyone role ID first
            tgt_roles_res = requests.get(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers)
            if tgt_roles_res.status_code == 200:
                for tr in tgt_roles_res.json():
                    if tr['name'] == "@everyone":
                        for sr in roles:
                            if sr['name'] == "@everyone":
                                role_map[sr['id']] = tr['id']
                        # Update @everyone permissions immediately
                        for sr in roles:
                            if sr['name'] == "@everyone":
                                requests.patch(f"https://discord.com/api/v10/guilds/{target_id}/roles/{tr['id']}", headers=headers, json={"permissions": str(sr['permissions'])})

            # Create custom roles
            position_payload = []
            for r in roles:
                if r['name'] == "@everyone" or r.get("managed"):
                    continue
                payload = {
                    "name": r['name'], 
                    "permissions": str(r['permissions']),
                    "color": r['color'], 
                    "hoist": r['hoist'], 
                    "mentionable": r['mentionable']
                }
                r_create = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers, json=payload)
                if r_create.status_code == 429:
                    time.sleep(float(r_create.json().get("retry_after", 2)))
                    r_create = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers, json=payload)
                
                if r_create.status_code in [200, 201]:
                    new_role = r_create.json()
                    role_map[r['id']] = new_role['id']
                    position_payload.append({"id": new_role['id'], "position": r['position']})
                    log_message(f"✨ Created Role: {r['name']}")
                time.sleep(0.3)

            # Apply correct hierarchical role sorting sequence
            if position_payload:
                requests.patch(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers, json=position_payload)
                log_message("📋 Applied correct role hierarchy sequence!")

    if form_data.get("clone_channels") or form_data.get("clone_categories"):
        log_message("📁 Cloning Categories & Channels with Permissions...")
        channels_res = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/channels", headers=headers)
        if channels_res.status_code == 200:
            channels = sorted(channels_res.json(), key=lambda x: x.get('position', 0))
            category_map = {}

            # Helper to build permission overwrites mapping source role IDs to target role IDs
            def build_overwrites(channel_obj):
                if not form_data.get("clone_perms") or "permission_overwrites" not in channel_obj:
                    return []
                new_overwrites = []
                for ow in channel_obj["permission_overwrites"]:
                    if ow['type'] == 0: # Role overwrite
                        if ow['id'] in role_map:
                            new_overwrites.append({
                                "id": role_map[ow['id']], 
                                "type": 0, 
                                "allow": str(ow['allow']), 
                                "deny": str(ow['deny'])
                            })
                    elif ow['type'] == 1: # Member overwrite
                        new_overwrites.append({
                            "id": ow['id'], 
                            "type": 1, 
                            "allow": str(ow['allow']), 
                            "deny": str(ow['deny'])
                        })
                return new_overwrites

            # 1. Clone Categories First
            if form_data.get("clone_categories"):
                for c in channels:
                    if c['type'] == 4:
                        payload = {
                            "name": c['name'], 
                            "type": 4,
                            "permission_overwrites": build_overwrites(c)
                        }
                        cr = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers, json=payload)
                        if cr.status_code in [200, 201]:
                            new_cat = cr.json()
                            category_map[c['id']] = new_cat['id']
                            log_message(f"📁 Created Category: {c['name']}")
                        time.sleep(0.3)

            # 2. Clone Channels Next
            if form_data.get("clone_channels"):
                for c in channels:
                    if c['type'] != 4:
                        payload = {
                            "name": c['name'], 
                            "type": c['type'],
                            "topic": c.get("topic"), 
                            "nsfw": c.get("nsfw", False),
                            "bitrate": c.get("bitrate"), 
                            "user_limit": c.get("user_limit"),
                            "permission_overwrites": build_overwrites(c)
                        }
                        if c.get("parent_id") and c["parent_id"] in category_map:
                            payload["parent_id"] = category_map[c["parent_id"]]

                        cr = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers, json=payload)
                        if cr.status_code in [200, 201]:
                            log_message(f"💬 Created Channel: {c['name']}")
                        time.sleep(0.3)

    log_message("🎉 Spider-Cloning complete successfully!")
    is_cloning = False

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/clone", methods=["POST"])
def clone_action():
    global is_cloning
    if is_cloning:
        return "Cloning already in progress!", 400

    token = request.form.get("token")
    source_id = request.form.get("source_id")
    target_id = request.form.get("target_id")
    
    form_data = {
        "del_channels": request.form.get("del_channels"),
        "del_categories": request.form.get("del_categories"),
        "del_roles": request.form.get("del_roles"),
        "clone_channels": request.form.get("clone_channels"),
        "clone_categories": request.form.get("clone_categories"),
        "clone_roles": request.form.get("clone_roles"),
        "clone_perms": request.form.get("clone_perms")
    }

    thread = threading.Thread(target=run_cloning_task, args=(token, source_id, target_id, form_data))
    thread.start()
    
    return """
    <script>
        alert("Cloning initiated successfully!");
        window.location.href = "/";
    </script>
    """

@app.route("/logs")
def get_logs():
    return jsonify({"logs": current_logs, "active": is_cloning})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
