"""Pagination shared by every list endpoint."""

from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """Page-number pagination with the metadata the SPA's toolbars need.

    DRF's default response gives you `count`, `next` and `previous`. The shop
    toolbar renders "Showing 13-24 of 60 products" and a numbered pager, which
    needs the page count and the current page as numbers rather than as URLs
    to parse.
    """

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 60

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("total_pages", self.page.paginator.num_pages),
                    ("current_page", self.page.number),
                    ("page_size", self.get_page_size(self.request)),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )


class LargePagination(StandardPagination):
    """For dashboard tables, which the old app hard-coded to 20 per page."""

    page_size = 20
    max_page_size = 100
