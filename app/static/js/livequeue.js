document.addEventListener('DOMContentLoaded', function () {
    // Connect to the queue namespace
    const socket = io('/queue');

    socket.on('connect', function () {
        console.log('Connected to queue namespace');
        updateTicketTable();
        console.log('Initial ticket table loaded');
    });

    socket.on('new_ticket', function (data) {
        console.log('New ticket created:', data);
        updateTicketTable();
    });

    socket.on('queue_refresh', function (data) {
        console.log('Queue refresh event received');
        refreshLiveQueue();
    });

    socket.on('disconnect', function () {
        console.log('Disconnected from queue namespace');
    });

    function refreshLiveQueue() {
        location.reload();
    }

    function updateRefreshTime() {
        const refreshTime = document.getElementById('refresh-time');

        if (!refreshTime) {
            return;
        }

        refreshTime.style.transition = 'opacity 0.2s ease';
        refreshTime.style.opacity = '0';

        window.setTimeout(() => {
            refreshTime.textContent = new Date().toLocaleTimeString();
            refreshTime.style.opacity = '1';
        }, 160);
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

                if (!ticketTableBody) {
                    return;
                }

                ticketTableBody.innerHTML = '';

                if (tickets.length === 0) {
                    const emptyRow = document.createElement('tr');
                    emptyRow.className = 'animate-ticket-in';

                    emptyRow.innerHTML = `
            <td colspan="4" class="px-6 py-12 text-center">
                <div class="mx-auto max-w-sm animate-fade-up">
                    <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400">
                        <svg class="h-6 w-6" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3M4 11h16M5 21h14a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v13a1 1 0 0 0 1 1Z"/>
                        </svg>
                    </div>
                    <p class="text-sm font-semibold text-gray-900 dark:text-gray-100">No one is currently waiting</p>
                    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">New help requests will appear here automatically.</p>
                </div>
            </td>
        `;

                    ticketTableBody.appendChild(emptyRow);
                }

                tickets.forEach((ticket, index) => {
                    const row = document.createElement('tr');
                    row.id = `ticket-${ticket.id}`;
                    row.className = 'interactive-table-row animate-ticket-in hover:bg-orange-50/60 dark:hover:bg-osu-navy-dark/30';
                    row.style.animationDelay = `${index * 55}ms`;

                    const positionCell = document.createElement('td');
                    positionCell.className = 'px-6 py-4 align-middle';

                    const positionBadge = document.createElement('span');

                    if (ticket.status === 'in_progress') {
                        positionBadge.className =
                            'inline-flex min-w-28 items-center justify-center rounded-full bg-purple-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-purple-800 ring-1 ring-purple-200 dark:bg-osu-lavender/20 dark:text-osu-lavender-dark dark:ring-osu-lavender-dark/30';
                        positionBadge.textContent = 'In progress';
                    } else {
                        positionBadge.className =
                            'inline-flex h-9 min-w-12 items-center justify-center rounded-lg bg-osu-navy px-3 text-sm font-bold tabular-nums text-white shadow-sm ring-1 ring-osu-navy/30 dark:bg-osu-navy-dark dark:ring-osu-blue-light/20';
                        positionBadge.textContent = `#${index + 1}`;
                    }

                    positionCell.appendChild(positionBadge);

                    const nameCell = document.createElement('td');
                    nameCell.className = 'px-6 py-4 align-middle font-medium text-gray-900 dark:text-gray-100';
                    nameCell.textContent = ticket.student_name || 'Unknown student';

                    const tableCell = document.createElement('td');
                    tableCell.className = 'px-6 py-4 align-middle text-gray-700 dark:text-gray-200';

                    const tableBadge = document.createElement('span');
                    tableBadge.className =
                        'inline-flex min-w-10 items-center justify-center rounded-lg bg-gray-100 px-2.5 py-1 text-sm font-semibold tabular-nums text-gray-800 ring-1 ring-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:ring-osu-blue-light/20';
                    tableBadge.textContent = ticket.table || '—';

                    tableCell.appendChild(tableBadge);

                    const courseCell = document.createElement('td');
                    courseCell.className = 'px-6 py-4 align-middle text-gray-700 dark:text-gray-200';
                    courseCell.textContent = ticket.physics_course || '—';

                    row.appendChild(positionCell);
                    row.appendChild(nameCell);
                    row.appendChild(tableCell);
                    row.appendChild(courseCell);

                    ticketTableBody.appendChild(row);
                });

                updateRefreshTime();
            })
    }
});