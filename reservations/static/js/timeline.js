const $prevDateBtn = document.getElementById('prev-date-btn');
const $nextDateBtn = document.getElementById('next-date-btn');
const $calendarDateInput = document.getElementById('calendar-date');
const $container = document.getElementById('timeline-container');
const $formContainer = document.querySelector('.reservation-form-container');

// Global variables
let timeline = null;
let items = new vis.DataSet([]);
let groups = new vis.DataSet([]);

const DAYS_BEFORE = 2;
const DAYS_AFTER = 2;
const BUTTON_SKIP = 2;

// Initialize the timeline
function initTimeline() {

    const options = {
        orientation: 'top',
        timeAxis: {
            scale: 'hour',
            step: 1
        },

        // Interaction
        editable: true,
        onAdd: eventCreated,

        selectable: false,
        moveable: true,

        zoomable: true,
        zoomMin: 1000 * 60 * 60,
        zoomMax: 1000 * 60 * 60 * 24 * 7,

        zoomKey: 'ctrlKey',
        horizontalScroll: true,
        // horizontalScrollKey: 'shiftKey',

        // Design stuff
        margin: {
            item: 0
        },

        // Hide morning and evening
        hiddenDates: [{
                start: "2025-01-01T00:01:00",
                end: "2025-01-01T07:00:00",
                repeat: 'daily'
            },
            {
                start: "2025-01-01T19:00:00",
                end: "2025-01-01T23:58:59",
                repeat: 'daily'
            }
        ]
    };

    // Create the timeline
    timeline = new vis.Timeline($container, items, groups, options);

    // Add event listeners
    timeline.on('click', function(properties) {
        if (properties.item !== null) {
            eventClicked(properties.item);
        }
    });

    //Set up the initial data
    loadReservables();
}

var stringToColor = (string, saturation = 50, lightness = 50) => {
    let hash = 0;
    for (let i = 0; i < string.length; i++) {
        hash = string.charCodeAt(i) + ((hash << 5) - hash);
        hash = hash & hash;
    }
    return `hsl(${(hash % 360)}, ${saturation}%, ${lightness}%)`;
}

function eventSource({startStr,endStr}, successCallback, failureCallback) {
    fetchEventsInRange(startStr, endStr)
        .then(data => {
            const events = data.results.map(reservation => {
                return {
                    id: reservation.id,
                    content: reservation.reason,
                    title: reservation.reason,
                    start: new Date(reservation.start),
                    end: new Date(reservation.end),
                    group: reservation.reservables[0], // TODO: Assuming first reservable for grouping
                    style: `background-color: ${stringToColor(reservation.reason)}`
                };
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

function hijackForms(formContainer) {
    const forms = formContainer.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            formContainer.classList.add("loading");
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'Modal': 'Yes'
                }
            });
            if (response.headers["Modal-Close"] === "Yes") {

            }
            formContainer.innerHTML = await response.text();
            hijackForms(formContainer);
            formContainer.classList.remove("loading");
        });
    });
}

// Source - https://stackoverflow.com/a/47614491
// Posted by allenhwkim, modified by community. See post 'Timeline' for change history
// Retrieved 2026-04-02, License - CC BY-SA 4.0

function setInnerHTML(elm, html) {
  elm.innerHTML = html;
  
  Array.from(elm.querySelectorAll("script"))
    .forEach( oldScriptEl => {
      const newScriptEl = document.createElement("script");
      
      Array.from(oldScriptEl.attributes).forEach( attr => {
        newScriptEl.setAttribute(attr.name, attr.value) 
      });
      
      const scriptText = document.createTextNode(oldScriptEl.innerHTML);
      newScriptEl.appendChild(scriptText);
      
      oldScriptEl.parentNode.replaceChild(newScriptEl, oldScriptEl);
  });
}


function openForm(formUrl) {

  // Show modal
  const modalElement = document.getElementById('reservationModal');
  const modal = new bootstrap.Modal(modalElement);
  modal.show();
  // Clear on close
  modalElement.addEventListener('hidden.bs.modal', () => {
    $formContainer.innerHTML = '';
    // Force refresh data
    $calendarDateInput.dispatchEvent(new Event('change'));

  });

    fetch(formUrl, {
            headers: {
                'Modal': 'Yes'
            }
        }).then(async resp1 => {
            // Insert form HTML into modal
            setInnerHTML($formContainer, await resp1.text());
            hijackForms($formContainer);
        })
        .catch(error => {
            console.error('Error loading form:', error);
            alert('Error loading reservation form. Please try again.');
        });
}

function eventClicked(event_id) {
    openForm(`/reservations/${event_id}/`);
}

function eventCreated(props, callback) {
  // Immediately destroy the temporary item
  callback(null)
  // Open the creation form
  openForm(`/reservations/create?start=${props.start.toISOString()}&end=${props.end.toISOString()}&reservables=${props.group}`)
}


function setCalendarDate(centerDate) {
    // Default to today
    if (!centerDate)
        centerDate = new Date();

    // Set center date to mid day
    centerDate.setHours(12);
    centerDate.setMinutes(0);

    console.debug("Setting center date:", centerDate)

    // Start and end of date range
    const start = new Date(centerDate.getFullYear(), centerDate.getMonth(), centerDate.getDate() - DAYS_BEFORE);
    start.setHours(0);
    start.setMinutes(0);
    const end = new Date(centerDate.getFullYear(), centerDate.getMonth(), centerDate.getDate() + DAYS_AFTER);
		end.setHours(23);
    end.setMinutes(59);

    // Start loading data
    eventSource({
        startStr: start.toISOString(),
        endStr: end.toISOString()
    }, function(events) {
        items.clear();
        items.add(events);
    }, function(error) {
        console.error('Error loading events:', error);
    });

    // Move the timeline
    timeline.setOptions({
        min: start,
        max: end,
    });
    timeline.moveTo(centerDate);
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
document.addEventListener('DOMContentLoaded', function() {
    initTimeline();

    // Handle previous date button click
    $prevDateBtn.addEventListener('click', function() {
        const prevDate = new Date($calendarDateInput.value);
        prevDate.setDate(prevDate.getDate() - BUTTON_SKIP);
        $calendarDateInput.value = prevDate.toISOString().split('T')[0];
        $calendarDateInput.dispatchEvent(new Event('change'));
    });

    // Handle next date button click
    $nextDateBtn.addEventListener('click', function() {
        const nextDate = new Date($calendarDateInput.value);
        nextDate.setDate(nextDate.getDate() + BUTTON_SKIP);
        $calendarDateInput.value = nextDate.toISOString().split('T')[0];
        $calendarDateInput.dispatchEvent(new Event('change'));
    });

    // Handle date input change
    $calendarDateInput.addEventListener('change', function() {
        const selectedDate = new Date(this.value);
        if (!isNaN(selectedDate.getTime())) {
            setCalendarDate(selectedDate);
        }
    });

    const initialDate = getDateFromURL();
    $calendarDateInput.value = (initialDate || new Date()).toISOString().split('T')[0]
    $calendarDateInput.dispatchEvent(new Event('change'));
});

async function fetchReservables() {
    const res = await fetch(`/api/reservables/?reservableset_set__slug=${window.RESERVABLE_SET_SLUG}&type=${window.RESERVABLE_TYPE_SLUG}`)
    return await res.json()
}

async function fetchEventsInRange(startDate, endDate) {
    const res = await fetch(`/api/reservations/?reservables__reservableset_set__slug=${window.RESERVABLE_SET_SLUG}&reservables__type=${window.RESERVABLE_TYPE_SLUG}&start__gte=${startDate}&end__lte=${endDate}`)
    return await res.json()
}
