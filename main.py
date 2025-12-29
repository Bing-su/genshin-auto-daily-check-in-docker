# /// script
# dependencies = [
#     "genshin>=1.7.2",
#     "rich",
#     "schedule",
# ]
# requires-python = ">=3.11"
# ///
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
import tomllib
from asyncio import Semaphore
from contextlib import nullcontext, suppress
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import genshin
import httpx
import schedule
from genshin import Game
from pydantic import TypeAdapter, ValidationError
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table

console = Console()
is_true_ta = TypeAdapter(bool)


@dataclass
class CookieInfo:
    ltuid: str
    ltoken: str
    ltmid: str = ""
    env_name: str = ""

    def asdict(self) -> dict[str, str]:
        if self.ltoken.startswith("v2"):
            d = {"ltuid_v2": self.ltuid, "ltoken_v2": self.ltoken}
            if self.ltmid:
                d["ltmid_v2"] = self.ltmid
            return d
        return {"ltuid": self.ltuid, "ltoken": self.ltoken}


@dataclass
class RewardInfo:
    uid: str = "❓"
    level: str = "❓"
    name: str = "❓"
    server: str = "❓"
    status: str = "❌"
    check_in_count: str = "❓"
    reward: str = "❓"
    success: bool = False


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
    try:
        return is_true_ta.validate_python(value)
    except ValidationError:
        return False


def is_there_any_success(results: list[RewardInfo]) -> bool:
    return any(result.success for result in results)


def censor_uid(uid: int | str) -> str:
    uid = str(uid)
    return uid[:-6] + "■■■■■" + uid[-1]


def parse_cookie(cookie: str, env_name: str = "") -> CookieInfo | None:
    a = [c.strip() for c in cookie.split(",")]
    if len(a) == 2:
        return CookieInfo(ltuid=a[0], ltoken=a[1], env_name=env_name)
    if len(a) == 3:
        return CookieInfo(ltuid=a[0], ltoken=a[1], ltmid=a[2], env_name=env_name)
    return None


class GetDailyReward:
    def __init__(self, game: Game = Game.GENSHIN, semaphore: Semaphore | None = None):
        self.rewards = []
        self.game = game
        self.semaphore = semaphore if semaphore is not None else nullcontext()

    async def __call__(self, cookie: CookieInfo, server: str) -> RewardInfo:
        async with self.semaphore:
            return await self._call(cookie=cookie, server=server)

    async def _call(self, cookie: CookieInfo, server: str) -> RewardInfo:
        client = genshin.Client(lang=server, game=self.game)
        client.set_cookies(cookie.asdict())

        info = RewardInfo()

        try:
            await client.claim_daily_reward(reward=False)
        except genshin.InvalidCookies:
            console.log(
                f"{cookie.env_name}: 쿠키 정보가 잘못되었습니다. ltuid와 ltoken을 확인해주세요."
            )
            return info
        except genshin.AlreadyClaimed:
            info.status = "🟡"
        except genshin.GenshinException as e:
            if e.retcode != -10002:
                game = str(self.game).split(".")[-1]
                console.log(f"\\[{game}] {cookie.env_name}: {e}")
        else:
            info.status = "✅"

        try:
            accounts = await client.get_game_accounts()
        except genshin.GenshinException as e:
            console.log(f"\\[{self.game}] {cookie.env_name}: {e}")
            return info

        accounts_game = [acc for acc in accounts if acc.game == self.game]
        if not accounts_game:
            return info

        account = max(accounts_game, key=lambda acc: acc.level)

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
        info.success = True

        return info


async def get_one_game_reward(
    info: list[CookieInfo],
    server: str,
    game: Game,
    semaphore: Semaphore | None = None,
) -> list[RewardInfo]:
    get_daily_reward = GetDailyReward(game=game, semaphore=semaphore)
    funcs = (get_daily_reward(cookie=cookie, server=server) for cookie in info)
    return await asyncio.gather(*funcs)


async def get_all_reward(
    info: list[CookieInfo],
    server: str,
    max_parallel: int = 10,
) -> list[GameAndReward]:
    mapping = Game.__members__
    semaphore = Semaphore(max_parallel) if max_parallel > 0 else None

    tasks: list[asyncio.Task[list[RewardInfo]]] = []
    async with asyncio.TaskGroup() as tg:
        for name in mapping:
            env_name = f"NO_{name}"
            if is_true(os.getenv(env_name, "0")):
                continue

            func = get_one_game_reward(
                info=info,
                server=server,
                game=mapping[name],
                semaphore=semaphore,
            )
            task = tg.create_task(func, name=name)
            tasks.append(task)

    all_results = {task.get_name(): task.result() for task in tasks}
    output: list[GameAndReward] = []
    for name, results in all_results.items():
        if is_there_any_success(results):
            game_and_reward = GameAndReward(name, mapping[name], results)
            output.append(game_and_reward)

    return output


def init_table(name: str = "GENSHIN") -> Table:
    title = f"🎮{name}"
    table = Table(title=title, title_style="bold", header_style="bold", expand=True)

    table.add_column("UID", justify="center", style="dim")
    table.add_column("이름", justify="center")
    table.add_column("레벨", justify="center")
    table.add_column("서버", justify="center")
    table.add_column("일수", justify="center")
    table.add_column("성공", justify="right")
    table.add_column("보상", justify="right", style="green")

    return table


def get_cookie_info_in_env() -> list[CookieInfo]:
    info = []
    for name, value in os.environ.items():
        if name.startswith("ACCOUNT"):
            cookie = parse_cookie(value, name)
            if cookie:
                info.append(cookie)

    return info


def get_cookie_info_from_file(file_path: str | Path) -> list[CookieInfo]:
    with Path(file_path).open("rb") as f:
        data = tomllib.load(f)

    info = []
    for name, value in data.items():
        cookie = parse_cookie(value, name)
        if cookie:
            info.append(cookie)

    return info


def get_cookie_info(file_path: str | Path = "cookie.toml") -> list[CookieInfo]:
    info = get_cookie_info_in_env()

    if file_path and Path(file_path).is_file():
        try:
            info += get_cookie_info_from_file(file_path)
        except tomllib.TOMLDecodeError as e:
            console.log(f"{file_path}: TOML 파일을 읽는 중 오류가 발생했습니다: {e}")

    info.sort(key=lambda x: x.env_name)
    return info


async def send_discord_webhook(
    results: list[GameAndReward], timestamp: str
) -> None:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return

    fields = []
    for result in results:
        game_results = []
        for info in result.rewards:
            game_results.append(
                f"{info.status} `{info.uid}` **{info.name}** Lv.{info.level} | "
                f"{info.server} | {info.check_in_count}일 | {info.reward}"
            )

        fields.append(
            {
                "name": f"🎮 {result.name}",
                "value": "\n".join(game_results) if game_results else "결과 없음",
                "inline": False,
            }
        )

    embed = {
        "title": "✅ HoYoLab 일일 출석체크 완료",
        "color": 0x00FF00,
        "fields": fields,
        "footer": {"text": timestamp},
    }

    payload = {"embeds": [embed]}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
        except httpx.HTTPError as e:
            console.log(f"Discord 웹훅 전송 실패: {e}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--once", action="store_true", help="Run only once")
    parser.add_argument("--on-launch", action="store_true", help="Run on launch")
    parser.add_argument(
        "--cookie-file",
        type=str,
        default="cookie.toml",
        metavar="<file>",
        help="Path to the cookie file (default: cookie.toml)",
    )
    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    file_path = args.cookie_file
    cookies = get_cookie_info(file_path)

    server = os.getenv("SERVER", "ko-kr")
    server = check_server(server)
    max_parallel = int(os.getenv("MAX_PARALLEL", "-1"))
    results = asyncio.run(
        get_all_reward(info=cookies, server=server, max_parallel=max_parallel)
    )

    if not results:
        return

    now = datetime.strftime(datetime.now(), "%Y-%m-%d %I:%M:%S %p")
    group = []

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

        group.append(table)

    panel = Panel(Group(*group), title=now)
    console.print(panel)

    # Send Discord webhook
    asyncio.run(send_discord_webhook(results, now))


def entry() -> None:
    args = parse_args()

    with suppress(Exception):
        from dotenv import load_dotenv

        load_dotenv()

    if args.once or is_true(os.getenv("RUN_ONCE", "0")):
        main(args)
        sys.exit(0)

    schedule_time = os.getenv("TIME", "00:00")
    try:
        schedule.every().day.at(schedule_time).do(main, args)
    except schedule.ScheduleValueError:
        m = f"'{schedule_time}'은 잘못된 시간 형식입니다. TIME을 HH:MM(:SS)형태로 입력해주십시오."
        console.log(m)
        console.log("앱이 종료되었습니다.")
        sys.exit(1)

    console.log("앱이 실행되었습니다.")

    if args.on_launch or is_true(os.getenv("RUN_ON_LAUNCH", "0")):
        main(args)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    entry()
