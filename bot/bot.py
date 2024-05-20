import logging
import re
import paramiko
import os
import psycopg2

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from dotenv import load_dotenv

from psycopg2 import Error

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Получаем данные из .env
try:

    load_dotenv()
    TOKEN = os.getenv('TOKEN')
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')
    db_name = os.getenv('DB_DATABASE')  # имя базы данных
    db_user = os.getenv('DB_USER')  # имя пользователя базы данных
    db_password = os.getenv('DB_PASSWORD')  # пароль пользователя базы данных
    db_host = os.getenv('DB_HOST')  # хост базы данных
    db_port = os.getenv('DB_PORT')




except Exception as e:
    print("Ошибка при чтении файла .env или получении переменных окружения: %s" % e)
# Подключаемся по SSH
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, port, username, password)
except paramiko.AuthenticationException:
    print("Ошибка аутентификации, пожалуйста, проверьте ваши учетные данные.")
except paramiko.SSHException as sshException:
    print("Невозможно установить SSH-соединение: %s" % sshException)
except paramiko.BadHostKeyException as badHostKeyException:
    print("Невозможно проверить ключ хоста сервера: %s" % badHostKeyException)
except Exception as e:
    print("Ошибка операции: %s" % e)

# Подключаемся к базе данных


# Определение команд
commands = {
    "get_release": "cat /etc/*release",
    "get_uname": "uname -a",
    "get_uptime": "uptime",
    "get_df": "df -h",
    "get_free": "free -h",
    "get_mpstat": "mpstat",
    "get_w": "w",
    "get_auths": "last -n 10",
    "get_critical": "journalctl -p 2 -n 5",
    "get_ps": "ps aux | head -n 10",
    "get_ss": "ss -tulwn",
    "get_apt_list": "dpkg-query -l | tail -n 10",
    "get_services": "systemctl list-units --type=service | head -n 5",
    "get_repl_logs": "docker logs db_repl --tail 10"

}

updater = Updater(token='7182513679:AAFN2ePWFA3Vg-UuxZfm4-T_VtEzXa12UKQ', use_context=True)


# Выполнение команд

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!\nВведите команду /help для получения списка всех комманд')


def helpCommand(update: Update, context):
    commands = [
        '/start - Начать диалог',
        '/help - Показать доступные команды',
        '/verify_password - Проверить сложность пароля',

        f'\nSSH текущий сервер: {host}',
        'Сбор информации о системе:',
        '/get_release - Получить информацию о релизе системы',
        '/get_uname - Получить информацию об архитектуре процессора, имени хоста системы и версии ядра',
        '/get_uptime - Получить информацию о времени работы системы',
        '/get_df - Получить информацию о состоянии файловой системы',
        '/get_free - Получить информацию о состоянии оперативной памяти',
        '/get_mpstat - Получить информацию о производительности системы',
        '/get_w - Получить информацию о работающих в данной системе пользователях',
        '/get_auths - Получить последние 10 входов в систему',
        '/get_critical - Получить последние 5 критических события',
        '/get_ps - Получить информацию о запущенных процессах',
        '/get_ss - Получить информацию об используемых портах',
        '/get_apt_list - Получить информацию об установленных пакетах',
        '/get_services - Получить информацию о запущенных сервисах',
        f'\nБаза данных: {db_name}',
        '/find_phone_number - Найти телефонные номера c возможностью записи в бд',
        '/find_email - Найти email-адреса в тексте с возможностью записи в бд',
        '/get_emails - Список email',
        '/get_phonenumbers - Список телефонов',
        '/get_repl_logs - вывод логов о репликации'

    ]
    update.message.reply_text("\n".join(commands))


def find_phone_number_command(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'


def find_phone_number(update: Update, context):
    user_input = update.message.text
    phoneNumRegex = re.compile(r'(?:\+7|8)[\s-]\(?(?:\d{3})\)?[\s-]\d{3}[\s-]\d{2}[\s-]\d{2}', re.IGNORECASE)
    phoneNumberList = phoneNumRegex.findall(user_input)
    if not phoneNumberList:
        update.message.reply_text('Номера телефонов не найдены')
        return
    phoneNumbers = ''
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i + 1}. {"".join(phoneNumberList[i])}\n'
    update.message.reply_text(phoneNumbers)

    # Предложение записать информацию в базу данных
    update.message.reply_text('Хотите ли вы записать эти номера телефонов в базу данных? Ответьте "да" или "нет".')
    context.user_data['phoneNumberList'] = phoneNumberList
    return 'decision'


def find_email_command(update: Update, context):
    update.message.reply_text('Введите текст для поиска email-адресов: ')
    return 'find_email'


def find_email(update: Update, context):
    user_input = update.message.text
    emailRegex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')  # формат email
    emailList = emailRegex.findall(user_input)
    if not emailList:
        update.message.reply_text('Email-адреса не найдены')
        return
    emails = ''
    for i in range(len(emailList)):
        emails += f'{i + 1}. {emailList[i]}\n'
    update.message.reply_text(emails)

    # Предложение записать информацию в базу данных
    update.message.reply_text('Хотите ли вы записать эти email-адреса в базу данных? Ответьте "да" или "нет".')
    context.user_data['emailList'] = emailList
    return 'decision'

def decision(update: Update, context):
    user_input = update.message.text.lower()
    if user_input == 'да':
        # Запись информации в базу данных
        try:
            # Подключение к базе данных
            connection = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port
            )
            cursor = connection.cursor()

            # Если в контексте есть email-адреса
            if 'emailList' in context.user_data:
                for email in context.user_data['emailList']:
                    # Запись email-адреса в базу данных
                    cursor.execute("INSERT INTO bot_emails (email) VALUES (%s);", (email,))
                    connection.commit()
            # Если в контексте есть номера телефонов
            if 'phoneNumberList' in context.user_data:
                for phone_number in context.user_data['phoneNumberList']:
                    # Запись номера телефона в базу данных
                    cursor.execute("INSERT INTO bot_phonenumbers (phone_number) VALUES (%s);", (phone_number,))
                    connection.commit()
            # Сохранение изменений и закрытие соединения с базой данных
            connection.commit()
            cursor.close()
            connection.close()

            update.message.reply_text('Информация успешно записана в базу данных.')
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
            update.message.reply_text('Произошла ошибка при записи в базу данных.')
    elif user_input == 'нет':
        update.message.reply_text('Запись в базу данных отменена.')
    else:
        update.message.reply_text('Я не понял ваш ответ. Пожалуйста, ответьте "да" или "нет".')
    return ConversationHandler.END


def verify_password_command(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')
    return 'verify_password'


def verify_password(update: Update, context):
    user_input = update.message.text
    passwordRegex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&^()])[A-Za-z\d@$!%*?&^()]{8,}$')
    if passwordRegex.fullmatch(user_input):
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')
    return ConversationHandler.END


# Функция для выполения команд в linux через SSH

def execute_command(command: str) -> str:
    try:
        stdin, stdout, stderr = ssh.exec_command(commands[command])
        error = stderr.read().decode().strip()
        if error:
            return f"Возникла ошибка: {error}"
        output = stdout.read().decode().strip()
        return output
    except Exception as e:
        return f"Произошло исключение: {str(e)}"


def get_repl_logs(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_repl_logs"))

def get_release(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_release"))


def get_uname(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_uname"))


def get_uptime(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_uptime"))


def get_df(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_df"))


def get_free(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_free"))


def get_mpstat(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_mpstat"))


def get_w(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_w"))


def get_auths(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_auths"))


def get_critical(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_critical"))


def get_ps(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_ps"))


def get_ss(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_ss"))


def get_apt_list_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Введите название пакета или впишите all для вывода всех пакетов:')
    return 'get_apt_list'


def get_apt_list(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    if user_input == 'all':
        update.message.reply_text(execute_command('get_apt_list'))
    elif user_input != 'all':
        stdin, stdout, stderr = ssh.exec_command('apt show ' + user_input)
        output = stdout.read().decode().strip()
        update.message.reply_text(output)
    return ConversationHandler.END


def get_emails_command(update: Update, context: CallbackContext) -> None:
    try:
        connection = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
    except psycopg2.Error as e:
        print("Ошибка при подключении к базе данных: %s" % e)

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT email FROM bot_emails;")
        emails = cursor.fetchall()
        update.message.reply_text('Email адреса: \n')
        update.message.reply_text("\n".join(email[0] for email in emails))
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection:
            cursor.close()
            connection.close()


def get_phone_numbers_command(update: Update, context: CallbackContext) -> None:
    try:
        connection = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
    except psycopg2.Error as e:
        print("Ошибка при подключении к базе данных: %s" % e)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT phone_number FROM bot_phonenumbers;")
        phone_numbers = cursor.fetchall()
        update.message.reply_text('Телефоны: \n')
        update.message.reply_text("\n".join(phone_number[0] for phone_number in phone_numbers))
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection:
            cursor.close()
            connection.close()


def get_services(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(execute_command("get_services"))


def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', find_phone_number_command)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, find_phone_number)],
            'decision': [MessageHandler(Filters.text & ~Filters.command, decision)]
        },
        fallbacks=[]
    )

    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', find_email_command)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, find_email)],
            'decision': [MessageHandler(Filters.text & ~Filters.command, decision)]
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verify_password_command)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )
    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(CommandHandler('get_release', get_release))
    dp.add_handler(CommandHandler('get_uname', get_uname))
    dp.add_handler(CommandHandler('get_uptime', get_uptime))
    dp.add_handler(CommandHandler('get_df', get_df))
    dp.add_handler(CommandHandler('get_free', get_free))
    dp.add_handler(CommandHandler('get_mpstat', get_mpstat))
    dp.add_handler(CommandHandler('get_w', get_w))
    dp.add_handler(CommandHandler('get_auths', get_auths))
    dp.add_handler(CommandHandler('get_critical', get_critical))
    dp.add_handler(CommandHandler('get_ps', get_ps))
    dp.add_handler(CommandHandler('get_ss', get_ss))
    dp.add_handler(CommandHandler('get_repl_logs', get_repl_logs))
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', get_apt_list_command)],
        states={'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, get_apt_list)]},
        fallbacks=[]
    ))
    dp.add_handler(CommandHandler('get_services', get_services))
    # Регистрируем обработчик текстовых сообщений

    dp.add_handler(CommandHandler("get_emails", get_emails_command))
    dp.add_handler(CommandHandler("get_phonenumbers", get_phone_numbers_command))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()