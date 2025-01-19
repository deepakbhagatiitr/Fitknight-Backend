I'll create a comprehensive README.md file that explains the entire project:

```markdown:README.md
# Fitness Buddy Backend API

A Django REST API for a fitness buddy application that helps users find workout partners and join fitness groups.

## Features

### 1. User Management
- **Registration**: Users can register as either:
  - Workout Buddy
  - Group Organizer
- **Authentication**: Token-based authentication
- **Profile Management**: Users can update their profiles with:
  - Profile Image
  - Location
  - Workout Preferences
  - Availability
  - Fitness Goals

### 2. Group Management
- Create fitness groups (Group Organizers only)
- Join/Leave groups
- Request to join groups
- Approve/Reject join requests
- View group details and members

### 3. Group Chat
- Group chat functionality for members
- Real-time messaging using WebSockets
- Message notifications
- Read/Unread status tracking

### 4. Notifications System
- Real-time notifications using WebSockets for:
  - Join requests
  - Request approvals/rejections
  - New group messages
  - Group suggestions
  - Buddy matches

## API Endpoints

### Authentication
```bash
POST /api/register/         # Register new user
POST /api/login/           # Login user
POST /api/logout/          # Logout user
```

### Profile Management
```bash
GET  /api/profile/                    # Get all profiles (with matching)
GET  /api/profile/<username>/         # Get specific profile
PUT  /api/profile/<username>/         # Update profile
```

### Groups
```bash
GET    /api/groups/                                    # List all groups
POST   /api/groups/                                    # Create new group
GET    /api/groups/<id>/                              # Get group details
PUT    /api/groups/<id>/                              # Update group
DELETE /api/groups/<id>/                              # Delete group
GET    /api/my-groups/                                # Get user's groups
POST   /api/groups/<id>/join-request/                 # Request to join
GET    /api/groups/join-requests/                     # List join requests
POST   /api/groups/<id>/requests/<username>/          # Approve/reject request
```

### Chat
```bash
GET  /api/chat/group/<group_name>/                    # Get/Create group chat
GET  /api/chat/rooms/<room_id>/messages/              # Get chat messages
POST /api/chat/rooms/<room_id>/messages/              # Send message
```

### Notifications
```bash
GET  /api/notifications/                              # List notifications
POST /api/notifications/<id>/read/                    # Mark as read
POST /api/notifications/clear/                        # Clear all notifications
```

## WebSocket Endpoints

```bash
ws://domain/ws/notifications/?token=<auth_token>      # Notification socket
```

## Models

### UserProfile
- User (OneToOne with Django User)
- Role (workout_buddy/group_organizer)
- Phone Number
- Location
- Profile Image
- Fitness Goals
- Workout Preferences
- Availability
- Group Details (for organizers)

### Group
- Organizer
- Name
- Activity Type
- Location
- Schedule
- Description
- Members

### ChatRoom
- Group
- Name
- Participants
- Messages

### Notification
- Recipient
- Type
- Title
- Message
- Read Status
- Related Object ID

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```env
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start Redis server (required for WebSockets):
```bash
redis-server
```

5. Run the development server:
```bash
python manage.py runserver
```

## Authentication

The API uses Token Authentication. Include the token in request headers:
```bash
Authorization: Token <your_token>
```

## Error Handling

All endpoints return consistent error responses:
```json
{
    "status": "error",
    "message": "Error description"
}
```

## Success Responses

Successful responses follow the format:
```json
{
    "status": "success",
    "data": {
        // Response data
    }
}
```

## Requirements
- Python 3.8+
- Django 4.0+
- Django REST Framework
- Channels
- Redis
- PostgreSQL

## Notes
- WebSocket connections require authentication via token
- Profile images are stored in media directory
- Redis is required for real-time features
```

