# -*- coding: utf-8 -*-
"""Quart request argument parsing module.

Example: ::

    from quart import Quart

    from webargs import fields
    from webargs.quartparser import use_args

    app = Quart(__name__)

    hello_args = {
        'name': fields.Str(required=True)
    }

    @app.route('/')
    @use_args(hello_args)
    def index(args):
        return 'Hello ' + args['name']

    app.run()
"""
import quart
from quart.exceptions import HTTPException

from webargs import core
from webargs.core import json
from webargs.asyncparser import AsyncParser


def abort(http_status_code, exc=None, **kwargs):
    """Raise a HTTPException for the given http_status_code. Attach any keyword
    arguments to the exception for later processing.
    """
    try:
        quart.abort(http_status_code)
    except HTTPException as err:
        err.data = kwargs
        err.exc = exc
        raise err


def is_json_request(req):
    return core.is_json(req.mimetype)


class QuartParser(AsyncParser):
    """Quart request argument parser."""

    __location_map__ = dict(view_args="parse_view_args",
                            **core.Parser.__location_map__)

    def parse_view_args(self, req, name, field):
        """Pull a value from the request's ``view_args``."""
        return core.get_value(req.view_args, name, field)

    async def parse_form(self, req, name, field):
        """Pull a form value from the request."""
        post_data = self._cache.get("post")
        if post_data is None:
            self._cache["post"] = await req.form
        return core.get_value(self._cache["post"], name, field)

    async def parse_json(self, req, name, field):
        """Pull a json value from the request."""
        body = await req.body
        if not (body and is_json_request(req)):
            return core.missing
        json_data = self._cache.get("json")
        if json_data is None:
            try:
                json_data = await req.json
            except json.JSONDecodeError as e:
                if e.doc == "":
                    return core.missing
                else:
                    return self.handle_invalid_json_error(e, req)
            self._cache["json"] = json_data
        return core.get_value(json_data, name, field, allow_many_nested=True)

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return core.get_value(req.args, name, field)

    def parse_headers(self, req, name, field):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, field)

    def parse_cookies(self, req, name, field):
        """Pull a value from the cookiejar."""
        return core.get_value(req.cookies, name, field)

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        return core.get_value(req.files, name, field)

    def handle_error(self, error, req, schema, error_status_code, error_headers):
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 422 error.
        """
        status_code = error_status_code or self.DEFAULT_VALIDATION_STATUS
        abort(
            status_code,
            exc=error,
            messages=error.messages,
            schema=schema,
            headers=error_headers,
        )

    def handle_invalid_json_error(self, error, req, *args, **kwargs):
        abort(400, exc=error, messages={"json": ["Invalid JSON body."]})

    def get_default_request(self):
        """Override to use Quart's thread-local request object by default"""
        return quart.request


parser = QuartParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
