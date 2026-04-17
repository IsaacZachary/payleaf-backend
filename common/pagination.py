from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from urllib import parse

class PayLeafPagination(CursorPagination):
    page_size = 25
    cursor_query_param = 'starting_after'
    ordering = '-created_at' # Default ordering

    def get_paginated_response(self, data):
        next_link = self.get_next_link()
        next_cursor = None
        if next_link:
            parsed = parse.urlparse(next_link)
            next_cursor = parse.parse_qs(parsed.query).get(self.cursor_query_param, [None])[0]

        return Response({
            'data': data,
            'has_more': bool(next_link),
            'next_cursor': next_cursor
        })
