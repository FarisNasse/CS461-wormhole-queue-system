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
        // Implementation for addding tickets dynamically
        fetch('/api/opentickets')
            .then(response => {
                console.log('Response status', response.status);
                return response.json()
            })
            .then(tickets => {
                console.log('API tickets:', tickets); // Check structure

                const ticketTableBody = document.querySelector('#tickets tbody');
                ticketTableBody.innerHTML = ''; // Clear existing rows

                let index = 0;

                tickets.forEach((ticket) => {
                    const row = document.createElement('tr');
                    row.id = `ticket-${ticket.id}`;

                    let queue_position;
                    if (ticket.status === 'in_progress') {
                        queue_position = 'In Progress';
                    } else {
                        index++;
                        queue_position = index;
                    }

                    row.innerHTML = `
                        <td>${queue_position}</td>
                        <td>${ticket.student_name}</td>
                        <td>${ticket.table}</td>
                        <td>${ticket.physics_course}</td>
                    `;
                    ticketTableBody.appendChild(row);
                });
                //document.getElementById('ticket-count').textContent = tickets.length;
                document.getElementById('refresh-time').textContent = new Date().toLocaleTimeString();
            })
            .catch(error => console.error('Error fetching tickets:', error));
    }
});
