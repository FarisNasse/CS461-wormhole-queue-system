document.addEventListener('DOMContentLoaded', function() {
    // Connect to the queue namespace
    const socket = io('/queue');

    socket.on('connect', function() {
        console.log('Connected to queue namespace');
        updateTicketTable();
        console.log('Initial ticket table loaded');
    });

    socket.on('new_ticket', function(data) {
        console.log('New ticket created:', data);
        updateTicketTable();
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

    function updateTicketTable() {
        fetch('/api/livequeuetickets')
            .then(response => {
                console.log('Response status', response.status);
                return response.json();
            })
            .then(tickets => {
                console.log('API tickets:', tickets);

                const ticketTableBody = document.querySelector('#tickets tbody');
                ticketTableBody.innerHTML = '';

                tickets.forEach((ticket, index) => {
                    const row = document.createElement('tr');
                    row.id = `ticket-${ticket.id}`;

                    const positionOrStatus = ticket.status === 'in_progress'
                        ? 'IN PROGRESS'
                        : index + 1;

                    row.innerHTML = `
                        <td>${positionOrStatus}</td>
                        <td>${ticket.student_name}</td>
                        <td>${ticket.table}</td>
                        <td>${ticket.physics_course}</td>
                    `;

                    ticketTableBody.appendChild(row);
                });

                document.getElementById('refresh-time').textContent =
                    new Date().toLocaleTimeString();
            })
            .catch(error => console.error('Error fetching tickets:', error));
    }
});