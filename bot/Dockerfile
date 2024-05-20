# Установка базового образа
FROM python:3.9-slim

# Установка рабочей директории
WORKDIR /bot

# Копирование файлов приложения в контейнер
COPY . .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Команда для запуска бота
CMD ["python", "./bot.py"]
