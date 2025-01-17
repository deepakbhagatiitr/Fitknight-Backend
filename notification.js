import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

export const setupNotifications = () => {
    const token = localStorage.getItem('token');
    if (!token) {
        console.error('No token found');
        return;
    }

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/notifications/?token=${token}`;
    console.log('Connecting to WebSocket:', wsUrl);

    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log('WebSocket connected');
    };

    socket.onmessage = (event) => {
        console.log('WebSocket message received:', event.data);
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'notification') {
                handleNotification(data);
            }
        } catch (error) {
            console.error('Error handling message:', error);
        }
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    socket.onclose = () => {
        console.log('WebSocket closed - attempting reconnect in 5s');
        setTimeout(setupNotifications, 5000);
    };

    return socket;
};

const handleNotification = (notification) => {
    const notificationData = notification.data;
    console.log('Handling notification:', notificationData);

    let message = notificationData.message;
    let onClick = null;
    let toastType = 'info';

    switch (notificationData.notification_type) {
        case 'join_request':
            onClick = () => window.location.href = `/groups/${notificationData.related_object_id}/requests`;
            toastType = 'info';
            break;

        case 'request_update':
            onClick = () => window.location.href = `/groups/${notificationData.related_object_id}`;
            // Use success/error toast based on acceptance
            toastType = message.includes('accepted') ? 'success' : 'error';
            break;

        case 'group_chat':
            onClick = () => window.location.href = `/chat/${notificationData.related_object_id}`;
            toastType = 'info';
            break;
    }

    // Show toast notification
    toast[toastType](message, {
        position: "top-right",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        onClick: onClick
    });
};

// Handle notification click
export const handleNotificationClick = (notification) => {
    switch (notification.notification_type) {
        case 'join_request':
            window.location.href = `/groups/${notification.related_object_id}/requests`;
            break;
        case 'group_chat':
            window.location.href = `/chat/${notification.related_object_id}`;
            break;
        case 'buddy_match':
            window.location.href = `/buddy/${notification.related_object_id}`;
            break;
    }
}; 