# ТЗ №3 — Каталог анкет и просмотр профилей мужчинами

## Цель

Мужчина открывает каталог через Telegram WebApp: анкеты, фото, ranking, избранное, переход к чату.

## Preconditions

MAN onboarding завершён:

```text
role:man -> confirmed name -> normalized city
```

В каталоге не создаётся и не используется публичная MAN-анкета.

## Hard filters

Ровно три обязательных условия отбора:

1. `profiles.status = 'ACTIVE'`;
2. владелец анкеты имеет роль WOMAN;
3. `profiles.city_normalized = male_search_context.city_normalized`.

Город — единственный продуктовый hard filter. До сравнения оба значения нормализуются.

## Optional ranking preferences

Допустимы только структурированные поля женской анкеты:

- возраст;
- район;
- рост;
- вес;
- числовой размер груди;
- диапазон цены;
- типы мест встречи;
- будущие реальные structured WOMAN fields.

NULL означает `не важно`. Он не влияет на score и не исключает анкету.

## Ranking

```text
matched_preferences = число совпавших заданных preferences
considered_preferences = число реально заданных preferences
match_score = matched_preferences / considered_preferences
```

При `considered_preferences = 0` score равен 0 и показываются все ACTIVE-анкеты WOMAN из города.

```text
ORDER BY match_score DESC,
         matched_preferences DESC,
         profiles.created_at DESC,
         profiles.id
```

На MVP все рассматриваемые preferences имеют одинаковый вес.

## Preferences UX

После города:

```text
[Настроить предпочтения] [Смотреть анкеты]
```

Заполнение preferences не может блокировать каталог. Настройки можно открыть и изменить позднее.

## Избранное и privacy

Повторное добавление в избранное запрещено. Ответ каталога не содержит Telegram ID, контакты, internal user ID владельца и moderation metadata.

## Ограничения

НЕ: чат, сообщения, встречи, оплата, отзывы.
