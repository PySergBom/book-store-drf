from django.contrib.auth.models import User

from store.logic import set_rating
from django.test import TestCase

from store.models import Book, UserBookRelation


class SetRatingTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='sergun', first_name='serg',
                                         last_name='bomeev')  # создаем пользователя
        self.user2 = User.objects.create(username='eva', first_name='jane', last_name='bomeeva')  # создаем пользователя
        self.user3 = User.objects.create(username='egor', first_name='egorka',
                                         last_name='bomeev')  # создаем пользователя

        self.book1 = Book.objects.create(name='Метро 2033', price=200.11, author='Глуховский', owner=self.user1)

        UserBookRelation.objects.create(user=self.user1, book=self.book1, like=True, rate=1)
        UserBookRelation.objects.create(user=self.user2, book=self.book1, like=True, rate=5)
        UserBookRelation.objects.create(user=self.user3, book=self.book1, like=True, rate=4)

    def test_ok(self):
        set_rating(self.book1)
        self.book1.refresh_from_db()
        self.assertEqual('3.33', str(self.book1.rating))
