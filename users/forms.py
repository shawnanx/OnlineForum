from django.contrib.auth.forms import UserCreationForm

from .models import User
from django.contrib.auth import get_user_model
User = get_user_model()

class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
