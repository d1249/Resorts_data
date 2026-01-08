# Climate Comfort Score (Streamlit)

Минимальный проект без базы данных: сбор климат-данных из API, агрегация в 12 месяцев, расчет ComfortScore и экспорт CSV.

## Быстрый старт

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Что делает

- Загружает климатические данные (Air/Sea/Rain/Wind/Wave).
- Считает месячные нормы за период из `config/sources.yaml`.
- Вычисляет ComfortScore и компоненты.
- Экспортирует CSV и provenance-файл в `outputs/`.

## Конфигурация

- `config/locations.yaml` — список локаций.
- `config/params.yaml` — параметры модели.
- `config/sources.yaml` — период норм, настройки источников и кэша.

## Кэш

Файловый кэш хранится в `data/cache/` и используется по умолчанию. В UI есть чекбокс **Force refresh** для обновления.
