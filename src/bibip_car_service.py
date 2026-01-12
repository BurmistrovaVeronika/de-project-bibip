import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale


class CarService:

    # Константы для работы с фиксированной длиной строк
    # Длина данных в символах
    LINE_DATA_LENGTH = 500
    # Длина строки в байтах (с учетом символа новой строки)
    LINE_TOTAL_LENGTH = 501

    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path
        os.makedirs(root_directory_path, exist_ok=True)

    def _write_fixed_length_line(
            self,
            filepath: str,
            line_number: int,
            data: str
    ) -> None:
        """
        Записывает строку фиксированной длины в файл на указанную позицию

        Args:
            filepath: путь к файлу
            line_number: номер строки для записи
            data: строка данных для записи

        Raises:
            ValueError: если длина данных превышает 500 символов
        """
        if len(data) > self.LINE_DATA_LENGTH:
            error_msg = (
                f'Данные слишком длинные: {len(data)} > '
                f'{self.LINE_DATA_LENGTH}'
            )
            raise ValueError(error_msg)

        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8'):
                pass

        # Заполнение пробелами до 500 символов
        formatted_data = data.ljust(self.LINE_DATA_LENGTH)
        line_to_write = formatted_data + '\n'

        with open(filepath, 'r+', encoding='utf-8') as f:
            position = line_number * self.LINE_TOTAL_LENGTH
            f.seek(position)
            f.write(line_to_write)

    def _read_fixed_length_line(self, filepath: str, line_number: int) -> str:
        """
        Читает строку фиксированной длины из файла

        Args:
            filepath: путь к файлу
            line_number: номер строки

        Returns:
            прочитанная строка

        Raises:
            FileNotFoundError: если файл не существует
        """

        with open(filepath, 'r', encoding='utf-8') as f:
            position = line_number * self.LINE_TOTAL_LENGTH
            f.seek(position)
            val = f.read(self.LINE_DATA_LENGTH)
            f.read(1)
            return val.rstrip()

    def _append_fixed_length_line(self, filepath: str, data: str) -> int:
        """
        Добавляет строку в конец файла фиксированной длины

        Args:
            filepath: путь к файлу
            data: данные для записи

        Returns:
            Номер строки, в которую записаны данные
        """

        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8'):
                pass

        with open(filepath, 'r', encoding='utf-8') as f:
            f.seek(0, 2)
            file_size = f.tell()

        line_number = file_size // self.LINE_TOTAL_LENGTH
        self._write_fixed_length_line(filepath, line_number, data)

        return line_number

    def _load_index(self, index_filepath: str) -> Dict[str, int]:
        """
        Загружает индекс из файла

        Args:
            index_filepath: путь к индексному файлу

        Returns:
            Словарь с индексом или пустой словарь, если файла нет.
        """
        if not os.path.exists(index_filepath):
            return {}
        try:
            with open(index_filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_index(self, index_filepath: str, index_data: dict) -> None:
        """
        Сохраняет индекс в файл

        Args:
            index_filepath: путь к индексному файлу
            index_data: данные индекса
        """
        with open(index_filepath, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2)

    def _get_file_line_count(self, filepath: str) -> int:
        """
        Определяет количество строк в файле

        Args:
            filepath: путь к файлу

        Returns:
            Количество строк в файле
        """
        if not os.path.exists(filepath):
            return 0

        # Размер файла в байтах
        file_size = os.path.getsize(filepath)

        # Целочисленное деление дает количество строк
        return file_size // self.LINE_TOTAL_LENGTH

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        """
        Добавляет модель автомобиля в базу данных.
        Создает запись в models.txt.
        Обновляет model_index.txt.

        Args:
            model: объект Model для добавления

        Returns:
            добавленная модель

        Raises:
            ValueError: если модель с таким ID уже существует
            ValueError: если длина данных модели больше 500 символов
        """
        # Определение пути к файлу
        models_file = os.path.join(self.root_directory_path, 'models.txt')
        models_index_file = os.path.join(
            self.root_directory_path, 'models_index.txt'
        )

        # Загрузка текущего индекса моделей
        index = self._load_index(models_index_file)

        # Получение ключа для индекса
        model_key = model.index()

        # Проверка на существование такого же ID
        if model_key in index:
            raise ValueError(f'Модель с ID {model.id} уже существует')

        # Сериализация модели в строку
        model_data = f'{model.id}|{model.name}|{model.brand}'

        # Проверка длины данных
        if len(model_data) > self.LINE_DATA_LENGTH:
            raise ValueError(
                f'Данные модели слишком длинные: {len(model_data)} символов'
            )

        # Добавление данных в models.txt
        line_number = self._append_fixed_length_line(models_file, model_data)

        # Обновление индекса (ID модели -> номер строки)
        index[model_key] = line_number

        # Сохранение обновленного индекса
        self._save_index(models_index_file, index)
        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        """
        Добавляет автомобиль в базу данных.
        Создает запись в cars.txt.
        Обновляет cars_index.txt.

        Args:
            car: объект Car для добавления

        Returns:
            добавленный автомобиль

        Raises:
            ValueError: если автомобиль с таким VIN уже существует
            ValueError: если модель автомобиля не найдена
            ValueError: если длина данных автомобиля больше 500 символов
        """
        # Определение путей к файлам
        cars_file = os.path.join(self.root_directory_path, 'cars.txt')
        cars_index_file = os.path.join(
            self.root_directory_path, 'cars_index.txt'
            )

        # Загрузка текущего индекса автомобилей
        cars_index = self._load_index(cars_index_file)

        # Проверка существования автомобиля
        car_key = car.index()
        if car_key in cars_index:
            raise ValueError(f'Автомобиль с VIN {car.vin} уже существует')

        # Проверка существования модели
        models_index_file = os.path.join(
            self.root_directory_path, 'models_index.txt'
        )
        models_index = self._load_index(models_index_file)
        model_key = str(car.model)
        if model_key not in models_index:
            raise ValueError(f'Модель с ID {car.model} не найдена')

        # Сериализация автомобиля
        price_str = str(car.price)
        date_str = car.date_start.isoformat()
        status_str = car.status.value
        car_data = f'{car.vin}|{car.model}|{price_str}|{date_str}|{status_str}'

        # Проверка длины данных
        if len(car_data) > self.LINE_DATA_LENGTH:
            raise ValueError(
                f'Данные автомобиля слишком длинные: {len(car_data)} символов'
            )

        # Запись данных
        line_number = self._append_fixed_length_line(cars_file, car_data)

        # Обновление индекса
        cars_index[car_key] = line_number
        self._save_index(cars_index_file, cars_index)
        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        """
        Фиксирует продажу автомобиля.

        Записывет продажу в sales.txt и sales_index.txt
        Находит автомобиль по VIN
        Обновляет статус автомобиля на 'sold'
        Записывает обновленный автомобиль обратно

        Args:
            sale: объект Sale с информацией о продаже

        Returns:
            обновленный объект Car c новым статусом

        Raises:
            ValueError: если автомобиль не найден
            ValueError: если автомобиль уже продан
            ValueError: если длина данных больше 500 символов
        """
        # Сохранение продажи
        # Определение путей к файлам продаж
        sales_file = os.path.join(self.root_directory_path, 'sales.txt')
        sales_index_file = os.path.join(
            self.root_directory_path, 'sales_index.txt'
        )

        # Загрузка индекса продаж
        sales_index = self._load_index(sales_index_file)

        # Сериализация продажи
        cost_str = str(sale.cost)
        date_str = sale.sales_date.isoformat()
        sale_data = (
            f'{sale.sales_number}|{sale.car_vin}|{cost_str}|{date_str}'
        )

        # Проверка длины данных
        if len(sale_data) > self.LINE_DATA_LENGTH:
            raise ValueError(
                f'Данные продажи слишком длинные: '
                f'{len(sale_data)} символов'
            )

        # Добавление продажи в файл
        sale_line_number = self._append_fixed_length_line(
            sales_file,
            sale_data
        )

        # Обновление индекса продаж
        sales_index[sale.index()] = sale_line_number
        self._save_index(sales_index_file, sales_index)

        # Поиск автомобиля
        # Определение пути к файлам автомобилей
        cars_file = os.path.join(self.root_directory_path, 'cars.txt')
        cars_index_file = os.path.join(
            self.root_directory_path, 'cars_index.txt'
        )

        # Загрузка индекса автомобилей
        cars_index = self._load_index(cars_index_file)

        # Поиск номера строки автомобиля по VIN
        car_line_number = cars_index.get(sale.car_vin)
        if car_line_number is None:
            error_msg = (
                f'Автомобиль с VIN {sale.car_vin} '
                f'не найден'
            )
            raise ValueError(error_msg)

        # Чтение данных автомобиля из файла
        car_data_str = self._read_fixed_length_line(cars_file, car_line_number)

        # Десериализация автомобиля
        parts = car_data_str.split('|')
        car = Car(
            vin=parts[0],
            model=int(parts[1]),
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=CarStatus(parts[4])
        )

        # Проверка статуса
        if car.status == CarStatus.sold:
            error_msg = (
                f'Автомобиль с VIN {car.vin} '
                f'уже продан'
            )
            raise ValueError(error_msg)

        # Обновление автомобиля
        # Изменение статуса на sold
        car.status = CarStatus.sold

        # Сериализация обновленного автомобиля
        price_str = str(car.price)
        date_start_str = car.date_start.isoformat()
        updated_car_data = (
            f'{car.vin}|{car.model}|{price_str}|'
            f'{date_start_str}|{car.status.value}'
        )

        # Проверка длины данных
        if len(updated_car_data) > self.LINE_DATA_LENGTH:
            raise ValueError(
                f'Данные обновленного автомобиля слишком длинные: '
                f'{len(updated_car_data)} символов'
            )

        # Запись обновленного автомобиля
        self._write_fixed_length_line(
            cars_file,
            car_line_number,
            updated_car_data
        )

        return car

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        """
        Возвращает список автомобилей с указанным статусом
        (универсально для любого статуса).
        Проверяет статус каждого автомобиля.

        Args:
            status: статус автомобилей

        Returns:
            Список автомобилей с заданным статусом, отсортированный по VIN
        """
        # Определение пути к файлу автомобилей
        cars_file = os.path.join(self.root_directory_path, 'cars.txt')

        # Проверка существования файла
        if not os.path.exists(cars_file):
            return []

        # Определение общего количества строк в файле
        total_lines = self._get_file_line_count(cars_file)

        # Созданние списка для результатов
        result_cars = []

        # Сканирование файла
        for line_number in range(total_lines):
            try:
                car_data_str = self._read_fixed_length_line(
                    cars_file,
                    line_number
                )
                if not car_data_str.strip():
                    continue

                # Десериализация автомобиля
                parts = car_data_str.split('|')
                if len(parts) != 5:
                    continue  # Некорректная строка

                car = Car(
                    vin=parts[0],
                    model=int(parts[1]),
                    price=Decimal(parts[2]),
                    date_start=datetime.fromisoformat(parts[3]),
                    status=CarStatus(parts[4])
                )
                # Проверка статуса
                if car.status == status:
                    result_cars.append(car)
            except (ValueError, IndexError, AttributeError):
                continue

            # Сортировка по VIN (по возрастанию)

        return result_cars

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        """
        Возвращает полную информацию об автомобиле по VIN.
        Собирает данные из трех файлов: cars.txt, models.txt, sales.txt

        Args:
            vin: VIN код автомобиля

        Returns:
            Объект CarFullInfo или None если автомобиль не найден
        """
        # Поиск автомобиля по VIN
        cars_file = os.path.join(self.root_directory_path, "cars.txt")
        cars_index_file = os.path.join(
            self.root_directory_path, "cars_index.txt"
        )

        # Загрузка индекса автомобилей
        cars_index = self._load_index(cars_index_file)

        # Поиск номера строки автомобиля
        car_line_number = cars_index.get(vin)
        if car_line_number is None:
            return None  # Автомобиль не найден

        # Чтение данных автомобиля
        try:
            car_data_str = self._read_fixed_length_line(
                cars_file,
                car_line_number
            )
        except (FileNotFoundError, ValueError):
            return None

        # Десериализация автомобиля
        parts = car_data_str.split("|")

        if len(parts) != 5:
            return None  # Некорректные данные

        car = Car(
            vin=parts[0],
            model=int(parts[1]),
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=CarStatus(parts[4])
        )

        # Поиск модели автомобиля
        models_file = os.path.join(self.root_directory_path, "models.txt")
        models_index_file = os.path.join(
            self.root_directory_path, "models_index.txt"
        )

        # Загрузка индекса моделей
        models_index = self._load_index(models_index_file)

        # Поиск номера строки модели
        model_line_number = models_index.get(str(car.model))

        if model_line_number is None:
            return None  # Модель не найдена

        # Чтение данные модели
        try:
            model_data_str = self._read_fixed_length_line(
                models_file,
                model_line_number
            )
        except (FileNotFoundError, ValueError):
            return None

        # Десериализация модели
        model_parts = model_data_str.split("|")

        if len(model_parts) != 3:
            return None  # Некорректные данные

        model = Model(
            id=int(model_parts[0]),
            name=model_parts[1],
            brand=model_parts[2]
        )

        # Поиск продажи (если автомобиль продан)
        sales_date = None
        sales_cost = None

        if car.status == CarStatus.sold:
            sales_file = os.path.join(self.root_directory_path, "sales.txt")

            if os.path.exists(sales_file):
                total_sales_lines = self._get_file_line_count(sales_file)

                # Сканирование файла продаж
                for line_num in range(total_sales_lines):
                    try:
                        sale_data_str = self._read_fixed_length_line(
                            sales_file,
                            line_num
                        )

                        if not sale_data_str.strip():
                            continue

                        sale_parts = sale_data_str.split("|")
                        if len(sale_parts) != 4:
                            continue

                        # Проверка отношения продажи к автомобилю
                        if sale_parts[1] == vin:  # sale_parts[1] = car_vin
                            sales_cost = Decimal(sale_parts[2])
                            sales_date = datetime.fromisoformat(sale_parts[3])
                            break  # Продажа найдена, выход из цикла

                    except (ValueError, IndexError):
                        continue

        return CarFullInfo(
            vin=car.vin,
            car_model_name=model.name,
            car_model_brand=model.brand,
            price=car.price,
            date_start=car.date_start,
            status=car.status,
            sales_date=sales_date,
            sales_cost=sales_cost
        )

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        """
        Обновляет VIN код автомобиля.

        Args:
            vin: текущий VIN код
            new_vin: новый VIN код

        Returns:
            Обновленный объект Car

        Raises:
            ValueError: если автомобиль с текущим VIN не найден
            ValueError: если автомобиль с новым VIN уже существует
        """
        # Проверка на дубликат нового VIN
        cars_index_file = os.path.join(
            self.root_directory_path, 'cars_index.txt'
        )
        cars_index = self._load_index(cars_index_file)

        if new_vin in cars_index:
            raise ValueError(f'Автомобиль с VIN {new_vin} уже существует')

        # Поиск автомобиля по старому VIN
        car_line_number = cars_index.get(vin)
        if car_line_number is None:
            raise ValueError(f'Автомобиль с VIN {vin} не найден')

        # Чтение данных автомобиля
        cars_file = os.path.join(self.root_directory_path, 'cars.txt')
        try:
            car_data_str = self._read_fixed_length_line(
                cars_file,
                car_line_number
            )
        except (FileNotFoundError, ValueError):
            raise ValueError(f'Не удалось прочитать данные автомобиля {vin}')

        # Десериализация автомобиля
        parts = car_data_str.split('|')
        if len(parts) != 5:
            raise ValueError(f'Некорректные данные автомобиля {vin}')

        car = Car(
            vin=parts[0],
            model=int(parts[1]),
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=CarStatus(parts[4])
        )

        # Обновление VIN в объекте
        car.vin = new_vin

        # Перезапись автомобиля с новым VIN
        price_str = str(car.price)
        date_start_str = car.date_start.isoformat()
        updated_car_data = (
            f'{car.vin}|{car.model}|{price_str}|'
            f'{date_start_str}|{car.status.value}'
        )

        if len(updated_car_data) > self.LINE_DATA_LENGTH:
            raise ValueError(
                f'Обновленные данные автомобиля слишком длинные: '
                f'{len(updated_car_data)} символов'
            )

        self._write_fixed_length_line(
            cars_file,
            car_line_number,
            updated_car_data
        )

        # Обновление индекса
        # Удаление старого ключа и добавление нового
        del cars_index[vin]
        cars_index[new_vin] = car_line_number

        # Сортировка индекса по ключам (VIN)
        # Создание нового отсортированного словаря
        sorted_index = {}
        for key in sorted(cars_index.keys()):
            sorted_index[key] = cars_index[key]

        # Сохранение обновленного индекса
        self._save_index(cars_index_file, sorted_index)

        return car

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        """
        Отменяет продажу автомобиля.
        Удаляет запись о продаже (помечает как удаленную)
        и изменяет статус автомобиля на 'available'.

        Args:
            sales_number: номер продажи для отмены

        Returns:
            Объект Car с обновленным статусом

        Raises:
            ValueError: если продажа не найдена
            ValueError: если автомобиль не найден
            ValueError: если автомобиль не в статусе sold
        """
        # Поиск продажи по номеру
        sales_file = os.path.join(self.root_directory_path, 'sales.txt')

        if not os.path.exists(sales_file):
            raise ValueError('Файл продаж не найден')

        total_sales_lines = self._get_file_line_count(sales_file)
        sale_found = False
        sale_line_number: Optional[int] = None
        sale_vin: Optional[str] = None
        sale_cost: Optional[Decimal] = None
        sale_date: Optional[datetime] = None

        # Сканирование файла продаж для поиска по sales_number
        for line_num in range(total_sales_lines):
            try:
                sale_data_str = self._read_fixed_length_line(
                    sales_file,
                    line_num
                )

                if not sale_data_str.strip():
                    continue

                parts = sale_data_str.split('|')
                if len(parts) != 4:
                    continue

                # Проверка не помечена ли строка как удаленная
                if parts[0].startswith('DELETED_'):
                    continue

                # Проверка номера продажи
                if parts[0] == sales_number:
                    sale_found = True
                    sale_line_number = line_num
                    sale_vin = parts[1]
                    sale_cost = Decimal(parts[2])
                    sale_date = datetime.fromisoformat(parts[3])
                    break

            except (ValueError, IndexError):
                continue

        if not sale_found:
            raise ValueError(f'Продажа с номером {sales_number} не найдена')

        # Проверка, что все данные найдены
        if sale_line_number is None:
            raise ValueError('Не удалось определить номер строки продажи')
        if sale_vin is None:
            raise ValueError('Не удалось определить VIN из данных продажи')
        if sale_cost is None:
            raise ValueError('Не удалось определить стоимость продажи')
        if sale_date is None:
            raise ValueError('Не удалось определить дату продажи')

        # Поиск и проверка автомобиля
        cars_file = os.path.join(self.root_directory_path, 'cars.txt')
        cars_index_file = os.path.join(
            self.root_directory_path, 'cars_index.txt'
        )

        cars_index = self._load_index(cars_index_file)
        car_line_number = cars_index.get(sale_vin)

        if car_line_number is None:
            raise ValueError(f'Автомобиль с VIN {sale_vin} не найден')

        # Чтение данных автомобиля
        try:
            car_data_str = self._read_fixed_length_line(
                cars_file,
                car_line_number
            )
        except (FileNotFoundError, ValueError):
            raise ValueError(
                f'Не удалось прочитать данные автомобиля '
                f'{sale_vin}'
            )

        # Десериализация автомобиля
        parts = car_data_str.split('|')
        if len(parts) != 5:
            raise ValueError(f'Некорректные данные автомобиля {sale_vin}')

        car = Car(
            vin=parts[0],
            model=int(parts[1]),
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=CarStatus(parts[4])
        )

        # Проверка статуса sold
        if car.status != CarStatus.sold:
            raise ValueError(
                f'Автомобиль с VIN {sale_vin} не продан '
                f'(статус: {car.status.value})'
            )

        # Удаление продажи (пометка как удаленной)
        # Добавление DELETED_ к номеру продажи
        deleted_sale_data = (
            f'DELETED_{sales_number}|{sale_vin}|{sale_cost}|'
            f'{sale_date.isoformat()}'
        )

        if len(deleted_sale_data) > self.LINE_DATA_LENGTH:
            raise ValueError(
                f'Данные удаленной продажи слишком длинные: '
                f'{len(deleted_sale_data)} символов'
            )

        self._write_fixed_length_line(
            sales_file,
            sale_line_number,
            deleted_sale_data
        )

        # Обновление индекса продажи
        sales_index_file = os.path.join(
            self.root_directory_path, 'sales_index.txt'
        )
        sales_index = self._load_index(sales_index_file)

        # Удаление записи из индекса продаж (если существует)
        if sale_vin in sales_index:
            del sales_index[sale_vin]
            self._save_index(sales_index_file, sales_index)

        # Обновление статуса автомобиля
        car.status = CarStatus.available

        # Сериализация обновленного автомобиля
        price_str = str(car.price)
        date_start_str = car.date_start.isoformat()
        updated_car_data = (
            f'{car.vin}|{car.model}|{price_str}|'
            f'{date_start_str}|{car.status.value}'
        )

        if len(updated_car_data) > self.LINE_DATA_LENGTH:
            raise ValueError(
                f'Обновленные данные автомобиля слишком длинные: '
                f'{len(updated_car_data)} символов'
            )

        self._write_fixed_length_line(
            cars_file,
            car_line_number,
            updated_car_data
        )

        return car

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        """
        Возвращает топ-3 модели по количеству продаж.

        Returns:
            Список из 3 объектов ModelSaleStats
        """

        sales_file = os.path.join(self.root_directory_path, 'sales.txt')
        cars_file = os.path.join(self.root_directory_path, 'cars.txt')
        cars_index_file = os.path.join(
            self.root_directory_path, 'cars_index.txt'
        )

        cars_index = self._load_index(cars_index_file)

        # Словари для статистики
        # model_id -> количество продаж
        model_sales_count: dict[int, int] = {}
        # model_id -> сумма цен продаж
        model_total_price: dict[int, Decimal] = {}

        if not os.path.exists(sales_file):
            return []

        # Сбор статистики
        total_sales_lines = self._get_file_line_count(sales_file)

        for line_num in range(total_sales_lines):
            try:
                sale_data_str = self._read_fixed_length_line(
                    sales_file,
                    line_num
                )

                # Пропуск пустых и удаленных строк
                is_empty = not sale_data_str.strip()
                is_deleted = sale_data_str.startswith('DELETED_')
                if is_empty or is_deleted:
                    continue

                parts = sale_data_str.split('|')
                if len(parts) != 4:
                    continue

                car_vin = parts[1]
                sale_price = Decimal(parts[2])

                # Поиск автомобиля
                car_line_number = cars_index.get(car_vin)
                if car_line_number is None:
                    continue

                # Чтение данных автомобиля
                car_data_str = self._read_fixed_length_line(
                    cars_file,
                    car_line_number
                )
                car_parts = car_data_str.split('|')

                if len(car_parts) < 2:
                    continue

                model_id = int(car_parts[1])

                # Обновление статистики
                current_count = model_sales_count.get(model_id, 0)
                model_sales_count[model_id] = current_count + 1
                model_total_price[model_id] = model_total_price.get(
                    model_id, Decimal("0")
                ) + sale_price

            except (ValueError, IndexError):
                continue

        # Создание списка кортежей
        models_for_sorting = []

        for model_id, sales_count in model_sales_count.items():
            total_price = model_total_price.get(model_id, Decimal('0'))
            if sales_count > 0:
                avg_price = total_price / sales_count
            else:
                avg_price = Decimal('0')
            models_for_sorting.append((model_id, sales_count, avg_price))

        # Сортировка
        # По sales_count (по убыванию), по avg_price (по убыванию)
        models_for_sorting.sort(key=lambda x: (x[1], x[2]), reverse=True)

        # Выборка топ-3
        top_models = models_for_sorting[:3]

        # Результат
        result = []
        models_file = os.path.join(self.root_directory_path, 'models.txt')
        models_index_file = os.path.join(
            self.root_directory_path, 'models_index.txt'
        )

        models_index = self._load_index(models_index_file)

        for model_id, sales_count, _ in top_models:
            model_line_number = models_index.get(str(model_id))

            if model_line_number is None:
                continue

            try:
                model_data_str = self._read_fixed_length_line(
                    models_file,
                    model_line_number
                )

                model_parts = model_data_str.split('|')
                if len(model_parts) != 3:
                    continue

                result.append(ModelSaleStats(
                    car_model_name=model_parts[1],
                    brand=model_parts[2],
                    sales_number=sales_count
                ))

            except (ValueError, IndexError):
                continue

        return result
