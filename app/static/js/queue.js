// app/static/js/queue.js
// Real-time queue updates using Socket.IO

document.addEventListener('DOMContentLoaded', function() {
    // Connect to the queue namespace (use simple namespace connect)
    const socket = io('/queue');

    // Handle connection
    socket.on('connect', function() {
        console.log('Connected to queue updates');
    });

    // Handle new ticket broadcast
    socket.on('new_ticket', function(data) {
        console.log('New ticket received:', data);
        // Refresh the queue display
        refreshQueue();
    });

    // Handle queue refresh signal
    socket.on('queue_refresh', function(data) {
        console.log('Queue refresh signal received');
        refreshQueue();
    });

    // Handle disconnect
    socket.on('disconnect', function() {
        console.log('Disconnected from queue updates');
    });

    // Function to refresh queue display (fetch updated data via API or reload)
    function refreshQueue() {
        location.reload();
    }
});
