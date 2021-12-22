import asyncio
import logging
import os
import time

import genshin
import schedule

logging.basicConfig(
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S %p",
    level=logging.INFO,
)

MESSAGE = """
##############################
  {day}일 출석체크 성공!
  {item} x{count}
##############################"""


async def get_daily_reward():
    LTUID = os.getenv("LTUID", "")
    LTOKEN = os.getenv("LTOKEN", "")
    LANG = os.getenv("LANG", "ko-kr")

    try:
        client = genshin.GenshinClient(lang=LANG)
    except ValueError:
        m = (
            f"'{LANG}'은 유효한 언어가 아닙니다. "
            "zh-cn, zh-tw, de-de, en-us, es-es, fr-fr, "
            "id-id, ja-jp, ko-kr, pt-pt, ru-ru, th-th, vi-vn "
            "중의 하나여야 합니다."
        )
        logging.error(m)
        return

    client.set_cookies(ltuid=LTUID, ltoken=LTOKEN)

    try:
        await client.claim_daily_reward(reward=False)
    except genshin.InvalidCookies:
        m = "쿠키 정보가 올바르지 않습니다. ltuid와 ltoken을 다시 확인해주세요."
        logging.error(m)
    except genshin.AlreadyClaimed:
        _, day = await client.get_reward_info()
        logging.info(f"{day}일차는 이미 출석체크를 했습니다.")
    else:
        _, day = await client.get_reward_info()
        rewards = await client.get_monthly_rewards()
        reward = rewards[day - 1]
        m = MESSAGE.format(day=day, item=reward.name, count=reward.amount)
        logging.info(m)
    finally:
        await client.close()


def main():
    asyncio.run(get_daily_reward())


TIME = os.getenv("TIME", "01:00")
try:
    schedule.every().day.at(TIME).do(main)
except schedule.ScheduleValueError:
    m = f"'{TIME}'은 잘못된 시간 형식입니다. TIME을 HH:MM(:SS)형태로 입력해주십시오."
    logging.error(m)
    raise SystemExit

if __name__ == "__main__":
    logging.info("앱이 실행되었습니다.")

    while True:
        schedule.run_pending()
        time.sleep(1)
