# genshin-auto-daily-check-in-docker

원신 호요랩 자동 출석체크 도커 이미지. 여러 계정을 한번에 등록할 수 있습니다.

[Github](https://github.com/Bing-su/genshin-auto-daily-check-in-docker)

## 사용법

### 1. 쿠키 정보 얻기

1. [hoyolab.com](https://www.hoyolab.com/)에 접속합니다.

2. 로그인 합니다.

3. `F12`를 눌러 개발자 도구를 엽니다.

4. `애플리케이션(Application)` 탭으로 가서, `쿠키(Cookies)`, `https://www.hoyolab.com`을 순서대로 들어갑니다.

5. 해당 탭에서 `ltuid`와 `ltoken`을 복사합니다. 만약 해당 항목 대신 `ltuid_v2`와 `ltoken_v2`, `ltmid_v2`가 있다면 대신 이 셋을 가져옵니다.

### 2-1. 도커 이미지 사용하기

해당 토큰은 예시입니다.

```bash
docker run -d \
    --restart always \
    -e ACCOUNT1=13435465,AbCdEFGhIjKLmnoPQRsTUvWxYZ \
    -e ACCOUNT2=10203045,v2_I0STD1NliEnsF1lt4rmA9rEs6ltOkForE4chLineiFlinereTurnLetaHasHs3tLinesP1ltWh1t3sPaceF0lt9rmApXxtOlOwerc4secHarsNt=,9bcdef9cpu_py \
    -e NO_HONKAI=TRUE \
    ks2515/genshin-auto-daily-check-in
```

### 2-2. docker compose 예시

```yaml
services:
  genshin-auto-daily-check-in:
    image: ks2515/genshin-auto-daily-check-in
    restart: always
    environment:
      ACCOUNT1: 13435465,AbCdEFGhIjKLmnoPQRsTUvWxYZ
      ACCOUNT2: 10203045,v2_I0STD1NliEnsF1lt4rmA9rEs6ltOkForE4chLineiFlinereTurnLetaHasHs3tLinesP1ltWh1t3sPaceF0lt9rmApXxtOlOwerc4secHarsNt=,9bcdef9cpu_py
      MAX_PARALLEL: "10"
      NO_HONKAI: "TRUE"
      TIME: "01:00"
      TZ: Asia/Seoul
```

`ACCOUNT`로 시작하는 모든 환경변수를 인식합니다.

`,`로 ltuid와 ltoken, ltmid를 구분하여 입력해주어야 합니다.

![예시 이미지](https://i.imgur.com/s8C8cJy.png)

위 처럼 결과가 나옵니다.

| 사용가능한 환경 변수 | 설명                                                                                                                                  | 예시                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| ACCOUNT\*            | 쿠키 정보입니다.                                                                                                                      | 13435465,AbCdEFGhIjKLmnoPQRsTUvWxYZ |
| SERVER               | 사용할 언어 정보입니다. 기본값 "ko-kr"                                                                                                | ko-kr                               |
| TIME                 | 매일 출석체크를 할 시간입니다. CST(UTC+8) 기준입니다. 기본값 "00:00"<br/>출석체크 기준 시각은 한국시간 오전 1시입니다. (중국시간 0시) | 00:00                               |
| TZ                   | 도커 컨테이너가 사용할 시간대입니다. <br/>출석체크 기준 시각에 맞춰 기본값은 Asia/Shanghai입니다.                                     | Asia/Shanghai                       |
| NO_GENSHIN           | 원신 출석체크를 하지 않습니다.                                                                                                        | true                                |
| NO_STARRAIL          | 스타레일 출석체크를 하지 않습니다.                                                                                                    | 1                                   |
| NO_HONKAI            | 붕괴3rd 출석체크를 하지 않습니다.                                                                                                     | yes                                 |
| MAX_PARALLEL         | 동시에 진행할 수 있는 작업의 수 제한 (기본값 10)<br/>계정 하나당 최대 게임 3개의 작업이 있다는걸 유의하세요.                          | 10                                  |

### 3. 기타

```bash
python main.py -o
```

main.py에 -o를 붙여 실행하면 매일 반복하는 것이 아니라 한 번만 실행합니다.

#### 빌드

```bash
docker buildx create --name genshin-builder --use

docker buildx build --platform linux/amd64,linux/arm64 --tag ks2515/genshin-auto-daily-check-in --push .
```

## 요구사항

python>=3.11<br>
[schedule](https://github.com/dbader/schedule)<br>
[genshin](https://github.com/thesadru/genshin.py)<br>
[rich](https://github.com/Textualize/rich)
