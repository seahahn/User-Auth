import email
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import auth
from django.http import HttpResponse
from .models import inactive_users, users, func_log, ml_project, ml_model, mail_confirm
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from django.core.mail import EmailMessage
import string
import random

# Create your views here.

#테스트 함수
def index(request):
    csrf_token = get_token(request)
    return HttpResponse("True")


@csrf_exempt
def nickname_check(request):
    result = None
    try:
        #해당 닉네임을 가진 유저가 존재하는지 확인
        #에러가 발생하면 해당 닉네임을 가진 유저가 없는 것으로 판단
        result = users.objects.get(nickname = request.GET['nickname'])
    except:
        #해당되는 유저가 없음으로 해당 닉네임으로 가입 가능
        return True
    #해당되는 유저가 있음으로 해당 닉네임으로 가입 불가능
    return False


@csrf_exempt
def email_check(request):
    try:
        #해당 이메일을 가진 유저가 존재하는지 확인
        #에러가 발생하면 해당 이메일을 가진 유저가 없는 것으로 판단
        result = users.objects.get(email = request.GET['email'])
    except:
        certification_number = ""
        for i in range(6):
            certification_number += random.choice(string.digits)
        mail_confirm(
                email = request.GET["email"],
                cert_number = certification_number).save()
        email = EmailMessage(
            '회원 가입 인증번호',        # 제목
            certification_number,       # 내용
            to=[request.GET['email']],  # 받는 이메일 리스트
        )
        email.send()
        return HttpResponse("True")
    #해당되는 이메일이 존재하여 해당 이메일로 신규가입 불가능
    return HttpResponse("False")


@csrf_exempt
def signup(request):
    if request.method == "POST":
        # TODO 프론트에서 비밀번호 일치 여부 확인 기능 추가하면 제외 예정
        #비밀번호와 비밀번호 확인 값의 일치를 확인, 불일치시 메시지 반환
        if request.POST['pw'] == request.POST['pw_confirm']:
            #입력으로 들어온 유저 정보를 이용해 데이터베이스 유저 테이블에 정보를 삽입, 성공메시지 반환
            # TODO DB 상에서 membership default 0으로 지정하기
            users(
                email = request.POST["email"],
                pw = request.POST["pw"],
                nickname = request.POST["nickname"],
                membership = int(request.POST["membership"])).save()
            return HttpResponse("success")

        return HttpResponse("password mismatch")

    return HttpResponse("NOT POST")


@csrf_exempt
def login(request):
    if request.method == "POST":
        #해당 유저를 데이터베이스에서 조회
        try:
            user = users.objects.get(email = request.POST['email'])
        except:
            # TODO 에러 메시지 사용자 친화적으로 변경하기
            return HttpResponse("이메일 존재X")

        #비밀번호 일치 여부 확인
        if request.POST['pw'] == user.pw:
            return HttpResponse("True")
        else:
            return HttpResponse("False")


    return HttpResponse("NOT POST")


@csrf_exempt
def search_pw(request):
    try:
        #해당 이메일을 가진 유저가 존재하는지 확인
        #에러가 발생하면 해당 이메일을 가진 유저가 없는 것으로 판단
        result = users.objects.get(email = request.GET['email'])
    except:
        #해당 이메일에 대한 정보가 존재하지 않음
        return HttpResponse("False")

    #새로운 임시 비밀번호 생성
    new_pw = ""
    string_pool = string.digits + string.ascii_lowercase
    for i in range(8):
        new_pw += random.choice(string_pool)
    result.pw = new_pw
    result.save()
    email = EmailMessage(
        '임시 비밀번호',             # 제목
        new_pw,                     # 내용
        to=[request.GET['email']],  # 받는 이메일 리스트
    )
    email.send()
    return HttpResponse("True")


@csrf_exempt
def nicknamechange(request):
    if request.method == "POST":
        #해당 유저를 데이터베이스에서 조회
        try:
            user = users.objects.get(email = request.POST['email'])
        except:
            return HttpResponse("이메일 존재X")

        #비밀번호 일치 여부 확인, 일치시 닉네임 변경
        user.nickname = request.POST['nickname']
        user.save()
        return HttpResponse("True")


    return HttpResponse("NOT POST")


@csrf_exempt
def pwchange(request):
    if request.method == "POST":
        #해당 유저를 데이터베이스에서 조회
        try:
            user = users.objects.get(email = request.POST['email'])
        except:
            return HttpResponse("이메일 존재X")

        #비밀번호 일치 여부 확인, 일치시 닉네임 변경
        if request.POST['pw'] == user.pw:
            user.pw = request.POST['new_pw']
            user.save()
            return HttpResponse("True")
        else:
            return HttpResponse("False")


    return HttpResponse("NOT POST")


@csrf_exempt
def profile_pic_change(request):
    if request.method == "POST":
        #해당 유저를 데이터베이스에서 조회
        try:
            user = users.objects.get(email = request.POST['email'])
        except:
            return HttpResponse("False")

        #프로필 사진 URL변경
        user.profile_pic = request.POST['profile_pic']
        user.save()
        return HttpResponse("True")

    return HttpResponse("NOT POST")


@csrf_exempt
def inactive(request):
    if request.method == "POST":
        #해당 유저를 데이터베이스에서 조회
        try:
            user = users.objects.get(email = request.POST['email'])
        except:
            return HttpResponse("이메일 존재X")
        #해당 유저를 비활성화 데이터베이스에 추가
        inactive_users(
                idx = user.idx,
                email = user.email,
                pw = user.pw,
                nickname = user.nickname,
                membership = user.membership,
                user_state = int(request.POST["user_state"])).save()
        #해당 유저정보를 유저 테이블에서 제거
        user.delete()

        return HttpResponse("success")

    return HttpResponse("NOT POST")
