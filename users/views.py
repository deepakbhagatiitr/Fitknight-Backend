from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer, GroupSerializer, ChatRoomSerializer, ChatMessageSerializer, NotificationSerializer
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import UserProfile, Group, GroupJoinRequest, ChatRoom, ChatMessage, Notification
from rest_framework import viewsets
import json  # Add this import at the top
from rest_framework import serializers  # Add this import
from rest_framework.decorators import action
from .utils import notify_join_request, notify_request_response, notify_new_message, notify_buddy_match, notify_group_suggestion
from rest_framework import generics
from django.contrib.auth.models import User  # Add this import at the top
from django.db import models
from django.db import IntegrityError

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def post(self, request):
        print("\n=== Registration Request ===")
        print("Headers:", request.headers)
        print("Content Type:", request.content_type)
        print("Data:", request.data)
        print("Files:", request.FILES)
        
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            print("\nValidated Data:", serializer.validated_data)
            user = serializer.save()
            response_data = {
                'status': 'success',
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.profile.role,
                }
            }
            print("\n=== Registration Response ===")
            print("Status: 201 Created")
            print("Response Data:", response_data)
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        print("\n=== Registration Error ===")
        print("Validation Errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (JSONParser,)

    def post(self, request):
        print("\n=== Login Request ===")
        print("Headers:", request.headers)
        print("Data:", request.data)
        
        try:
            # First check if user exists
            username = request.data.get('username')
            if not User.objects.filter(username=username).exists():
                return Response({
                    'status': 'error',
                    'message': 'User is not registered. Please sign up first.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # If user exists, proceed with login validation
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid():
                print("\nValidated Data:", serializer.validated_data)
                user = serializer.validated_data['user']
                token, created = Token.objects.get_or_create(user=user)
                
                profile = user.profile
                user_type = 'buddy' if profile.role == 'workout_buddy' else 'group'
                
                response_data = {
                    'status': 'success',
                    'message': 'Login successful',
                    'token': token.key,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'userType': user_type,
                    }
                }
                print("\n=== Login Response ===")
                print("Status: 200 OK")
                print("Response Data:", response_data)
                return Response(response_data, status=status.HTTP_200_OK)
            
            # If credentials are invalid
            return Response({
                'status': 'error',
                'message': 'Invalid username or password'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print("\n=== Login Error ===")
            print("Error:", str(e))
            return Response({
                'status': 'error',
                'message': 'An error occurred during login'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_user_by_id_or_username(self, identifier):
        """Get user by either ID or username"""
        try:
            # First try to get by ID
            if identifier.isdigit():
                return User.objects.get(id=identifier)
            # If not numeric, try username
            return User.objects.get(username=identifier)
        except User.DoesNotExist:
            return None

    def get(self, request, identifier):
        user = self.get_user_by_id_or_username(identifier)
        
        if not user:
            return Response({
                "status": "error",
                "message": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            profile = user.profile
            serializer = UserProfileSerializer(profile)
            return Response({
                "status": "success",
                "data": serializer.data
            })
        except UserProfile.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, identifier):
        if str(request.user.id) != str(identifier) and not request.user.username == identifier:
            return Response({
                "status": "error",
                "message": "You can only update your own profile"
            }, status=status.HTTP_403_FORBIDDEN)

        user = self.get_user_by_id_or_username(identifier)
        if not user:
            return Response({
                "status": "error",
                "message": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            profile = user.profile
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": "success",
                    "message": "Profile updated successfully",
                    "data": serializer.data
                })
            return Response({
                "status": "error",
                "message": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except UserProfile.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        print("\n=== Group List GET Request ===")
        print("Headers:", self.request.headers)
        print("User:", self.request.user)
        print("Query Params:", self.request.query_params)
        
        queryset = Group.objects.all()
        
        # Filter by membership if specified
        membership = self.request.query_params.get('membership', None)
        if membership == 'member':
            # Get groups where user is either a member or organizer
            queryset = queryset.filter(
                models.Q(members=self.request.user.profile) | 
                models.Q(organizer=self.request.user.profile)
            ).distinct()
        
        # Filter by activity type
        activity_type = self.request.query_params.get('activity_type', None)
        if activity_type:
            print("Filtering by activity_type:", activity_type)
            queryset = queryset.filter(activity_type=activity_type)
            
        # Filter by location
        location = self.request.query_params.get('location', None)
        if location:
            print("Filtering by location:", location)
            queryset = queryset.filter(location__icontains=location)
        
        print("Total groups found:", queryset.count())
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        print("\n=== Group List Response ===")
        print("Status: 200 OK")
        print("Count:", len(response.data))
        print("Response Data:", response.data)
        return response
    
    def retrieve(self, request, *args, **kwargs):
        print("\n=== Group Detail GET Request ===")
        print("Headers:", request.headers)
        print("User:", request.user)
        print("Group ID:", kwargs.get('pk'))
        
        try:
            response = super().retrieve(request, *args, **kwargs)
            print("\n=== Group Detail Response ===")
            print("Status: 200 OK")
            print("Response Data:", response.data)
            return response
        except Exception as e:
            error_msg = {'error': str(e)}
            print("\n=== Group Detail Error ===")
            print("Status: 404 Not Found")
            print("Error:", error_msg)
            return Response(error_msg, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request, *args, **kwargs):
        try:
            # Add organizer to request data
            request.data['organizer'] = request.user.profile.id
            return super().create(request, *args, **kwargs)
            
        except IntegrityError:
            return Response({
                'status': 'error',
                'error': 'A group with this name already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_create(self, serializer):
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        print("\n=== Group Update Request ===")
        print("Headers:", request.headers)
        print("User:", request.user)
        print("Group ID:", kwargs.get('pk'))
        print("Data:", request.data)
        
        try:
            response = super().update(request, *args, **kwargs)
            print("\n=== Group Update Response ===")
            print("Status: 200 OK")
            print("Response Data:", response.data)
            return response
        except Exception as e:
            error_msg = {'error': str(e)}
            print("\n=== Group Update Error ===")
            print("Status: 400 Bad Request")
            print("Error:", error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        print("\n=== Group Delete Request ===")
        print("Headers:", request.headers)
        print("User:", request.user)
        print("Group ID:", kwargs.get('pk'))
        
        try:
            group = self.get_object()
            if group.organizer.user != request.user:
                error_msg = {"error": "Only the organizer can delete the group"}
                print("\n=== Group Delete Error ===")
                print("Status: 403 Forbidden")
                print("Error:", error_msg)
                return Response(error_msg, status=status.HTTP_403_FORBIDDEN)
            
            response = super().destroy(request, *args, **kwargs)
            print("\n=== Group Delete Response ===")
            print("Status: 204 No Content")
            return response
            
        except Exception as e:
            error_msg = {'error': str(e)}
            print("\n=== Group Delete Error ===")
            print("Status: 404 Not Found")
            print("Error:", error_msg)
            return Response(error_msg, status=status.HTTP_404_NOT_FOUND)

class UserProfileListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        print("\n=== Profile List GET Request ===")
        print("Headers:", request.headers)
        print("User:", request.user)
        
        try:
            # Get current user's profile
            user_profile = request.user.profile
            print(f"Current user preferences: {user_profile.workout_preferences}")
            print(f"Current user location: {user_profile.user_location}")
            
            # Get all profiles except current user
            profiles = UserProfile.objects.exclude(user=request.user)
            
            # Filter by role if specified (default to workout_buddy)
            role = request.query_params.get('role', 'workout_buddy')
            if role:
                profiles = profiles.filter(role=role)

            matching_profiles = []
            for profile in profiles:
                match_details = {
                    'score': 0,
                    'reasons': []
                }
                
                # Check location match
                if profile.user_location and user_profile.user_location:
                    if profile.user_location.lower() == user_profile.user_location.lower():
                        match_details['score'] += 1
                        match_details['reasons'].append(f"Same location: {profile.user_location}")
                
                # Check workout preferences match
                if user_profile.workout_preferences and profile.workout_preferences:
                    try:
                        # Get user preferences
                        user_prefs = set([
                            pref.lower().strip() 
                            for pref in user_profile.workout_preferences
                        ])
                        
                        # Get profile preferences
                        profile_prefs = set([
                            pref.lower().strip() 
                            for pref in profile.workout_preferences
                        ])
                        
                        # Find common preferences
                        common_prefs = user_prefs.intersection(profile_prefs)
                        if common_prefs:
                            match_details['score'] += len(common_prefs)
                            match_details['reasons'].append(
                                f"Shared interests: {', '.join(common_prefs)}"
                            )
                            
                        print(f"Profile {profile.user.username}:")
                        print(f"- User prefs: {user_prefs}")
                        print(f"- Profile prefs: {profile_prefs}")
                        print(f"- Common prefs: {common_prefs}")
                        
                    except Exception as e:
                        print(f"Error matching preferences: {str(e)}")
                
                # Add profile if there's at least one match
                if match_details['score'] > 0:
                    profile_data = UserProfileSerializer(profile).data
                    profile_data['match_score'] = match_details['score']
                    profile_data['match_reasons'] = match_details['reasons']
                    matching_profiles.append(profile_data)
            
            # Sort by match score
            matching_profiles.sort(key=lambda x: x['match_score'], reverse=True)
            
            response_data = {
                'count': len(matching_profiles),
                'results': matching_profiles
            }
            
            print("\n=== Profile List Response ===")
            print(f"Found {len(matching_profiles)} matches")
            print(f"Response: {response_data}")
            
            return Response(response_data)
            
        except Exception as e:
            print(f"\nError in profile list: {str(e)}")
            return Response({
                'count': 0,
                'results': []
            }, status=status.HTTP_200_OK)

class GroupJoinRequestView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, group_id):
        """Get join request status for a group"""
        try:
            group = Group.objects.get(pk=group_id)
            
            # If user is organizer, show all requests for their group
            if request.user == group.organizer.user:
                requests = GroupJoinRequest.objects.filter(group=group)
                response_data = {
                    "status": "success",
                    "is_organizer": True,
                    "requests": [{
                        'id': req.id,
                        'user': {
                            'id': req.user.user.id,
                            'username': req.user.user.username,
                            'profile_image': req.user.profile_image.url if req.user.profile_image else None
                        },
                        'status': req.status,
                        'created_at': req.created_at
                    } for req in requests]
                }
            else:
                # Show user's own request status for this group
                request_obj = GroupJoinRequest.objects.filter(
                    group=group,
                    user=request.user.profile
                ).first()
                
                if request_obj:
                    response_data = {
                        "status": "success",
                        "is_organizer": False,
                        "request": {
                            'id': request_obj.id,
                            'status': request_obj.status,
                            'created_at': request_obj.created_at
                        }
                    }
                else:
                    response_data = {
                        "status": "success",
                        "is_organizer": False,
                        "request": None
                    }
            
            return Response(response_data)
            
        except Group.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Group not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, group_id):
        """Send a join request for a group"""
        try:
            group = Group.objects.get(pk=group_id)
            user_profile = request.user.profile
            
            # First check if user is already a member
            if user_profile in group.members.all():
                return Response({
                    "status": "error",
                    "message": "You are already a member of this group"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get existing request if any
            existing_request = GroupJoinRequest.objects.filter(
                group=group,
                user=user_profile
            ).first()
            
            if existing_request:
                if existing_request.status == 'pending':
                    return Response({
                        "status": "error",
                        "message": "You already have a pending request for this group"
                    }, status=status.HTTP_400_BAD_REQUEST)
                elif existing_request.status == 'approved':
                    return Response({
                        "status": "error",
                        "message": "Your request was already approved"
                    }, status=status.HTTP_400_BAD_REQUEST)
                elif existing_request.status == 'rejected':
                    # Update the existing rejected request to pending
                    existing_request.status = 'pending'
                    existing_request.save(update_fields=['status'])
                    
                    # Send notification to group organizer
                    notify_join_request(
                        organizer_id=group.organizer.user.id,
                        group_id=group.id,
                        requester_name=request.user.username
                    )
                    
                    return Response({
                        "status": "success",
                        "message": "Join request sent successfully"
                    })
            else:
                # Create new join request
                GroupJoinRequest.objects.create(
                    group=group,
                    user=user_profile,
                    status='pending'
                )
                
                # Send notification to group organizer
                notify_join_request(
                    organizer_id=group.organizer.user.id,
                    group_id=group.id,
                    requester_name=request.user.username
                )
                
                return Response({
                    "status": "success",
                    "message": "Join request sent successfully"
                })
            
        except Group.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Group not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ManageJoinRequestView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            if request.user.profile.role == 'group_organizer':
                # For organizers - show requests for their groups
                requests = GroupJoinRequest.objects.filter(
                    group__organizer=request.user.profile
                )
            else:
                # For workout buddies - show their own requests
                requests = GroupJoinRequest.objects.filter(
                    user=request.user.profile
                )
            
            response_data = []
            for req in requests:
                data = {
                    "id": req.id,
                    "group": {
                        "id": req.group.id,
                        "name": req.group.name,
                        "activity_type": req.group.activity_type
                    },
                    "user": {
                        "id": req.user.user.id,
                        "username": req.user.user.username,
                        "profile_image": req.user.profile_image.url if req.user.profile_image else None
                    },
                    "status": req.status,
                    "created_at": req.created_at
                }
                response_data.append(data)
            
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def post(self, request, request_id):
        print("\n=== Manage Join Request - Request ===")
        print("Headers:", request.headers)
        print("User:", request.user)
        print("Request ID:", request_id)
        print("Data:", request.data)
        
        try:
            join_request = GroupJoinRequest.objects.get(pk=request_id)
            
            # Verify that the current user is the group organizer
            if request.user != join_request.group.organizer.user:
                error_msg = {"error": "Only group organizer can manage join requests"}
                print("\n=== Manage Join Request Error ===")
                print("Status: 403 Forbidden")
                print("Error:", error_msg)
                return Response(error_msg, status=status.HTTP_403_FORBIDDEN)
            
            action = request.data.get('action')
            if action not in ['approve', 'reject']:
                error_msg = {"error": "Invalid action. Use 'approve' or 'reject'"}
                print("\n=== Manage Join Request Error ===")
                print("Status: 400 Bad Request")
                print("Error:", error_msg)
                return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
            
            if action == 'approve':
                join_request.status = 'approved'
                join_request.save()
                # Add user to group members
                join_request.group.members.add(join_request.user)
                
                # Get updated group data
                group_serializer = GroupSerializer(join_request.group, context={'request': request})
                
                response_data = {
                    "message": "Join request approved",
                    "group": group_serializer.data,
                    "request": {
                        "id": join_request.id,
                        "status": join_request.status,
                        "user": {
                            "id": join_request.user.user.id,
                            "username": join_request.user.user.username,
                            "profile_image": join_request.user.profile_image.url if join_request.user.profile_image else None
                        }
                    }
                }
            else:
                join_request.status = 'rejected'
                join_request.save()
                response_data = {
                    "message": "Join request rejected",
                    "request": {
                        "id": join_request.id,
                        "status": join_request.status,
                        "user": {
                            "id": join_request.user.user.id,
                            "username": join_request.user.user.username
                        }
                    }
                }
            
            print("\n=== Manage Join Request Response ===")
            print("Status: 200 OK")
            print("Response Data:", response_data)
            return Response(response_data)
            
        except GroupJoinRequest.DoesNotExist:
            error_msg = {"error": "Join request not found"}
            print("\n=== Manage Join Request Error ===")
            print("Status: 404 Not Found")
            print("Error:", error_msg)
            return Response(error_msg, status=status.HTTP_404_NOT_FOUND)

class ApproveRejectJoinRequestView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, group_id, username):
        try:
            group = Group.objects.get(pk=group_id)
            user_profile = UserProfile.objects.get(user__username=username)
            join_request = GroupJoinRequest.objects.get(
                group=group,
                user=user_profile,
                status='pending'
            )
            
            # Verify that the current user is the group organizer
            if request.user != group.organizer.user:
                return Response({
                    "status": "error",
                    "message": "Only group organizer can manage join requests"
                }, status=status.HTTP_403_FORBIDDEN)
            
            action = request.data.get('action')
            if action not in ['approve', 'reject']:
                return Response({
                    "status": "error",
                    "message": "Invalid action. Use 'approve' or 'reject'"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update request status and send notification
            is_approved = action == 'approve'
            join_request.status = 'approved' if is_approved else 'rejected'
            join_request.save()
            
            # Send notification to the requester
            notify_request_response(
                user_id=user_profile.user.id,
                group_id=group.id,
                accepted=is_approved
            )
            
            if is_approved:
                group.members.add(user_profile)
            
            return Response({
                "status": "success",
                "message": f"Join request {action}ed successfully"
            })
            
        except (Group.DoesNotExist, UserProfile.DoesNotExist, GroupJoinRequest.DoesNotExist) as e:
            return Response({
                "status": "error", 
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)

class GroupChatView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, group_id):
        """Get or create chat room for group"""
        try:
            # Get group and verify membership
            group = Group.objects.get(id=group_id)
            user_profile = request.user.profile
            
            # Check if user is member or organizer
            if user_profile != group.organizer and user_profile not in group.members.all():
                return Response({
                    'status': 'error',
                    'error': f'Must be member of {group.name} to access chat'
                }, status=status.HTTP_403_FORBIDDEN)
            
            try:
                # First try to get existing chat room
                room = ChatRoom.objects.get(group=group)
            except ChatRoom.DoesNotExist:
                # If no chat room exists, create one
                room = ChatRoom.objects.create(
                    group=group,
                    name=f"Group Chat: {group.name}",
                    room_type='group'
                )
            
            # Add user as participant if not already
            if user_profile not in room.participants.all():
                room.participants.add(user_profile)
            
            return Response({
                'status': 'success',
                'data': {
                    'room_id': room.id,
                    'group_id': group.id,
                    'group_name': group.name,
                    'message': f'Group chat ready'
                }
            })
            
        except Group.DoesNotExist:
            return Response({
                'status': 'error',
                'error': f'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Chat room error: {str(e)}")  # Add logging
            return Response({
                'status': 'error',
                'error': 'Failed to initialize chat room'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            room_id = self.kwargs.get('room_id')
            room = get_object_or_404(ChatRoom, id=room_id)
            
            # Verify user is a participant
            if self.request.user.profile not in room.participants.all():
                raise serializers.ValidationError({
                    'status': 'error',
                    'error': 'Must be a participant to view messages'
                })
            
            # Mark messages as read
            unread_messages = room.messages.filter(
                is_read=False
            ).exclude(sender=self.request.user.profile)
            unread_messages.update(is_read=True)
            
            return room.messages.all()
            
        except Exception as e:
            print(f"Message query error: {str(e)}")  # Add logging
            raise
    
    def perform_create(self, serializer):
        try:
            room_id = self.kwargs.get('room_id')
            room = get_object_or_404(ChatRoom, id=room_id)
            
            # Verify user is a participant
            if self.request.user.profile not in room.participants.all():
                raise serializers.ValidationError({
                    'status': 'error',
                    'error': 'Must be a participant to send messages'
                })
            
            # Create message
            message = serializer.save(
                room=room,
                sender=self.request.user.profile
            )
            
            # Notify other participants (removed current chat check)
            for participant in room.participants.all():
                # Don't notify the sender
                if participant.id != self.request.user.profile.id:
                    notify_new_message(
                        user_id=participant.user.id,
                        chat_id=room.id,
                        sender_name=self.request.user.username,
                        message_content=message.content
                    )
                    print(f"Notification sent to {participant.user.username}")
                    
        except Exception as e:
            print(f"Message creation error: {str(e)}")
            raise

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user.profile)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'notifications marked as read'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get all notifications for the current user, ordered by newest first
        return Notification.objects.filter(
            recipient__user=self.request.user
        ).order_by('-created_at')

class MarkNotificationReadView(generics.UpdateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})

class TestNotificationView(APIView):
    def post(self, request):
        # Test buddy match notification
        notify_buddy_match(
            user_id=request.user.id,
            matched_buddy_id=1  # Example buddy ID
        )
        
        # Test group suggestion
        notify_group_suggestion(
            user_id=request.user.id,
            group_id=1  # Example group ID
        )
        
        return Response({'status': 'test notifications sent'})

class ClearNotificationsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get user profile
            user_profile = request.user.profile
            
            # Delete all notifications for the current user
            deleted_count = Notification.objects.filter(
                recipient=user_profile
            ).delete()[0]
            
            return Response({
                'status': 'success',
                'message': f'Successfully cleared {deleted_count} notifications',
                'count': deleted_count
            })
        except Exception as e:
            print(f"Error clearing notifications: {str(e)}")  # For debugging
            return Response({
                'status': 'error',
                'message': f'Failed to clear notifications: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Delete the user's auth token
            request.user.auth_token.delete()
            return Response({
                'status': 'success',
                'message': 'Successfully logged out'
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class UserGroupsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get user's profile
            user_profile = request.user.profile
            
            # Get groups where user is either member or organizer
            groups = Group.objects.filter(
                models.Q(members=user_profile) | 
                models.Q(organizer=user_profile)
            ).distinct()
            
            serializer = GroupSerializer(groups, many=True, context={'request': request})
            
            return Response({
                'status': 'success',
                'count': len(serializer.data),
                'groups': serializer.data
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
