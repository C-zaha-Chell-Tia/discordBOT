import os
import sys
import random
import time

def print_shutdown_sequence(RST, WHT, GRN, YEL):
    """シャットダウン（落とす時）のログ表示処理"""
    print("\n" + "=" * 60, flush=True)
    print(" Initiating System Shutdown / Cleanup Sequence...", flush=True)
    print("=" * 60, flush=True)
    
    services = [
        "Unmounting Discord Bot Virtual Filesystem (/dev/discord/bot-env)",
        "Stopping Roomba Control Daemon Service",
        "Disconnecting Active Gateway Websocket Connections",
        "Clearing Local Workspace Cache and Temporary Objects",
        "Sending Final Termination Signal (SIGTERM) to Python Processes",
        "Flushing Pending Log Buffers to Console Output",
        "Deallocating Execution Context and Environment Memory"
    ]
    
    for svc in services:
        time.sleep(0.1)  # ログ出力の演出用ウェイト
        print(f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {WHT}{svc}.{RST}", flush=True)

    print(f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {WHT}Stopped All Background Services.{RST}", flush=True)
    print(f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {WHT}Reached Target System Power-Off / Runner Exit.{RST}", flush=True)
    print("=" * 60 + "\n", flush=True)

def main():
    step_outcome = os.getenv("STEP_OUTCOME", "")
    step_conclusion = os.getenv("STEP_CONCLUSION", "")
    
    if step_conclusion == "cancelled" or step_outcome == "cancelled":
        outcome = "cancelled"
    elif step_conclusion == "success" or step_outcome == "success":
        outcome = "success"
    else:
        outcome = "failure"

    exit_code_str = os.getenv("BOT_EXIT_CODE", "1")
    try:
        exit_code = int(exit_code_str)
    except ValueError:
        exit_code = 1

    log_content = ""
    if os.path.exists("bot_output.log"):
        with open("bot_output.log", "r", encoding="utf-8", errors="ignore") as f:
            log_content = f.read()

    RST = "\033[0m"
    WHT = "\033[37m"
    RED = "\033[31m"
    GRN = "\033[32m"
    YEL = "\033[33m"

    print("::group::Execution Log Summary & System Status", flush=True)

    # 1. 正常終了の場合
    if outcome == "success":
        print(f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {WHT}Roomba Control Daemon completed execution without errors.{RST}", flush=True)
        print_shutdown_sequence(RST, WHT, GRN, YEL)

    # 2. キャンセルの場合
    elif outcome == "cancelled":
        print(f"{WHT}[{RST} {YEL}****{RST}{WHT}]{RST} {WHT}Roomba Control Daemon execution cancelled.{RST}", flush=True)
        print(f"{WHT}[{RST} {YEL} WARN {RST}{WHT}]{RST} {WHT}Received cancellation signal from user or system.{RST}", flush=True)
        print_shutdown_sequence(RST, WHT, GRN, YEL)

    # 3. 異常終了の場合（エラー判定とカーネルパニック風出力）
    else:
        if "SyntaxError" in log_content or "IndentationError" in log_content:
            err_module = "PyParser_ASTFromFileObject"
            err_msg = "Invalid python syntax detected before module import"
            bios_bug = "ACPI: [Firmware Bug]: Your BIOS is broken; FW bug workaround enabled."
        elif "ModuleNotFoundError" in log_content or "ImportError" in log_content:
            err_module = "PyImport_ImportModuleLevelObject"
            err_msg = "Required library dependency missing from environment"
            bios_bug = "ACPI: [Firmware Bug]: Your BIOS is broken; replace hardware immediately."
        elif "LoginFailure" in log_content or "Improper token" in log_content:
            err_module = "discord_auth_login"
            err_msg = "Invalid or expired authentication token"
            bios_bug = "ACPI: [Firmware Bug]: ACPI: BIOS _OSI(Linux) query ignored"
        else:
            err_module = "roomba_bot_main_crash"
            err_msg = "Unhandled exception in bot runtime"
            bios_bug = "ACPI: [Firmware Bug]: Your BIOS is broken; FW bug workaround enabled."

        hex_code = f"0x{exit_code & 0xFFFFFFFF:08x}"
        rip_addr = f"0xffffffff81{random.randint(0x100000, 0xFFFFFF):06x}"
        rnd_ino = random.randint(1000000, 9999999)
        rnd_blk = random.randint(10000, 99999)

        print(f"{WHT}[    0.000000] [Firmware Bug]: ACPI: BIOS _OSI(Linux) query ignored{RST}", flush=True)
        print(f"{WHT}[    0.000000] ACPI BIOS Error (bug): Could not resolve symbol [\\_SB.PCI0._OSC], AE_NOT_FOUND{RST}", flush=True)
        print(f"{WHT}[    0.052144] {bios_bug}{RST}", flush=True)
        print(f"{WHT}[    1.849201] VFS: Cannot open root device \"/dev/discord/bot-env\" or unknown-block(0,0): error -{exit_code}{RST}", flush=True)
        print(f"{WHT}[    1.849265] Please check system environment; cause: {err_msg}{RST}", flush=True)
        print(f"{WHT}[    1.849312] Kernel panic - not syncing: VFS: Unable to mount roomba-bot environment on unknown-block(0,0){RST}", flush=True)
        print(f"{WHT}[    1.849370] CPU: 0 PID: 1 Comm: roomba-bot Not tainted 6.1.0-18-amd64 #1 Debian 6.1.76-1{RST}", flush=True)
        print(f"{WHT}[    1.849400] RIP: 0010:[<{rip_addr}>] {err_module}+0x12/0x80{RST}", flush=True)
        print(f"{WHT}[    1.849420] Call Trace:{RST}", flush=True)
        print(f"{WHT}[    1.849435]  <TASK>{RST}", flush=True)
        print(f"{WHT}[    1.849451]  dump_stack_lvl+0x44/0x5c{RST}", flush=True)
        print(f"{WHT}[    1.849480]  panic+0x118/0x2e4{RST}", flush=True)
        print(f"{WHT}[    1.849509]  {err_module}+0x42/0x1e8{RST}", flush=True)
        print(f"{WHT}[    1.849542]  python_main_entry+0x80/0x100{RST}", flush=True)
        print(f"{WHT}[    1.849574]  python_runtime_init+0x110/0x250{RST}", flush=True)
        print(f"{WHT}[    1.849638]  ret_from_fork+0x1f/0x30{RST}", flush=True)
        print(f"{WHT}[    1.849667]  </TASK>{RST}", flush=True)
        print(f"{WHT}[    2.108432] Kernel panic - not syncing: Attempted to kill roomba-daemon! exitcode={hex_code}{RST}", flush=True)
        print(f"{WHT}[    2.108491] CPU: 2 PID: 1 Comm: roomba-bot Tainted: G        W          6.1.0-18-amd64{RST}", flush=True)
        print(f"{WHT}[    2.108871] Kernel Offset: disabled{RST}", flush=True)
        print(f"{WHT}[    2.108900] ---[ end Kernel panic - not syncing: Attempted to kill roomba-daemon! exitcode={hex_code} ]---{RST}", flush=True)
        print(f"{WHT}[{RST}{RED} FAILED {RST}{WHT}]{RST} {WHT}Failed to start Roomba Control Daemon service.{RST}", flush=True)
        print(f"{WHT}[{RST}{YEL} DEPEND {RST}{WHT}]{RST} {WHT}Dependency failed for Discord Gateway Connection.{RST}", flush=True)
        print(f"{WHT}[{RST}{YEL} DEPEND {RST}{WHT}]{RST} {WHT}Dependency failed for Cleanup Local Workspace Cache.{RST}", flush=True)
        print(f"{WHT}EXT4-fs error (device sda2): ext4_lookup:1845: inode #2: comm roomba-bot: deleted inode referenced: {rnd_ino}{RST}", flush=True)
        print(f"{WHT}EXT4-fs error (device sda2): ext4_dirty_inode:5943: inode #2: block {rnd_blk}: comm discord.py: core dump failed{RST}", flush=True)
        print(f"{WHT}Aborting journal on device sda2-8.{RST}", flush=True)
        print(f"{WHT}EXT4-fs (sda2): Remounting filesystem read-only{RST}", flush=True)

        # 異常時であっても強制的にアンマウント等のシャットダウンシーケンスを実行
        print_shutdown_sequence(RST, WHT, GRN, YEL)

    print("::endgroup::", flush=True)

if __name__ == "__main__":
    main()
