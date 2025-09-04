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
    Birthdate = models.DateField()
    MobileNo = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex='^\d{10}$', message='Enter exactly 10 digits.')]
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

    # Soft delete flag
    is_deleted = models.BooleanField(default=False)

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
    member = models.ForeignKey(
        'FamilyMember',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='member_hobbies'
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
    Relationship = models.CharField(max_length=50)
    Birthdate = models.DateField()
    MobileNo = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex='^\d{10}$', message='Enter exactly 10 digits.')],
        null=True, blank=True
    )
    Photo = models.ImageField(upload_to='photos/', null=True, blank=True)
    AddressOverride = models.BooleanField(default=False)
    Address = models.TextField(null=True, blank=True)
    State = models.CharField(max_length=50, null=True, blank=True)
    City = models.CharField(max_length=50, null=True, blank=True)
    Pincode = models.CharField(
        max_length=6,
        validators=[RegexValidator(regex='^\d{6}$', message='Enter exactly 6 digits.')],
        null=True, blank=True
    )

    # Soft delete flag
    is_deleted = models.BooleanField(default=False)

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





class State(models.Model):
    name = models.CharField(max_length=100)
    country_id = models.IntegerField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'state'


class City(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, related_name="cities", on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'city'



class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"