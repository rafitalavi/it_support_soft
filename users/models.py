from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, user_id, name, email, password=None, **extra_fields):
        if not user_id:
            raise ValueError("The User ID must be provided")
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(user_id=user_id, name=name, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, name, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(user_id, name, email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Custom unique ID for login (e.g., "EMP001", "IT1024")
    user_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    # Tells Django to use 'user_id' for authentication/login
    USERNAME_FIELD = 'user_id'
    
    # Prompted alongside user_id and password when running 'createsuperuser'
    REQUIRED_FIELDS = ['name', 'email']

    def __str__(self):
        return f"{self.name} ({self.user_id})"