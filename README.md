venv\Scripts\activate


# Проект мониторинга EURUSD/AUDUSD для MT5

Это стартовый каркас под нашу схему: **MT5 ECN Demo + Python + EURUSD/AUDUSD + M1 за 2 суток**.

## Что уже есть
- подключение к MT5 из Python;
- загрузка последних `HISTORY_BARS` минутных баров по двум символам;
- расчёт `beta`, `corr`, `spread_z`, `resid_z`, `combo_z`;
- cost-модель для `spread + commission + slippage`;
- event-study по последним 2 суткам;
- live-наблюдение за текущим перекосом и оценка, достаточно ли он велик после издержек.

## Быстрый старт
1. Установить desktop MetaTrader 5 и войти в демо-счёт RoboForex.
2. Скопировать `.env.example` в `.env` и заполнить логин/пароль/сервер/путь к терминалу.
3. Создать виртуальное окружение и установить зависимости.
4. Запустить офлайн-анализ:

python -m src.app.analyze_last_2d

5. Запустить live-наблюдение:

python -m src.app.live_watch`

## Замечания
- Символы в `.env` должны совпадать с именами у брокера в Market Watch.
- Для Python-интеграции используется установленный desktop-терминал MT5.
- История ограничена объёмом баров, доступных в терминале; если баров не хватает, увеличьте историю/макс. бары в MT5.


3) Cointegration / spread hedge ratio — нужен, если ты хочешь именно mean reversion пары

Если задача не просто приглушить риск, а строить торговый spread, который потом возвращается к среднему, тогда коэффициент надо оценивать уже на ценовой связи, а не на диапазоне.

Для пары EUR/USD и USD/CHF удобнее писать так:

x_t = ln(EURUSD_t)
y_t = ln(USDCHF_t)

Дальше:

x_t = a - β y_t + u_t

или, что то же самое по смыслу:

ln(EURUSD_t) = a + β ln(CHFUSD_t) + u_t

где CHFUSD = 1 / USDCHF.

Тогда твой spread — это residual:

spread_t = u_t = ln(EURUSD_t) + β ln(USDCHF_t) - a

И уже не просто divergence, а именно stationary residual должен давать сигнал. Engle–Granger как раз строится через такую двухшаговую схему: сначала long-run regression, потом проверка residual на стационарность. Johansen — стандартный альтернативный тест на cointegration rank.

Важно: β из коинтеграции — это не готовый lot ratio для исполнения, пока ты его не приведёшь к PnL или notional scale. Это частая ошибка.