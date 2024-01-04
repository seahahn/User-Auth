from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.core.mail import EmailMessage
from base import settings
from .models import inactive_users, users, mail_confirm
from datetime import datetime, timezone, timedelta
import bcrypt, string, random, boto3, json, jwt
from rest_framework.decorators import api_view
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


SECRET_KEY = settings.SECRET_KEY
JWT_ISS = settings.JWT_ISS

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
            jwt.decode(rt, SECRET_KEY, issuer=JWT_ISS, algorithms="HS256") # refresh_token이 유효하지 않으면 에러 발생
            jwt.decode(at, SECRET_KEY, algorithms="HS256")
            return original(request)
        except Exception as e:
            return JsonResponse({"result":False, "token_state":False, "message": str(e)})

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



@swagger_auto_schema(
        method='get',
        operation_summary="사용자 접속 중 JWT 토큰 갱신하기 위한 함수",
        operation_description="""
        사용자 접속 중 JWT 토큰 갱신하기 위한 함수
        ---
        - 사용자의 쿠키에 저장된 refresh_token과 access_token 검증
            - 유효하지 않은 토큰인 경우 메시지와 함께 False 반환
        - 검증되면 access_token 재발급
            - refresh_token 유효 기간이 1시간 이내이면 refresh_token도 함께 재발급
        - 재발급한 토큰을 쿠키에 포함
            - access_token은 응답 데이터에도 포함

        ### Returns:
        #### 유효하지 않은 토큰인 경우
        - JsonResponse: {"result":False, "token_state":False, "message":"비정상적 갱신 요청"}
        #### 유효한 토큰인 경우
        - JsonResponse: {"result":True, "token_state":True, "token":access_token}
        """,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description='토큰 유효 ? True : False', type=openapi.TYPE_BOOLEAN),
                    'token_state': openapi.Schema(description='토큰 유효 ? True : False', type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(description='토큰 유효 ? None : "비정상적 갱신 요청"', type=openapi.TYPE_STRING),
                    'token': openapi.Schema(description='토큰 유효 ? access_token : None', type=openapi.TYPE_STRING),
                    }
            )
        },
        tags=['token'],
    )
@api_view(['GET'])
def refresh_jwt(request):
    # 토큰을 검증하여 유효한 토큰인지 확인
    rt = request.COOKIES.get("refresh_token")
    at = request.COOKIES.get("access_token")
    try:
        jwt.decode(rt, SECRET_KEY, issuer=JWT_ISS, algorithms="HS256") # refresh_token이 유효하지 않으면 에러 발생
        jwt.decode(at, SECRET_KEY, algorithms="HS256")
    except Exception as e:
        return JsonResponse({"result":False, "token_state":False, "message":"비정상적 갱신 요청"})

    # 토큰을 갱신하기 위해 새로운 토큰을 발급
    at_data = jwt.decode(at, SECRET_KEY, algorithms="HS256")
    at_data['exp'] = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    access_token = jwt.encode(at_data, SECRET_KEY, algorithm='HS256')

    response = JsonResponse({"result":True, "token_state":True, "token":access_token})
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="None", secure=True)

    # refresh_token의 유효 기간 확인 후 만료 1시간 이내이면 갱신하기
    rt_data = jwt.decode(rt, SECRET_KEY, algorithms="HS256")
    if datetime.fromtimestamp(rt_data['exp'], tz=timezone.utc) < datetime.now(tz=timezone.utc) + timedelta(hours=1):
        rt_data['exp'] = datetime.now(tz=timezone.utc) + timedelta(days=1)
        refresh_token = jwt.encode(rt_data, SECRET_KEY, algorithm='HS256')
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="None", secure=True)

    return response


@swagger_auto_schema(
        method='get',
        operation_summary="사용자 로그아웃 시 토큰 삭제하기 위한 함수",
        operation_description="""
        사용자 로그아웃 시 토큰 삭제하기 위한 함수
        ---
        - 사용자가 웹 앱에서 로그아웃하는 경우 쿠키에 저장된 사용자의 토큰을 삭제

        ### Returns:
        - JsonResponse: {"result":True}
        """,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description='문제 없으면 True', type=openapi.TYPE_BOOLEAN),
                    }
            )
        },
        tags=['token'],
    )
@api_view(['GET'])
def remove_jwt(_):
    response = JsonResponse({"result":True})
    response.delete_cookie("access_token", samesite="None")
    response.delete_cookie("refresh_token", samesite="None")
    return response


@swagger_auto_schema(
        method='get',
        operation_summary="웹 앱 접속 시 CSRF Token 발급 위한 함수",
        operation_description="""
        웹 앱 접속 시 CSRF Token 발급 위한 함수
        ---
        ### Returns:
        - JsonResponse: {"result":True, "csrf_token":csrf_token}
        """,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description='문제 없으면 True', type=openapi.TYPE_BOOLEAN),
                    'csrf_token': openapi.Schema(description='CSRF 토큰', type=openapi.TYPE_STRING),
                    }
            )
        },
        tags=['token'],
    )
@api_view(['GET'])
def index(request):
    csrf_token = get_token(request)
    return JsonResponse({"result":True, "csrf_token":csrf_token})


@swagger_auto_schema(
        method='get',
        operation_summary="회원가입 시 닉네임 중복 체크를 위한 함수",
        operation_description="""
            회원가입 시 닉네임 중복 체크를 위한 함수
            ---
            ### Args:
            - request (HttpRequest):
                - nickname (String): 중복 체크 대상 닉네임

            ### Returns:
            - JsonResponse: {"result":Boolean}
            """,
        manual_parameters=[openapi.Parameter('nickname', openapi.IN_QUERY, description="중복 체크 대상 닉네임", type=openapi.TYPE_STRING)],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description="중복 ? False : True", type=openapi.TYPE_BOOLEAN),
                    }
            )
        },
        tags=['check'],
    )
@api_view(['GET'])
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


@swagger_auto_schema(
        method='post',
        operation_summary="회원가입 시 이메일 인증 메일 발송을 위한 함수",
        operation_description="""
            회원가입 시 이메일 인증 번호 발송을 위한 함수
            ---
            - 입력받은 이메일을 DB users table에서 조회
            - 조회된 이메일이 없으면 무작위 6자리 인증 번호 생성
            - 이메일과 인증 번호를 DB mail_confirm table에 저장
                - 이후 동일 이메일로 인증 재요청 시 기존에 저장된 DB row의 인증 번호를 업데이트
            - 생성된 인증 번호를 사용자 이메일로 발송

            ### Args:
            - data (JSON):
                - email (String): 이메일

            ### Returns:
            - JsonResponse: {"result":Boolean}
            """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(description="사용자가 중복 확인을 위해 입력한 이메일", type=openapi.TYPE_STRING)
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description="중복 ? False : True", type=openapi.TYPE_BOOLEAN),
                    }
            )
        },
        tags=['check'],
    )
@api_view(['POST'])
@requestBodyToJson
def email_check(data):
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


@swagger_auto_schema(
        method='post',
        operation_summary="회원가입 시 이메일 인증 번호 체크를 위한 함수",
        operation_description="""
            회원가입 시 이메일 인증 번호 체크를 위한 함수
            ---
            - 입력받은 이메일과 인증번호를 DB mail_confirm table에서 조회
            - 일치하는 기록이 존재하면 DB 데이터 삭제 및 인증 완료 처리
            - 일치하는 기록이 없으면 인증번호가 틀린 것으로 판단

            ### Args:
            - data (JSON):
                - email (String): 이메일
                - cert_number (Integer): 인증 번호

            ### Returns:
            - JsonResponse: {"result":Boolean}
            """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'cert_number'],
            properties={
                'email': openapi.Schema(description="사용자가 중복 확인을 위해 입력한 이메일", type=openapi.TYPE_STRING),
                'cert_number': openapi.Schema(description="사용자가 입력한 이메일 인증 번호", type=openapi.TYPE_INTEGER),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description="인증 완료 ? True : False", type=openapi.TYPE_BOOLEAN),
                    }
            )
        },
        tags=['check'],
    )
@api_view(['POST'])
@requestBodyToJson
def email_confirm(data):
    try:
        result = mail_confirm.objects.get(email = data['email'], cert_number = data['cert_number'])
        result.delete() # 인증 완료된 기록은 삭제
        return JsonResponse({"result":True})
    except Exception as e:
        return JsonResponse({"result":False})


@swagger_auto_schema(
        method='post',
        operation_summary="사용자 회원가입 처리를 위한 함수",
        operation_description="""
            사용자 회원가입 처리를 위한 함수
            ---
            ### Args:
            - data (JSON):
                - email (String): 이메일
                - pw (String): 비밀번호
                - nickname (String): 닉네임

            ### Returns:
            - JsonResponse: {"result":Boolean}
            """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'pw', 'nickname'],
            properties={
                'email': openapi.Schema(description="사용자 이메일", type=openapi.TYPE_STRING),
                'pw': openapi.Schema(description="사용자 비밀번호", type=openapi.TYPE_STRING),
                'nickname': openapi.Schema(description="사용자 닉네임", type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description="회원가입 완료 ? True : False", type=openapi.TYPE_BOOLEAN),
                    }
            )
        },
        tags=['auth'],
    )
@api_view(['POST'])
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
        return JsonResponse({"result":False})


@swagger_auto_schema(
        method='post',
        operation_summary="사용자 로그인 처리를 위한 함수",
        operation_description="""
            사용자 로그인 처리를 위한 함수
            ---
            - 사용자가 입력한 이메일과 비밀번호를 데이터베이스에서 조회하여 로그인 처리
            - 로그인 성공 시 JWT 토큰을 생성
                - access_token은 응답 데이터에 포함
                - refresh_token은 쿠키에 포함되어 오직 User-Auth 서버와의 통신에서만 사용됨

            ### Args:
            - data (JSON):
                - email (String): 이메일
                - pw (String): 비밀번호

            ### Returns:
            #### 가입하지 않은 경우
            - JsonResponse: {"result":False, "email_state":False}

            #### 가입한 경우 & 비밀번호가 틀린 경우
            - JsonResponse: {"result":False, "email_state":True}

            #### 가입한 경우 & 비밀번호가 일치하는 경우
            - JsonResponse: {"result":True, "email_state":True, "user_data":Object, "token":String}
            """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'pw'],
            properties={
                'email': openapi.Schema(description="사용자 이메일", type=openapi.TYPE_STRING),
                'pw': openapi.Schema(description="사용자 비밀번호", type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description="로그인 성공 ? True : False", type=openapi.TYPE_BOOLEAN),
                    'email_state': openapi.Schema(description="가입된 이메일 ? True : False", type=openapi.TYPE_BOOLEAN),
                    'user_data': openapi.Schema(
                        properties={
                            "idx":openapi.Schema(description="사용자 고유 번호", type=openapi.TYPE_INTEGER),
                            "email":openapi.Schema(description="사용자 이메일", type=openapi.TYPE_STRING),
                            "membership":openapi.Schema(description="사용자 멤버십 등급", type=openapi.TYPE_INTEGER),
                            "nickname":openapi.Schema(description="사용자 닉네임", type=openapi.TYPE_STRING),
                            "profile_pic":openapi.Schema(description="사용자 프로필 사진 S3 URL", type=openapi.TYPE_STRING),
                        },
                        description="로그인 성공 ? {idx, email, membership, nickname, profile_pic} : None", type=openapi.TYPE_OBJECT),
                    'token': openapi.Schema(description="로그인 성공 ? access_token : None", type=openapi.TYPE_STRING),
                    }
            )
        },
        tags=['auth'],
    )
@api_view(['POST'])
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

        response = JsonResponse({"result":True, "email_state":True, "user_data":user_data, "token":access_token})
        response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="None", secure=True)
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="None", secure=True)
        return response
    else:
        return JsonResponse({"result":False, "email_state":True})


@swagger_auto_schema(
        method='post',
        operation_summary="사용자 임시 비밀번호 발급을 위한 함수",
        operation_description="""
            사용자 임시 비밀번호 발급을 위한 함수
            ---
            - 입력받은 이메일을 데이터베이스에서 조회
                - 데이터베이스에 존재하지 않는 이메일인 경우 False 반환
            - 가입된 이메일인 경우 8자의 임시 비밀번호 생성 후 메일로 발송

            ### Args:
            - data (JSON):
                - email (String): 사용자 이메일

            ### Returns:
            - JsonResponse: {"result":Boolean}
            """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(description="사용자 이메일", type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description="사용자 존재 ? True : False", type=openapi.TYPE_BOOLEAN),
                    }
            )
        },
        tags=['change'],
    )
@api_view(['POST'])
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


@swagger_auto_schema(
        method='post',
        operation_summary="사용자 닉네임 변경을 위한 함수",
        operation_description="""
            사용자 닉네임 변경을 위한 함수
            ---
            - 입력받은 idx(사용자 고유 번호)를 데이터베이스에서 조회
            - 조회된 유저의 닉네임을 입력받은 닉네임으로 변경

            ### Args:
            - data (JSON):
                - idx (Integer): 사용자 고유 번호
                - nickname (String): 닉네임

            ### Returns:
            - JsonResponse: {"result":Boolean, "user_state":Boolean}
            """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['idx', 'nickname'],
            properties={
                'idx': openapi.Schema(description="사용자 이메일", type=openapi.TYPE_INTEGER),
                'nickname': openapi.Schema(description="사용자 닉네임", type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description="변경 완료 ? True : False", type=openapi.TYPE_BOOLEAN),
                    'user_state': openapi.Schema(description="사용자 존재 ? True : False", type=openapi.TYPE_BOOLEAN),
                    }
            )
        },
        tags=['change'],
    )
@api_view(['POST'])
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


@swagger_auto_schema(
        method='post',
        operation_summary="사용자 비밀번호 변경을 위한 함수",
        operation_description="""
            사용자 비밀번호 변경을 위한 함수
            ---
            - 입력받은 idx(사용자 고유 번호)를 데이터베이스에서 조회
            - 조회된 사용자의 비밀번호와 pw(입력받은 기존 비밀번호)의 일치 여부 확인
            - 일치하는 경우 사용자 비밀번호를 new_pw(새로운 비밀번호)로 변경

            ### Args:
            - data (JSON):
                - idx (Integer): 사용자 고유 번호
                - pw (String): 기존 비밀번호
                - new_pw (String): 새로운 비밀번호

            ### Returns:
            - JsonResponse: {"result":Boolean, "user_state":Boolean}
            """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['idx', 'pw', 'new_pw'],
            properties={
                'idx': openapi.Schema(description="사용자 이메일", type=openapi.TYPE_INTEGER),
                'pw': openapi.Schema(description="기존 사용자 비밀번호", type=openapi.TYPE_STRING),
                'new_pw': openapi.Schema(description="새로운 사용자 비밀번호", type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description="비밀번호 변경 완료 ? True : False", type=openapi.TYPE_BOOLEAN),
                    'user_state': openapi.Schema(description="사용자 존재 ? True : False", type=openapi.TYPE_BOOLEAN),
                    }
            )
        },
        tags=['change'],
    )
@api_view(['POST'])
@verify_token
@requestBodyToJson
def pwchange(data):
    # 해당 유저를 데이터베이스에서 조회
    try:
        user = users.objects.get(idx=data['idx'])
    except Exception as e:
        return JsonResponse({"result":False, "user_state":False})

    # 기존 비밀번호 일치 여부 확인, 일치시 비밀번호 변경
    if bcrypt.checkpw(data['pw'].encode('utf-8'), user.pw.encode('utf-8')):
        user.pw = hashingPw(data["new_pw"])
        user.save()
        return JsonResponse({"result":True, "user_state":True})
    else:
        return JsonResponse({"result":False, "user_state":True})


@swagger_auto_schema(
        method='post',
        operation_summary="사용자 프로필 사진 변경을 위한 함수",
        operation_description="""
            사용자 프로필 사진 변경을 위한 함수
            ---
            - 입력받은 idx(사용자 고유 번호)를 데이터베이스에서 조회
            - 프로필 사진 변경인 경우 (len(request.FILES) != 0)
                - 프로필 사진 파일을 S3에 업로드
                - (최초 업로드인 경우) 사용자 프로필 사진 S3 URL을 사용자 DB row의 profile_pic column에 저장
            - 프로필 사진 삭제인 경우 (len(request.FILES) == 0)
                - S3에 저장된 사용자의 프로필 사진 파일 삭제
                - DB에 저장된 사용자의 프로필 사진 S3 URL 제거

            ### Args:
            - request (HttpRequest):
                - idx (Integer): 사용자 고유 번호 # request.POST
                - profile_pic (File): 사용자 프로필 사진 # request.FILES

            ### Returns:
            #### 존재하지 않는 사용자인 경우
            - JsonResponse: {"result":False, "user_state":False}
            #### 존재하는 사용자인 경우
            - JsonResponse: {"result":True, "profile_pic":String | None}
            """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['idx'],
            properties={
                'idx': openapi.Schema(description="사용자 이메일", type=openapi.TYPE_INTEGER),
                'profile_pic': openapi.Schema(description="새로운 사용자 프로필 사진", type=openapi.TYPE_FILE),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description="요청 수행 완료 ? True : False", type=openapi.TYPE_BOOLEAN),
                    'user_state': openapi.Schema(description="사용자 존재 ? True : False", type=openapi.TYPE_BOOLEAN),
                    'profile_pic': openapi.Schema(description="사진 업로드 ? pic_url : None", type=openapi.TYPE_STRING),
                    }
            )
        },
        tags=['change'],
    )
@api_view(['POST'])
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


@swagger_auto_schema(
        method='post',
        operation_summary="사용자 탈퇴 처리를 위한 함수",
        operation_description="""
            사용자 탈퇴 처리를 위한 함수
            ---
            - 입력받은 idx(사용자 고유 번호)를 데이터베이스에서 조회
            - 조회된 사용자의 비밀번호와 pw(입력받은 비밀번호)의 일치 여부 확인
            - 일치하는 경우 inactive_users table에 사용자 정보 저장
            - users table에서 사용자 정보 삭제

            ### Args:
            - request (JSON):
                - idx (Integer): 사용자 고유 번호
                - pw (String): 사용자 비밀번호

            ### Returns:
            - JsonResponse: {"result":Boolean, "user_state":Boolean}
            """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['idx', 'pw'],
            properties={
                'idx': openapi.Schema(description="사용자 이메일", type=openapi.TYPE_INTEGER),
                'pw': openapi.Schema(description="사용자 비밀번호", type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                    properties={
                    'result': openapi.Schema(description="요청 수행 완료 ? True : False", type=openapi.TYPE_BOOLEAN),
                    'user_state': openapi.Schema(description="사용자 존재 ? True : False", type=openapi.TYPE_BOOLEAN),
                    }
            )
        },
        tags=['auth'],
    )
@api_view(['POST'])
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
