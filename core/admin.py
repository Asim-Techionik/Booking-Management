from django.contrib import admin
from .models import UserModel, Client, Accessor, Job, Bid, Notification, Project, Quote
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    # Fields displayed in the user list view
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active', 'is_superuser')

    # Fields displayed when editing a user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'user_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields displayed when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'user_type', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    # Configurations for searching and ordering
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('email',)

    def save_model(self, request, obj, form, change):
        """Ensure the password is hashed before saving the user and trigger user creation."""
        if not change:  # Only create a new user if it's a new record, not an update
            # Use the custom create_user method to create the user and related model (Client/Accessor)
            user_type = form.cleaned_data.get('user_type', 'client')  # Default to 'client'
            user = UserModel.objects.create_user(
                email=obj.email,
                first_name=obj.first_name,
                last_name=obj.last_name,
                phone_number=obj.phone_number,
                password=form.cleaned_data['password1'],  # Set password
                user_type=user_type
            )
            # If this is a new user, don't save the form object (obj) directly, as we've already created the user
            obj = user
        super().save_model(request, obj, form, change)

# Register the user model with the custom admin class
admin.site.register(UserModel, CustomUserAdmin)
admin.site.register(Client)
admin.site.register(Accessor)
admin.site.register(Job)
admin.site.register(Bid)
admin.site.register(Notification)
admin.site.register(Project)
admin.site.register(Quote)