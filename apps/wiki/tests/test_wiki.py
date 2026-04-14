from django.test import TestCase
from django.urls import reverse

from apps.wiki.models import WikiPage


class WikiPageModelTest(TestCase):

    def test_create_wiki_page(self):
        page = WikiPage.objects.create(
            slug='test-page',
            title='Test Page',
            content='# Hello\n\nSome content.',
        )
        self.assertEqual(str(page), 'Test Page')
        self.assertEqual(page.slug, 'test-page')

    def test_ordering_by_title(self):
        WikiPage.objects.create(slug='zebra', title='Zebra', content='')
        WikiPage.objects.create(slug='alpha', title='Alpha', content='')
        pages = list(WikiPage.objects.all())
        self.assertEqual(pages[0].title, 'Alpha')
        self.assertEqual(pages[1].title, 'Zebra')


class WikiListViewTest(TestCase):

    def setUp(self):
        WikiPage.objects.create(slug='guide', title='Guide', content='Hello')
        WikiPage.objects.create(slug='faq', title='FAQ', content='Questions')

    def test_list_returns_200(self):
        resp = self.client.get(reverse('wiki-list'))
        self.assertEqual(resp.status_code, 200)

    def test_list_shows_all_pages(self):
        resp = self.client.get(reverse('wiki-list'))
        self.assertEqual(len(resp.context['pages']), 2)


class WikiDetailViewTest(TestCase):

    def setUp(self):
        self.page = WikiPage.objects.create(
            slug='getting-started',
            title='Getting Started',
            content='# Welcome\n\nThis is a guide.',
        )

    def test_detail_returns_200(self):
        resp = self.client.get(reverse('wiki-detail', args=['getting-started']))
        self.assertEqual(resp.status_code, 200)

    def test_detail_renders_markdown_to_html(self):
        resp = self.client.get(reverse('wiki-detail', args=['getting-started']))
        self.assertIn('<h1>', resp.context['content_html'])

    def test_detail_404_on_unknown_slug(self):
        resp = self.client.get(reverse('wiki-detail', args=['does-not-exist']))
        self.assertEqual(resp.status_code, 404)
