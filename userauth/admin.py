from django.contrib import admin
from .models import users, func_log, ml_project, ml_model, mail_confirm, inactive_users

# Register your models here.
admin.site.register(users)
admin.site.register(func_log)
admin.site.register(ml_project)
admin.site.register(ml_model)
admin.site.register(mail_confirm)
admin.site.register(inactive_users)
