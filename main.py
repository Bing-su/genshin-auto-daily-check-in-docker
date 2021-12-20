import logging
import os
import time

import genshinstats as gs
import schedule

logging.basicConfig(
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S %p",
    level=logging.INFO,
)

LANG = "ko-kr"

message = """
##############################
  {day}일 출석체크 성공!
  {item} x{count}
##############################"""


def main(ltuid: str, ltoken: str, lang: str = "ko-kr"):
    gs.set_cookie(ltuid=ltuid, ltoken=ltoken)
    try:
        reward = gs.claim_daily_reward(lang=lang)
    except gs.errors.NotLoggedIn:
        logging.error("쿠키 정보가 올바르지 않습니다. ltuid와 ltoken을 다시 확인해주세요.")
        return

    _, day = gs.get_daily_reward_info()
    if reward is not None:
        item = reward["name"]
        count = reward["cnt"]
        logging.info(message.format(day=day, item=item, count=count))
    else:
        logging.info(f"{day}일차는 이미 출석체크를 했습니다.")


if __name__ == "__main__":
    LTUID = os.getenv("LTUID", "")
    LTOKEN = os.getenv("LTOKEN", "")
    main(LTUID, LTOKEN)
