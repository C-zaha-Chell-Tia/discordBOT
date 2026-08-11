import os
import sys
import random
import time
from datetime import datetime

def print_systemd_shutdown():
    """Ubuntu LTS の本物の systemd シャットダウンログを模倣"""
    now = datetime.now().strftime("%b %d %H:%M:%S")
    hostname = "ubuntu"
    
    shutdown_logs = [
        f"{now} {hostname} systemd[1]: Reached target shutdown.target - System Shutdown.",
        f"{now} {hostname} systemd[1]: Reached target final.target - Late Shutdown Services.",
        f"{now} {hostname} systemd[1]: systemd-poweroff.service: Deactivated successfully.",
        f"{now} {hostname} systemd[1]: Finished systemd-poweroff.service - System Power Off.",
        f"{now} {hostname} systemd[1]: Reached target poweroff.target - System Power Off.",
        f"{now} {hostname} systemd[1]: Shutting down.",
        f"{now} {hostname} systemd-shutdown[1]: Syncing filesystems and block devices.",
        f"{now} {hostname} systemd-shutdown[1]: Sending SIGTERM to remaining processes...",
        f"{now} {hostname} systemd-journald[258]: Received SIGTERM from PID 1 (systemd-shutdow).",
        f"{now} {hostname} systemd-journald[258]: Journal stopped"
    ]
    
    print("\nInitiating System Shutdown Sequence...", flush=True)
    for log in shutdown_logs:
        time.sleep(0.02)
        print(log, flush=True)

def print_normal_boot_sequence():
    """Ubuntu 24.04 LTS (Noble Numbat) 起動 (dmesg) ログの模倣"""
    now = datetime.now().strftime("%b %d %H:%M:%S")
    hostname = "ubuntu"
    boot_id = "".join(random.choices("0123456789abcdef", k=32))

    print(f"-- Boot {boot_id} --", flush=True)
    print(f"{now} {hostname} kernel: microcode: microcode updated early to revision 0x22, date = 2024-01-15", flush=True)
    print(f"{now} {hostname} kernel: Linux version 6.8.0-1015-azure (buildd@bos03-amd64-001) (x86_64-linux-gnu-gcc-13) #18-Ubuntu SMP PREEMPT_DYNAMIC", flush=True)
    print(f"{now} {hostname} kernel: Command line: BOOT_IMAGE=/boot/vmlinuz-6.8.0-1015-azure root=/dev/discord/bot-env ro quiet splash", flush=True)
    print(f"{now} {hostname} kernel: BIOS-provided physical RAM map:", flush=True)
    print(f"{now} {hostname} kernel: BIOS-e820: [mem 0x0000000000000000-0x000000000009b3ff] usable", flush=True)
    print(f"{now} {hostname} kernel: BIOS-e820: [mem 0x000000000009b400-0x000000000009ffff] reserved", flush=True)
    print(f"{now} {hostname} kernel: BIOS-e820: [mem 0x0000000000100000-0x000000000fffffff] usable", flush=True)
    print(f"{now} {hostname} kernel: EXT4-fs (discord-bot-env): mounted filesystem with ordered data mode.", flush=True)
    print(f"{now} {hostname} systemd[1]: Started Roomba Control Daemon Service.", flush=True)
    print(f"{now} {hostname} systemd[1]: Connected to Discord Gateway Websocket.", flush=True)

def main():
    step_outcome = os.getenv("STEP_OUTCOME", "")
    step_conclusion = os.getenv("STEP_CONCLUSION", "")
    exit_code_str = os.getenv("BOT_EXIT_CODE", "0")

    try:
        exit_code = int(exit_code_str)
    except ValueError:
        exit_code = 1

    log_content = ""
    if os.path.exists("bot_output.log"):
        with open("bot_output.log", "r", encoding="utf-8", errors="ignore") as f:
            log_content = f.read()

    # 判定
    if step_conclusion == "cancelled" or step_outcome == "cancelled":
        outcome = "cancelled"
    elif exit_code != 0 or "Traceback" in log_content or "Error" in log_content:
        outcome = "failure"
    else:
        outcome = "success"

    print("::group::Execution Log Summary & System Status", flush=True)

    # 1. 正常終了
    if outcome == "success":
        print_normal_boot_sequence()
        print_systemd_shutdown()
        print("::endgroup::", flush=True)
        sys.exit(0)

    # 2. 実行キャンセル（OK判定で正常終了）
    elif outcome == "cancelled":
        now = datetime.now().strftime("%b %d %H:%M:%S")
        print_normal_boot_sequence()
        print(f"{now} ubuntu systemd[1]: Stopping Roomba Control Daemon Service (SIGTERM requested)...", flush=True)
        print_systemd_shutdown()
        print("::endgroup::", flush=True)
        sys.exit(0)

    # 3. エラー時（Kernel Panic）
    else:
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
            err_msg = "Unhandled exception in bot runtime"
            bios_bug = "ACPI: [Firmware Bug]: Your BIOS is broken; FW bug workaround enabled."

        hex_code = f"0x{exit_code & 0xFFFFFFFF:08x}"
        rip_addr = f"0xffffffff81{random.randint(0x100000, 0xFFFFFF):06x}"
        rnd_ino = random.randint(1000000, 9999999)
        rnd_blk = random.randint(10000, 99999)

        print(f"[    0.000000] [Firmware Bug]: ACPI: BIOS _OSI(Linux) query ignored", flush=True)
        print(f"[    0.052144] {bios_bug}", flush=True)
        print(f"[    1.849201] VFS: Cannot open root device \"/dev/discord/bot-env\" error -{exit_code}", flush=True)
        print(f"[    1.849265] Please check system environment; cause: {err_msg}", flush=True)
        print(f"[    1.849312] Kernel panic - not syncing: Unable to mount roomba-bot environment", flush=True)
        print(f"[    1.849400] RIP: 0010:[<{rip_addr}>] {err_module}+0x12/0x80", flush=True)
        print(f"[    1.849420] Call Trace:", flush=True)
        print(f"[    1.849435]  <TASK>", flush=True)
        print(f"[    1.849451]  dump_stack_lvl+0x44/0x5c", flush=True)
        print(f"[    1.849480]  panic+0x118/0x2e4", flush=True)
        print(f"[    1.849509]  {err_module}+0x42/0x1e8", flush=True)
        print(f"[    1.849638]  ret_from_fork+0x1f/0x30", flush=True)
        print(f"[    1.849667]  </TASK>", flush=True)
        print(f"[    2.108432] Kernel panic - not syncing: Attempted to kill roomba-daemon! exitcode={hex_code}", flush=True)
        print(f"[    2.108900] ---[ end Kernel panic - not syncing: Attempted to kill roomba-daemon! exitcode={hex_code} ]---", flush=True)
        print(f"EXT4-fs error: inode #{rnd_ino}, block {rnd_blk}: core dump registered", flush=True)

        print("::endgroup::", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
