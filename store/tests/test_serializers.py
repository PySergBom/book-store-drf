from collections import OrderedDict

from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg, F
from django.test import TestCase

from store.models import Book, UserBookRelation
from store.serializers import BookSerializer


class BookSerializerTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='sergun', first_name='serg',
                                         last_name='bomeev')  # создаем пользователя
        self.user2 = User.objects.create(username='eva', first_name='jane', last_name='bomeeva')  # создаем пользователя
        self.user3 = User.objects.create(username='egor', first_name='egorka',
                                         last_name='bomeev')  # создаем пользователя

        self.book1 = Book.objects.create(name='Метро 2033', price=200.11, author='Глуховский', owner=self.user1)
        self.book2 = Book.objects.create(name='Гарри Поттер', price=200.61, author='Роалинг', owner=self.user2)
        UserBookRelation.objects.create(user=self.user1, book=self.book1, like=True, rate=1)
        UserBookRelation.objects.create(user=self.user2, book=self.book1, like=True, rate=4)
        UserBookRelation.objects.create(user=self.user3, book=self.book1, like=True, rate=5)

        UserBookRelation.objects.create(user=self.user1, book=self.book2, like=True, rate=3)
        UserBookRelation.objects.create(user=self.user2, book=self.book2, like=True, rate=2)
        UserBookRelation.objects.create(user=self.user3, book=self.book2, like=False)

    def test_ok(self):
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
        ).prefetch_related('readers').order_by('id')
        data = BookSerializer(books, many=True).data
        expected_data_1 = [OrderedDict()]

        expected_data = [
            OrderedDict(
                {
                    'id': self.book1.id,
                    'name': 'Метро 2033',
                    'price': '200.11',
                    'author': 'Глуховский',
                    'annotated_likes': 3,
                    'rating': '3.33',
                    'owner_name': 'sergun',
                    'readers': [OrderedDict(
                        {
                            'first_name': 'serg',
                            'last_name': 'bomeev',
                        }), OrderedDict(
                        {
                            'first_name': 'jane',
                            'last_name': 'bomeeva',
                        }), OrderedDict(
                        {
                            'first_name': 'egorka',
                            'last_name': 'bomeev',
                        })

                    ]
                }),
            OrderedDict(
                {
                    'id': self.book2.id,
                    'name': 'Гарри Поттер',
                    'price': '200.61',
                    'author': 'Роалинг',
                    'annotated_likes': 2,
                    'rating': '2.50',
                    'owner_name': 'eva',
                    'readers': [OrderedDict(
                        {
                            'first_name': 'serg',
                            'last_name': 'bomeev',
                        }), OrderedDict(
                        {
                            'first_name': 'jane',
                            'last_name': 'bomeeva',
                        }), OrderedDict(
                        {
                            'first_name': 'egorka',
                            'last_name': 'bomeev',
                        })

                    ]
                })
        ]
        self.assertEqual(expected_data, data)
