import os
import sys
import random
import time
from datetime import datetime

def print_systemd_shutdown_ok(RST, WHT, GRN):
    """画像の表記スタイルを正確に模倣した [  OK  ] 付きシャットダウンログ"""
    
    ok_prefix = f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {WHT}"
    
    logs = [
        "Stopping Network Time Synchronization...",
        "Stopping Update UTMP about System Boot/Shutdown...",
        f"{ok_prefix}Stopped Entropy daemon using the HAVEGE algorithm.{RST}",
        "Stopping Load/Save Random Seed...",
        f"{ok_prefix}Stopped Network Time Synchronization.{RST}",
        f"{ok_prefix}Stopped Update UTMP about System Boot/Shutdown.{RST}",
        f"{ok_prefix}Stopped Create Volatile Files and Directories.{RST}",
        f"{ok_prefix}Stopped target Local File Systems.{RST}",
        "Unmounting /boot/efi...",
        "Unmounting /media/Data...",
        "Unmounting /dev/discord/bot-env...",
        "Unmounting Mount unit for roomba-daemon, revision 10958...",
        f"{ok_prefix}Stopped Load/Save Random Seed.{RST}",
        f"{ok_prefix}Unmounted /boot/efi.{RST}",
        f"{ok_prefix}Unmounted /media/Data.{RST}",
        f"{ok_prefix}Unmounted /dev/discord/bot-env.{RST}",
        f"{ok_prefix}Unmounted Mount unit for roomba-daemon, revision 10958.{RST}",
        f"{ok_prefix}Stopped File System Check on /dev/disk/by-uuid/D4E3-641F.{RST}",
        f"{ok_prefix}Removed slice system-systemd\\x2dfsck.slice.{RST}",
        f"{ok_prefix}Stopped target Local File Systems (Pre).{RST}",
        f"{ok_prefix}Stopped target Swap.{RST}",
        "Deactivating swap /swapfile...",
        f"{ok_prefix}Stopped Create Static Device Nodes in /dev.{RST}",
        f"{ok_prefix}Stopped Create System Users.{RST}",
        f"{ok_prefix}Deactivated swap /swapfile.{RST}",
        f"{ok_prefix}Reached target Unmount All Filesystems.{RST}",
        f"{ok_prefix}Stopped Remount Root and Kernel File Systems.{RST}",
        f"{ok_prefix}Reached target Shutdown.{RST}",
        f"{ok_prefix}Reached target Final Step.{RST}",
        f"{ok_prefix}Finished Power-Off.{RST}",
        f"{ok_prefix}Reached target Power-Off.{RST}"
    ]

    print("\nInitiating System Shutdown Sequence...", flush=True)
    for line in logs:
        time.sleep(0.015)
        print(line, flush=True)

    # 最後の systemd-shutdown タイムスタンプ表示（画像一番下スタイル）
    uptime_sec = round(random.uniform(30000, 40000), 6)
    print(f"{WHT}[{uptime_sec:12.6f}] systemd-shutdown[1]: Syncing filesystems and block devices.{RST}", flush=True)
    print(f"{WHT}[{uptime_sec + 0.000120:12.6f}] systemd-shutdown[1]: Powering off.{RST}\n", flush=True)

def print_normal_boot_sequence(RST, WHT, GRN):
    """Ubuntu 24.04 LTS (Noble Numbat) Boot ログ"""
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
    print(f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {WHT}Started Roomba Control Daemon Service.{RST}", flush=True)
    print(f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {WHT}Connected to Discord Gateway Websocket.{RST}", flush=True)

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

    RST = "\033[0m"
    WHT = "\033[37m"
    GRN = "\033[32m"

    print("::group::Execution Log Summary & System Status", flush=True)

    # 1. 正常終了
    if outcome == "success":
        print_normal_boot_sequence(RST, WHT, GRN)
        print_systemd_shutdown_ok(RST, WHT, GRN)
        print("::endgroup::", flush=True)
        sys.exit(0)

    # 2. 実行キャンセル（[ OK ] 付与でクリーンシャットダウンし exit 0）
    elif outcome == "cancelled":
        print_normal_boot_sequence(RST, WHT, GRN)
        print(f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {WHT}Stopped Roomba Control Daemon Service (SIGTERM/SIGINT processed).{RST}", flush=True)
        print_systemd_shutdown_ok(RST, WHT, GRN)
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
