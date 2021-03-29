from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse


class Sitemap(Sitemap):
    def items(self):
        return ["about", "frontpage", "contact", "exam:exam"]

    def location(self, item):
        return reverse(item)
