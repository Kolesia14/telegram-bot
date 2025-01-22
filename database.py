import sqlite3
import logging

class Database:
    def __init__(self, db_path):
        """Инициализация базы данных."""
        try:
            self.connection = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.connection.cursor()
            self._create_tables()
            self._initialize_data()
            logging.info("База данных успешно подключена и инициализирована.")
        except sqlite3.Error as e:
            logging.error(f"Ошибка при подключении к базе данных: {e}")

    def _create_tables(self):
        """Создание таблицы для хранения данных, если она ещё не существует."""
        try:
            self.cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section TEXT NOT NULL,
                    item TEXT NOT NULL UNIQUE,
                    quantity INTEGER NOT NULL CHECK (quantity >= 0)
                )
                '''
            )
            self.connection.commit()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при создании таблиц: {e}")

    def _initialize_data(self):
        """Инициализация базы данных начальными данными."""
        try:
            initial_data = {
                "Сталь": [
                    ("4мм(1250×2500мм)", 10),
                    ("4мм(1250×4000мм)", 10),
                    ("4мм(1500×6000мм)", 10),
                    ("5мм(1500×6000мм)", 10),
                    ("8мм(1500×6000мм)", 10),
                    ("10мм(1500×6000мм)", 10),
                    ("14мм (размер указывает пользователь)", 5),
                    ("20мм (размер указывает пользователь)", 5),
                    ("30мм (размер указывает пользователь)", 5),
                ],
                "09г2с": [
                    ("4мм(1500×6000мм)", 10),
                    ("5мм(1500×6000мм)", 10),
                    ("6мм(1500×6000мм)", 10),
                    ("8мм(1500×6000мм)", 10),
                    ("16мм(1500×4000мм)", 10),
                    ("16мм(1500×6000мм)", 10),
                ]
            }

            for section, items in initial_data.items():
                for item, quantity in items:
                    self.cursor.execute(
                        "INSERT OR IGNORE INTO inventory (section, item, quantity) VALUES (?, ?, ?)",
                        (section, item, quantity),
                    )
            self.connection.commit()
            logging.info("Начальные данные успешно добавлены в базу.")
        except sqlite3.Error as e:
            logging.error(f"Ошибка при инициализации данных: {e}")

    def get_inventory(self):
        """Получение текущего состояния склада.

        Возвращает:
            dict: Словарь в формате {section: [(item, quantity), ...]}
        """
        try:
            self.cursor.execute("SELECT section, item, quantity FROM inventory")
            rows = self.cursor.fetchall()
            inventory = {}
            for section, item, quantity in rows:
                if section not in inventory:
                    inventory[section] = []
                inventory[section].append((item, quantity))
            return inventory
        except sqlite3.Error as e:
            logging.error(f"Ошибка при получении данных склада: {e}")
            return {}

    def add_item(self, section, item, quantity):
        """Добавление новой позиции на склад.

        Args:
            section (str): Раздел (например, "Сталь" или "09г2с").
            item (str): Наименование позиции.
            quantity (int): Количество.
        """
        try:
            self.cursor.execute(
                "INSERT INTO inventory (section, item, quantity) VALUES (?, ?, ?)",
                (section, item, quantity),
            )
            self.connection.commit()
            logging.info(f"Добавлена новая позиция: {item} в разделе {section}.")
        except sqlite3.Error as e:
            logging.error(f"Ошибка при добавлении позиции {item}: {e}")

    def update_item(self, item, quantity):
        """Обновление количества существующей позиции.

        Args:
            item (str): Наименование позиции.
            quantity (int): Новое количество.
        """
        try:
            self.cursor.execute(
                "UPDATE inventory SET quantity = ? WHERE item = ?",
                (quantity, item),
            )
            self.connection.commit()
            logging.info(f"Обновлено количество позиции: {item}. Новое количество: {quantity}.")
        except sqlite3.Error as e:
            logging.error(f"Ошибка при обновлении позиции {item}: {e}")

    def delete_item(self, item):
        """Удаление позиции с указанным именем.

        Args:
            item (str): Наименование позиции.
        """
        try:
            self.cursor.execute("DELETE FROM inventory WHERE item = ?", (item,))
            self.connection.commit()
            logging.info(f"Удалена позиция: {item}.")
        except sqlite3.Error as e:
            logging.error(f"Ошибка при удалении позиции {item}: {e}")

    def close(self):
        """Закрытие соединения с базой данных."""
        try:
            self.connection.close()
            logging.info("Соединение с базой данных закрыто.")
        except sqlite3.Error as e:
            logging.error(f"Ошибка при закрытии базы данных: {e}")