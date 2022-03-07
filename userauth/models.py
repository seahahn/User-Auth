from django.db import models
from datetime import datetime


# # Create your models here.
class users(models.Model):
    idx = models.AutoField(primary_key=True, db_column="idx")
    email = models.CharField(max_length=255)
    pw = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255)
    membership = models.IntegerField()
    last_update = models.DateTimeField('last access', auto_now_add=True)
    created_at = models.DateTimeField('sign up', auto_now_add=True)
    class Meta:
        db_table = "users"


class func_log(models.Model):
    user_idx = models.ForeignKey(users, db_column="user_idx", on_delete=models.DO_NOTHING)
    func_code = models.CharField(max_length=255)
    is_worked = models.BooleanField()
    start_time = models.DateTimeField('start time')
    end_time = models.DateTimeField('end time')
    created_time = models.DateTimeField('create time', auto_now_add=True)
    class Meta:
        db_table = "func_log"


class ml_project(models.Model):
    idx = models.AutoField(primary_key=True, db_column="idx")
    user_idx = models.ForeignKey(users, db_column="user_idx", on_delete=models.DO_NOTHING)
    proj_name = models.CharField(max_length=255)
    last_update = models.DateTimeField('last update', auto_now_add=True)
    created_time = models.DateTimeField('create time', auto_now_add=True)
    class Meta:
        db_table = "ml_project"


class ml_model(models.Model):
    idx = models.AutoField(primary_key=True, db_column="idx")
    user_idx = models.ForeignKey(users, db_column="user_idx", on_delete=models.DO_NOTHING)
    model_name = models.CharField(max_length=255)
    last_update = models.DateTimeField('last update', auto_now_add=True)
    created_time = models.DateTimeField('create time', auto_now_add=True)
    class Meta:
        db_table = "ml_model"


class mail_confirm(models.Model):
    email = models.CharField(max_length=255)
    cert_number = models.CharField(max_length=6)
    class Meta:
            db_table = "mail_confirm"


class inactive_users(models.Model):
    idx = models.IntegerField()
    email = models.CharField(max_length=255)
    pw = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255)
    membership = models.IntegerField()
    user_state = models.IntegerField()
    last_update = models.DateTimeField('last access', auto_now_add=True)
    created_at = models.DateTimeField('secession', auto_now_add=True)
    class Meta:
        db_table = "inactive_users"