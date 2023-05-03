import argparse
import asyncio
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime

import genshin
import schedule
from genshin import Game
from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class CookieInfo:
    ltuid: str
    ltoken: str
    env_name: str = ""


@dataclass
class RewardInfo:
    uid: str = "❓"
    level: str = "❓"
    name: str = "❓"
    server: str = "❓"
    status: str = "❌ 실패"
    check_in_count: str = "❓"
    reward: str = "❓"


@dataclass
class GameAndReward:
    name: str
    game: Game
    rewards: list[RewardInfo]


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


def is_true(value: str) -> bool:
    return value.lower() in ("true", "1", "yes", "y", "on")


def is_there_any_success(results: list[RewardInfo]) -> bool:
    return any(result.status != "❌ 실패" for result in results)


def censor_uid(uid: int | str) -> str:
    uid = str(uid)
    uid = uid[:2] + "■■■■■■" + uid[-1]
    return uid


class GetDailyReward:
    def __init__(self, game: Game = Game.GENSHIN):
        self.rewards = []
        self.game = game

    async def __call__(self, cookie: CookieInfo, server: str) -> RewardInfo:
        client = genshin.Client(lang=server, game=self.game)
        client.set_cookies(ltuid=cookie.ltuid, ltoken=cookie.ltoken)

        info = RewardInfo()

        try:
            await client.claim_daily_reward(reward=False)
        except genshin.InvalidCookies:
            console.log(f"{cookie.env_name}: 쿠키 정보가 잘못되었습니다. ltuid와 ltoken을 확인해주세요.")
            return info
        except genshin.AlreadyClaimed:
            info.status = "🟡 이미 했음"
        except genshin.GenshinException as e:
            if "No genshin account" not in str(e):
                console.log(f"{cookie.env_name}: {e}")
            return info
        else:
            info.status = "✅ 출석 성공"

        accounts = await client.get_game_accounts()

        # 원신 계정에서 가장 레벨이 높은 지역의 계정 정보만 사용
        account = max(
            (acc for acc in accounts if acc.game == self.game),
            key=lambda acc: acc.level,
        )
        _, day = await client.get_reward_info()
        if not self.rewards:
            self.rewards = await client.get_monthly_rewards()
        reward = self.rewards[day - 1]

        info.uid = censor_uid(account.uid)
        info.level = str(account.level)
        info.name = account.nickname
        info.server = account.server_name.rsplit(maxsplit=1)[0]
        info.check_in_count = str(day)
        info.reward = f"{reward.name} x{reward.amount}"

        return info


async def get_all_reward(info: list[CookieInfo], server: str) -> list[GameAndReward]:
    all_results = []

    env_and_enum = [
        ("NO_GENSHIN", Game.GENSHIN),
        ("NO_STARRAIL", Game.STARRAIL),
        ("NO_HONKAI", Game.HONKAI),
    ]

    for env, game in env_and_enum:
        if is_true(os.getenv(env, "0")):
            continue
        get_daily_reward = GetDailyReward(game=game)
        funcs = (get_daily_reward(cookie=cookie, server=server) for cookie in info)
        results = await asyncio.gather(*funcs)

        if is_there_any_success(results):
            game_and_reward = GameAndReward(env.removeprefix("NO_"), game, results)
            all_results.append(game_and_reward)

    return all_results


def init_table(name: str = "GENSHIN") -> Table:
    now = datetime.strftime(datetime.now(), "%Y-%m-%d %I:%M:%S %p")
    title = f"🎮{name} 🕰️{now}"
    table = Table(title=title, title_style="bold", header_style="bold", expand=True)

    table.add_column("UID", justify="center", style="dim")
    table.add_column("이름", justify="center")
    table.add_column("레벨", justify="center")
    table.add_column("서버", justify="center")
    table.add_column("출석 일수", justify="center")
    table.add_column("출석 성공여부", justify="right")
    table.add_column("출석 보상", justify="right", style="green")

    return table


def get_cookie_info_in_env() -> list[CookieInfo]:
    info = []
    for name, value in os.environ.items():
        if name.startswith("ACCOUNT") and "," in value:
            ltuid, ltoken = map(str.strip, value.split(",", maxsplit=1))
            cookie = CookieInfo(ltuid, ltoken, name)
            info.append(cookie)
    info.sort(key=lambda cookie: cookie.env_name)
    return info


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--once", action="store_true", help="Run only once")
    return parser.parse_args()


def fix_asyncio_windows_error() -> None:
    "https://github.com/encode/httpx/issues/914#issuecomment-622586610"
    if (
        sys.version_info[0] == 3
        and sys.version_info[1] >= 8
        and sys.platform.startswith("win")
    ):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def main() -> None:
    cookies = get_cookie_info_in_env()

    server = os.getenv("SERVER", "ko-kr")
    server = check_server(server)
    results = asyncio.run(get_all_reward(cookies, server))

    if not results:
        return

    for result in results:
        table = init_table(result.name)

        for info in result.rewards:
            table.add_row(
                info.uid,
                info.name,
                info.level,
                info.server,
                info.check_in_count,
                info.status,
                info.reward,
            )

        console.print(table)


if __name__ == "__main__":
    fix_asyncio_windows_error()
    args = parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    if args.once:
        main()
        sys.exit(0)

    TIME = os.getenv("TIME", "00:00")
    try:
        schedule.every().day.at(TIME).do(main)
    except schedule.ScheduleValueError:
        m = f"'{TIME}'은 잘못된 시간 형식입니다. TIME을 HH:MM(:SS)형태로 입력해주십시오."
        console.log(m)
        console.log("앱이 종료되었습니다.")
        sys.exit(1)

    console.log("앱이 실행되었습니다.")

    while True:
        schedule.run_pending()
        time.sleep(1)
