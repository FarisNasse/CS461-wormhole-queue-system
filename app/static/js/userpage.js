document.addEventListener('DOMContentLoaded', function() {
    // Connect to the queue namespace
    const socket = io('/queue');

    socket.on('connect', function() {
        console.log('Connected to queue namespace (userpage)');
    });

    socket.on('new_ticket', function(data) {
        console.log('New ticket event (userpage):', data);
        refreshUserPage();
    });

    socket.on('queue_refresh', function(data) {
        console.log('Queue refresh event (userpage)');
        refreshUserPage();
    });

    socket.on('disconnect', function() {
        console.log('Disconnected from queue namespace (userpage)');
    });

    function refreshUserPage() {
        location.reload();
    }
});
