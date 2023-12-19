# ❇️ AI Play User-Auth

AI Play의 사용자 계정 및 인증 관련 기능을 담당할 API 서버

## :one: Stack

- Python 3.8.12
- DJango 4.0.3
- PostgreSQL(ElephantSQL)
- AWS S3
- JWT
- Swagger

<br/>

## :two: 배포 플랫폼 및 서버 주소

- 플랫폼 : Heroku
- 주소 : [https://ai-play-user-auth.herokuapp.com](https://ai-play-user-auth.herokuapp.com)

<br/>

## :three: API 명세

- DOCS : https://aiplay-user-auth.herokuapp.com/userauth/swagger/

| Method                 | URL (BASE_URL = /userauth) | Description                       |
| ---------------------- | -------------------------- | --------------------------------- |
| 이메일, 닉네임 체크    |                            |                                   |
| POST                   | /email_check               | 회원가입 시 이메일 인증 번호 발송 |
| POST                   | /email_confirm             | 회원가입 시 이메일 인증 번호 체크 |
| GET                    | /nickname_check            | 프로젝트 구조 업데이트            |
| 로그인, 회원가입, 탈퇴 |                            |                                   |
| POST                   | /login                     | 사용자 로그인 처리                |
| POST                   | /signup                    | 사용자 회원가입 처리              |
| POST                   | /inactive                  | 사용자 탈퇴 처리                  |
| CSRF 토큰 & JWT        |                            |                                   |
| GET                    | /index                     | 웹 앱 접속 시 CSRF Token 발급     |
| GET                    | /refresh_jwt               | 사용자 접속 중 JWT 토큰 갱신하기  |
| GET                    | /remove_jwt                | 사용자 로그아웃 시 토큰 삭제하기  |
| 사용자 정보 변경       |                            |                                   |
| POST                   | /nickname_change           | 사용자 닉네임 변경                |
| POST                   | /profile_pic_change        | 사용자 프로필 사진 변경           |
| POST                   | /pw_change                 | 사용자 비밀번호 변경              |
| POST                   | /search_pw                 | 사용자 임시 비밀번호 발급         |

<br/>

## 4️⃣ 트러블 슈팅 기록

- https://github.com/AI-Play/User-Auth/discussions

<br/>

## :five: 개발 환경 준비 사항

<details>
  <summary><b>준비 사항</b></summary>

```
# 필요한 패키지 설치
python -m pip install -r requirements.txt
```

##### 로컬 테스트 환경 구축

```
# 1. docker postgres 이미지 준비 및 컨테이너 실행
# https://hub.docker.com/_/postgres
docker run -p 5432:5432 --name postgres -e POSTGRES_PASSWORD=aiplay -d postgres
# ※ 주의사항 : 아래 2번 과정에서 DB 세팅이 이루어질 것이므로 컨테이너 생성 및 실행만 하고 그 외에는 건드리지 말 것

# 2. DJango migration 실행
# userauth의 models.py에 의해서 생성된 migration 파일이 이미 존재함(0001_initial.py)
# 따라서 아래 명령어를 실행하면 DB 세팅이 이루어짐
python manage.py migrate

# 3. DB Table이 생성되었는지 확인

# 4. Architecture Repo의 dbscript.sql 하단에 있는 'Trigger 생성하기' 부분의 스크립트를 실행
```

##### 개발 서버 실행

```
python manage.py runserver
```

</details>
