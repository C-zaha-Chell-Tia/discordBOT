import asyncio
import os
import re
import signal
import sys
from datetime import datetime
import aiohttp
from aiohttp import web
import discord
from discord.ext import commands, tasks

import send_log

# ==================================================
# --- Configuration & Environment Variables ---
# ==================================================

RECORD_CHANNEL_ID = 1531955600819359808
LIFETIME_SECONDS = 20700  

# Local PC / LM Studio / Detector Configuration
DETECTOR_URL = os.getenv("DETECTOR_URL")      # e.g., https://xxxx.ngrok-free.app/game-status
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL")    # e.g., https://yyyy.ngrok-free.app/v1/chat/completions
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "rinna/japanese-gpt-neox-3.6b-instruction-ppo")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Character Persona Configuration
BOT_CHARACTER_NAME = os.getenv("BOT_CHARACTER_NAME", "Meteorite")

# Operational hours (Suspended between 23:00 and 06:00)
SLEEP_START_HOUR = 23
SLEEP_END_HOUR = 6

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
shutdown_event = asyncio.Event()

# State Management Flags
is_suspended_by_game = False
is_suspended_by_time = False
detected_game_name = ""
timer_task = None

# Hook unhandled exceptions to kernel panic handler in send_log
sys.excepthook = lambda t, v, tb: send_log.trigger_kernel_panic(
    t, v, tb, token=DISCORD_TOKEN, channel_id=RECORD_CHANNEL_ID
)


# ==================================================
# --- Local Log Receiver (Aiohttp Web Server) ---
# ==================================================

async def handle_local_log(request):
    try:
        data = await request.json()
        log_msg = data.get("log", "")
        if log_msg:
            send_log.log_local_detector(log_msg)
        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400)

async def start_log_server():
    app = web.Application()
    app.router.add_post('/local-log', handle_local_log)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    send_log.log_ubuntu_ok("Local log receiver API started on port 8080.")


# ==================================================
# --- Monitor Tasks (Game Detector & Schedule) ---
# ==================================================

def check_time_sleeping():
    current_hour = datetime.now().hour
    if SLEEP_START_HOUR > SLEEP_END_HOUR:
        return current_hour >= SLEEP_START_HOUR or current_hour < SLEEP_END_HOUR
    else:
        return SLEEP_START_HOUR <= current_hour < SLEEP_END_HOUR

@tasks.loop(seconds=30)
async def monitor_system():
    global is_suspended_by_game, is_suspended_by_time, detected_game_name

    is_suspended_by_time = check_time_sleeping()

    if DETECTOR_URL:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(DETECTOR_URL, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        is_suspended_by_game = data.get("game_running", False)
                        detected_game_name = data.get("game_name", "")
                    else:
                        is_suspended_by_game = False
        except Exception:
            is_suspended_by_game = False

    if is_suspended_by_game:
        await bot.change_presence(
            status=discord.Status.dnd, 
            activity=discord.Game(name=f"Suspended: Game Detected ({detected_game_name})")
        )
    elif is_suspended_by_time:
        await bot.change_presence(
            status=discord.Status.idle, 
            activity=discord.Game(name="Suspended: Out of Operating Hours")
        )
    else:
        await bot.change_presence(
            status=discord.Status.online, 
            activity=discord.Activity(type=discord.ActivityType.listening, name="Mentions")
        )


# ==================================================
# --- AI Engine Integration (rinna Persona / LM Studio) ---
# ==================================================

async def generate_rinna_response(prompt: str) -> str:
    if not LM_STUDIO_URL:
        return "(Error: LM Studio URL is not configured)"

    # 名前は BOT_CHARACTER_NAME を使用し、言動・口調は「りんな」のスタイルを維持
    system_prompt = (
        f"ユーザー: {BOT_CHARACTER_NAME}\n"
        f"システム: あなたの名前は「{BOT_CHARACTER_NAME}」です。"
        "言動やトーン、口調は「りんな」として、親しみやすく明るい友人のような日本語で会話してください。"
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(LM_STUDIO_URL, json=payload, timeout=20) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    return f"(Error: AI Server Response Code {resp.status})"
    except Exception as e:
        send_log.log_ubuntu_failed(f"LM Studio Connection Error: {e}")
        return "(The AI Engine is currently offline or unreachable)"


# ==================================================
# --- Admin Shutdown Utilities ---
# ==================================================

async def scheduled_shutdown_timer(seconds: int, channel: discord.TextChannel):
    """Delayed shutdown task"""
    send_log.log_ubuntu_ok(f"Scheduled shutdown initiated. System will power off in {seconds} seconds.")
    await asyncio.sleep(seconds)
    await channel.send(f"[SYSTEM] Scheduled shutdown timer expired ({seconds}s). Initiating system halt.")
    shutdown_event.set()

def parse_shutdown_command(content: str):
    """
    Parses command type and timer from prompt.
    Returns (is_cmd, mode, seconds)
    """
    cmd = content.strip().lower()

    # Immediate shutdown keywords
    if cmd in ["/shutdown now", "shutdown /s /t 0", "shutdown /s /t0", "halt", "poweroff", "init 0", "shutdown -h now"]:
        return True, "NOW", 0

    # Timer based shutdown patterns
    win_match = re.search(r"shutdown\s+/s\s+/t\s*(\d+)", cmd)
    if win_match:
        return True, "TIMER", int(win_match.group(1))

    linux_match = re.search(r"shutdown\s+-h\s+\+?(\d+)", cmd)
    if linux_match:
        return True, "TIMER", int(linux_match.group(1)) * 60 if "+" in cmd else int(linux_match.group(1))

    return False, None, 0


# ==================================================
# --- Event Handlers & Chat Routine ---
# ==================================================

async def scheduled_graceful_shutdown(delay: int):
    await asyncio.sleep(delay)
    shutdown_event.set()

@bot.event
async def on_ready():
    await start_log_server()
    await send_log.log_ubuntu_working(f"Starting Roomba Control Daemon Service for {bot.user}...", duration=2.0)
    send_log.log_ubuntu_ok("Connected to Discord Gateway Websocket.")
    
    monitor_system.start()
    bot.loop.create_task(scheduled_graceful_shutdown(LIFETIME_SECONDS))

@bot.event
async def on_error(event, *args, **kwargs):
    send_log.log_ubuntu_failed(f"Unhandled error in event '{event}'.")

@bot.event
async def on_message(message: discord.Message):
    global timer_task

    if message.author.bot:
        return

    # Trigger on Mention or DM
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()

        # Check for admin shutdown commands
        is_cmd, mode, delay_sec = parse_shutdown_command(prompt)
        
        if is_cmd:
            # Check Administrator permission
            is_admin = False
            if isinstance(message.author, discord.Member):
                is_admin = message.author.guild_permissions.administrator
            elif isinstance(message.channel, discord.DMChannel):
                is_admin = True  # Allow in Direct Messages

            if not is_admin:
                await message.reply("[ERROR] Permission denied. Required: Administrator privileges.")
                send_log.log_ubuntu_failed(f"Unauthorized shutdown attempt by user: {message.author} (ID: {message.author.id})")
                return

            if mode == "NOW":
                await message.reply("[SYSTEM] Shutdown command accepted. Halting system immediately...")
                send_log.log_ubuntu_ok(f"Immediate shutdown requested by administrator: {message.author}")
                shutdown_event.set()
                return

            elif mode == "TIMER":
                if timer_task and not timer_task.done():
                    timer_task.cancel()
                timer_task = asyncio.create_task(scheduled_shutdown_timer(delay_sec, message.channel))
                await message.reply(f"[SYSTEM] Scheduled shutdown registered. System will halt in {delay_sec} seconds.")
                return

        # Normal Chat Handling
        if is_suspended_by_game:
            await message.reply(f"[WARNING] Currently suspended because a game ({detected_game_name}) is running on the host PC.")
            return
        if is_suspended_by_time:
            await message.reply("[WARNING] Currently suspended due to off-hours operation schedule.")
            return

        if not prompt:
            await message.reply("Say something to me!")
            return

        async with message.channel.typing():
            ai_reply = await generate_rinna_response(prompt)
            await message.reply(ai_reply)
            return

    await bot.process_commands(message)


# ==================================================
# --- Entry Point ---
# ==================================================

async def main():
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN environment variable is not set (Critical)")

    send_log.show_ubuntu_boot_banner()

    loop = asyncio.get_running_loop()

    def signal_handler():
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            signal.signal(sig, lambda s, f: shutdown_event.set())

    bot_task = asyncio.create_task(bot.start(DISCORD_TOKEN))
    shutdown_task = asyncio.create_task(shutdown_event.wait())

    done, pending = await asyncio.wait(
        [bot_task, shutdown_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    if shutdown_event.is_set():
        print(f"{send_log.WHT}[{send_log.RST} {send_log.GRN} OK {send_log.RST}{send_log.WHT}]{send_log.RST} Stopped Roomba Control Daemon Service (SIGTERM/SIGINT processed).", flush=True)
        send_log.print_systemd_shutdown_ok()
        await bot.close()
        sys.exit(0)

    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    if bot_task in done and bot_task.exception():
        raise bot_task.exception()

if __name__ == "__main__":
    try:
        asyncio.run(main())
        sys.exit(0)
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
    except Exception as e:
        send_log.trigger_kernel_panic(type(e), e, e.__traceback__, token=DISCORD_TOKEN, channel_id=RECORD_CHANNEL_ID, exit_code=1)
        sys.exit(1)
