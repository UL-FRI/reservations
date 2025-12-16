## Frontend

The site uses almost exclusively normal Django templating, except for the timeline view. That view is fully client-side implemented in JavaScript, but it still uses Django forms for editing and creating events.

When a user wants to edit or create an event, a modal popup is opened and a `fetch` request is made to the correct UpdateView or CreateView. This request has a special header `Modal: Yes`, which signals to the backend that it shouldn't use the usual base template (with a header and footer - `base.html`), but a special base template (`modal_base.html`) which does not contain anything but the `content` block. The returned HTML is then inserted into the modal.

If the response contains and `<form>` elements, the JavaScript "hijacks" their `submit` event and handles it using `fetch`. The response is included back into the modal and the "form hijacking" is set up again. Once the modal is closed, the timeline data is refreshed. 

This setup allows all form generation and validation logic to happen on the backend using Django's form system and `crispy-forms`, but the client can still have a seamless redirect-free experience.
