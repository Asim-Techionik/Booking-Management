from django.contrib import admin
from .models import UserModel, Client, Accessor, Job, Bid, Notification, Project, Quote
from django.contrib.auth.forms import UserChangeForm

class UserModelChangeForm(UserChangeForm):
    class Meta:
        model = UserModel
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'user_type', 'is_active', 'is_staff')

class UserModelAdmin(admin.ModelAdmin):
    form = UserModelChangeForm
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('user_type', 'is_active', 'is_staff')

admin.site.register(Client)
admin.site.register(UserModel, UserModelAdmin)
admin.site.register(Accessor)
admin.site.register(Job)
admin.site.register(Bid)
admin.site.register(Notification)
admin.site.register(Project)
admin.site.register(Quote)