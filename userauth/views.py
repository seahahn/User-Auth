from django.contrib.auth.models import User
from django.contrib import auth
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.core.mail import EmailMessage
from base import settings
from .models import inactive_users, users, mail_confirm
import bcrypt, string, random, boto3, json



# JSON으로 들어오는 데이터를 파싱하기 위한 데코레이터
def requestBodyToJson(original):
    def wrapper(request):
        return original(json.loads(request.body))

    return wrapper

# 비밀번호 해싱 기능
def hashingPw(pw):
    hash = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
    return hash.decode('utf-8') # DB에 byte string 저장이 불가능하므로 decode함

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
    print(data)
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
        user_data = {
            "idx":user.idx,
            "email":user.email,
            "nickname":user.nickname,
            "profile_pic":user.profile_pic,
            "membership":user.membership,
        }
        return JsonResponse({"result":True, "email_state":True, "user_data":user_data})
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


def profile_pic_change(request):
    s3_client = boto3.client(
        's3',
        aws_access_key_id = settings.AWS_S3_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_S3_SECRET_ACCESS_KEY,
    )
    if len(request.FILES) != 0:

        file = request.FILES['profile_pic']
        pic_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/profile_pic/{request.POST['user_idx']}/{request.POST['user_idx']}.png"

        s3_client.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            f"profile_pic/{request.POST['user_idx']}/{request.POST['user_idx']}.png",
            ExtraArgs={
                "ContentType": file.content_type,
            }
        )

        user = users.objects.get(idx = request.POST['user_idx'])
        user.profile_pic = pic_url
        user.save()

        return JsonResponse({"result":True, "profile_pic":pic_url})
    else:
        s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=f"profile_pic/{request.POST['user_idx']}/{request.POST['user_idx']}.png")

        user = users.objects.get(idx = request.POST['user_idx'])
        user.profile_pic = ''
        user.save()

        return JsonResponse({"result":True, "profile_pic":None})


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
