# Fitness Buddy Backend API

A Django REST API for a fitness buddy application that helps users find workout partners and join fitness groups.

## Core Features

### 1. User Management
- **User Types**:
  - Workout Buddy (for individuals seeking workout partners)
  - Group Organizer (can create and manage fitness groups)
- **Profile Features**:
  - Profile Image
  - Location
  - Phone Number
  - Workout Preferences
  - Fitness Goals
  - Availability Schedule

### 2. Group Management
- **Group Creation** (Group Organizers only)
  - Group name (unique)
  - Activity type
  - Location (automatically synced with organizer's location)
  - Schedule
  - Description
- **Group Membership**
  - Join request system
  - Member management
  - Member list with profile images

### 3. Real-time Chat
- Group chat functionality
- Real-time message delivery
- Chat notifications

### 4. Real-time Notifications
- Join requests
- Request approvals/rejections
- New chat messages

## API Endpoints

### Authentication
```bash
# Register new user
POST /api/register/
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password",
    "password_confirm": "secure_password",
    "role": "workout_buddy",  # or "group_organizer"
    "phone_number": "1234567890",
    "user_location": "Delhi",
    "workout_preferences": ["yoga", "weightlifting"],
    "fitness_goals": "Build strength and flexibility",
    "availability": "Mornings and evenings"
}

# Login
POST /api/login/
{
    "username": "john_doe",
    "password": "secure_password"
}

# Logout
POST /api/logout/
```

### Profile Management
```bash
# Get all profiles
GET /api/profile/

# Get specific profile
GET /api/profile/<username>/

# Update profile
PUT /api/profile/<username>/
{
    "user_location": "New Delhi",  # Updates group location if organizer
    "workout_preferences": ["yoga", "running"],
    "availability": "Weekends only"
}
```

### Groups
```bash
# Create group (Group Organizers only)
POST /api/groups/
{
    "name": "Morning Yoga",
    "activity_type": "Yoga",
    "schedule": "Every morning at 6 AM",
    "description": "Start your day with yoga"
}

# Get all groups
GET /api/groups/

# Get specific group
GET /api/groups/<id>/

# Get my groups
GET /api/my-groups/

# Request to join group
POST /api/groups/<id>/request-join/

# Get join requests
GET /api/groups/join-requests/

# Approve/Reject request
POST /api/groups/<id>/requests/<username>/
{
    "action": "approve"  # or "reject"
}
```

### Chat
```bash
# Initialize group chat
GET /api/chat/group/<group_id>/

# Get chat messages
GET /api/chat/rooms/<room_id>/messages/

# Send message
POST /api/chat/rooms/<room_id>/messages/
{
    "content": "Hello everyone!"
}
```

### Notifications
```bash
# Get all notifications
GET /api/notifications/

# Mark notification as read
POST /api/notifications/<id>/read/

# Clear all notifications
POST /api/notifications/clear/
```

## WebSocket Connections

### Chat & Notifications Socket
```javascript
// Connect to WebSocket
const ws = new WebSocket(`ws://your-domain/ws/notifications/?token=${authToken}`);

// Listen for notifications
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'notification') {
        // Handle notification
        console.log(data.data.message);
    }
};
```

## Models

### UserProfile
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User)
    role = models.CharField(choices=['workout_buddy', 'group_organizer'])
    phone_number = models.CharField(max_length=10)
    user_location = models.CharField(max_length=100)
    profile_image = models.ImageField()
    fitness_goals = models.TextField()
    workout_preferences = models.JSONField()
    availability = models.TextField()
```

### Group
```python
class Group(models.Model):
    organizer = models.ForeignKey(UserProfile)
    name = models.CharField(unique=True)
    activity_type = models.CharField()
    location = models.CharField()  # Synced with organizer's location
    schedule = models.TextField()
    description = models.TextField()
    members = models.ManyToManyField(UserProfile)
```

### ChatRoom
```python
class ChatRoom(models.Model):
    group = models.OneToOneField(Group)
    participants = models.ManyToManyField(UserProfile)
```

### ChatMessage
```python
class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom)
    sender = models.ForeignKey(UserProfile)
    content = models.TextField()
    is_read = models.BooleanField()
```

## Setup & Installation

1. **Prerequisites**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Redis (for WebSocket support)
sudo apt-get install redis-server
```

2. **Environment Setup**
```bash
# Start Redis server
sudo service redis-server start

# Run migrations
python manage.py migrate

# Start server with Daphne (for WebSocket support)
daphne -b 0.0.0.0 -p 8000 fitness_backend.asgi:application
```

## Key Features Implementation

### Location Sync
- Group location automatically syncs with organizer's location
- When organizer updates their location, all their groups' locations update
- Location is read-only in group API

### Real-time Chat
- WebSocket-based chat system
- Automatic chat room creation for groups
- Message notifications for offline users
- Read/unread status tracking

### Notifications
- Real-time notifications via WebSocket
- Different notification types:
  - Chat messages: "john: Hello everyone!"
  - Join requests: "John wants to join your group Fitness Warriors"
  - Request updates: "Your request to join Morning Yoga was approved"

## Security

- Token-based authentication
- WebSocket connections require authentication
- Role-based access control
- Location sync only for group organizers
- Join request verification

## Error Handling

All endpoints return consistent error responses:
```json
{
    "status": "error",
    "message": "Detailed error message"
}
```

## Success Responses

Successful responses follow the format:
```json
{
    "status": "success",
    "data": {
        // Response data here
    }
}
```

## Dependencies
- Django 4.0+
- Django REST Framework
- Channels (for WebSocket)
- Redis (for real-time features)
- PostgreSQL (database)

