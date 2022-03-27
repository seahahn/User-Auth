# AI-Play User-Auth

사용자 계정 및 인증 관련 기능을 담당할 API 서버

## Stack

Python 3.8.12
[DJango 4.0.2](https://www.djangoproject.com/)

## 준비 사항

```
python -m pip install Django
pip install psycopg2 # PostgreSQL 사용을 위한 DB API Package
```

### 로컬 테스트 환경 구축

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

## 개발 서버 실행

```
python manage.py runserver
```

## 배포 플랫폼 및 서버 주소

- 플랫폼 : Heroku
- 주소 : [https://ai-play-user-auth.herokuapp.com](https://ai-play-user-auth.herokuapp.com)
