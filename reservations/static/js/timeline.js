const $prevDateBtn = document.getElementById('prev-date-btn');
const $nextDateBtn = document.getElementById('next-date-btn');
const $calendarDateInput = document.getElementById('calendar-date');
const $container = document.getElementById('timeline-container');
const modalElement = document.getElementById('reservationModal');
const $formContainer = document.querySelector('#reservationModalInside');
const $daysDropdownButton = document.getElementById('daysDropdown');

// Global variables
let timeline = null;
let items = new vis.DataSet([]);
let groups = new vis.DataSet([]);
let start, end;

let DISPLAY_DAYS = 5;
let BUTTON_SKIP = 2;
let DONE_LOADING = false;

// Default to 1 day on small screens
if (window.screen.width < 900) {
    DISPLAY_DAYS = 1
}

// Initialize the timeline
function initTimeline(centerDate) {
    DISPLAY_DAYS = parseInt(localStorage.getItem('displayDays'), 10) || DISPLAY_DAYS;
    const [start, end] = getRange(centerDate)

    const options = {
        orientation: 'top',
        timeAxis: {
            scale: 'hour',
            step: 1
        },

        // Interaction
        editable: IS_LOGGED_IN,
        onAdd: eventCreated,
        onInitialDrawComplete: () => DONE_LOADING = true,

        selectable: false,
        moveable: true,

        zoomable: true,
        zoomMin: 1000 * 60 * 60,
        zoomMax: 1000 * 60 * 60 * 24 * 7,
        zoomKey: 'ctrlKey',
        horizontalScrollKey: 'shiftKey',
        
        // Design stuff
        margin: {
            item: 0
        },

        // Hide morning and evening
        hiddenDates: [
            {
                start: "2025-01-01T00:00:00",
                end: "2025-01-01T06:00:00",
                repeat: 'daily'
            },
            {
                start: "2025-01-01T20:00:00",
                end: "2025-01-02T00:00:00",
                repeat: 'daily'
            }
        ],
        // Initial start/end and min/max
        start: start,
        min: start,
        max: end,
        end: end,
    };

    // Create the timeline
    timeline = new vis.Timeline($container, items, groups, options);

    // Add event listeners
    timeline.on('click', function (properties) {
        if (properties.item !== null) {
            const realItem = items.get(properties.item);
            eventClicked(realItem.reservationId);
        }
    });

    //Set up the initial data
    loadReservables();
}

var stringToColor = (string, saturation = 70, lightness = 70) => {
    let hash = 0;
    for (let i = 0; i < string.length; i++) {
        hash = string.charCodeAt(i) + ((hash << 5) - hash);
        hash = hash & hash;
    }
    return `hsl(${(hash % 360)}, ${saturation}%, ${lightness}%)`;
}

function eventSource({ startStr, endStr }, successCallback, failureCallback) {
    fetchEventsInRange(startStr, endStr)
        .then(data => {
            const events = data.results.flatMap(reservation => {
                return (reservation.reservables || []).map(reservableId => ({
                    id: `${reservation.id}-${reservableId}`,
                    content: reservation.reason,
                    title: reservation.reason,
                    start: new Date(reservation.start),
                    end: new Date(reservation.end),
                    group: reservableId,
                    style: `background-color: ${stringToColor(reservation.reason)}`,
                    reservationId: reservation.id,
                }));
            });
            successCallback(events);
        })
        .catch(error => {
            console.error('Error loading events:', error);
            alert('Error loading reservations. Please try again.');
            failureCallback(error);
        });
}

function loadReservables() {
    fetchReservables()
        .then(data => {
            const resources = data.results.map(reservable => {
                return {
                    id: reservable.id,
                    content: reservable.name,
                };
            });
            // Add resources to groups dataset
            groups.clear();
            timeline.setGroups(resources);
        });
}


function openForm(formUrl = `/reservations/create?reservableset_slug=${window.RESERVABLE_SET_SLUG}`) {
    // Show modal
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    // Load form content
    htmx.ajax('GET', formUrl, $formContainer).then(() => {
        // Focus on the first input field since something seems to be stealing it, no idea what...
        setTimeout(() => $formContainer.querySelector('[autofocus]')?.focus({focusVisible: true}), 400);
    });
    // Clear on close
    modalElement.addEventListener('hidden.bs.modal', () => {
        $formContainer.innerHTML = '';
    });
}

function eventClicked(event_id) {
    openForm(`/reservations/${event_id}/`);
}

function eventCreated(props, callback) {
    // Immediately destroy the temporary item
    callback(null)
    // Open the creation form
    openForm(`/reservations/create?start=${props.start.toISOString()}&end=${props.end.toISOString()}&reservables=${props.group}&reservableset_slug=${window.RESERVABLE_SET_SLUG}`)
}


function getRange(centerDate) {
    // Default to today
    if (!centerDate)
        centerDate = new Date();

    // Set center date to mid day
    centerDate.setHours(12);
    centerDate.setMinutes(0);

    // Start and end of date range based on DISPLAY_DAYS
    const before = Math.floor((DISPLAY_DAYS - 1) / 2);
    const after = DISPLAY_DAYS - before - 1;
    const start = new Date(centerDate.getFullYear(), centerDate.getMonth(), centerDate.getDate() - before);
    start.setHours(0);
    start.setMinutes(0);
    const end = new Date(centerDate.getFullYear(), centerDate.getMonth(), centerDate.getDate() + after);
    end.setHours(23);
    end.setMinutes(59);

    return [start, end]
}

function loadData() {
    eventSource({
        startStr: start.toISOString(),
        endStr: end.toISOString()
    }, function (events) {
        // Drop items that used to be in this range but are no longer returned
        // (e.g. the reservation was deleted, or edited to drop a reservable).
        const newIds = new Set(events.map(event => event.id));
        const staleIds = items.getIds().filter(id => !newIds.has(id));
        items.remove(staleIds);
        items.update(events);
        console.log(`Loaded ${events.length} events from ${start.toISOString()} to ${end.toISOString()}`);
    }, function (error) {
        console.error('Error loading events:', error);
    });
}

function updateDateInURL(dateStr) {
    const url = new URL(window.location);
    url.searchParams.set('date', dateStr);
    history.replaceState({}, '', url);
}

function setCalendarDate(centerDate) {
    // $calendarDateInput.value is already kept in ISO (YYYY-MM-DD) format.
    updateDateInURL($calendarDateInput.value);

    [start, end] = getRange(centerDate);

    // Start loading data
    loadData();

    if (!DONE_LOADING)
        return;

    // Disable the limit before moving
    timeline.setOptions({
        min: 0,
        max: Number.MAX_SAFE_INTEGER,
    });
    // Animate to the new location
    timeline.setWindow(start, end, {
        animation: true,
    },
        // Re-enable the limit after the animation
        () => {
        timeline.setOptions({
            min: start,
            max: end,
        });
    });
}

function getDateFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const dateParam = urlParams.get('date');
    if (dateParam) {
        const date = new Date(dateParam);
        if (!isNaN(date.getTime())) {
            return date;
        }
    }
    return null;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    const initialDate = getDateFromURL() || new Date();
    $calendarDateInput.value = initialDate.toISOString().split('T')[0];

    initTimeline(initialDate);

    // Handle previous date button click
    $prevDateBtn.addEventListener('click', function () {
        const prevDate = new Date($calendarDateInput.value);
        prevDate.setDate(prevDate.getDate() - BUTTON_SKIP);
        $calendarDateInput.value = prevDate.toISOString().split('T')[0];
        $calendarDateInput.dispatchEvent(new Event('change'));
    });

    // Handle next date button click
    $nextDateBtn.addEventListener('click', function () {
        const nextDate = new Date($calendarDateInput.value);
        nextDate.setDate(nextDate.getDate() + BUTTON_SKIP);
        $calendarDateInput.value = nextDate.toISOString().split('T')[0];
        $calendarDateInput.dispatchEvent(new Event('change'));
    });

    // Handle date input change
    $calendarDateInput.addEventListener('change', function () {
        const selectedDate = new Date(this.value);
        if (!isNaN(selectedDate.getTime())) {
            setCalendarDate(selectedDate);
        }
    });

    // Handle zoom days dropdown
    document.querySelectorAll('.days-option').forEach(el => el.addEventListener('click', function(e) {
        e.preventDefault();
        const days = parseInt(this.getAttribute('data-days'), 10);
        setDays(days)
    }));

    setDays(DISPLAY_DAYS)
});

function setDays(days) {
    DISPLAY_DAYS = days;
    BUTTON_SKIP = days > 1 ? 2 : 1;
    $daysDropdownButton.textContent = `${days}d`;
    localStorage.setItem('displayDays', days);
    setCalendarDate(new Date($calendarDateInput.value));
}

async function fetchReservables() {
    const res = await fetch(`/api/reservables/?reservableset_set__slug=${window.RESERVABLE_SET_SLUG}&type=${window.RESERVABLE_TYPE_SLUG}`)
    return await res.json()
}

async function fetchEventsInRange(startDate, endDate) {
    const res = await fetch(`/api/reservations/?reservables__reservableset_set__slug=${window.RESERVABLE_SET_SLUG}&reservables__type=${window.RESERVABLE_TYPE_SLUG}&start__lte=${endDate}&end__gte=${startDate}`)
    return await res.json()
}
