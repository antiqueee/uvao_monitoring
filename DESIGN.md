# Design System

Спецификация визуального языка сервиса. Используется при верстке Jinja2-шаблонов. Только светлая тема — внутренний инструмент, тёмный режим не нужен.

## Принципы

- Editorial calm, не enterprise SaaS. Интерфейс должен ощущаться как книжная страница, не как админ-панель.
- Один акцентный цвет (clay-оранжевый), всё остальное — нейтральные тона.
- Serif для заголовков и крупных цифр, sans-serif для всего остального.
- Тонкие линии (0.5px), щедрые отступы, никаких теней и градиентов.
- Цвет = смысл. Никакой декоративной раскраски.

## Шрифты

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=Fraunces:opsz,wght@9..144,400;9..144,500&display=swap" rel="stylesheet">
```

- `--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;`
- `--font-serif: 'Fraunces', Georgia, 'Times New Roman', serif;`

Веса: только 400 (regular) и 500 (medium). Не использовать 600/700 — выглядит тяжело.

## Цветовые токены

```css
:root {
  /* Backgrounds */
  --bg-page: #ECE9DF;        /* фон страницы (вне приложения) */
  --bg-chrome: #FAF9F5;      /* сайдбар, выключенные поля, sub-surfaces */
  --bg-surface: #FFFFFF;     /* основная рабочая поверхность */

  /* Text */
  --text-primary: #1A1612;   /* тёплый чёрный */
  --text-secondary: #6B6660; /* подписи, метаданные */
  --text-tertiary: #8E8A82;  /* подсказки, плейсхолдеры */

  /* Borders */
  --border-light: rgba(26, 22, 18, 0.08);  /* разделители таблиц, лёгкие границы */
  --border-medium: rgba(26, 22, 18, 0.16); /* поля ввода, кнопки-призраки */

  /* Accent — clay/orange, только для primary CTA */
  --accent: #B85C3F;
  --accent-hover: #A04E33;

  /* Semantic dots — только для индикаторов статуса */
  --status-ok: #4A7C3D;      /* готов, активен */
  --status-err: #A85040;     /* ошибка */
  --status-off: #8E8A82;     /* отключён */
}
```

## Типографика

### Заголовки (serif)

```css
h1 { font-family: var(--font-serif); font-size: 24px; font-weight: 400; letter-spacing: -0.02em; color: var(--text-primary); }
h2 { font-family: var(--font-serif); font-size: 20px; font-weight: 400; letter-spacing: -0.015em; }
h3 { font-family: var(--font-serif); font-size: 16px; font-weight: 400; letter-spacing: -0.01em; }
```

Заголовки всегда в sentence case (первая буква заглавная, остальное строчными). Никаких Title Case или ALL CAPS.

### Текст (sans)

- Body: 13–14px, weight 400, line-height 1.5
- Кнопки: 13px, weight 500
- Лейблы форм: 12px, weight 400, цвет `--text-secondary`
- Микроподписи и подписи колонок: 11px, weight 400, цвет `--text-tertiary`, uppercase с `letter-spacing: 0.06em`

### Крупные цифры (статистика)

```css
.stat-value { font-family: var(--font-serif); font-size: 32px; font-weight: 400; letter-spacing: -0.025em; line-height: 1; }
.stat-label { font-size: 11px; color: var(--text-tertiary); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px; }
```

## Отступы

Базовая шкала: 4, 8, 12, 16, 24, 32, 48 px.

- Padding внутри ячейки таблицы: 14px вертикально, 0 горизонтально (используем разделители-линии, не колоночные отступы).
- Padding основного контента: 32px 36px.
- Padding sidebar: 20px 16px.
- Margin между крупными секциями: 28–32px.

## Радиусы

- `--radius-sm: 5px` — кнопки, инпуты, мелкие плашки.
- `--radius-md: 8px` — карточки, секции с фоном.

## Компоненты

### Кнопка primary

```html
<button class="btn">Сформировать</button>
```

```css
.btn {
  background: var(--accent);
  color: #FFFFFF;
  border: none;
  padding: 8px 16px;
  font-family: var(--font-sans);
  font-size: 13px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.btn:hover { background: var(--accent-hover); }
```

Используется только для главного действия страницы. На одной странице — максимум одна primary-кнопка.

### Кнопка ghost

```css
.btn-ghost {
  background: transparent;
  color: var(--text-primary);
  border: 0.5px solid var(--border-medium);
  padding: 8px 16px;
  font-size: 13px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.btn-ghost:hover { background: var(--bg-chrome); }
```

### Input

```css
.input {
  width: 100%;
  padding: 9px 12px;
  font-family: var(--font-sans);
  font-size: 13px;
  border: 0.5px solid var(--border-medium);
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
  color: var(--text-primary);
}
.input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px rgba(184, 92, 63, 0.12); }
.input:disabled { background: var(--bg-chrome); color: var(--text-secondary); }
```

### Лейбл поля

```css
.label { font-size: 12px; color: var(--text-secondary); margin-bottom: 7px; display: block; }
```

Под полем — подсказка через `.hint`:

```css
.hint { font-size: 12px; color: var(--text-tertiary); margin-top: 6px; }
```

### Sidebar

```css
.sidebar {
  background: var(--bg-chrome);
  border-right: 0.5px solid var(--border-light);
  padding: 20px 16px;
  width: 170px;
}
.nav-brand {
  font-family: var(--font-serif);
  font-size: 16px;
  letter-spacing: -0.01em;
  padding: 0 8px 24px;
  color: var(--text-primary);
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 10px;
  font-size: 13px;
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  text-decoration: none;
}
.nav-item.active {
  color: var(--text-primary);
  font-weight: 500;
}
.nav-item:hover { background: rgba(0, 0, 0, 0.03); }
```

### Таблица

```css
.tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
.tbl th {
  text-align: left;
  font-weight: 400;
  color: var(--text-tertiary);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 10px 0;
  border-bottom: 0.5px solid var(--border-light);
}
.tbl td {
  padding: 14px 0;
  border-bottom: 0.5px solid var(--border-light);
  color: var(--text-primary);
  vertical-align: top;
}
```

Только горизонтальные разделители, без вертикальных. Под названием в первой колонке — мелкая метаданная подпись (`color: var(--text-tertiary); font-size: 12px;`).

### Статус-индикатор

```html
<span class="status"><span class="dot status-ok"></span>готов</span>
```

```css
.status { font-size: 11px; color: var(--text-secondary); letter-spacing: 0.04em; }
.dot { display: inline-block; width: 5px; height: 5px; border-radius: 50%; vertical-align: 2px; margin-right: 6px; }
.dot.status-ok { background: var(--status-ok); }
.dot.status-err { background: var(--status-err); }
.dot.status-off { background: var(--status-off); }
```

### Категория ресурса

Без цветных плашек. Просто мелкий текст:

```css
.category { font-size: 11px; color: var(--text-secondary); letter-spacing: 0.04em; }
```

Значения: «район», «округ», «ЛОМ», «другое».

### Метрика (большая статистика)

```html
<div class="stat">
  <div class="stat-label">Репостов</div>
  <div class="stat-value">18</div>
</div>
```

Несколько метрик располагаются в строку через grid с равными колонками, разделитель снизу — `border-bottom: 0.5px solid var(--border-light); padding-bottom: 28px;`.

### Хлебные крошки

```html
<div class="breadcrumb">← К списку отчётов</div>
```

```css
.breadcrumb { font-size: 12px; color: var(--text-tertiary); margin-bottom: 6px; }
```

## Layout: app shell

Для всех страниц после логина:

```html
<div class="app">
  <aside class="sidebar">...</aside>
  <main class="content">...</main>
</div>
```

```css
.app { display: grid; grid-template-columns: 170px 1fr; min-height: 100vh; }
.content { padding: 32px 36px; background: var(--bg-surface); }
```

Страница логина — без app-shell, центрированная карточка на `var(--bg-page)`.

## Шапка страницы

Стандартный паттерн заголовка раздела:

```html
<div class="breadcrumb">← К списку отчётов</div>
<div class="page-header">
  <h1>Субботник в Кузьминском парке</h1>
  <button class="btn">Excel</button>
</div>
<div class="page-meta">Кузьминки · 13 мая 2026 · vk.com/wall-...</div>
```

```css
.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 6px; }
.page-meta { color: var(--text-secondary); font-size: 13px; margin-bottom: 32px; }
```

## Иконки

Tabler Icons (outline only):

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/dist/tabler-icons.min.css">
```

Используем:
- `ti-file-text` — отчёты в навигации
- `ti-adjustments-horizontal` — админка
- `ti-logout` — выйти
- `ti-plus` — добавить / новый
- `ti-download` — скачать Excel
- `ti-chevron-right` — стрелка в списках
- `ti-dots` — меню действий в строке таблицы

Размеры: 15px в навигации, 12-13px внутри кнопок. Декоративные иконки — `aria-hidden="true"`. Иконочные кнопки без текста — `aria-label="..."`.

## Чего не делать

- ❌ Никаких эмодзи в интерфейсе.
- ❌ Никаких градиентов, теней, glow, blur.
- ❌ Никаких цветных карточек или фонов под секции (кроме `--bg-chrome` для chrome-элементов).
- ❌ Никаких цветных бэйджей для категорий — только текст-метка.
- ❌ Никаких bold-вкраплений в тексте mid-sentence. Bold — только для заголовков и активных пунктов меню.
- ❌ Никаких font-weight больше 500.
- ❌ Не использовать `--accent` нигде кроме primary-кнопок и фокус-обводки полей. Никаких акцентных подчёркиваний, иконок, ссылок в clay-цвете.
- ❌ Не использовать вертикальные разделители в таблицах.
- ❌ Не делать кнопки шире 200px — primary CTA должна быть компактной.

## Опорная страница

`mockups.html` в репозитории — статичный референс с собранными воедино всеми семью экранами. Открывается в любом браузере. При сомнениях в верстке — открыть его и сверить.
