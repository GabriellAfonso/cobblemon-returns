from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.collector.models import CollectionLog
from apps.wiki.models import WikiPage

User = get_user_model()


def _staff_user():
    return User.objects.create_user(username='staff', password='pass', is_staff=True)


def _regular_user():
    return User.objects.create_user(username='regular', password='pass', is_staff=False)


class StaffRequiredTest(TestCase):

    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse('dashboard:home'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin/login/', resp['Location'])

    def test_non_staff_redirected_to_login(self):
        _regular_user()
        self.client.login(username='regular', password='pass')
        resp = self.client.get(reverse('dashboard:home'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin/login/', resp['Location'])

    def test_staff_can_access(self):
        _staff_user()
        self.client.login(username='staff', password='pass')
        resp = self.client.get(reverse('dashboard:home'))
        self.assertEqual(resp.status_code, 200)


class WikiCreateViewTest(TestCase):

    def setUp(self):
        _staff_user()
        self.client.login(username='staff', password='pass')

    def test_create_wiki_page(self):
        self.client.post(reverse('dashboard:wiki-create'), {
            'title': 'New Page',
            'slug': 'new-page',
            'content': '# Hello\nContent here.',
        })
        self.assertEqual(WikiPage.objects.filter(slug='new-page').count(), 1)

    def test_create_redirects_to_list(self):
        resp = self.client.post(reverse('dashboard:wiki-create'), {
            'title': 'Redirect Test',
            'slug': 'redirect-test',
            'content': 'Some content.',
        })
        self.assertRedirects(resp, reverse('dashboard:wiki-list'))

    def test_create_get_returns_200(self):
        resp = self.client.get(reverse('dashboard:wiki-create'))
        self.assertEqual(resp.status_code, 200)


class WikiDeleteViewTest(TestCase):

    def setUp(self):
        _staff_user()
        self.client.login(username='staff', password='pass')
        self.page = WikiPage.objects.create(slug='to-delete', title='To Delete', content='bye')

    def test_delete_removes_page(self):
        self.client.post(reverse('dashboard:wiki-delete', args=['to-delete']))
        self.assertFalse(WikiPage.objects.filter(slug='to-delete').exists())

    def test_delete_get_shows_confirmation(self):
        resp = self.client.get(reverse('dashboard:wiki-delete', args=['to-delete']))
        self.assertEqual(resp.status_code, 200)

    def test_delete_redirects_to_list(self):
        resp = self.client.post(reverse('dashboard:wiki-delete', args=['to-delete']))
        self.assertRedirects(resp, reverse('dashboard:wiki-list'))


class CollectionLogViewTest(TestCase):

    def setUp(self):
        _staff_user()
        self.client.login(username='staff', password='pass')
        for i in range(60):
            CollectionLog.objects.create(status='ok', players_updated=i)

    def test_log_view_returns_200(self):
        resp = self.client.get(reverse('dashboard:logs'))
        self.assertEqual(resp.status_code, 200)

    def test_log_view_returns_at_most_50(self):
        resp = self.client.get(reverse('dashboard:logs'))
        self.assertLessEqual(len(resp.context['logs']), 50)
