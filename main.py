import argparse
import asyncio
import os
import sys
import time
from datetime import datetime

import genshin
import schedule
from genshin.types import Game
from rich.console import Console
from rich.table import Table

console = Console()


def check_server(server: str) -> str:
    valid = {
        "zh-cn",
        "zh-tw",
        "de-de",
        "en-us",
        "es-es",
        "fr-fr",
        "id-id",
        "ja-jp",
        "ko-kr",
        "pt-pt",
        "ru-ru",
        "th-th",
        "vi-vn",
    }

    server = server.lower()
    if server not in valid:
        console.log(
            f"'{server}': 유효한 서버가 아닙니다. "
            "'zh-cn', 'zh-tw', 'de-de', 'en-us', 'es-es', "
            "'fr-fr', 'id-id', 'ja-jp', 'ko-kr', 'pt-pt', "
            "'ru-ru', 'th-th', 'vi-vn' 중의 하나여야 합니다. "
            "'ko-kr'을 사용합니다."
        )
        server = "ko-kr"
    return server


def censor_uid(uid: int) -> str:
    uid = str(uid)
    uid = uid[:2] + "■■■■■■" + uid[-1]
    return uid


async def get_daily_reward(
    ltuid: str, ltoken: str, lang: str = "ko-kr", env_name: str = ""
) -> dict[str, str]:

    client = genshin.Client(lang=lang, game=Game.GENSHIN)
    client.set_cookies(ltuid=ltuid, ltoken=ltoken)

    info = dict(
        uid="❓",
        level="❓",
        name="❓",
        server="❓",
        status="❌ 실패",
        check_in_count="❓",
        reward="❓",
    )

    try:
        await client.claim_daily_reward(reward=False)
    except genshin.InvalidCookies:
        console.log(f"{env_name}: 쿠키 정보가 잘못되었습니다. ltuid와 ltoken을 확인해주세요.")
        return info
    except genshin.AlreadyClaimed:
        info["status"] = "🟡 이미 했음"
    else:
        info["status"] = "✅ 출석 성공"

    accounts = await client.get_game_accounts()

    # 원신 계정에서 가장 레벨이 높은 지역의 계정 정보만 사용
    account = max(
        (acc for acc in accounts if acc.game == Game.GENSHIN), key=lambda acc: acc.level
    )
    _, day = await client.get_reward_info()
    rewards = await client.get_monthly_rewards()
    reward = rewards[day - 1]

    info["uid"] = censor_uid(account.uid)
    info["level"] = str(account.level)
    info["name"] = account.nickname
    info["server"] = account.server_name.rsplit(maxsplit=1)[0]
    info["check_in_count"] = str(day)
    info["reward"] = f"{reward.name} x{reward.amount}"

    return info


async def get_all_reward(
    info: list[tuple[str, str, str]], server: str
) -> tuple[dict[str, str]]:

    funcs = (
        get_daily_reward(ltuid, ltoken, server, env_name)
        for env_name, ltuid, ltoken in info
    )

    results = await asyncio.gather(*funcs)

    return results


def init_table() -> Table:
    today = datetime.strftime(datetime.now(), "%Y-%m-%d %I:%M:%S %p")
    table = Table(title=today, title_style="bold", header_style="bold")

    table.add_column("UID", justify="center", style="dim")
    table.add_column("이름", justify="center")
    table.add_column("레벨", justify="center")
    table.add_column("서버", justify="center")
    table.add_column("출석 일수", justify="center")
    table.add_column("출석 성공여부", justify="right")
    table.add_column("출석 보상", justify="right", style="green")

    return table


def get_cookie_info_in_env() -> list[tuple[str, str, str]]:
    info = []
    for name, value in os.environ.items():
        if name.startswith("ACCOUNT"):
            ltuid, ltoken = map(str.strip, value.split(","))
            info.append((name, ltuid, ltoken))
    info.sort()
    return info


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--once", action="store_true", help="Run only once")
    args = parser.parse_args()
    return args


def solve_asyncio_windows_error() -> None:
    "https://github.com/encode/httpx/issues/914#issuecomment-622586610"
    if (
        sys.version_info[0] == 3
        and sys.version_info[1] >= 8
        and sys.platform.startswith("win")
    ):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def main() -> None:
    cookies = get_cookie_info_in_env()

    SERVER = os.getenv("SERVER", "ko-kr")
    SERVER = check_server(SERVER)
    results = asyncio.run(get_all_reward(cookies, SERVER))

    table = init_table()

    for info in results:
        table.add_row(
            info["uid"],
            info["name"],
            info["level"],
            info["server"],
            info["check_in_count"],
            info["status"],
            info["reward"],
        )

    console.print(table)


if __name__ == "__main__":
    solve_asyncio_windows_error()
    args = parse_args()
    if args.once:
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ModuleNotFoundError:
            pass

        main()
        raise SystemExit

    TIME = os.getenv("TIME", "01:00")
    try:
        schedule.every().day.at(TIME).do(main)
    except schedule.ScheduleValueError:
        m = f"'{TIME}'은 잘못된 시간 형식입니다. TIME을 HH:MM(:SS)형태로 입력해주십시오."
        console.log(m)
        console.log("앱이 종료되었습니다.")
        raise SystemExit

    console.log("앱이 실행되었습니다.")

    while True:
        schedule.run_pending()
        time.sleep(1)
