# Country model

from django.db import models
from django.core.validators import RegexValidator, ValidationError
from datetime import date
from django.contrib.auth.models import User
import uuid

# Family Head Model
class FamilyHead(models.Model):
    HeadID = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)
    Surname = models.CharField(max_length=50)
    Gender = models.CharField(
        max_length=6,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        default='Male',
        null=False
    )
    Birthdate = models.DateField()
    MobileNo = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex='^\d{10}$', message='Enter exactly 10 digits.')],
        unique=True
        
    )
    Address = models.TextField()
    State = models.CharField(max_length=50)
    City = models.CharField(max_length=50)
    Pincode = models.CharField(
        max_length=6,
        validators=[RegexValidator(regex='^\d{6}$', message='Enter exactly 6 digits.')]
    )
    MaritalStatus = models.CharField(
        max_length=10,
        choices=[('Married', 'Married'), ('Unmarried', 'Unmarried')]
    )
    WeddingDate = models.DateField(null=True, blank=True)
    Photo = models.ImageField(upload_to='photos/', null=True, blank=True)

    EDUCATION_CHOICES = [
        ('Graduate', 'Graduate'),
        ('Post Graduate', 'Post Graduate'),
        ('Diploma', 'Diploma'),
    ]
    Education = models.CharField(max_length=20, choices=EDUCATION_CHOICES, default='Graduate')


    STATUS_CHOICES = [
        (0, 'Inactive'),
        (1, 'Active'),
        (9, 'Soft Deleted'),
    ]
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)

    def clean(self):
        if self.Birthdate and (date.today() - self.Birthdate).days < 21 * 365:
            raise ValidationError("The head must be at least 21 years old.")
        if self.MaritalStatus == 'Married' and not self.WeddingDate:
            raise ValidationError("Wedding date is required if married.")

    def __str__(self):
        return f'{self.Name} {self.Surname}'

    class Meta:
        db_table = 'family_head'

# Hobby model

class Hobby(models.Model):
    head = models.ForeignKey(
        'FamilyHead',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='head_hobbies'
    )
    Hobby = models.CharField(max_length=100)
    is_deleted = models.BooleanField(default=False)


    def __str__(self):
        if self.head:
            return f'{self.name} (Head: {self.head.Name})'
        elif self.member:
            return f'{self.name} (Member: {self.member.Name})'
        return self.name

    class Meta:
        db_table = 'hobby'


# Family Member Model
class FamilyMember(models.Model):
    MemberID = models.AutoField(primary_key=True)
    HeadID = models.ForeignKey(FamilyHead, on_delete=models.CASCADE)
    Name = models.CharField(max_length=50)
    Surname = models.CharField(max_length=50)
    
    Gender = models.CharField(
        max_length=6,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    )
    Relationship = models.CharField(max_length=50)
    Birthdate = models.DateField()
    MobileNo = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex='^\d{10}$', message='Enter exactly 10 digits.')],
        null=True, blank=True
    )
    Photo = models.ImageField(upload_to='photos/', null=True, blank=True)

    MaritalStatus = models.CharField(
        max_length=10,
        choices=[('Married', 'Married'), ('Unmarried', 'Unmarried')],
        default='Unmarried'
    )
    WeddingDate = models.DateField(null=True, blank=True)
    Education = models.CharField(max_length=50, null=True, blank=True)

    STATUS_CHOICES = [
        (0, 'Inactive'),
        (1, 'Active'),
        (9, 'Soft Deleted'),
    ]
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)

    def clean(self):
        if self.AddressOverride:
            if not all([self.Address, self.State, self.City, self.Pincode]):
                raise ValidationError("All address fields are required if AddressOverride is True.")
        else:
            self.Address = None
            self.State = None
            self.City = None
            self.Pincode = None

    def __str__(self):
        return f'{self.Name} {self.Surname} ({self.Relationship})'

    class Meta:
        db_table = 'family_member'


class Country(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'countries'


class State(models.Model):
    objects = models.Manager()
    STATUS_CHOICES = [
        (0, 'Inactive'),
        (1, 'Active'),
        (9, 'Soft Deleted'),
    ]
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    name = models.CharField(max_length=100)
    country = models.ForeignKey('Country', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'state'


class City(models.Model):

    STATUS_CHOICES = [
        (0, 'Inactive'),
        (1, 'Active'),
        (9, 'Soft Deleted'),
    ]
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, related_name="cities", on_delete=models.CASCADE)
    country_id = models.IntegerField()

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'city'



class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"

class AdminLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('other', 'Other'),
    ]
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=150)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    object_id = models.CharField(max_length=100, blank=True)
    object_type = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.username} - {self.action} at {self.timestamp}" 

    class Meta:
        db_table = 'admin_log'
        ordering = ['-timestamp']