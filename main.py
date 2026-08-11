import asyncio
import os
import random
import signal
import sys
import time
import traceback
import unicodedata
import discord
from discord.ext import commands
sys.exit(3)
# ==================================================
# --- Debian風 ＆ Kernel Panic システムログユーティリティ ---
# ==================================================

def log_debian_ok(message: str):
    """Debianの [  OK  ] ログを表示"""
    print(f"[  \033[1;32mOK\033[0m  ] {message}")
    sys.stdout.flush()

async def log_debian_working(message: str, duration: float = 1.8):
    """
    Debian風 [****] バウンシング（跳ね返り）アニメーション
    """
    width = 7
    pat_len = 4
    max_pos = width - pat_len
    
    pos = 0
    direction = 1
    end_time = time.time() + duration
    
    while time.time() < end_time:
        pattern = " " * pos + "*" * pat_len + " " * (max_pos - pos)
        sys.stdout.write(f"\r[ \033[1;33m{pattern}\033[0m ] {message}")
        sys.stdout.flush()
        
        await asyncio.sleep(0.08)
        
        pos += direction
        if pos >= max_pos or pos <= 0:
            direction *= -1
    
    sys.stdout.write(f"\r[  \033[1;32mOK\033[0m  ] {message}\n")
    sys.stdout.flush()

def show_debian_boot_banner():
    """起動時の Debian 風システムログ"""
    print("\nLinux roomba-bot 6.1.0-18-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.76-1 x86_64\n")
    log_debian_ok("Created slice System Slice.")
    log_debian_ok("Starting Roomba Control Daemon...")
    log_debian_ok("Mounted /dev/discord/bot-env.")

async def show_debian_shutdown_sequence():
    """停止時の Debian 風シャットダウンアニメーション ＆ ログ"""
    print("\n")
    await log_debian_working("Stopping Roomba Control Daemon...", duration=1.2)
    log_debian_ok("Closed Discord Gateway Socket.")
    log_debian_ok("Unmounted /dev/discord/bot-env.")
    log_debian_ok("Stopped target Local File Systems.")
    log_debian_ok("Reached target System Shutdown.")
    log_debian_ok("Finished Power-Off.")
    print("[  \033[1;32mOK\033[0m  ] Reached target Power-Off.\n")
    sys.stdout.flush()

def trigger_kernel_panic(exc_type, exc_value, exc_traceback):
    """異常終了時に Kernel Panic 画面を出力する"""
    print("\n")
    print("\033[1;31m[    0.000000] Kernel panic - not syncing: Fatal exception in interrupt\033[0m")
    print(f"[    0.000005] CPU: 0 PID: 1 Comm: roomba-bot Tainted: G        W          6.1.0-18-amd64")
    print(f"[    0.000010] Hardware name: QEMU Standard PC (i440FX + PIIX, 1996), BIOS 1.15.0-1")
    print(f"[    0.000015] Call Trace:")
    print(f"[    0.000020]  <TASK>")
    
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    for line in tb_lines:
        for sub_line in line.strip().split('\n'):
            print(f"[    0.000025]  [<ffffffff81{random.randint(100000, 999999):x}>] {sub_line}")
            
    print(f"[    0.000030]  </TASK>")
    print(f"[    0.000035] Kernel Offset: disabled")
    print(f"[    0.000040] ---[ end Kernel panic - not syncing: {exc_type.__name__}: {exc_value} ]---\033[0m\n")
    sys.stdout.flush()

# 未捕獲例外をカーネルパニックにフック
sys.excepthook = trigger_kernel_panic


# ==================================================
# --- Bot 設定 ＆ ワードリスト ---
# ==================================================

RECORD_CHANNEL_ID = 1531955600819359808
LIFETIME_SECONDS = 20700  

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# シャットダウン検知用の非同期フラグ
shutdown_event = asyncio.Event()

BAN_WORDS = [
    "野獣先輩", "YJSPY", "yjspy", "やじゅうせんぱい", "ヤジュウセンパイ",
    "死ね", "タヒね", "しね", "シネ", "殺す", "殺すぞ",
    "田所浩二", "114514", "114,514", "いいよこいよ", "いいよ！こいよ！",
    "1919", "810", "114514810"
]

DELETE_WORDS = [
    "障害者", "ガイジ", "キチガイ", "きちがい",
    "ゴミ", "カス", "雑魚", "ざこ", "不細工", "ぶさいく",
    "頭悪い", "低能", "無能", "語彙力ないね",
    "何がありがとうなの？", "はい論破",
    "逝きすぎ", "いきすぎ", "イキすぎ", "イクイク", "いくいく",
    "ヌッ！", "ぬっ！", "王道を往く", "悔い上げて", 
    "悔い改めて", "歪みねぇな", "だらしねぇな", "そうだよ（便乗）"
]

def normalize_text(text: str) -> str:
    return unicodedata.normalize('NFKC', text).lower()

def bite_text(text: str, chance: float = 0.25) -> str:
    if random.random() > chance:
        return text

    replacements = {
        "でした": ["でひた", "でふた", "でしゅた"],
        "しました": ["ひました", "しやした", "しまひた"],
        "ます": ["まふ", "ましゅ", "まつ"],
        "ごちそうさま": ["ごひちそうさま", "ごちほうさま", "ごちそうしゃま"],
        "禁止": ["きんひ", "きんしぃ"],
        "捕食": ["ほほく", "ほふぉく"],
        "清掃": ["ふぇいそう", "せいそうっ"],
        "美味しく": ["おいひく", "おひしく"],
        "食されました": ["たべられまひた", "くわれまひた"],
        "二度と": ["にろと", "に、二度と"],
        "ありません": ["ありまひぇん", "ありやせん"],
        "完了": ["かんりょうっ", "か、完了"],
        "ルンバ": ["るんばっ", "ル、ルンバ"],
        "弱肉強食": ["じゃくにくきょうしょくっ", "じゃく、弱肉強食"],
    }

    bitten = text
    bitten_flag = False

    for original, changed in replacements.items():
        if original in bitten:
            if isinstance(changed, list):
                bitten = bitten.replace(original, random.choice(changed), 1)
            else:
                bitten = bitten.replace(original, changed, 1)
            bitten_flag = True

    particles = ["は", "が", "を", "に"]
    for p in particles:
        if p in bitten and random.random() < 0.3:
            bitten = bitten.replace(p, f"{p}、{p}", 1)
            bitten_flag = True
            break

    if bitten_flag:
        fix_phrases = [
            "……あ、コホン！……違います、です！",
            "……っ！……じゃなくて、です！",
            "……噛みました。……ゲホン、です！",
            "……あふっ！……気を取り直して、です！",
            "……〜〜〜っ！……噛んでないです、です！"
        ]
        bitten += f" {random.choice(fix_phrases)}"
    else:
        bitten += "……あ、噛みました。"

    return bitten


# ==================================================
# --- イベント・タスクハンドラ ---
# ==================================================

async def scheduled_graceful_shutdown(delay: int):
    """一定時間経過による自動シャットダウン"""
    await asyncio.sleep(delay)
    shutdown_event.set()

@bot.event
async def on_ready():
    show_debian_boot_banner()
    await log_debian_working(f"Starting Discord Bot Service for {bot.user}...", duration=2.0)
    log_debian_ok("Reached target Multi-User System / Ready for prey.")
    bot.loop.create_task(scheduled_graceful_shutdown(LIFETIME_SECONDS))

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content_normalized = normalize_text(message.content)

    # 1. 捕食（即BAN処理）
    detected_ban_words = [
        word for word in BAN_WORDS 
        if normalize_text(word) in content_normalized
    ]

    if detected_ban_words:
        try:
            await message.delete()
        except discord.HTTPException:
            pass

        words_str = "』『".join(detected_ban_words)

        raw_dm_notice = (
            f"【捕食通知】\n"
            f"あなたは禁止ワード『{words_str}』を放ったため、弱肉強食の理により食されました。\n"
            f"ごちそうさでした。二度とお目にかかることはないでしょう。"
        )
        dm_notice = bite_text(raw_dm_notice, chance=0.25)

        try:
            await message.author.send(dm_notice)
            log_debian_ok(f"Sent prey notification DM to {message.author}")
        except discord.Forbidden:
            log_debian_ok(f"DM closed for {message.author}. Proceeding directly to ban.")
        except discord.HTTPException as e:
            print(f"[ \033[1;31mFAILED\033[0m ] DM Error: {e}")

        try:
            reason_words = ", ".join(detected_ban_words)
            await message.guild.ban(
                message.author,
                reason=f"禁止ワード（{reason_words}）の検出により子分BOTが捕食（BAN）しました。"
            )
            
            raw_channel_eat_text = f"🍖 **捕食完了:** {message.author.mention} は禁止ワードを放ったため、美味しく食されました。ごちそうさでした！"
            channel_eat_text = bite_text(raw_channel_eat_text, chance=0.25)
            eat_msg = await message.channel.send(channel_eat_text)
            await eat_msg.delete(delay=5)

            record_channel = bot.get_channel(RECORD_CHANNEL_ID)
            if record_channel:
                title_text = bite_text("📜 【捕食アーカイブ】処分ユーザー記録", chance=0.25)
                desc_text = "弱肉強食の理により、新たな荒らしが食されました。ごちそうさでした！"
                footer_text = bite_text("弱肉強食の理により、サーバーの平和は保たれた…", chance=0.25)

                embed = discord.Embed(
                    title=title_text,
                    description=desc_text,
                    color=discord.Color.dark_red()
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                embed.add_field(name="対象ユーザー", value=f"{message.author.mention} (`{message.author.name}`)", inline=False)
                embed.add_field(name="検出ワード", value=f"`{reason_words}`", inline=False)
                embed.set_footer(text=footer_text)
                
                await record_channel.send(embed=embed)

            log_debian_ok(f"Banned user {message.author} successfully.")

        except discord.Forbidden:
            raw_err_msg = "【エラー】捕食しようとしましたが、権限が足りず食べ残してしまいました（BOTより権限が高いか同等です）。"
            err_msg = bite_text(raw_err_msg, chance=0.35)
            await message.channel.send(err_msg)
        except discord.HTTPException as e:
            await message.channel.send(f"【エラー】捕食処理に失敗しました: {e}")

        return

    # 2. 清掃（メッセージ削除処理）
    for word in DELETE_WORDS:
        if normalize_text(word) in content_normalized:
            try:
                await message.delete()
                raw_clean_text = f"🧹 **清掃完了:** {message.author.mention} の不適切な発言をルンバがキレイに清掃しました。"
                clean_text = bite_text(raw_clean_text, chance=0.25)
                clean_msg = await message.channel.send(clean_text)
                await clean_msg.delete(delay=5)
                log_debian_ok(f"Cleaned message from {message.author}")
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                print(f"[ \033[1;31mFAILED\033[0m ] Delete Error: {e}")
            return

    await bot.process_commands(message)


# ==================================================
# --- エントリーポイント (シグナル ＆ 起動管理) ---
# ==================================================

async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN environment variable is not set")

    loop = asyncio.get_running_loop()

    # シグナルハンドラからはフラグを立てるだけ（安全）
    def signal_handler():
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows環境などのバックアップ
            signal.signal(sig, lambda s, f: shutdown_event.set())

    # Bot起動タスクとシャットダウン監視タスクを並列実行
    bot_task = asyncio.create_task(bot.start(token))
    shutdown_task = asyncio.create_task(shutdown_event.wait())

    # いずれかのイベントが発生するまで待機
    done, pending = await asyncio.wait(
        [bot_task, shutdown_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    # シャットダウンイベントが検知された場合
    if shutdown_event.is_set():
        await show_debian_shutdown_sequence()
        await bot.close()

    # 残りのタスクをキャンセル＆クリーンアップ
    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # bot_task で例外が起きていた場合は再スローして Kernel Panic を発火させる
    if bot_task in done and bot_task.exception():
        raise bot_task.exception()

if __name__ == "__main__":
    try:
        asyncio.run(main())
        sys.exit(0)
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
    except Exception as e:
        trigger_kernel_panic(type(e), e, e.__traceback__)
        sys.exit(1)
