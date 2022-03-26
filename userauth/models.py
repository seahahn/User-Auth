from django.db import models
from datetime import datetime


# # Create your models here.
class users(models.Model):
    idx = models.AutoField(primary_key=True, db_column="idx")
    email = models.CharField(max_length=255)
    pw = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255)
    profile_pic = models.CharField(max_length=255, default="")
    membership = models.IntegerField(default= 0)
    last_update = models.DateTimeField('last access', auto_now_add=True)
    created_at = models.DateTimeField('sign up', auto_now_add=True)
    class Meta:
        db_table = "users"


class func_log(models.Model):
    user_idx = models.IntegerField()
    func_code = models.CharField(max_length=255)
    is_worked = models.IntegerField(default= 0)
    error_msg = models.TextField(default="")
    start_time = models.DateTimeField('start time')
    end_time = models.DateTimeField('end time')
    created_at = models.DateTimeField('create time', auto_now_add=True)
    class Meta:
        db_table = "func_log"


class ml_project(models.Model):
    idx = models.AutoField(primary_key=True, db_column="idx")
    user_idx = models.ForeignKey(users, db_column="user_idx", on_delete=models.CASCADE)
    proj_name = models.CharField(max_length=255)
    last_update = models.DateTimeField('last update', auto_now_add=True)
    created_at = models.DateTimeField('create time', auto_now_add=True)
    class Meta:
        db_table = "ml_project"


class ml_model(models.Model):
    idx = models.AutoField(primary_key=True, db_column="idx")
    user_idx = models.ForeignKey(users, db_column="user_idx", on_delete=models.CASCADE)
    model_name = models.CharField(max_length=255)
    model_url = models.CharField(max_length=255, default="")
    last_update = models.DateTimeField('last update', auto_now_add=True)
    created_at = models.DateTimeField('create time', auto_now_add=True)
    class Meta:
        db_table = "ml_model"


class mail_confirm(models.Model):
    email = models.CharField(max_length=255)
    cert_number = models.CharField(max_length=6)
    last_update = models.DateTimeField('last update', auto_now_add=True)
    created_at = models.DateTimeField('create time', auto_now_add=True)
    class Meta:
            db_table = "mail_confirm"


class inactive_users(models.Model):
    idx = models.IntegerField(primary_key=True)
    email = models.CharField(max_length=255)
    pw = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255)
    membership = models.IntegerField()
    last_update = models.DateTimeField('last access')
    created_at = models.DateTimeField('create time')
    user_state = models.IntegerField(default=1)
    inactivated_at = models.DateTimeField('secession', auto_now_add=True)
    class Meta:
        db_table = "inactive_users"