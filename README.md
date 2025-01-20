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

# Login
POST /api/login/

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
```

### Groups
```bash
# Create group (Group Organizers only)
POST /api/groups/

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
```

### Chat
```bash
# Initialize group chat
GET /api/chat/group/<group_id>/

# Get chat messages
GET /api/chat/rooms/<room_id>/messages/

# Send message
POST /api/chat/rooms/<room_id>/messages/
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
I make this endpoint but not used it due to some issues

## WebSocket Connections

### Chat & Notifications Socket
```javascript
// Connect to WebSocket
const ws = new WebSocket(`ws://10.81.93.48:8000/ws/notifications/?token=${authToken}`);

// Listen for notifications
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'notification') {
        // Handle notification
        console.log(data.data.message);
    }
};
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
