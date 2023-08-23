import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg, F
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase
from store.models import Book, UserBookRelation
from store.serializers import BookSerializer
from django.test.utils import CaptureQueriesContext
from django.db import connection



class BooksApiTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='username')  # создаем пользователя
        self.book1 = Book.objects.create(name='Метро 2033', price=400.11, author='Глуховский',
                                         owner=self.user)
        self.book2 = Book.objects.create(name='Глуховский Метро 2034', price=300.11, author='Gluhovski',
                                         owner=self.user)
        self.book3 = Book.objects.create(name='Гарри Поттер', price=200.61, author='Роалинг',
                                         owner=self.user)
        self.book4 = Book.objects.create(name='Игра престолов', price=700.23, author='Мартин',
                                         owner=self.user)
        UserBookRelation.objects.create(user=self.user, book=self.book1, like=True, rate=1)

    def test_get_without_filter(self):
        url = reverse('book-list')
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
            # print('queries', len(queries))
            self.assertEqual(2, len(queries))
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
        ).prefetch_related('readers').order_by('id')
        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)  # проверка на статус ответа
        self.assertEqual(serializer_data, response.data)  # сравнение данных
        self.assertEqual(serializer_data[0]['rating'], '1.00')  # дополнительная проверка, что работает annotate
        # self.assertEqual(serializer_data[0]['likes_count'], 1)
        self.assertEqual(serializer_data[0]['annotated_likes'], 1)

    def test_get_filter(self):
        url = reverse('book-list')
        books = Book.objects.filter(id__in=[self.book1.id, self.book2.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
        ).prefetch_related('readers').order_by('id')
        response = self.client.get(url, data={'search': 'Глуховский'})
        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)  # проверка на статус ответа
        self.assertEqual(serializer_data, response.data)  # сравнение данных

    def test_get_sort(self):
        url = reverse('book-list')
        books = Book.objects.filter(id__in=[self.book1.id, self.book2.id, self.book3.id, self.book4.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
        ).prefetch_related('readers').order_by('price')
        response = self.client.get(url, data={'ordering': 'price'})
        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)  # проверка на статус ответа
        self.assertEqual(serializer_data, response.data)  # сравнение данных

    def test_create(self):
        self.assertEqual(4, Book.objects.all().count())
        url = reverse('book-list')
        data = {
            "name": "Марсианин",
            "price": 23,
            "author": "Эдгар Берроуз"
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)  # логиним ранее созданного в setUp пользователя
        response = self.client.post(url, data=json_data,
                                    content_type='application/json')
        self.assertEqual(5, Book.objects.all().count())  # проверка на то, что книга реально создана
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)  # проверка на статус ответа
        # print(Book.objects.last().owner)

    def test_update(self):
        url = reverse('book-detail', args=(self.book1.id,))  # Т.к. в урл нужно отправить id книги
        data = {
            "name": self.book1.name,
            "price": 199,
            "author": self.book1.name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)  # логиним ранее созданного в setUp пользователя
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)  # проверка на статус ответа
        # self.book1 = Book.objects.get(id=self.book1.id)
        # Если это не сделать, то тесты упадут, т.к. объект book1 не изменится, нужно еще раз из базы эту инфу скачать
        # Есть другой вариант:
        self.book1.refresh_from_db()
        self.assertEqual(199, self.book1.price)

    def test_delete(self):
        self.assertEqual(4, Book.objects.all().count())
        url = reverse('book-detail', args=(self.book1.id,))  # Т.к. в урл нужно отправить id книги
        self.client.force_login(self.user)  # логиним ранее созданного в setUp пользователя
        response = self.client.delete(url)
        self.assertEqual(3, Book.objects.all().count())  # проверка на то, что книга реально удалена
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)  # проверка на статус ответа

    def test_update_not_owner(self):
        url = reverse('book-detail', args=(self.book1.id,))  # Т.к. в урл нужно отправить id книги
        self.user2 = User.objects.create(username='not_owner')  # создаем пользователя
        data = {
            "name": self.book1.name,
            "price": 199,
            "author": self.book1.name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)  # логиним ранее созданного в setUp пользователя
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')
        # print(response.data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)  # проверка на статус ответа
        # self.book1 = Book.objects.get(id=self.book1.id)
        # Если это не сделать, то тесты упадут, т.к. объект book1 не изменится, нужно еще раз из базы эту инфу скачать
        # Есть другой вариант:
        self.book1.refresh_from_db()
        self.assertEqual(Decimal('400.11'), self.book1.price)
        self.assertEqual({'detail': ErrorDetail(string='You do not have permission to perform this action.',
                                                code='permission_denied')}, response.data)

    def test_delete_not_owner(self):
        self.user2 = User.objects.create(username='not_owner')
        self.assertEqual(4, Book.objects.all().count())
        url = reverse('book-detail', args=(self.book1.id,))  # Т.к. в урл нужно отправить id книги
        self.client.force_login(self.user2)  # логиним ранее созданного в setUp пользователя
        response = self.client.delete(url)
        self.assertEqual(4, Book.objects.all().count())  # проверка на то, что книга реально удалена
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)  # проверка на статус ответа

    def test_update_not_owner_but_stuff(self):
        url = reverse('book-detail', args=(self.book1.id,))  # Т.к. в урл нужно отправить id книги
        self.user2 = User.objects.create(username='not_owner', is_staff=True)  # создаем пользователя
        data = {
            "name": self.book1.name,
            "price": 199,
            "author": self.book1.author,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)  # логиним ранее созданного в setUp пользователя
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')
        # print(response.data)
        self.assertEqual(status.HTTP_200_OK, response.status_code)  # проверка на статус ответа
        # self.book1 = Book.objects.get(id=self.book1.id)
        # Если это не сделать, то тесты упадут, т.к. объект book1 не изменится, нужно еще раз из базы эту инфу скачать
        # Есть другой вариант:
        self.book1.refresh_from_db()
        self.assertEqual(199, self.book1.price)


class BooksRelationTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create(username='username1234')  # создаем пользователя
        self.user2 = User.objects.create(username='username2')  # создаем пользователя 2
        self.book1 = Book.objects.create(name='Метро 2033', price=400.11, author='Глуховский',
                                         owner=self.user)
        self.book2 = Book.objects.create(name='Гарри Поттер', price=200.61, author='Роалинг',
                                         owner=self.user)

    def test_like(self):
        url = reverse('userbookrelation-detail', args=(self.book1.id,))
        print(url)
        data = {
            'like': True,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)  # проверка на статус ответа
        relation = UserBookRelation.objects.get(user=self.user, book=self.book1)
        self.assertTrue(relation.like)  # ожидание лайка
        data = {
            'in_bookmarks': True,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)  # проверка на статус ответа
        relation = UserBookRelation.objects.get(user=self.user, book=self.book1)
        self.assertTrue(relation.in_bookmarks)  # ожидание лайка

    def test_rate(self):
        url = reverse('userbookrelation-detail', args=(self.book1.id,))
        data = {
            'rate': 3,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)  # проверка на статус ответа
        relation = UserBookRelation.objects.get(user=self.user, book=self.book1)
        self.assertEqual(3, relation.rate)  # ожидание лайка

    def test_rate_wrong(self):
        url = reverse('userbookrelation-detail', args=(self.book1.id,))
        data = {
            'rate': 6,  # введем неправильные данные
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code, response.data)
