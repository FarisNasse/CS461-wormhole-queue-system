// app/static/js/attendance.js
// Lightweight heartbeat for assistant attendance sessions.

(function() {
    const script = document.currentScript;
    const heartbeatUrl = script ? script.dataset.heartbeatUrl : null;
    const csrfToken = script ? script.dataset.csrfToken : null;

    if (!heartbeatUrl || !window.fetch) {
        return;
    }

    let heartbeatEnabled = true;
    let intervalId = null;

    function stopHeartbeat() {
        heartbeatEnabled = false;
        if (intervalId !== null) {
            window.clearInterval(intervalId);
            intervalId = null;
        }
    }

    function sendHeartbeat() {
        if (!heartbeatEnabled) {
            return;
        }
        if (document.visibilityState && document.visibilityState !== 'visible') {
            return;
        }

        const headers = {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        };

        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        fetch(heartbeatUrl, {
            method: 'POST',
            credentials: 'same-origin',
            headers: headers
        })
            .then(function(response) {
                if (!response.ok) {
                    return null;
                }
                return response.json();
            })
            .then(function(data) {
                if (data && data.checked_in === false) {
                    stopHeartbeat();
                }
            })
            .catch(function() {
                // Heartbeat failures should not interrupt normal page use.
            });
    }

    window.setTimeout(sendHeartbeat, 10000);
    intervalId = window.setInterval(sendHeartbeat, 60000);

    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            sendHeartbeat();
        }
    });
})();
