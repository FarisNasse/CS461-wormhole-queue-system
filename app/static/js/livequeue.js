document.addEventListener('DOMContentLoaded', function() {
    // Connect to the queue namespace
    const socket = io('/queue');

    socket.on('connect', function() {
        console.log('Connected to queue namespace');
    });

    socket.on('new_ticket', function(data) {
        console.log('New ticket created:', data);
        refreshLiveQueue();
    });

    socket.on('queue_refresh', function(data) {
        console.log('Queue refresh event received');
        refreshLiveQueue();
    });

    socket.on('disconnect', function() {
        console.log('Disconnected from queue namespace');
    });

    function refreshLiveQueue() {
        location.reload();
    }
});
