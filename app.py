from flask import Flask, request, render_template_string
import requests
import time

app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spidey Cloner v2</title>
    <style>
        body { background: #050505; color: #e0e0e0; font-family: sans-serif; padding: 20px; }
        .container { max-width: 500px; margin: auto; background: #0b0b0e; padding: 20px; border-radius: 8px; border: 1px solid #8b0000; }
        input, button { width: 100%; padding: 10px; margin-top: 10px; background: #111; color: #fff; border: 1px solid #333; border-radius: 5px; }
        button { background: #8b0000; font-weight: bold; cursor: pointer; }
        pre { background: #000; padding: 10px; height: 150px; overflow-y: scroll; color: #ff4d4d; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🕷️ SPIDEY CLONER 🕸️</h2>
        <form method="POST" action="/">
            <label>User Token</label>
            <input type="password" name="token" required placeholder="User token...">
            
            <label>Source Guild ID</label>
            <input type="text" name="source_id" required placeholder="Source ID">
            
            <label>Target Guild ID</label>
            <input type="text" name="target_id" required placeholder="Target ID">

            <div style="margin-top: 10px;">
                <label><input type="checkbox" name="del_channels" checked> Delete Channels</label><br>
                <label><input type="checkbox" name="clone_channels" checked> Clone Channels</label>
            </div>
            
            <button type="submit">START CLONING</button>
        </form>
        
        <h3>Logs:</h3>
        <pre>{{ logs | join('\\n') if logs else "Idle..." }}</pre>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    logs = None
    if request.method == "POST":
        token = request.form.get("token")
        source_id = request.form.get("source_id")
        target_id = request.form.get("target_id")
        
        headers = {"Authorization": token, "Content-Type": "application/json"}
        logs = ["🕸️ Connecting to Discord API..."]

        src_res = requests.get(f"https://discord.com/api/v10/guilds/{source_id}", headers=headers)
        if src_res.status_code != 200:
            logs.append(f"❌ Error accessing source: {src_res.text}")
            return render_template_string(HTML_TEMPLATE, logs=logs)
        
        logs.append(f"✅ Source Acquired: {src_res.json().get('name')}")
        
        if request.form.get("del_channels"):
            tgt_chan = requests.get(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers)
            if tgt_chan.status_code == 200:
                for c in tgt_chan.json():
                    if c['type'] != 4:
                        requests.delete(f"https://discord.com/api/v10/channels/{c['id']}", headers=headers)
                        logs.append(f"🗑️ Deleted Channel: {c['name']}")
                        time.sleep(0.3)

        if request.form.get("clone_channels"):
            channels = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/channels", headers=headers).json()
            for c in channels:
                if c['type'] != 4:
                    payload = {"name": c['name'], "type": c['type'], "topic": c.get("topic")}
                    cr = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers, json=payload)
                    if cr.status_code in [200, 201]:
                        logs.append(f"💬 Created Channel: {c['name']}")
                    time.sleep(0.3)

        logs.append("🎉 Done!")
    return render_template_string(HTML_TEMPLATE, logs=logs)

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
