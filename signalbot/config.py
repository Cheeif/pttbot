# Конфигурация Telegram-бота для пересылки сигналов

# Токен бота от @BotFather
TOKEN = "8230078379:AAF6MjmGprRLlQ1YFoXHW4-QaTrxe2gn4U8"

# ID администраторов (список)
ADMIN_IDS = [5506126690, 612781324]

# Контактная информация для поддержки
ADMIN_USERNAME = "admin_username"  # Замените на реальный username админа
SUPPORT_EMAIL = "support@signalbot.pro"
WEBSITE_URL = "https://yourwebsite.com/how-to-pay"

# URL для примера сигнала (замените на реальную ссылку)
SIGNAL_EXAMPLE_URL = "data/photo.jpg, data/fuck.jpg"

# Криптоадрес для оплаты (TRC20 USDT)
CRYPTO_ADDRESS = "TTeq3zoxzngwSW6rmWTTdW3bkohRfvnkCh"

# Ссылка на Tribute mini app
TRIBUTE_LINK = "https://t.me/tribute/app?startapp=dzcf"

# ID канала с сигналами (откуда пересылаем)
SIGNAL_CHANNEL_ID = -1003136921053

# ID канала для логов
LOG_CHANNEL_ID = -1003038695844

# Интервал проверки новых сообщений (секунды)
CHECK_INTERVAL = 10

# Статусы пользователей
STATUS_PENDING = "pending"    # Ожидает подтверждения оплаты
STATUS_ACTIVE = "active"      # Активная подписка
STATUS_INACTIVE = "inactive"  # Неактивная подписка
STATUS_EXPIRED = "expired"    # Просроченная подписка

# Сообщения для статусов
STATUS_MESSAGES = {
    STATUS_PENDING: "⏳ Ожидает подтверждения оплаты",
    STATUS_ACTIVE: "✅ Активная подписка",
    STATUS_INACTIVE: "❌ Подписка неактивна",
    STATUS_EXPIRED: "⏰ Подписка истекла"
}