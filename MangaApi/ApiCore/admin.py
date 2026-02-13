from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from ApiCore.models.user_models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

# Define a new UserAdmin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    
    list_display = ['username', 'email', 'first_name', 'get_profile', 'is_staff']
    
    def get_profile(self, instance):
         if hasattr(instance, 'userprofile'):
              return instance.userprofile.get_profile_display()
         return '-'
    get_profile.short_description = 'Profile'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
