from django.db import IntegrityError
from django.test import TestCase, tag
from django.urls import reverse

from features.wiki.models import WikiPage


@tag("unit")
class WikiPageModelTest(TestCase):
    def test_create_wiki_page(self):
        page = WikiPage.objects.create(
            slug="test-page",
            title="Test Page",
            content="# Hello\n\nSome content.",
        )
        self.assertEqual(str(page), "Test Page")
        self.assertEqual(page.slug, "test-page")

    def test_ordering_by_title(self):
        WikiPage.objects.create(slug="zebra", title="Zebra", content="")
        WikiPage.objects.create(slug="alpha", title="Alpha", content="")
        pages = list(WikiPage.objects.all())
        self.assertEqual(pages[0].title, "Alpha")
        self.assertEqual(pages[1].title, "Zebra")

    def test_slug_unique_constraint(self):
        WikiPage.objects.create(slug="unique-slug", title="First", content="")
        with self.assertRaises(IntegrityError):
            WikiPage.objects.create(slug="unique-slug", title="Second", content="")

    def test_updated_at_is_set_on_create(self):
        page = WikiPage.objects.create(slug="ts-page", title="TS", content="")
        self.assertIsNotNone(page.updated_at)


@tag("integration")
class WikiListViewTest(TestCase):
    def setUp(self):
        WikiPage.objects.create(slug="guide", title="Guide", content="Hello")
        WikiPage.objects.create(slug="faq", title="FAQ", content="Questions")

    def test_list_returns_200(self):
        resp = self.client.get(reverse("wiki:wiki-list"))
        self.assertEqual(resp.status_code, 200)

    def test_list_shows_all_pages(self):
        resp = self.client.get(reverse("wiki:wiki-list"))
        self.assertEqual(len(resp.context["pages"]), 2)

    def test_list_uses_correct_template(self):
        resp = self.client.get(reverse("wiki:wiki-list"))
        self.assertTemplateUsed(resp, "wiki/list.html")

    def test_list_empty_when_no_pages(self):
        WikiPage.objects.all().delete()
        resp = self.client.get(reverse("wiki:wiki-list"))
        self.assertEqual(len(resp.context["pages"]), 0)


@tag("integration")
class WikiDetailViewTest(TestCase):
    def setUp(self):
        self.page = WikiPage.objects.create(
            slug="getting-started",
            title="Getting Started",
            content="# Welcome\n\nThis is a guide.",
        )

    def test_detail_returns_200(self):
        resp = self.client.get(reverse("wiki:wiki-detail", args=["getting-started"]))
        self.assertEqual(resp.status_code, 200)

    def test_detail_renders_markdown_to_html(self):
        resp = self.client.get(reverse("wiki:wiki-detail", args=["getting-started"]))
        self.assertIn("<h1>", resp.context["content_html"])

    def test_detail_404_on_unknown_slug(self):
        resp = self.client.get(reverse("wiki:wiki-detail", args=["does-not-exist"]))
        self.assertEqual(resp.status_code, 404)

    def test_detail_uses_correct_template(self):
        resp = self.client.get(reverse("wiki:wiki-detail", args=["getting-started"]))
        self.assertTemplateUsed(resp, "wiki/detail.html")

    def test_detail_content_html_in_context(self):
        resp = self.client.get(reverse("wiki:wiki-detail", args=["getting-started"]))
        self.assertIn("content_html", resp.context)

    def test_detail_markdown_bold_renders_to_html(self):
        self.page.content = "**bold text**"
        self.page.save()
        resp = self.client.get(reverse("wiki:wiki-detail", args=["getting-started"]))
        self.assertIn("<strong>", resp.context["content_html"])
