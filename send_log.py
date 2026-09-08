import sys
import time
import random
import traceback
import urllib.request
import json
from datetime import datetime

# Terminal Color Codes
RST = "\033[0m"
WHT = "\033[1;37m"
GRN = "\033[1;32m"
RED = "\033[1;31m"
YEL = "\033[1;33m"
BLU = "\033[1;34m"

def log_ubuntu_ok(message: str):
    """Outputs Systemd style [ OK ] log"""
    print(f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {message}", flush=True)

def log_ubuntu_failed(message: str):
    """Outputs Systemd style [ FAILED ] log"""
    print(f"{WHT}[{RST} {RED}FAILED{RST}{WHT}]{RST} {message}", flush=True)

def log_local_detector(message: str):
    """Outputs logs received from the local detector"""
    print(f"{WHT}[{RST} {BLU}LOCAL-DETECTOR{RST}{WHT}]{RST} {message}", flush=True)

async def log_ubuntu_working(message: str, duration: float = 1.8):
    """Simulates Systemd bouncing star animation"""
    import asyncio
    width = 7
    pat_len = 4
    max_pos = width - pat_len
    pos = 0
    direction = 1
    end_time = time.time() + duration
    
    while time.time() < end_time:
        pattern = " " * pos + "*" * pat_len + " " * (max_pos - pos)
        sys.stdout.write(f"\r{WHT}[{RST} {YEL}{pattern}{RST}{WHT}]{RST} {message}")
        sys.stdout.flush()
        await asyncio.sleep(0.08)
        pos += direction
        if pos >= max_pos or pos <= 0:
            direction *= -1
    
    sys.stdout.write(f"\r{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {message}\n")
    sys.stdout.flush()

def show_ubuntu_boot_banner():
    """Prints Ubuntu boot logs on startup"""
    now = datetime.now().strftime("%b %d %H:%M:%S")
    boot_id = "".join(random.choices("0123456789abcdef", k=32))
    print(f"\n-- Boot {boot_id} --", flush=True)
    print(f"{now} ubuntu kernel: Linux version 6.8.0-1015-azure (x86_64-linux-gnu-gcc-13)", flush=True)
    log_ubuntu_ok("Started Roomba Control Daemon Service.")

def print_systemd_shutdown_ok():
    """Full systemd shutdown log sequence"""
    ok_prefix = f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} "
    shutdown_logs = [
        "Stopping Network Time Synchronization...",
        "Stopping Update UTMP about System Boot/Shutdown...",
        f"{ok_prefix}Stopped Entropy daemon using the HAVEGE algorithm.",
        "Stopping Load/Save Random Seed...",
        f"{ok_prefix}Stopped Network Time Synchronization.",
        f"{ok_prefix}Stopped Update UTMP about System Boot/Shutdown.",
        f"{ok_prefix}Stopped Create Volatile Files and Directories.",
        f"{ok_prefix}Stopped target Local File Systems.",
        "Unmounting /boot/efi...",
        "Unmounting /media/Data...",
        "Unmounting /dev/discord/bot-env...",
        "Unmounting Mount unit for roomba-daemon, revision 10958...",
        f"{ok_prefix}Stopped Load/Save Random Seed.",
        f"{ok_prefix}Unmounted /boot/efi.",
        f"{ok_prefix}Unmounted /media/Data.",
        f"{ok_prefix}Unmounted /dev/discord/bot-env.",
        f"{ok_prefix}Unmounted Mount unit for roomba-daemon, revision 10958.",
        f"{ok_prefix}Stopped File System Check on /dev/disk/by-uuid/D4E3-641F.",
        f"{ok_prefix}Removed slice system-systemd\\x2dfsck.slice.",
        f"{ok_prefix}Stopped target Local File Systems (Pre).",
        f"{ok_prefix}Stopped target Swap.",
        "Deactivating swap /swapfile...",
        f"{ok_prefix}Stopped Create Static Device Nodes in /dev.",
        f"{ok_prefix}Stopped Create System Users.",
        f"{ok_prefix}Deactivated swap /swapfile.",
        f"{ok_prefix}Reached target Unmount All Filesystems.",
        f"{ok_prefix}Stopped Remount Root and Kernel File Systems.",
        f"{ok_prefix}Reached target Shutdown.",
        f"{ok_prefix}Reached target Final Step.",
        f"{ok_prefix}Finished Power-Off.",
        f"{ok_prefix}Reached target Power-Off."
    ]
    for log in shutdown_logs:
        if log.startswith(ok_prefix):
            print(log, flush=True)
        else:
            print(f"[      ] {log}", flush=True)

def send_panic_report_to_discord(token: str, channel_id: int, exc_type, exc_value, tb_str):
    """Synchronously sends fatal kernel panic logs to Discord channel without emojis"""
    if not token or not channel_id:
        return

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    
    embed_payload = {
        "embeds": [{
            "title": "[KERNEL PANIC] Fatal System Exception",
            "description": "A fatal exception occurred in the cloud runtime instance. System halted.",
            "color": 15158332,
            "fields": [
                {"name": "Exception Type", "value": f"`{exc_type.__name__}`", "inline": True},
                {"name": "Error Message", "value": f"`{str(exc_value)}`", "inline": True},
                {"name": "Call Trace", "value": f"```python\n{tb_str[-1500:]}\n```", "inline": False}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }]
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(embed_payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception as e:
        print(f"Failed to post panic log to Discord: {e}", file=sys.stderr)

def trigger_kernel_panic(exc_type, exc_value, exc_traceback, token: str = None, channel_id: int = None, exit_code: int = 1):
    """Outputs Kernel Panic logs and notifies Discord"""
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_str = "".join(tb_lines)
    log_content = tb_str

    if "No such file" in log_content or "can't open file" in log_content or "FileNotFoundError" in log_content:
        err_module = "vfs_mount_root_device"
        err_msg = "Cannot locate root entry /dev/discord/bot-env/main.py"
        bios_bug = "ACPI: [Firmware Bug]: Unable to resolve root filesystem block."
    elif "ModuleNotFoundError" in log_content or "ImportError" in log_content:
        err_module = "PyImport_ImportModuleLevelObject"
        err_msg = "Required library dependency missing from environment"
        bios_bug = "ACPI: [Firmware Bug]: Your BIOS is broken; replace hardware immediately."
    elif "LoginFailure" in log_content or "Improper token" in log_content:
        err_module = "discord_auth_login"
        err_msg = "Invalid or expired authentication token"
        bios_bug = "ACPI: [Firmware Bug]: ACPI: BIOS _OSI(Linux) query ignored"
    elif "SyntaxError" in log_content or "IndentationError" in log_content:
        err_module = "PyParser_ASTFromFileObject"
        err_msg = "Invalid python syntax detected before module import"
        bios_bug = "ACPI: [Firmware Bug]: Your BIOS is broken; FW bug workaround enabled."
    else:
        err_module = "roomba_bot_main_crash"
        err_msg = f"Unhandled exception: {exc_value}"
        bios_bug = "ACPI: [Firmware Bug]: Your BIOS is broken; FW bug workaround enabled."

    hex_code = f"0x{exit_code & 0xFFFFFFFF:08x}"
    rip_addr = f"0xffffffff81{random.randint(0x100000, 0xFFFFFF):06x}"
    rnd_ino = random.randint(1000000, 9999999)
    rnd_blk = random.randint(10000, 99999)

    print(f"\n[    0.000000] [Firmware Bug]: ACPI: BIOS _OSI(Linux) query ignored", flush=True)
    print(f"[    0.052144] {bios_bug}", flush=True)
    print(f"[    1.849201] VFS: Cannot open root device \"/dev/discord/bot-env\" error -{exit_code}", flush=True)
    print(f"[    1.849265] Please check system environment; cause: {err_msg}", flush=True)
    print(f"[    1.849312] Kernel panic - not syncing: Unable to mount roomba-bot environment", flush=True)
    print(f"[    1.849400] RIP: 0010:[<{rip_addr}>] {err_module}+0x12/0x80", flush=True)
    print(f"[    1.849420] Call Trace:", flush=True)
    print(f"[    1.849435]  <TASK>", flush=True)
    for line in tb_lines:
        for sub_line in line.strip().split('\n'):
            print(f"[    1.849451]  {sub_line}", flush=True)
    print(f"[    1.849667]  </TASK>", flush=True)
    print(f"[    2.108432] Kernel panic - not syncing: Attempted to kill roomba-daemon! exitcode={hex_code}", flush=True)
    print(f"[    2.108900] ---[ end Kernel panic - not syncing: Attempted to kill roomba-daemon! exitcode={hex_code} ]---", flush=True)
    print(f"EXT4-fs error: inode #{rnd_ino}, block {rnd_blk}: core dump registered", flush=True)

    if token and channel_id:
        send_panic_report_to_discord(token, channel_id, exc_type, exc_value, tb_str)
