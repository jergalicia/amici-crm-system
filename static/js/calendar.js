document.addEventListener('DOMContentLoaded', function () {
    let currentDate = new Date();
    let events = [];

    // Fetch events
    fetch('/calendar/api/events')
        .then(response => response.json())
        .then(data => {
            events = data;
            renderCalendar(currentDate);
        });

    window.prevMonth = function () {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar(currentDate);
    }

    window.nextMonth = function () {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar(currentDate);
    }

    function renderCalendar(date) {
        const monthLabel = document.getElementById('currentMonthLabel');
        const grid = document.getElementById('calendar-grid');

        // Clear previous days (keep headers)
        while (grid.children.length > 7) {
            grid.removeChild(grid.lastChild);
        }

        const year = date.getFullYear();
        const month = date.getMonth();

        monthLabel.textContent = new Intl.DateTimeFormat('es-ES', { month: 'long', year: 'numeric' }).format(date);

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);

        // Padding days
        for (let i = 0; i < firstDay.getDay(); i++) {
            const pad = document.createElement('div');
            pad.className = 'cal-day';
            pad.style.backgroundColor = '#fa_fa_fa';
            grid.appendChild(pad);
        }

        // Days of month
        const today = new Date();
        for (let i = 1; i <= lastDay.getDate(); i++) {
            const dayCell = document.createElement('div');
            dayCell.className = 'cal-day';
            dayCell.innerHTML = `<div style="font-weight:600; margin-bottom:4px;">${i}</div>`;

            if (year === today.getFullYear() && month === today.getMonth() && i === today.getDate()) {
                dayCell.classList.add('today');
            }

            // Find events for this day
            const dayEvents = events.filter(e => {
                const eDate = new Date(e.start);
                return eDate.getFullYear() === year && eDate.getMonth() === month && eDate.getDate() === i;
            });

            dayEvents.forEach(evt => {
                const pill = document.createElement('div');
                pill.className = 'event-pill';
                pill.textContent = evt.title;
                pill.onclick = (clickEvent) => {
                    clickEvent.stopPropagation();
                    window.showEventDetails(evt);
                };
                dayCell.appendChild(pill);
            });

            grid.appendChild(dayCell);
        }
    }

    window.openEventModal = function () {
        document.getElementById('createEventModal').style.display = 'flex';
    }

    window.closeModals = function () {
        document.getElementById('createEventModal').style.display = 'none';
        document.getElementById('viewEventModal').style.display = 'none';
    }

    window.saveEvent = function (e) {
        e.preventDefault();

        const title = document.getElementById('eventTitle').value;
        const start = document.getElementById('eventStart').value;
        const end = document.getElementById('eventEnd').value;
        const location = document.getElementById('eventLocation').value;
        const description = document.getElementById('eventDescription').value;

        const data = {
            title: title,
            start: start,
            end: end,
            location: location,
            description: description
        };

        fetch('/calendar/api/events/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    closeModals();
                    document.getElementById('createEventForm').reset();
                    // Refresh events
                    fetch('/calendar/api/events')
                        .then(response => response.json())
                        .then(data => {
                            events = data;
                            renderCalendar(currentDate);
                        });
                } else {
                    alert('Error al crear evento: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al crear evento');
            });
    }

    window.showEventDetails = function (event) {
        document.getElementById('viewEventTitle').textContent = event.title;

        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
        const startDate = new Date(event.start).toLocaleDateString('es-ES', options);
        let timeStr = `Inicio: ${startDate}`;

        if (event.end) {
            const endDate = new Date(event.end).toLocaleDateString('es-ES', options);
            timeStr += `<br>Fin: ${endDate}`;
        }

        document.getElementById('viewEventTime').innerHTML = timeStr;
        document.getElementById('viewEventLocation').textContent = event.location ? `📍 ${event.location}` : '';
        document.getElementById('viewEventDescription').textContent = event.description || 'Sin descripción';

        document.getElementById('viewEventModal').style.display = 'flex';
    }
});
