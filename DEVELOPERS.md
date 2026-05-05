## Frontend

The site uses almost exclusively normal Django templating, except for the timeline view, which is a bit more JS-heavy. Interactivity (outside of the timeline) is handled using [htmx](https://htmx.org).

In order to take advantage of the form generation and validation provided by Django and `crispy-forms`, while keeping a seamless modal popup experience, the CreateView and UpdateView uses a hacky template (`auto_base.html`), which detects if the request is an HTMX request and renders only the form, without the rest of the page.
