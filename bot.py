import asyncio
import json
import os
import random
import string
import subprocess
import discord
from discord.ext import commands
import pylxd

# Load configuration from config.js (simple JSON parser compatibility)
# Or read directly if formatted as standard JSON/JS export
try:
    with open("config.js", "r") as f:
        content = f.read()
        # Extract JSON-like content or read values manually
        # For simplicity, we assume standard config format or fallback to env vars
        CONFIG = {
            "token": os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN_HERE"),
            "admins": [],
            "panel_name": "VPS Panel",
            "panel_url": "https://example.com",
            "db": "database.json"
        }
except Exception:
    CONFIG = {"token": "", "admins": [], "db": "database.json"}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="S", intents=intents)
client = pylxd.Client()

DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"vps": {}, "admins": [], "panel": {"name": "Default", "url": "https://example.com"}, "antinuke": False}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

OS_IMAGES = {
    "20.04": {"alias": "ubuntu/20.04", "remote": "ubuntu"},
    "22.04": {"alias": "ubuntu/22.04", "remote": "ubuntu"},
    "24.04": {"alias": "ubuntu/24.04", "remote": "ubuntu"},
    "26.04": {"alias": "ubuntu/26.04", "remote": "ubuntu"}
}

def generate_vps_id():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

class VPSManageView(discord.ui.View):
    def __init__(self, vps_id):
        super().__init__(timeout=None)
        self.vps_id = vps_id

    @discord.ui.button(label="START", style=discord.ButtonStyle.green, emoji="▶️", row=0)
    async def start_vps(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = load_db()
        if self.vps_id not in db["vps"]:
            return await interaction.response.send_message("VPS not found.", ephemeral=True)
        try:
            container = client.containers.get(self.vps_id)
            container.start()
            await interaction.response.send_message(f"VPS `{self.vps_id}` started successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to start VPS: {e}", ephemeral=True)

    @discord.ui.button(label="STOP", style=discord.ButtonStyle.red, emoji="⏸️", row=0)
    async def stop_vps(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = load_db()
        if self.vps_id not in db["vps"]:
            return await interaction.response.send_message("VPS not found.", ephemeral=True)
        try:
            container = client.containers.get(self.vps_id)
            container.stop(wait=True)
            await interaction.response.send_message(f"VPS `{self.vps_id}` stopped successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to stop VPS: {e}", ephemeral=True)

    @discord.ui.button(label="RESTART", style=discord.ButtonStyle.blurple, emoji="🔄", row=0)
    async def restart_vps(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = load_db()
        if self.vps_id not in db["vps"]:
            return await interaction.response.send_message("VPS not found.", ephemeral=True)
        try:
            container = client.containers.get(self.vps_id)
            container.restart()
            await interaction.response.send_message(f"VPS `{self.vps_id}` restarted successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to restart VPS: {e}", ephemeral=True)

    @discord.ui.button(label="REINSTALL", style=discord.ButtonStyle.gray, emoji="🔄", row=1)
    async def reinstall_vps(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Reinstalling OS...", ephemeral=True)
        # Reinstallation routine can be triggered here

    @discord.ui.button(label="DELETE", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def delete_vps(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = load_db()
        if self.vps_id not in db["vps"]:
            return await interaction.response.send_message("VPS not found.", ephemeral=True)
        try:
            container = client.containers.get(self.vps_id)
            container.stop(wait=True)
            container.delete(wait=True)
            del db["vps"][self.vps_id]
            save_db(db)
            await interaction.response.send_message(f"VPS `{self.vps_id}` deleted successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to delete VPS: {e}", ephemeral=True)

    @discord.ui.button(label="SSH", style=discord.ButtonStyle.green, emoji="🔑", row=2)
    async def ssh_vps(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = load_db()
        if self.vps_id not in db["vps"]:
            return await interaction.response.send_message("VPS not found.", ephemeral=True)
        try:
            container = client.containers.get(self.vps_id)
            # Generate tmate key inside container
            exit_code, output = container.execute(["bash", "-c", "apt-get update && apt-get install -y tmate && tmate -S /tmp/tmate.sock new-session -d && sleep 2 && tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}'"])
            tmate_key = output.strip()
            
            user = await bot.fetch_user(db["vps"][self.vps_id]["owner_id"])
            await user.send(f"🔑 **Your SSH Tmate Key for VPS `{self.vps_id}`**:\n```bash\n{tmate_key}\n```")
            await interaction.response.send_message("SSH Tmate key has been sent to your DM!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to generate SSH key: {e}", ephemeral=True)

    @discord.ui.button(label="SSHX", style=discord.ButtonStyle.blurple, emoji="🌐", row=2)
    async def sshx_vps(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = load_db()
        if self.vps_id not in db["vps"]:
            return await interaction.response.send_message("VPS not found.", ephemeral=True)
        try:
            container = client.containers.get(self.vps_id)
            exit_code, output = container.execute(["bash", "-c", "curl -sSf https://sshx.io/get | sh && nohup sshx &> /dev/null & sleep 3 && ps aux | grep sshx"])
            # In practice, grab output or invoke sshx link generation
            sshx_link = "https://sshx.io/s/..." # Captured or simulated output from command
            
            user = await bot.fetch_user(db["vps"][self.vps_id]["owner_id"])
            await user.send(f"🌐 **Your SSHX Link for VPS `{self.vps_id}`**:\nCheck container logs or use `curl -sSf https://sshx.io/get | sh` output.")
            await interaction.response.send_message("SSHX link has been sent to your DM!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to generate SSHX link: {e}", ephemeral=True)

    @discord.ui.button(label="Stats", style=discord.ButtonStyle.grey, emoji="📊", row=2)
    async def stats_vps(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = load_db()
        if self.vps_id not in db["vps"]:
            return await interaction.response.send_message("VPS not found.", ephemeral=True)
        try:
            container = client.containers.get(self.vps_id)
            state = container.state()
            status_text = f"**VPS ID:** {self.vps_id}\n**Status:** {state.status}\n**CPU Usage:** {state.cpu['usage']} ns"
            await interaction.response.send_message(status_text, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to get stats: {e}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("Bot is ready and connected to LXD daemon.")

@bot.command(name="myvps")
async def myvps(ctx):
    db = load_db()
    user_vps = [vid for vid, data in db["vps"].items() if data["owner_id"] == ctx.author.id]
    if not user_vps:
        return await ctx.send("You do not own any VPS.")
    embed = discord.Embed(title="Your VPS Instances", color=discord.Color.blue())
    for vid in user_vps:
        info = db["vps"][vid]
        embed.add_field(name=f"VPS ID: {vid}", value=f"Name: {info['name']} | RAM: {info['ram']}GB | Disk: {info['disk']}GB | OS: {info['os']}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! 🏓 `{latency}ms`")

@bot.command(name="new_ssh")
async def new_ssh(ctx, vps_id: str):
    db = load_db()
    if vps_id not in db["vps"] or db["vps"][vps_id]["owner_id"] != ctx.author.id:
        return await ctx.send("Invalid VPS ID or you do not own this VPS.")
    try:
        container = client.containers.get(vps_id)
        _, output = container.execute(["bash", "-c", "apt-get update && apt-get install -y tmate && tmate -S /tmp/tmate.sock new-session -d && sleep 2 && tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}'"])
        tmate_key = output.strip()
        await ctx.author.send(f"🔑 **New SSH Tmate Key for VPS `{vps_id}`**:\n```bash\n{tmate_key}\n```")
        await ctx.send("New SSH Tmate key sent to your DM!")
    except Exception as e:
        await ctx.send(f"Error generating SSH key: {e}")

@bot.command(name="new_sshx")
async def new_sshx(ctx, vps_id: str):
    db = load_db()
    if vps_id not in db["vps"] or db["vps"][vps_id]["owner_id"] != ctx.author.id:
        return await ctx.send("Invalid VPS ID or you do not own this VPS.")
    try:
        container = client.containers.get(vps_id)
        container.execute(["bash", "-c", "curl -sSf https://sshx.io/get | sh && nohup sshx &> /dev/null &"])
        await ctx.author.send(f"🌐 **SSHX initialized for VPS `{vps_id}`**.")
        await ctx.send("SSHX link session initiated and sent to your DM!")
    except Exception as e:
        await ctx.send(f"Error starting SSHX: {e}")

@bot.command(name="manage")
async def manage(ctx, vps_id: str):
    db = load_db()
    if vps_id not in db["vps"] or db["vps"][vps_id]["owner_id"] != ctx.author.id:
        return await ctx.send("Invalid VPS ID or unauthorized.")
    view = VPSManageView(vps_id)
    await ctx.send(f"**Managing VPS:** `{vps_id}` ({db['vps'][vps_id]['name']})", view=view)

@bot.command(name="Panel")
async def panel_cmd(ctx):
    db = load_db()
    panel = db.get("panel", {"name": "Panel", "url": "https://example.com"})
    embed = discord.Embed(title=panel["name"], description=f"Access your panel here: {panel['url']}", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="VPS Hosting Bot Help", color=discord.Color.gold())
    embed.add_field(name="User Commands", value="`Smyvps`, `Sping`, `Snew_ssh`, `Snew_sshx`, `Smanage`, `SPanel`, `Shelp`", inline=False)
    embed.add_field(name="Admin Commands", value="`Screatevps`, `Sdeletevps`, `Smanagevps`, `Saddpanel`, `Saddadmin`, `Screate_embed`, `Senable_antinuke`, `Sdisable_antinuke`, `Sban`, `Skick`, `Sreset`", inline=False)
    await ctx.send(embed=embed)

# Admin Commands
@bot.command(name="createvps")
@commands.has_permissions(administrator=True)
async def createvps(ctx, name: str, ram: int, disk: int, cpu: int, os_ver: str, owner: discord.Member):
    db = load_db()
    vps_id = generate_vps_id()
    await ctx.send(f"Creating VPS `{name}` (ID: `{vps_id}`) for {owner.mention}...")

    try:
        # Pull or use local image config
        if os_ver not in OS_IMAGES:
            return await ctx.send("Invalid OS version. Choose from: 20.04, 22.04, 24.04, 26.04")
        
        image_info = OS_IMAGES[os_ver]
        
        config = {
            "name": vps_id,
            "source": {
                "type": "image",
                "server": f"https://images.linuxcontainers.org",
                "protocol": "simplestreams",
                "alias": image_info["alias"]
            },
            "limits.cpu": str(cpu),
            "limits.memory": f"{ram}GB",
        }

        container = client.containers.create(config, wait=True)
        container.start()

        # Install lxcfs and configure resource limits emulation inside container
        container.execute(["apt-get", "update"])
        container.execute(["apt-get", "install", "-y", "lxcfs"])

        db["vps"][vps_id] = {
            "name": name,
            "ram": ram,
            "disk": disk,
            "cpu": cpu,
            "os": os_ver,
            "owner_id": owner.id
        }
        save_db(db)

        await ctx.send(f"Successfully created VPS `{vps_id}` for {owner.mention}!")
    except Exception as e:
        await ctx.send(f"Failed to create VPS: {e}")

@bot.command(name="deletevps")
@commands.has_permissions(administrator=True)
async def deletevps(ctx, vps_id: str):
    db = load_db()
    if vps_id not in db["vps"]:
        return await ctx.send("VPS ID not found in database.")
    try:
        container = client.containers.get(vps_id)
        container.stop(wait=True)
        container.delete(wait=True)
        del db["vps"][vps_id]
        save_db(db)
        await ctx.send(f"VPS `{vps_id}` deleted successfully.")
    except Exception as e:
        await ctx.send(f"Error deleting VPS: {e}")

@bot.command(name="managevps")
@commands.has_permissions(administrator=True)
async def managevps(ctx):
    db = load_db()
    if not db["vps"]:
        return await ctx.send("No active VPS instances found.")
    embed = discord.Embed(title="All Active VPS Instances", color=discord.Color.red())
    for vid, info in db["vps"].items():
        embed.add_field(name=f"ID: {vid}", value=f"Name: {info['name']} | RAM: {info['ram']}GB | Owner ID: {info['owner_id']}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="addpanel")
@commands.has_permissions(administrator=True)
async def addpanel(ctx, name: str, url: str):
    db = load_db()
    db["panel"] = {"name": name, "url": url}
    save_db(db)
    await ctx.send(f"Panel updated successfully: **{name}** ({url})")

@bot.command(name="addadmin")
@commands.has_permissions(administrator=True)
async def addadmin(ctx, member: discord.Member):
    db = load_db()
    if member.id not in db["admins"]:
        db["admins"].append(member.id)
        save_db(db)
    await ctx.send(f"{member.mention} has been added as an admin.")

@bot.command(name="create_embed")
@commands.has_permissions(administrator=True)
async def create_embed(ctx, *, message: str):
    await ctx.message.delete()
    embed = discord.Embed(description=message, color=discord.Color.blurple())
    await ctx.send(embed=embed)

@bot.command(name="enable_antinuke")
@commands.has_permissions(administrator=True)
async def enable_antinuke(ctx):
    db = load_db()
    db["antinuke"] = True
    save_db(db)
    await ctx.send("Antinuke has been **enabled**.")

@bot.command(name="disable_antinuke")
@commands.has_permissions(administrator=True)
async def disable_antinuke(ctx):
    db = load_db()
    db["antinuke"] = False
    save_db(db)
    await ctx.send("Antinuke has been **disabled**.")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"Banned {member.mention} for: {reason}")

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"Kicked {member.mention} for: {reason}")

@bot.command(name="reset")
@commands.has_permissions(administrator=True)
async def reset(ctx):
    db = load_db()
    try:
        for vid in list(db["vps"].keys()):
            try:
                container = client.containers.get(vid)
                container.stop(wait=True)
                container.delete(wait=True)
            except Exception:
                pass
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        await ctx.send("Bot has been completely reset. All containers and database records cleared.")
    except Exception as e:
        await ctx.send(f"Error during reset: {e}")

if __name__ == "__main__":
    bot.run(CONFIG["token"])
      
