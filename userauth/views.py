from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.core.mail import EmailMessage
from base import settings
from .models import inactive_users, users, mail_confirm
from datetime import datetime, timezone, timedelta
import bcrypt, string, random, boto3, json, jwt

SECRET_KEY = settings.SECRET_KEY

# JSON으로 들어오는 데이터를 파싱하기 위한 데코레이터
def requestBodyToJson(original):
    def wrapper(request):
        return original(json.loads(request.body))

    return wrapper


# 사용자 인증이 필요한 기능에 JWT 토큰 인증 과정을 붙이기 위한 데코레이터
def verify_token(original):
    def wrapper(request):
        try:
            # 토큰을 검증하여 유효한 토큰인지 확인
            rt = request.COOKIES.get("refresh_token")
            at = request.COOKIES.get("access_token")
            jwt.decode(rt, SECRET_KEY, algorithms="HS256") # refresh_token이 유효하지 않으면 에러 발생
            jwt.decode(at, SECRET_KEY, algorithms="HS256")
            return original(request)
        except Exception as e:
            return JsonResponse({"result":False, "token_state":False})

    return wrapper


# 비밀번호 해싱 기능
def hashingPw(pw):
    hash = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
    return hash.decode('utf-8') # DB에 byte string 저장이 불가능하므로 decode함


# JWT 토큰 생성하기 위한 함수(login에서 사용)
def create_jwt(token_data):
    at_data = token_data
    at_data['exp'] = datetime.now(tz=timezone.utc) + timedelta(hours=1)

    # refresh_token에는 iss까지 포함해서 반환
    rt_data = token_data
    rt_data['exp'] = datetime.now(tz=timezone.utc) + timedelta(days=1)
    rt_data['iss'] = settings.JWT_ISS

    access_token = jwt.encode(at_data, SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(rt_data, SECRET_KEY, algorithm='HS256')

    return access_token, refresh_token


# 사용자 접속 중 JWT 토큰 갱신하기 위한 함수
def refresh_jwt(request):
    # 토큰을 검증하여 유효한 토큰인지 확인
    rt = request.COOKIES.get("refresh_token")
    at = request.COOKIES.get("access_token")
    try:
        jwt.decode(rt, SECRET_KEY, algorithms="HS256") # refresh_token이 유효하지 않으면 에러 발생
        jwt.decode(at, SECRET_KEY, algorithms="HS256")
    except Exception as e:
        return JsonResponse({"result":False, "token_state":False, "message":"비정상적 갱신 요청"})

    response = JsonResponse({"result":True})

    # 토큰을 갱신하기 위해 새로운 토큰을 발급
    at_data = jwt.decode(at, SECRET_KEY, algorithms="HS256")
    at_data['exp'] = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    access_token = jwt.encode(at_data, SECRET_KEY, algorithm='HS256')

    # refresh_token의 유효 기간 확인 후 만료 1시간 전이면 갱신하기
    rt_data = jwt.decode(rt, SECRET_KEY, algorithms="HS256")
    if datetime.fromtimestamp(rt_data['exp'], tz=timezone.utc) < datetime.now(tz=timezone.utc) + timedelta(hours=1):
        rt_data['exp'] = datetime.now(tz=timezone.utc) + timedelta(days=1)
        refresh_token = jwt.encode(rt_data, SECRET_KEY, algorithm='HS256')
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)

    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response


# 사용자 로그아웃 시 토큰 삭제하기 위한 함수
def remove_jwt(_):
    # 토큰을 검증하여 유효한 토큰인지 확인
    # rt = request.COOKIES.get("refresh_token")
    # at = request.COOKIES.get("access_token")
    # try:
    #     jwt.decode(rt, SECRET_KEY, algorithms="HS256") # refresh_token이 유효하지 않으면 에러 발생
    #     jwt.decode(at, SECRET_KEY, algorithms="HS256")
    # except Exception as e:
    #     return JsonResponse({"result":False, "token_state":False})

    response = JsonResponse({"result":True})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


# 웹 앱 접속 시 CSRF Token 발급 위한 함수
def index(request):
    csrf_token = get_token(request)
    return JsonResponse({"result":True, "csrf_token":csrf_token})


def nickname_check(request):
    try:
        #해당 닉네임을 가진 유저가 존재하는지 확인
        #에러가 발생하면 해당 닉네임을 가진 유저가 없는 것으로 판단
        result = users.objects.get(nickname = request.GET['nickname'])
    except Exception as e:
        #해당되는 유저가 없음으로 해당 닉네임으로 가입 가능
        return JsonResponse({"result":True})

    #해당되는 유저가 있음으로 해당 닉네임으로 가입 불가능
    return JsonResponse({"result":False})


@requestBodyToJson
def email_check(data):
    print(data)
    try:
        #해당 이메일을 가진 유저가 존재하는지 확인
        #에러가 발생하면 해당 이메일을 가진 유저가 없는 것으로 판단
        result = users.objects.get(email = data['email'])
    except Exception as e:
        certification_number = ""
        for i in range(6):
            certification_number += random.choice(string.digits)

        # 이전 인증 요청이 있는지 확인
        try:
            # 있으면 기존 인증 요청 업데이트
            prev_check = mail_confirm.objects.get(email = data['email'])
            prev_check.cert_number = certification_number
            prev_check.save()
        except Exception as e:
            # 없으면 mail_confirm 테이블에 인증번호 저장
            mail_confirm(
                    email = data["email"],
                    cert_number = certification_number).save()

        email = EmailMessage(
            '회원 가입 인증번호',        # 제목
            certification_number,       # 내용
            to=[data['email']],  # 받는 이메일 리스트
        )
        email.send()
        return JsonResponse({"result":True})

    #해당되는 이메일이 존재하여 해당 이메일로 신규가입 불가능
    return JsonResponse({"result":False})


@requestBodyToJson
def email_confirm(data):
    try:
        result = mail_confirm.objects.get(email = data['email'], cert_number = data['cert_number'])
        result.delete() # 인증 완료된 기록은 삭제
        return JsonResponse({"result":True})
    except Exception as e:
        return JsonResponse({"result":False})


@requestBodyToJson
def signup(data):
    #입력으로 들어온 유저 정보를 이용해 데이터베이스 유저 테이블에 정보를 삽입, 성공메시지 반환
    try:
        users(
            email = data["email"],
            pw = hashingPw(data["pw"]),
            nickname = data["nickname"]).save()

        return JsonResponse({"result":True})
    except Exception as e:
        print(e)
        return JsonResponse({"result":False})


@requestBodyToJson
def login(data):
    #해당 유저를 데이터베이스에서 조회
    try:
        user = users.objects.get(email = data['email'])
    except Exception as e:
        # 가입하지 않은 이메일인 경우
        return JsonResponse({"result":False, "email_state":False})

    #비밀번호 일치 여부 확인
    if bcrypt.checkpw(data['pw'].encode('utf-8'), user.pw.encode('utf-8')):
        # 닉네임과 프로필 사진 URL만 포함
        user_data = {
            "idx":user.idx,
            "email":user.email,
            "membership":user.membership,
            "nickname":user.nickname,
            "profile_pic":user.profile_pic
        }

        token_data = {
            "idx":user.idx,
            "email":user.email,
            "membership":user.membership,
        }
        # idx, email, membership은 JWT에 담아서 반환
        access_token, refresh_token = create_jwt(token_data)

        response = JsonResponse({"result":True, "email_state":True, "user_data":user_data})
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
        return response
    else:
        return JsonResponse({"result":False, "email_state":True})


@requestBodyToJson
def search_pw(data):
    try:
        #해당 이메일을 가진 유저가 존재하는지 확인
        #에러가 발생하면 해당 이메일을 가진 유저가 없는 것으로 판단
        result = users.objects.get(email = data['email'])
    except Exception as e:
        #해당 이메일에 대한 정보가 존재하지 않음
        return JsonResponse({"result":False})

    #새로운 임시 비밀번호 생성
    new_pw = ""
    string_pool = string.digits + string.ascii_lowercase

    for i in range(8):
        new_pw += random.choice(string_pool)

    result.pw = hashingPw(new_pw)
    result.save()

    email = EmailMessage(
        '임시 비밀번호',             # 제목
        new_pw,                     # 내용
        to=[data['email']],  # 받는 이메일 리스트
    )
    email.send()
    return JsonResponse({"result":True})


@verify_token
@requestBodyToJson
def nicknamechange(data):
    #해당 유저를 데이터베이스에서 조회
    try:
        user = users.objects.get(idx=data['idx'])
    except Exception as e:
        return JsonResponse({"result":False, "user_state":False})

    # 닉네임 변경
    user.nickname = data['nickname']
    user.save()

    return JsonResponse({"result":True, "user_state":True})


@verify_token
@requestBodyToJson
def pwchange(data):
    #해당 유저를 데이터베이스에서 조회
    try:
        user = users.objects.get(idx=data['idx'])
    except Exception as e:
        return JsonResponse({"result":False, "user_state":False})

    #비밀번호 일치 여부 확인, 일치시 닉네임 변경
    if bcrypt.checkpw(data['pw'].encode('utf-8'), user.pw.encode('utf-8')):
        user.pw = hashingPw(data["new_pw"])
        user.save()
        return JsonResponse({"result":True, "user_state":True})
    else:
        return JsonResponse({"result":False, "user_state":True})


@verify_token
def profile_pic_change(request):
    #해당 유저를 데이터베이스에서 조회
    try:
        user = users.objects.get(idx = request.POST['idx'])
    except:
        return JsonResponse({"result":False, "user_state":False})

    s3_client = boto3.client(
        's3',
        aws_access_key_id = settings.AWS_S3_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_S3_SECRET_ACCESS_KEY,
    )
    if len(request.FILES) != 0:

        file = request.FILES['profile_pic']
        pic_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/profile_pic/{request.POST['idx']}/{request.POST['idx']}.png"

        s3_client.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            f"profile_pic/{request.POST['idx']}/{request.POST['idx']}.png",
            ExtraArgs={
                "ContentType": file.content_type,
            }
        )

        user.profile_pic = pic_url
        user.save()

        return JsonResponse({"result":True, "profile_pic":pic_url})
    else:
        s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=f"profile_pic/{request.POST['idx']}/{request.POST['idx']}.png")

        user = users.objects.get(idx = request.POST['idx'])
        user.profile_pic = ''
        user.save()

        return JsonResponse({"result":True, "profile_pic":None})


@verify_token
@requestBodyToJson
def inactive(data):
    #해당 유저를 데이터베이스에서 조회
    try:
        user = users.objects.get(idx = data['idx'])
    except Exception as e:
        return JsonResponse({"result":False, "user_state":False})

    if bcrypt.checkpw(data['pw'].encode('utf-8'), user.pw.encode('utf-8')):
        # 비밀번호 일치 시 해당 유저를 비활성화 데이터베이스에 추가
        inactive_users(
                idx = user.idx,
                email = user.email,
                pw = user.pw,
                nickname = user.nickname,
                membership = user.membership,
                last_update = user.last_update,
                created_at = user.created_at).save()

        #해당 유저정보를 유저 테이블에서 제거
        user.delete()
        return JsonResponse({"result":True, "user_state":True})
    else:
        return JsonResponse({"result":False, "user_state":True})
