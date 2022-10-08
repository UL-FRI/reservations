"""
Renderers are used to serialize a response into specific media types.

They give us a generic way of being able to handle various media types
on the response, such as JSON encoded data or HTML output.

REST framework also provides an HTML renderer the renders the browsable API.
"""
from __future__ import unicode_literals


from django.template import RequestContext, Template, loader
from django.template.loader import render_to_string
from django.urls import resolve

from rest_framework import VERSION, exceptions, status
from rest_framework.exceptions import ParseError
from rest_framework.renderers import BaseRenderer, BrowsableAPIRenderer
from rest_framework.request import is_form_media_type, override_method
from rest_framework.settings import api_settings
from rest_framework.utils.breadcrumbs import get_breadcrumbs


class HTMLFormRenderer(BaseRenderer):
    """
    Renderers serializer data into an HTML form.

    If the serializer was instantiated without an object then this will
    return an HTML form not bound to any object,
    otherwise it will return an HTML form with the appropriate initial data
    populated from the object.

    Note that rendering of field and form errors is not currently supported.
    """

    media_type = "text/html"
    format = "form"
    template = "rest_framework/inline/form.html"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render serializer data and return an HTML form, as a string.
        """
        renderer_context = renderer_context or {}
        return render_to_string(self.template, renderer_context)


class TemplateRenderer(BrowsableAPIRenderer):
    """Pass"""

    def resolve_template(self, template_names):
        return loader.select_template(template_names)

    def get_template_names(self, response, view):
        if response.template_name:
            return [response.template_name]
        elif hasattr(self, "template_name"):
            return [self.template_name]
        elif hasattr(view, "get_template_names"):
            return view.get_template_names()
        elif hasattr(view, "template_name"):
            return [view.template_name]
        match = resolve(view.request.path)
        l = [
            "{app_name}/{url_name}.html",
            "{url_name}.html",
            "reservations/{url_name}.html",
            "{app_name}/{url_type}.html",
            "{url_type}.html",
            "reservations/{url_type}.html",
        ]
        d = {
            "app_name": match.app_name,
            "url_name": match.url_name,
            "url_type": match.url_name.split("-")[-1],
        }
        result = [i.format(**d) for i in l]
        print("Result", result)
        return result

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render the HTML for the browsable API representation.
        """
        view = renderer_context["view"]
        response = renderer_context["response"]
        template_names = self.get_template_names(response, view)

        self.accepted_media_type = accepted_media_type or ""
        self.renderer_context = renderer_context or {}

        context = self.get_context(data, accepted_media_type, renderer_context)
        template = self.resolve_template(template_names)
        ret = template.render(context, request=renderer_context["request"])

        # Munge DELETE Response code to allow us to return content
        # (Do this *after* we've rendered the template so that we include
        # the normal deletion response code in the output)
        response = renderer_context["response"]
        if response.status_code == status.HTTP_204_NO_CONTENT:
            response.status_code = status.HTTP_200_OK

        return ret


class TemplateAPIRenderer(BaseRenderer):
    """
    HTML renderer used to self-document the API, with booze and hookers.
    """

    media_type = "text/html"
    format = "template"
    template_name = None
    exception_template_names = ["%(status_code)s.html", "api_exception.html"]
    charset = "utf-8"
    form_renderer_class = HTMLFormRenderer

    def show_form_for_method(self, view, method, request, obj):
        """
        Returns True if a form should be shown for this method.
        """
        if not method in view.allowed_methods:
            return  # Not a valid method
        try:
            view.check_permissions(request)
            if obj is not None:
                view.check_object_permissions(request, obj)
        except exceptions.APIException:
            return False  # Doesn't have permissions
        return True

    def get_rendered_html_form(self, view, method, request):
        """
        Return a string representing a rendered HTML form, possibly bound to
        either the input or output data.

        In the absence of the View having an associated form then return None.
        """
        if request.method == method:
            try:
                data = request.data
                files = request.FILES
            except ParseError:
                data = None
                files = None
        else:
            data = None
            files = None

        with override_method(view, request, method) as request:
            obj = getattr(view, "object", None)
            if not self.show_form_for_method(view, method, request, obj):
                return

            if method in ("DELETE", "OPTIONS"):
                return True  # Don't actually need to return a form

            if not getattr(view, "get_serializer", None) or not any(
                is_form_media_type(parser.media_type) for parser in view.parser_classes
            ):
                return
            # try loading the partial data
            serializer = view.get_serializer(instance=obj, data=data)
            data_complete = serializer.is_valid()
            data = serializer.data
            if not data_complete:
                for k, f in serializer.fields.items():
                    if k in data and k in request.GET:
                        try:
                            if type(data[k]) == list:
                                x = list()
                                for i in request.GET.getlist(k):
                                    try:
                                        x.append(f.from_native(i).id)
                                    except:
                                        pass
                            else:
                                x = f.from_native(request.GET.get(k))
                            data[k] = x
                            data.fields[k]._value = x
                        except Exception:
                            pass
            form_renderer = self.form_renderer_class()
            return form_renderer.render(
                data, self.accepted_media_type, self.renderer_context
            )

    def get_name(self, view):
        return view.get_view_name()

    def get_description(self, view):
        return view.get_view_description(html=True)

    def get_breadcrumbs(self, request):
        return get_breadcrumbs(request.path)

    def get_context(self, data, accepted_media_type, renderer_context):
        """
        Returns the context used to render.
        """
        view = renderer_context["view"]
        request = renderer_context["request"]
        response = renderer_context["response"]
        response_headers = dict(response.items())
        context = {
            "data": data,
            "data_listlike": not hasattr(data, "get"),
            "view": view,
            "request": request,
            "response": response,
            "description": self.get_description(view),
            "name": self.get_name(view),
            "version": VERSION,
            "breadcrumblist": self.get_breadcrumbs(request),
            "allowed_methods": view.allowed_methods,
            "available_formats": [
                renderer.format for renderer in view.renderer_classes
            ],
            "response_headers": response_headers,
            "put_form": self.get_rendered_html_form(view, "PUT", request),
            "post_form": self.get_rendered_html_form(view, "POST", request),
            "delete_form": self.get_rendered_html_form(view, "DELETE", request),
            "display_edit_forms": bool(response.status_code != 403),
            "api_settings": api_settings,
        }
        return context

    def get_template_names(self, response, view):
        if response.template_name:
            return [response.template_name]
        elif self.template_name:
            return [self.template_name]
        elif hasattr(view, "get_template_names"):
            return view.get_template_names()
        elif hasattr(view, "template_name"):
            return [view.template_name]
        match = resolve(view.request.path)
        l = [
            "{app_name}/{url_name}.html",
            "{url_name}.html",
            "reservations/{url_name}.html",
            "{app_name}/{url_type}.html",
            "{url_type}.html",
            "reservations/{url_type}.html",
        ]
        d = {
            "app_name": match.app_name,
            "url_name": match.url_name,
            "url_type": match.url_name.split("-")[-1],
        }
        result = [i.format(**d) for i in l]
        print("Result", result)
        return result

    def resolve_template(self, template_names):
        return loader.select_template(template_names)

    def get_exception_template(self, response):
        template_names = [
            name % {"status_code": response.status_code}
            for name in self.exception_template_names
        ]
        try:
            # Try to find an appropriate error template
            return self.resolve_template(template_names)
        except Exception:
            # Fall back to using eg '404 Not Found'
            return Template(
                "%d %s" % (response.status_code, response.status_text.title())
            )

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render the HTML for the template
        """
        print("Rendering")
        self.accepted_media_type = accepted_media_type or ""
        self.renderer_context = renderer_context or {}
        print("Context", self.renderer_context)
        view = renderer_context["view"]
        request = renderer_context["request"]
        response = renderer_context["response"]
        if response.exception:
            template = self.get_exception_template(response)
        else:
            template_names = self.get_template_names(response, view)
            template = self.resolve_template(template_names)
        context = self.get_context(data, accepted_media_type, renderer_context)
        # context = RequestContext(renderer_context['request'], context)
        print("Data", data)
        data.update(context)
        ret = template.render(data, request=request)

        # Munge DELETE Response code to allow us to return content
        # (Do this *after* we've rendered the template so that we include
        # the normal deletion response code in the output)
        response = renderer_context["response"]
        if response.status_code == status.HTTP_204_NO_CONTENT:
            response.status_code = status.HTTP_200_OK

        return ret
