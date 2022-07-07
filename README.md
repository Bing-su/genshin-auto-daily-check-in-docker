# genshin-auto-daily-check-docker

원신 호요랩 자동 출석체크 도커 이미지. 여러 계정을 한번에 등록할 수 있습니다.

## 사용법

### 1. 쿠키 정보 얻기

1. [hoyolab.com](https://www.hoyolab.com/)에 접속합니다.

2. 로그인 합니다.

3. `F12`를 눌러 개발자 도구를 엽니다.

4. `애플리케이션(Application)` 탭으로 가서, `쿠키(Cookies)`, `https://www.hoyolab.com`을 순서대로 들어갑니다.

5. 해당 탭에서 `ltuid`와 `ltoken`을 복사합니다.

### 2. 도커 이미지 사용하기

해당 토큰은 예시입니다.

```bash
docker run -d
    -e ACCOUNT1=13435465,AbCdEFGhIjKLmnoPQRsTUvWxYZ
    -e ACCOUNT2=32132132,PQRsTUvWxYZAbCdEFGhIjKLmno
    ks2515/genshin-auto-daily-check-in
```

`ACCOUNT`로 시작하는 모든 환경변수를 인식합니다.

`,`로 ltuid와 ltoken을 구분하여 입력해주어야 합니다.

![예시 이미지](https://i.imgur.com/AJKfjrO.png)

위 처럼 결과가 나옵니다.

| 사용가능한 환경 변수 | 설명                                                                                       | 예시                                  |
| ----------- | ---------------------------------------------------------------------------------------- | ----------------------------------- |
| ACCOUNT~    | 쿠키 정보입니다.                                                                                | 13435465,AbCdEFGhIjKLmnoPQRsTUvWxYZ |
| SERVER      | 사용할 언어 정보입니다. 기본값 "ko-kr"                                                                | ko-kr                               |
| TIME        | 매일 출석체크를 할 시간입니다. KST(UTC+9) 기준입니다. 기본값 "01:00"<br/>출석체크 기준 시각은 한국시간 오전 1시입니다. (중국시간 0시) | 01:00                               |

### 3. 기타

```bash
python main.py -o
```

main.py에 -o를 붙여 실행하면 매일 반복하는 것이 아니라 한 번만 실행합니다.

## 요구사항

python>=3.9
schedule
[genshin](https://github.com/thesadru/genshin.py)
rich
