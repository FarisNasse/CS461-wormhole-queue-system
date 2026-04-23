// app/static/js/attendance.js
// Lightweight heartbeat for assistant attendance sessions.

(function() {
    const script = document.currentScript;
    const heartbeatUrl = script ? script.dataset.heartbeatUrl : null;

    if (!heartbeatUrl || !window.fetch) {
        return;
    }

    function sendHeartbeat() {
        if (document.visibilityState && document.visibilityState !== 'visible') {
            return;
        }

        fetch(heartbeatUrl, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).catch(function() {
            // Heartbeat failures should not interrupt normal page use.
        });
    }

    window.setTimeout(sendHeartbeat, 10000);
    window.setInterval(sendHeartbeat, 60000);

    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            sendHeartbeat();
        }
    });
})();
