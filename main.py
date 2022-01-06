import asyncio
import argparse
import os
import time
from datetime import datetime

import genshin
import schedule
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

    if server not in valid:
        console.log(
            f"'{server}': 유효한 서버가 아닙니다. "
            '"zh-cn", "zh-tw", "de-de", "en-us", "es-es", '
            '"fr-fr", "id-id", "ja-jp", "ko-kr", "pt-pt", '
            '"ru-ru", "th-th", "vi-vn" 중의 하나여야 합니다.'
            "'ko-kr'을 사용합니다."
        )
        server = "ko-kr"
    return server


def censor_uid(uid: int) -> str:
    uid = str(uid)
    uid = uid[:2] + "■■■■■■" + uid[-1]
    return uid


async def get_daily_reward(ltuid: str, ltoken: str, lang: str = "ko-kr", i: int = 1):
    client = genshin.GenshinClient(lang=lang)
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
        console.log(f"{i}번 계정: 쿠키 정보가 잘못되었습니다. ltuid와 ltoken을 확인해주세요.")
        await client.close()
        return info
    except genshin.AlreadyClaimed:
        info["status"] = "🟡 이미 했음"
    else:
        info["status"] = "✅ 출석 성공"

    accounts = await client.genshin_accounts()

    # 계정에서 가장 레벨이 높은 계정 정보만 사용
    account = max((acc for acc in accounts), key=lambda a: a.level)
    _, day = await client.get_reward_info()
    rewards = await client.get_monthly_rewards()
    reward = rewards[day - 1]

    info["uid"] = censor_uid(account.uid)
    info["level"] = str(account.level)
    info["name"] = account.nickname
    info["server"] = account.server_name.split()[0]
    info["check_in_count"] = str(day)
    info["reward"] = f"{reward.name} x{reward.amount}"

    await client.close()

    return info


async def get_all_reward(
    ltuids: list[str], ltokens: list[str], server: str
) -> tuple[dict[str, str]]:

    funcs = (
        get_daily_reward(ltuid, ltoken, server, i)
        for i, (ltuid, ltoken) in enumerate(zip(ltuids, ltokens), 1)
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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--once", action="store_true", help="Run only once")
    args = parser.parse_args()
    return args


def main():
    LTUID = os.getenv("LTUID", "")
    LTOKEN = os.getenv("LTOKEN", "")

    ltuids = list(map(str.strip, LTUID.split(",")))
    ltokens = list(map(str.strip, LTOKEN.split(",")))

    SERVER = os.getenv("SERVER", "ko-kr")
    SERVER = check_server(SERVER)
    results = asyncio.run(get_all_reward(ltuids, ltokens, SERVER))

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
    args = parse_args()
    if args.once:
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ModuleNotFoundError:
            console.log("python-dotenv 설치가 필요합니다.")
        else:
            main()
        finally:
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
