from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('workout_buddy', 'Workout Buddy'),
        ('group_organizer', 'Group Organizer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=10)  # 10 digits only
    user_location = models.CharField(max_length=100)  # User's personal location
    profile_image = models.ImageField(
        upload_to='profile_images/',
        null=True,
        blank=True,
        default='profile_images/hulk.jpg'
    )
    
    # Workout Buddy fields
    fitness_goals = models.TextField(null=True, blank=True)
    workout_preferences = models.JSONField(default=list, blank=True)
    availability = models.TextField(null=True, blank=True)
    
    # Group Organizer fields
    group_name = models.CharField(max_length=100, null=True, blank=True)
    activity_type = models.CharField(max_length=100, null=True, blank=True)
    schedule = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

class Group(models.Model):
    organizer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='organized_groups')
    name = models.CharField(max_length=100)
    activity_type = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    schedule = models.TextField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    members = models.ManyToManyField(UserProfile, related_name='joined_groups', blank=True)
    
    def __str__(self):
        return self.name

class GroupJoinRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    
    id = models.AutoField(primary_key=True)  # This is the request_id
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['group', 'user']  # Prevent duplicate requests

class ChatRoom(models.Model):
    ROOM_TYPES = [
        ('group', 'Group Chat'),
        ('direct', 'Direct Message')
    ]
    
    name = models.CharField(max_length=255)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='group')
    group = models.OneToOneField(Group, on_delete=models.CASCADE, null=True, blank=True)
    participants = models.ManyToManyField(UserProfile, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['group']
    
    def __str__(self):
        if self.room_type == 'group':
            return f"Group Chat: {self.group.name}"
        return f"DM: {self.name}"

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.user.username}: {self.content[:50]}"

class Notification(models.Model):
    recipient = models.ForeignKey(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} for {self.recipient.user.username}"

