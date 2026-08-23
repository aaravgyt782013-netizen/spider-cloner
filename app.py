from flask import Flask, render_template, request, Response
import requests
import time

app = Flask(__name__)

def log_stream(data):
    token = data.get("token")
    source_id = data.get("source_id")
    target_id = data.get("target_id")
    
    headers = {"Authorization": token, "Content-Type": "application/json"}
    
    yield "🕸️ Connecting to Discord API...\n"

    # 1. Fetch Source Data
    src_res = requests.get(f"https://discord.com/api/v10/guilds/{source_id}", headers=headers)
    if src_res.status_code != 200:
        yield f"❌ Error accessing source server: {src_res.text}\n"
        return
    yield f"✅ Target Source Acquired: {src_res.json().get('name')}\n"

    # 2. Handle Deletions in Target Server
    yield "🧹 Cleaning target server based on preferences...\n"
    
    # Delete Target Channels & Categories if checked
    if data.get("del_channels") or data.get("del_categories"):
        tgt_chan_res = requests.get(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers)
        if tgt_chan_res.status_code == 200:
            for c in tgt_chan_res.json():
                is_cat = (c['type'] == 4)
                if (is_cat and data.get("del_categories")) or (not is_cat and data.get("del_channels")):
                    del_res = requests.delete(f"https://discord.com/api/v10/channels/{c['id']}", headers=headers)
                    if del_res.status_code in [200, 204]:
                        yield f"🗑️ Deleted {'Category' if is_cat else 'Channel'}: {c['name']}\n"
                    time.sleep(0.5)

    # Delete Target Roles if checked
    if data.get("del_roles"):
        tgt_roles_res = requests.get(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers)
        if tgt_roles_res.status_code == 200:
            for r in tgt_roles_res.json():
                if r['name'] != "@everyone" and not r.get("managed"):
                    r_del = requests.delete(f"https://discord.com/api/v10/guilds/{target_id}/roles/{r['id']}", headers=headers)
                    if r_del.status_code in [204]:
                        yield f"🗑️ Deleted Role: {r['name']}\n"
                    time.sleep(0.5)

    # 3. Clone Roles first if checked (needed for role-based permission overwrites)
    role_map = {} # Maps source role IDs to newly created target role IDs
    if data.get("clone_roles"):
        yield "🎭 Cloning Roles...\n"
        src_roles_res = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/roles", headers=headers)
        if src_roles_res.status_code == 200:
            # Sort roles by position descending/ascending safely
            roles = sorted(src_roles_res.json(), key=lambda x: x.get('position', 0))
            for r in roles:
                if r['name'] == "@everyone" or r.get("managed"):
                    continue # Skip default/bot integration roles
                
                payload = {
                    "name": r['name'],
                    "permissions": r['permissions'],
                    "color": r['color'],
                    "hoist": r['hoist'],
                    "mentionable": r['mentionable']
                }
                r_create = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/roles", headers=headers, json=payload)
                if r_create.status_code in [200, 201]:
                    new_role = r_create.json()
                    role_map[r['id']] = new_role['id']
                    yield f"✨ Created Role: {r['name']}\n"
                time.sleep(0.5)

    # 4. Clone Categories and Channels
    if data.get("clone_channels") or data.get("clone_categories"):
        yield "📁 Cloning Categories & Channels...\n"
        channels_res = requests.get(f"https://discord.com/api/v10/guilds/{source_id}/channels", headers=headers)
        if channels_res.status_code == 200:
            channels = sorted(channels_res.json(), key=lambda x: x.get('position', 0))
            category_map = {}

            # First pass: Create categories
            if data.get("clone_categories"):
                for c in channels:
                    if c['type'] == 4: # Category
                        payload = {"name": c['name'], "type": 4}
                        cr = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers, json=payload)
                        if cr.status_code in [200, 201]:
                            new_cat = cr.json()
                            category_map[c['id']] = new_cat['id']
                            yield f"📁 Created Category: {c['name']}\n"
                        time.sleep(0.5)

            # Second pass: Create channels and map permission overwrites if selected
            if data.get("clone_channels"):
                for c in channels:
                    if c['type'] != 4: # Text or Voice
                        payload = {
                            "name": c['name'],
                            "type": c['type'],
                            "topic": c.get("topic"),
                            "nsfw": c.get("nsfw", False),
                            "bitrate": c.get("bitrate"),
                            "user_limit": c.get("user_limit")
                        }

                        if c.get("parent_id") and c["parent_id"] in category_map:
                            payload["parent_id"] = category_map[c["parent_id"]]

                        # Map permission overwrites if enabled
                        if data.get("clone_perms") and "permission_overwrites" in c:
                            new_overwrites = []
                            for ow in c["permission_overwrites"]:
                                # If it's a role overwrite, map it to the newly created target role ID
                                if ow['type'] == 0 and ow['id'] in role_map:
                                    new_overwrites.append({
                                        "id": role_map[ow['id']],
                                        "type": 0,
                                        "allow": ow['allow'],
                                        "deny": ow['deny']
                                    })
                                elif ow['type'] == 1: # Member overwrite
                                    new_overwrites.append({
                                        "id": ow['id'],
                                        "type": 1,
                                        "allow": ow['allow'],
                                        "deny": ow['deny']
                                    })
                            payload["permission_overwrites"] = new_overwrites

                        cr = requests.post(f"https://discord.com/api/v10/guilds/{target_id}/channels", headers=headers, json=payload)
                        if cr.status_code in [200, 201]:
                            yield f"💬 Created Channel: {c['name']}\n"
                        time.sleep(0.5)

    yield "🎉 Spider-Cloning complete! All web lines secured.\n"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/clone", methods=["POST"])
def clone():
    return Response(log_stream(request.json), mimetype='text/plain')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

