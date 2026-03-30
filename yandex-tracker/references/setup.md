# Настройка Yandex Tracker

## 1. Получение токена

### OAuth 2.0 токен (рекомендуется)

1. Перейти на страницу [управления API-токенами](https://oauth.yandex.ru/)
2. Создать новое приложение (или использовать существующее)
3. В разделе «Платформы» выбрать «Веб-сервисы»
4. В «Права» добавить доступ к Yandex Tracker (`tracker:read`, `tracker:write`)
5. Получить токен по ссылке:
   ```
   https://oauth.yandex.ru/authorize?response_type=token&client_id=<ID_приложения>
   ```
6. Скопировать токен из URL после авторизации

Документация: https://yandex.ru/support/tracker/en/api-ref/access

### IAM-токен (для организаций Yandex Cloud)

1. Установить [Yandex Cloud CLI](https://cloud.yandex.ru/docs/cli/quickstart)
2. Авторизоваться: `yc init`
3. Получить IAM-токен: `yc iam create-token`

⚠️ IAM-токены временные (действуют ~12 часов). Для долгосрочной работы используйте OAuth.

Документация: https://cloud.yandex.ru/docs/iam/concepts/authorization/iam-token

## 2. Определение ID организации

### org_id (Yandex Connect / Yandex 360)

1. Открыть [Yandex Tracker](https://tracker.yandex.ru/)
2. Перейти в «Администрирование» → «Настройки»
3. ID организации отображается в URL: `https://tracker.yandex.ru/admin/orgs/<org_id>`

Альтернативно — через API:
```bash
curl -s -H "Authorization: OAuth <TOKEN>" \
  https://api.tracker.yandex.net/v2/myself | jq '.organization.id'
```

### cloud_org_id (Yandex Cloud)

1. Открыть [консоль Yandex Cloud](https://console.cloud.yandex.ru/)
2. В верхнем меню выбрать организацию
3. ID виден в URL или в разделе «Обзор»

Либо через CLI:
```bash
yc organization-manager organization list
```

## 3. Настройка переменных окружения

Добавить в `~/.bashrc`, `~/.zshrc` или `.env`:

```bash
# OAuth-авторизация (стандартный способ)
export YANDEX_TRACKER_TOKEN="y0_AgAAAA..."
export YANDEX_TRACKER_ORG_ID="12345"

# ИЛИ для Yandex Cloud организации
export YANDEX_TRACKER_TOKEN="y0_AgAAAA..."
export YANDEX_TRACKER_CLOUD_ORG_ID="bpf..."

# ИЛИ IAM-токен (только с cloud_org_id)
export YANDEX_TRACKER_IAM_TOKEN="t1.9euelZ..."
export YANDEX_TRACKER_CLOUD_ORG_ID="bpf..."
```

⚠️ Нельзя использовать `org_id` и `cloud_org_id` одновременно.
⚠️ Нельзя использовать `TOKEN` и `IAM_TOKEN` одновременно.

## 4. Проверка подключения

```bash
python3 tracker.py user me
```

Должен вернуть JSON с информацией о текущем пользователе (login, display name, email).

Если ошибка авторизации — проверить:
- Токен не истёк
- Правильный org_id / cloud_org_id
- У пользователя есть доступ к Tracker
