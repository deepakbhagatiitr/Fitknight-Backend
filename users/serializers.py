from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile, Group, ChatMessage, ChatRoom, Notification
from django.contrib.auth import authenticate

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )
    
    # Profile fields
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES)
    profile_image = serializers.ImageField(required=False)
    phone_number = serializers.CharField(required=True, max_length=10)
    user_location = serializers.CharField(required=True, max_length=100)
    
    # Workout Buddy fields
    fitness_goals = serializers.CharField(required=False, allow_blank=True)
    workout_preferences = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    availability = serializers.CharField(required=False, allow_blank=True)
    
    # Group Organizer fields
    group_name = serializers.CharField(required=False, allow_blank=True)
    activity_type = serializers.CharField(required=False, allow_blank=True)
    schedule = serializers.CharField(required=False, allow_blank=True)
    
    # Add description field
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'role', 'profile_image', 'phone_number', 'user_location',
            'fitness_goals', 'workout_preferences',
            'availability', 'group_name', 'activity_type', 
            'schedule', 'description'
        ]

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords must match.")
        
        validate_password(data['password'])
        
        # Validate phone number
        phone = data.get('phone_number', '')
        if not phone.isdigit() or len(phone) != 10:
            raise serializers.ValidationError(
                "Phone number must be exactly 10 digits."
            )
        
        # Check required fields for all users
        if not data.get('user_location'):
            raise serializers.ValidationError("User location is required.")
        
        # Validate role-specific fields
        if data['role'] == 'workout_buddy':
            if not data.get('workout_preferences'):
                raise serializers.ValidationError(
                    "Workout preferences are required for Workout Buddy role."
                )
        elif data['role'] == 'group_organizer':
            required_fields = ['group_name', 'activity_type', 'schedule']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError(
                        f"{field.replace('_', ' ').title()} is required for Group Organizer role."
                    )
        
        return data

    def create(self, validated_data):
        # Remove confirmation field and profile data
        validated_data.pop('password_confirm')
        role = validated_data.pop('role')
        phone_number = validated_data.pop('phone_number')
        user_location = validated_data.pop('user_location')
        
        # Extract profile data
        profile_data = {
            'role': role,
            'phone_number': phone_number,
            'user_location': user_location,
            'fitness_goals': validated_data.pop('fitness_goals', None),
            'workout_preferences': validated_data.pop('workout_preferences', []),
            'availability': validated_data.pop('availability', None),
            'group_name': validated_data.pop('group_name', None),
            'activity_type': validated_data.pop('activity_type', None),
            'schedule': validated_data.pop('schedule', None),
        }

        # Get description for group
        description = validated_data.pop('description', '')

        # Handle profile image
        profile_image = validated_data.pop('profile_image', None)
        if profile_image:
            profile_data['profile_image'] = profile_image
        # If no image provided, the default will be used automatically

        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )

        # Create user profile
        profile = UserProfile.objects.create(user=user, **profile_data)
        
        # If user is a group organizer, create their group automatically
        if role == 'group_organizer':
            Group.objects.create(
                organizer=profile,
                name=profile_data['group_name'],
                activity_type=profile_data['activity_type'],
                location=profile_data['user_location'],
                schedule=profile_data['schedule'],
                description=description
            )
        
        return user

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        # Add profile image URL to response
        if instance.profile.profile_image:
            ret['profile_image'] = instance.profile.profile_image.url
        
        # Add group info for organizers
        if instance.profile.role == 'group_organizer':
            try:
                group = instance.profile.organized_groups.first()
                if group:
                    ret['group'] = {
                        'id': group.id,
                        'name': group.name,
                        'activity_type': group.activity_type,
                        'location': group.location,
                        'schedule': group.schedule,
                    }
            except Group.DoesNotExist:
                pass
        
        return ret

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                data['user'] = user
                return data
            raise serializers.ValidationError('Invalid username or password.')
        raise serializers.ValidationError('Must provide username and password.')

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.CharField(source='user.email')

    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'role', 'phone_number',
            'user_location', 'profile_image', 'fitness_goals', 
            'workout_preferences', 'availability', 'group_name', 
            'activity_type', 'schedule'
        ]
        read_only_fields = ['role']

    def update(self, instance, validated_data):
        # Update User model fields
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            user.username = user_data.get('username', user.username)
            user.email = user_data.get('email', user.email)
            user.save()

        # Update UserProfile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

class GroupSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source='organizer.user.username', read_only=True)
    member_count = serializers.SerializerMethodField()
    is_organizer = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'activity_type', 'location', 'schedule',
            'description', 'created_at', 'updated_at', 'organizer_name',
            'member_count', 'is_organizer', 'members'
        ]
        read_only_fields = ['organizer', 'location', 'organizer_name']

    def get_members(self, obj):
        return [{
            'id': member.user.id,
            'username': member.user.username,
            'profile_image': member.profile_image.url if member.profile_image else None
        } for member in obj.members.all()]

    def get_member_count(self, obj):
        return obj.members.count()

    def get_is_organizer(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.organizer.user == request.user
        return False

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")
            
        try:
            organizer_profile = request.user.profile
            if organizer_profile.role != 'group_organizer':
                raise serializers.ValidationError("Only group organizers can create groups")
                
            # Remove organizer from validated_data if it exists
            validated_data.pop('organizer', None)
            
            group = Group.objects.create(
                organizer=organizer_profile,
                location=organizer_profile.user_location,
                **validated_data
            )
            return group
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError("User profile not found")

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.user.username', read_only=True)
    sender_image = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'room', 'sender', 'sender_name', 'sender_image', 
                 'content', 'created_at', 'is_read']
        read_only_fields = ['sender', 'is_read']
    
    def get_sender_image(self, obj):
        if obj.sender.profile_image:
            return obj.sender.profile_image.url
        return None

class ChatRoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    participants_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'room_type', 'group', 'participants', 
                 'participants_info', 'last_message', 'unread_count', 
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'content': last_msg.content,
                'sender_name': last_msg.sender.user.username,
                'created_at': last_msg.created_at
            }
        return None
    
    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender__user=user).count()
    
    def get_participants_info(self, obj):
        return [{
            'id': p.user.id,
            'username': p.user.username,
            'profile_image': p.profile_image.url if p.profile_image else None
        } for p in obj.participants.all()]

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'created_at',
            'related_object_id'
        ]
