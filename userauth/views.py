import email
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import auth
from django.http import HttpResponse
from .models import users, func_log, ml_project, ml_model
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token

# Create your views here.

#테스트 함수
def index(request):
    csrf_token = get_token(request)
    return HttpResponse("True")


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


def email_check(request):
    try:
        #해당 이메일을 가진 유저가 존재하는지 확인
        #에러가 발생하면 해당 이메일을 가진 유저가 없는 것으로 판단
        result = users.objects.get(email = request.GET['email'])
    except:
        #이메일 난수 전송
        return True
    #해당되는 이메일이 존재하여 해당 이메일로 신규가입 불가능
    return False

@csrf_exempt
def signup(request):
    if request.method == "POST":
        #비밀번호와 비밀번호 확인 값의 일치를 확인, 불일치시 메시지 반환
        if request.POST['pw'] == request.POST['pw_confirm']:
            #입력으로 들어온 유저 정보를 이용해 데이터베이스 유저 테이블에 정보를 삽입, 성공메시지 반환
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
        
        try:
            user = users.objects.get(email = request.POST['email'])
        except:
            return HttpResponse("이메일 존재X")


        if request.POST['pw'] == user.pw:
            return HttpResponse("True")
        else:
            return HttpResponse("False")


    return HttpResponse("NOT POST")