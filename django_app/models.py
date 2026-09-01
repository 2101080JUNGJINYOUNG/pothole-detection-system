"""
Django models for Deep-Guardian
These models match the existing PostgreSQL schema
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import bcrypt


class UserManager(BaseUserManager):
    """Custom user manager"""
    def create_user(self, username, password=None, role='user'):
        user = self.model(username=username, role=role)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None):
        return self.create_user(username, password, role='admin')


class User(models.Model):
    """User model matching existing users table"""
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, default='user')  # 'user' or 'admin'
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        managed = False  # Don't manage table creation (use existing table)
    
    def set_password(self, raw_password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(raw_password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, raw_password):
        """Check password using bcrypt"""
        return bcrypt.checkpw(raw_password.encode('utf-8'), self.password_hash.encode('utf-8'))


class Pothole(models.Model):
    """Pothole model matching existing potholes table"""
    id = models.AutoField(primary_key=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    depth_ratio = models.DecimalField(max_digits=5, decimal_places=4)
    validation_result = models.BooleanField()
    detected_at = models.DateTimeField(auto_now_add=True)
    image_path = models.CharField(max_length=500, null=True, blank=True)
    bbox_x1 = models.IntegerField(null=True, blank=True)
    bbox_y1 = models.IntegerField(null=True, blank=True)
    bbox_x2 = models.IntegerField(null=True, blank=True)
    bbox_y2 = models.IntegerField(null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Additional fields from add_user_auth.sql
    approved_for_training = models.BooleanField(null=True, blank=True, default=None)
    reviewed_by_id = models.IntegerField(null=True, blank=True, db_column='reviewed_by')  # IntegerField로 변경하여 기존 DB 스키마와 호환
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(null=True, blank=True)
    
    @property
    def reviewed_by(self):
        """reviewed_by_id를 통해 User 객체 반환"""
        if self.reviewed_by_id:
            try:
                return User.objects.get(id=self.reviewed_by_id)
            except User.DoesNotExist:
                return None
        return None
    
    @reviewed_by.setter
    def reviewed_by(self, user):
        """User 객체를 받아서 reviewed_by_id 설정"""
        if user:
            self.reviewed_by_id = user.id
        else:
            self.reviewed_by_id = None
    
    # Additional fields from add_risk_fields.sql
    location_type = models.CharField(max_length=50, default='general')
    risk_level = models.CharField(max_length=20, default='medium')
    priority_score = models.DecimalField(max_digits=10, decimal_places=4, default=1.0)
    location_description = models.CharField(max_length=200, null=True, blank=True)
    
    class Meta:
        db_table = 'potholes'
        managed = False  # Don't manage table creation (use existing table)
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['latitude', 'longitude'], name='idx_potholes_location'),
            models.Index(fields=['-detected_at'], name='idx_potholes_detected_at'),
            models.Index(fields=['validation_result'], name='idx_potholes_validation'),
            models.Index(fields=['-priority_score'], name='idx_potholes_priority'),
            models.Index(fields=['risk_level'], name='idx_potholes_risk_level'),
            models.Index(fields=['location_type'], name='idx_potholes_location_type'),
            models.Index(fields=['approved_for_training'], name='idx_potholes_approved'),
            models.Index(fields=['-reviewed_at'], name='idx_potholes_reviewed'),
        ]

