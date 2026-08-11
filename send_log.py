import os
import sys
import random
import time

def print_shutdown_sequence(RST, WHT, GRN, YEL):
    """正常時・キャンセル時のみ出力するシャットダウン処理"""
    print("\nInitiating System Shutdown / Cleanup Sequence...", flush=True)
    
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
        time.sleep(0.05)
        print(f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {WHT}{svc}.{RST}", flush=True)

    print(f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {WHT}Stopped All Background Services.{RST}", flush=True)
    print(f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {WHT}Reached Target System Power-Off / Runner Exit.{RST}\n", flush=True)

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
    RED = "\033[31m"
    GRN = "\033[32m"
    YEL = "\033[33m"

    print("::group::Execution Log Summary & System Status", flush=True)

    # 1. 正常終了
    if outcome == "success":
        print(f"{WHT}[{RST} {GRN} OK {RST}{WHT}]{RST} {WHT}Roomba Control Daemon completed execution without errors.{RST}", flush=True)
        print_shutdown_sequence(RST, WHT, GRN, YEL)
        print("::endgroup::", flush=True)
        sys.exit(0)

    # 2. 手動キャンセル
    elif outcome == "cancelled":
        print(f"{WHT}[{RST} {YEL}****{RST}{WHT}]{RST} {WHT}Roomba Control Daemon execution cancelled by user or runner.{RST}", flush=True)
        print(f"{WHT}[{RST} {YEL} WARN {RST}{WHT}]{RST} {WHT}SIGTERM/SIGINT received. Safe cancellation sequence initiated.{RST}", flush=True)
        print_shutdown_sequence(RST, WHT, GRN, YEL)
        print("::endgroup::", flush=True)
        sys.exit(1)

    # 3. エラー（本家 Linux カーネルパニック構文のみを出力）
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

        # 本家 Linux Kernel Panic 構文
        print(f"{WHT}[    0.000000] [Firmware Bug]: ACPI: BIOS _OSI(Linux) query ignored{RST}", flush=True)
        print(f"{WHT}[    0.052144] {bios_bug}{RST}", flush=True)
        print(f"{WHT}[    1.849201] VFS: Cannot open root device \"/dev/discord/bot-env\" error -{exit_code}{RST}", flush=True)
        print(f"{WHT}[    1.849265] Please check system environment; cause: {err_msg}{RST}", flush=True)
        print(f"{WHT}[    1.849312] Kernel panic - not syncing: Unable to mount roomba-bot environment{RST}", flush=True)
        print(f"{WHT}[    1.849400] RIP: 0010:[<{rip_addr}>] {err_module}+0x12/0x80{RST}", flush=True)
        print(f"{WHT}[    1.849420] Call Trace:{RST}", flush=True)
        print(f"{WHT}[    1.849435]  <TASK>{RST}", flush=True)
        print(f"{WHT}[    1.849451]  dump_stack_lvl+0x44/0x5c{RST}", flush=True)
        print(f"{WHT}[    1.849480]  panic+0x118/0x2e4{RST}", flush=True)
        print(f"{WHT}[    1.849509]  {err_module}+0x42/0x1e8{RST}", flush=True)
        print(f"{WHT}[    1.849638]  ret_from_fork+0x1f/0x30{RST}", flush=True)
        print(f"{WHT}[    1.849667]  </TASK>{RST}", flush=True)
        print(f"{WHT}[    2.108432] Kernel panic - not syncing: Attempted to kill roomba-daemon! exitcode={hex_code}{RST}", flush=True)
        print(f"{WHT}[    2.108900] ---[ end Kernel panic - not syncing: Attempted to kill roomba-daemon! exitcode={hex_code} ]---{RST}", flush=True)
        print(f"{WHT}EXT4-fs error: inode #{rnd_ino}, block {rnd_blk}: core dump registered{RST}", flush=True)

        print("::endgroup::", flush=True)

        # 正常処理（OK群）は呼ばずに即座にエラーコード 1 で終了
        sys.exit(1)

if __name__ == "__main__":
    main()
