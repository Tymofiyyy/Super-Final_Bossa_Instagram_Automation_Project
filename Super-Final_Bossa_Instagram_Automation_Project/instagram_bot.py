import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import Config
from utils import AntiDetection

class InstagramBot:
    def __init__(self, username, password, proxy=None, browser_type="chrome"):
        self.username = username
        self.password = password
        self.proxy = proxy
        self.browser_type = browser_type.lower()  # ✅ зберігаємо тип браузера
        self.driver = None
        self.logged_in = False
        self.anti_detection = AntiDetection()
        self.dolphin_manager = None
        if self.browser_type == "dolphin anty":
            from utils import DolphinAntyManager
            self.dolphin_manager = DolphinAntyManager()
        self.setup_logging()

        
    def setup_logging(self):
        """Налаштування логування"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/{self.username}_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f'InstagramBot_{self.username}')
        
    def setup_driver(self):
        """Налаштування веб-драйвера з обходом детекції або через Dolphin Anty"""
        
        # Перевірка типу браузера
        if self.browser_type.lower() == "dolphin anty":
            # Перевірка доступності Dolphin
            if self.dolphin_manager and self.dolphin_manager.test_connection():
                return self.setup_dolphin_driver()
            else:
                self.logger.warning("⚠️ Dolphin Anty недоступний, використовуємо Chrome")
                self.browser_type = "chrome"
        
        # --- Chrome WebDriver (решта коду без змін) ---

        # --- Chrome WebDriver ---
        chrome_options = Options()

        # Обхід детекції ботів
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins-discovery')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')

        # Мобільна емуляція з випадковим User-Agent
        mobile_emulation = {
            "deviceMetrics": {"width": 375, "height": 667, "pixelRatio": 3.0},
            "userAgent": random.choice([
                "Mozilla/5.0 (Linux; Android 13; Pixel 6 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Mobile Safari/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ])
        }
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

        # Проксі (якщо є)
        if self.proxy:
            chrome_options.add_argument(f'--proxy-server={self.proxy}')

        # Headless (не рекомендується для Instagram)
        if Config.HEADLESS:
            chrome_options.add_argument('--headless=new')  # 'new' режим краще працює

        # Ініціалізація Chrome WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)

        # Обхід виявлення webdriver через Chrome DevTools Protocol
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })

        # Встановлення розміру вікна
        self.driver.set_window_size(375, 667)

        return self.driver

    def setup_dolphin_driver(self):
        """Налаштування драйвера для Dolphin Anty"""
        try:
            # Створення або отримання профілю
            profile_data = self.dolphin_manager.create_profile(self.username, self.proxy)
            
            if not profile_data:
                raise Exception("Не вдалося створити профіль Dolphin")
            
            # Запуск профілю
            automation_data = self.dolphin_manager.start_profile(self.username)
            
            if not automation_data:
                raise Exception("Не вдалося запустити профіль Dolphin")
            
            # Підключення до WebDriver через Dolphin
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            # Використовуємо правильний ключ для підключення
            debugger_address = automation_data.get('ws', {}).get('selenium')
            if not debugger_address:
                # Альтернативний варіант отримання адреси
                port = automation_data.get('port', 9222)
                debugger_address = f"127.0.0.1:{port}"
            
            options.add_experimental_option("debuggerAddress", debugger_address)
            
            # Ініціалізація драйвера
            self.driver = webdriver.Chrome(options=options)
            
            # Встановлення розміру вікна для мобільної версії
            self.driver.set_window_size(375, 667)
            
            self.logger.info(f"✅ Dolphin Anty профіль {self.username} підключено")
            
            return self.driver
            
        except Exception as e:
            self.logger.error(f"❌ Помилка налаштування Dolphin: {e}")
            # Fallback на Chrome якщо Dolphin не працює
            self.logger.warning("🔄 Перемикання на Chrome драйвер...")
            self.browser_type = "chrome"
            return self.setup_driver()
        
        
    def human_like_delay(self, min_delay=1, max_delay=3):
        """Затримка з імітацією людської поведінки"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
            
    def fast_typing(self, element, text):
        """Швидке введення тексту для повідомлень з підтримкою багаторядкових повідомлень"""
        try:
            # Очищення поля
            element.clear()
            time.sleep(0.2)
            
            # Фокус на елементі
            element.click()
            time.sleep(0.1)
            
            # Перевіряємо чи є перенос рядків у тексті
            if '\n' in text:
                self.logger.info(f"📝 Багаторядкове повідомлення: {len(text.splitlines())} рядків")
                
                # Метод 1: Посимвольне введення з Shift+Enter
                lines = text.splitlines(keepends=False)  # Розбиваємо на рядки без символів переносу
                
                for i, line in enumerate(lines):
                    # Вводимо кожен символ рядка
                    for char in line:
                        element.send_keys(char)
                        time.sleep(random.uniform(0.01, 0.02))
                    
                    # Якщо це не останній рядок - додаємо перенос
                    if i < len(lines) - 1:
                        # Використовуємо ActionChains для Shift+Enter
                        action = ActionChains(self.driver)
                        action.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
                        time.sleep(0.1)
                        self.logger.debug(f"➕ Додано перенос рядка після: {line[:30]}...")
                        
                self.logger.info(f"✅ Багаторядкове введення завершено")
                return True
                
            else:
                # Для однорядкового тексту - просте введення
                element.send_keys(text)
                self.logger.debug(f"✅ Однорядкове введення: {text}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Помилка при введенні тексту: {e}")
            
            # Fallback метод - через буфер обміну
            try:
                import pyperclip
                pyperclip.copy(text)
                element.click()
                time.sleep(0.1)
                
                # Ctrl+V для вставки
                action = ActionChains(self.driver)
                action.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                
                self.logger.info("✅ Текст вставлено через буфер обміну")
                return True
                
            except:
                # Останній варіант - JavaScript
                try:
                    # Екрануємо текст для JavaScript
                    js_text = text.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '').replace('"', '\\"').replace("'", "\\'")
                    
                    self.driver.execute_script("""
                        var element = arguments[0];
                        var text = arguments[1];
                        element.focus();
                        element.value = text;
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                    """, element, text)
                    
                    self.logger.info("✅ Текст введено через JavaScript")
                    return True
                    
                except Exception as e3:
                    self.logger.error(f"❌ Всі методи введення не спрацювали: {e3}")
                    return False
        
    def validate_credentials(self):
        """Перевірка правильності логіна і пароля"""
        if not self.username or not self.password:
            self.logger.error("Логін або пароль не вказані")
            return False
            
        if len(self.username) < 3:
            self.logger.error("Логін занадто короткий")
            return False
            
        if len(self.password) < 6:
            self.logger.error("Пароль занадто короткий")
            return False
            
        # Перевірка на недопустимі символи
        import re
        if not re.match("^[a-zA-Z0-9._]+$", self.username):
            self.logger.error("Логін містить недопустимі символи")
            return False
            
        self.logger.info(f"Логін {self.username} пройшов валідацію")
        return True

    # === НОВИЙ МЕТОД: ПАРСИНГ БАГАТЬОХ КОРИСТУВАЧІВ ===
    def parse_target_users(self, target_input):
        """Парсинг списку цільових користувачів"""
        # Якщо вже список - просто повертаємо його
        if isinstance(target_input, list):
            cleaned_users = []
            for user in target_input:
                if isinstance(user, str):
                    user = user.strip().replace('@', '')
                    if user and len(user) > 0:
                        import re
                        if re.match("^[a-zA-Z0-9._]+$", user) and len(user) >= 1:
                            cleaned_users.append(user)
            self.logger.info(f"Отримано список з {len(cleaned_users)} валідних користувачів")
            return cleaned_users
        
        # Якщо рядок - парсимо його
        if not target_input or not isinstance(target_input, str):
            return []
        
        # Різні варіанти розділювачів
        separators = [',', ';', '\n', ' ']
        users = [target_input]
        
        for sep in separators:
            if sep in target_input:
                users = target_input.split(sep)
                break
        
        # Очищення та фільтрація
        cleaned_users = []
        for user in users:
            user = user.strip().replace('@', '')  # Видаляємо @ якщо є
            if user and len(user) > 0:
                # Перевірка на валідність юзернейму Instagram
                import re
                if re.match("^[a-zA-Z0-9._]+$", user) and len(user) >= 1:
                    cleaned_users.append(user)
                else:
                    self.logger.warning(f"Невалідний юзернейм: {user}")
        
        self.logger.info(f"Знайдено {len(cleaned_users)} валідних користувачів: {cleaned_users}")
        return cleaned_users
        
    def login(self):
        """Універсальний вхід в акаунт з підтримкою ВСІХ типів сторінок Instagram"""
        try:
            # Перевірка правильності даних
            if not self.validate_credentials():
                return False
                
            self.setup_driver()
            self.driver.get("https://www.instagram.com/accounts/login/")
            self.human_like_delay(3, 5)
            
            # Спочатку визначаємо тип сторінки входу
            page_type = self.detect_login_page_type()
            self.logger.info(f"Виявлено тип сторінки входу: {page_type}")
            
            if page_type == "third_type_bloks":
                return self.login_third_type_bloks()
            elif page_type == "new_layout":
                return self.login_new_layout()
            elif page_type == "old_layout":
                return self.login_old_layout()
            else:
                # Якщо не вдалося визначити, пробуємо всі методи поспіль
                self.logger.info("Тип сторінки не визначено, пробуємо всі методи поспіль")
                
                # Спочатку пробуємо третій тип (найновіший)
                if self.login_third_type_bloks():
                    return True
                    
                # Потім новий тип
                if self.login_new_layout():
                    return True
                    
                # Нарешті старий тип
                return self.login_old_layout()
                
        except Exception as e:
            self.logger.error(f"Помилка при вході: {e}")
            return False

    def detect_login_page_type(self):
        """Покращене визначення типу сторінки входу з підтримкою третього типу (Bloks UI)"""
        try:
            # Очікуємо повного завантаження сторінки
            self.human_like_delay(3, 5)
            
            # Індикатори третього типу сторінки (новий Bloks UI)
            third_type_indicators = [
                "div[data-bloks-name='bk.components.Flexbox']",
                "div[aria-label='Увійти']",
                "div[role='button'][aria-label='Увійти']",
                "div[class*='wbloks']",
                "div[data-bloks-name]"
            ]
            
            # Сильні індикатори нової версії
            new_layout_strong = [
                "input[name='username']",
                "button[type='submit']"
            ]
            
            # Сильні індикатори старої версії
            old_layout_strong = [
                "input[aria-label*='Phone number, username, or email']",
                "div[role='button'][tabindex='0']"
            ]
            
            # Слабкі індикатори
            new_layout_weak = [
                "form[method='post']",
                "input[autocomplete='username']"
            ]
            
            old_layout_weak = [
                "div[role='button'] div[dir='auto']",
                "input[aria-label*='Username']"
            ]
            
            third_type_score = 0
            new_strong_score = 0
            old_strong_score = 0
            new_weak_score = 0
            old_weak_score = 0
            
            # Перевірка третього типу (Bloks UI) - найвища пріоритетність
            for selector in third_type_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if any(el.is_displayed() for el in elements):
                        third_type_score += 3  # Висока вага для Bloks UI
                        self.logger.debug(f"Знайдено індикатор третього типу: {selector}")
                except:
                    pass
            
            # Перевірка сильних індикаторів нової версії
            for selector in new_layout_strong:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if any(el.is_displayed() for el in elements):
                        new_strong_score += 2
                        self.logger.debug(f"Знайдено сильний індикатор нової версії: {selector}")
                except:
                    pass
            
            # Перевірка сильних індикаторів старої версії
            for selector in old_layout_strong:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if any(el.is_displayed() for el in elements):
                        old_strong_score += 2
                        self.logger.debug(f"Знайдено сильний індикатор старої версії: {selector}")
                except:
                    pass
            
            # Перевірка слабких індикаторів нової версії
            for selector in new_layout_weak:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if any(el.is_displayed() for el in elements):
                        new_weak_score += 1
                except:
                    pass
            
            # Перевірка слабких індикаторів старої версії
            for selector in old_layout_weak:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if any(el.is_displayed() for el in elements):
                        old_weak_score += 1
                except:
                    pass
            
            new_total_score = new_strong_score + new_weak_score
            old_total_score = old_strong_score + old_weak_score
            
            self.logger.debug(f"Оцінки: Третій тип (Bloks) - {third_type_score}")
            self.logger.debug(f"Оцінки: Нова версія - {new_total_score} (сильні: {new_strong_score}, слабкі: {new_weak_score})")
            self.logger.debug(f"Оцінки: Стара версія - {old_total_score} (сильні: {old_strong_score}, слабкі: {old_weak_score})")
            
            # Визначення типу на основі оцінок
            if third_type_score > 0:  # Якщо є хоча б один індикатор третього типу
                return "third_type_bloks"
            elif new_strong_score > 0 and old_strong_score == 0:
                return "new_layout"
            elif old_strong_score > 0 and new_strong_score == 0:
                return "old_layout"
            # Якщо обидва мають сильні індикатори або ніхто не має - дивимось загальну оцінку
            elif new_total_score > old_total_score:
                return "new_layout"
            elif old_total_score > new_total_score:
                return "old_layout"
            else:
                # Якщо оцінки рівні - додаткова перевірка по URL та заголовку
                page_source = self.driver.page_source.lower()
                if 'react' in page_source or 'webpack' in page_source:
                    self.logger.debug("Виявлено React/Webpack - ймовірно стара версія")
                    return "old_layout"
                else:
                    self.logger.debug("Не виявлено специфічних ознак - за замовчуванням нова версія")
                    return "new_layout"
                
        except Exception as e:
            self.logger.error(f"Помилка визначення типу сторінки: {e}")
            return "unknown"

    def login_third_type_bloks(self):
        """НОВИЙ метод для третього типу сторінки (Bloks UI) з покращеним виключенням кнопок пароля"""
        try:
            self.logger.info("Використання методу для третього типу сторінки (Bloks UI)")
            
            # Пошук поля username для третього типу
            username_selectors = [
                "input[name='username']",
                "input[placeholder*='Номер телефону, ім'я користувача']",
                "input[placeholder*='Phone number, username']",
                "input[autocomplete='username']",
                "input[type='text']"
            ]
            
            username_input = None
            for selector in username_selectors:
                try:
                    username_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if username_input.is_displayed():
                        self.logger.info(f"Знайдено поле username: {selector}")
                        break
                except:
                    continue
            
            if not username_input:
                self.logger.warning("Не знайдено поле username в третьому типі")
                return False
            
            # Пошук поля password для третього типу
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "input[autocomplete='current-password']"
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_input.is_displayed():
                        self.logger.info(f"Знайдено поле password: {selector}")
                        break
                except:
                    continue
            
            if not password_input:
                self.logger.warning("Не знайдено поле password в третьому типі")
                return False
            
            # Введення даних
            self.logger.info("Введення username...")
            username_input.clear()
            self.anti_detection.human_typing(username_input, self.username)
            self.human_like_delay(1, 2)
                
            self.logger.info("Введення password...")
            password_input.clear()
            self.anti_detection.human_typing(password_input, self.password)
            self.human_like_delay(1, 2)
            
            # ПОКРАЩЕНИЙ ПОШУК КНОПКИ ВХОДУ ДЛЯ ТРЕТЬОГО ТИПУ З ВИКЛЮЧЕННЯМ КНОПОК ПАРОЛЯ
            login_button = None
            
            # Метод 1: Пошук по aria-label (найточніший) з виключенням кнопок пароля
            aria_label_selectors = [
                "div[role='button'][aria-label='Увійти']",
                "button[aria-label='Увійти']",
                "div[role='button'][aria-label='Log in']",
                "button[aria-label='Log in']",
                "div[role='button'][aria-label='Log In']",
                "button[aria-label='Log In']"
            ]
            
            for selector in aria_label_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if not element.is_displayed() or not element.is_enabled():
                            continue
                            
                        # Додаткова перевірка: переконуємось що це НЕ кнопка показати/приховати пароль
                        aria_label = element.get_attribute('aria-label') or ''
                        element_text = element.get_attribute('textContent') or element.text or ''
                        
                        # КРИТИЧНО ВАЖЛИВО: Виключаємо кнопки пов'язані з паролем
                        password_keywords = ['show', 'hide', 'показати', 'приховати', 'password', 'пароль', 'show password', 'hide password']
                        if any(keyword.lower() in aria_label.lower() for keyword in password_keywords):
                            self.logger.debug(f"❌ Пропускаємо кнопку пароля: {aria_label}")
                            continue
                        
                        if any(keyword.lower() in element_text.lower() for keyword in password_keywords):
                            self.logger.debug(f"❌ Пропускаємо кнопку пароля по тексту: {element_text}")
                            continue
                        
                        # Виключаємо елементи без тексту або з неправильним текстом
                        if len(element_text.strip()) > 50:  # Занадто довгий текст
                            continue
                            
                        login_button = element
                        self.logger.info(f"✅ Знайдено кнопку входу по aria-label: {selector}, текст: '{element_text.strip()}'")
                        break
                    if login_button:
                        break
                except:
                    continue
            
            # Метод 2: Пошук по Bloks структурі (якщо aria-label не спрацював)
            if not login_button:
                bloks_selectors = [
                    "div[data-bloks-name='bk.components.Flexbox'][role='button'][tabindex='0']",
                    "div[data-bloks-name='bk.components.Flexbox'][role='button']",
                    "div[class*='wbloks'][role='button'][tabindex='0']",
                    "div[class*='wbloks'][role='button']"
                ]
                
                for selector in bloks_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if not element.is_displayed() or not element.is_enabled():
                                continue
                                
                            element_text = element.get_attribute('textContent') or element.text or ''
                            aria_label = element.get_attribute('aria-label') or ''
                            
                            # Виключаємо кнопки пароля
                            password_keywords = ['show', 'hide', 'показати', 'приховати', 'password', 'пароль']
                            if any(keyword.lower() in (element_text + aria_label).lower() for keyword in password_keywords):
                                self.logger.debug(f"❌ Пропускаємо кнопку пароля в Bloks: {element_text}")
                                continue
                            
                            # Перевіряємо що це кнопка входу
                            login_keywords = ['увійти', 'log in', 'login', 'sign in']
                            if any(keyword.lower() in element_text.lower() for keyword in login_keywords):
                                login_button = element
                                self.logger.info(f"✅ Знайдено кнопку входу по Bloks: {selector}, текст: '{element_text.strip()}'")
                                break
                        if login_button:
                            break
                    except:
                        continue
            
            # Метод 3: Пошук кнопки поруч з полями вводу (найбезпечніший)
            if not login_button:
                try:
                    # Знаходимо форму або контейнер з полями
                    form_container = password_input.find_element(By.XPATH, "./ancestor::form[1] | ./ancestor::div[contains(@class, '') or contains(@style, '')][3]")
                    
                    # Шукаємо кнопки в формі
                    form_buttons = form_container.find_elements(By.CSS_SELECTOR, "button, div[role='button']")
                    
                    for button in form_buttons:
                        if not button.is_displayed() or not button.is_enabled():
                            continue
                            
                        button_text = button.get_attribute('textContent') or button.text or ''
                        aria_label = button.get_attribute('aria-label') or ''
                        
                        # КРИТИЧНО: Виключаємо кнопки пароля
                        password_keywords = ['show', 'hide', 'показати', 'приховати', 'password', 'пароль']
                        if any(keyword.lower() in (button_text + aria_label).lower() for keyword in password_keywords):
                            self.logger.debug(f"❌ Пропускаємо кнопку пароля в формі: {button_text}")
                            continue
                        
                        # Шукаємо кнопку входу
                        login_keywords = ['увійти', 'log in', 'login']
                        if (any(keyword in button_text.lower() for keyword in login_keywords) or
                            any(keyword in aria_label.lower() for keyword in login_keywords) or
                            button.get_attribute('type') == 'submit'):
                            
                            login_button = button
                            self.logger.info(f"✅ Знайдено кнопку входу в формі, текст: '{button_text.strip()}'")
                            break
                            
                except Exception as e:
                    self.logger.debug(f"Помилка пошуку в формі: {e}")
            
            # Спроба входу
            if login_button:
                self.logger.info("Натискання кнопки входу (третій тип)...")
                try:
                    # Скролимо до кнопки якщо потрібно
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
                    self.human_like_delay(0.5, 1)
                    
                    # Спочатку звичайний клік
                    login_button.click()
                    self.logger.info("✅ Використано звичайний клік на кнопку входу")
                    
                except Exception as e:
                    self.logger.warning(f"Звичайний клік не спрацював: {e}")
                    try:
                        # JavaScript клік
                        self.driver.execute_script("arguments[0].click();", login_button)
                        self.logger.info("✅ Використано JavaScript клік на кнопку входу")
                    except Exception as e2:
                        self.logger.warning(f"JavaScript клік не спрацював: {e2}")
                        # Останній варіант - Enter
                        password_input.send_keys(Keys.RETURN)
                        self.logger.info("✅ Використано Enter як останній варіант")
            else:
                self.logger.info("Кнопка входу не знайдена, використовуємо Enter...")
                password_input.send_keys(Keys.RETURN)
            
            return self.wait_for_login_result()
                
        except Exception as e:
            self.logger.error(f"❌ Помилка в третьому типі входу: {e}")
            return False
            
    def login_new_layout(self):
        """Вхід для нової версії сторінки з покращеним виключенням кнопок пароля"""
        try:
            self.logger.info("Використання методу для нової версії сторінки")
            
            # Пошук поля username (нова версія)
            username_selectors = [
                "input[name='username']",
                "input[aria-label*='Phone number, username']",
                "input[placeholder*='Phone number, username']",
                "input[type='text']"
            ]
            
            username_input = None
            for selector in username_selectors:
                try:
                    username_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if username_input.is_displayed():
                        self.logger.info(f"Знайдено поле username: {selector}")
                        break
                except:
                    continue
            
            if not username_input:
                self.logger.warning("Не знайдено поле username в новій версії")
                return False
            
            # Пошук поля password (нова версія)
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "input[aria-label*='Password']"
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_input.is_displayed():
                        self.logger.info(f"Знайдено поле password: {selector}")
                        break
                except:
                    continue
            
            if not password_input:
                self.logger.warning("Не знайдено поле password в новій версії")
                return False
            
            # Введення даних
            self.logger.info("Введення username...")
            username_input.clear()
            self.anti_detection.human_typing(username_input, self.username)
            self.human_like_delay(1, 2)
                
            self.logger.info("Введення password...")
            password_input.clear()
            self.anti_detection.human_typing(password_input, self.password)
            self.human_like_delay(1, 2)
            
            # Пошук кнопки входу (нова версія) з виключенням кнопок пароля
            login_selectors = [
                "button[type='submit']",
                "div[role='button'][tabindex='0']",
                "//button[contains(text(), 'Log in')]",
                "//button[contains(text(), 'Log In')]",
                "//div[@role='button' and contains(text(), 'Log')]",
                "//button[contains(text(), 'Увійти')]",
                "//div[@role='button' and contains(text(), 'Увійти')]"
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if not element.is_displayed() or not element.is_enabled():
                            continue
                            
                        element_text = element.get_attribute('textContent') or element.text or ''
                        aria_label = element.get_attribute('aria-label') or ''
                        
                        # Виключаємо кнопки пароля
                        password_keywords = ['show', 'hide', 'показати', 'приховати', 'password', 'пароль']
                        if any(keyword.lower() in (element_text + aria_label).lower() for keyword in password_keywords):
                            self.logger.debug(f"❌ Пропускаємо кнопку пароля: {element_text}")
                            continue
                        
                        # Перевіряємо що це кнопка входу
                        if (len(element_text.strip()) < 50 and 
                            (any(keyword in element_text.lower() for keyword in ['log in', 'log', 'sign in', 'enter', 'увійти']) or
                             element.get_attribute('type') == 'submit')):
                            
                            login_button = element
                            self.logger.info(f"✅ Знайдено кнопку входу: {selector}, текст: '{element_text.strip()}'")
                            break
                    
                    if login_button:
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Помилка з селектором {selector}: {e}")
                    continue
            
            # Спроба входу
            if login_button:
                self.logger.info("Натискання кнопки для входу...")
                login_button.click()
            else:
                self.logger.info("Кнопка входу не знайдена, використовуємо Enter...")
                password_input.send_keys(Keys.RETURN)
            
            return self.wait_for_login_result()
                
        except Exception as e:
            self.logger.error(f"❌ Помилка в новій версії входу: {e}")
            return False
            
    def login_old_layout(self):
        """Покращений вхід для старої версії сторінки з виключенням кнопок пароля"""
        try:
            self.logger.info("Використання покращеного методу для старої версії сторінки")
            
            # Додаткове очікування для старої версії
            self.human_like_delay(2, 4)
            
            # Розширений пошук поля username для старої версії
            username_selectors = [
                "input[aria-label*='Phone number, username, or email']",
                "input[aria-label*='Phone number, username']", 
                "input[aria-label*='Username']",
                "input[placeholder*='Phone number, username, or email']",
                "input[placeholder*='Username']",
                "input[name='username']",
                "input[type='text']:first-of-type",
                "form input[type='text']"
            ]
            
            username_input = None
            for selector in username_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            username_input = element
                            self.logger.info(f"Знайдено поле username: {selector}")
                            break
                    if username_input:
                        break
                except Exception as e:
                    self.logger.debug(f"Селектор {selector} не спрацював: {e}")
                    continue
            
            if not username_input:
                self.logger.warning("Не знайдено поле username в старій версії")
                return False
            
            # Розширений пошук поля password для старої версії
            password_selectors = [
                "input[aria-label*='Password']",
                "input[type='password']",
                "input[name='password']",
                "form input[type='password']"
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            password_input = element
                            self.logger.info(f"Знайдено поле password: {selector}")
                            break
                    if password_input:
                        break
                except Exception as e:
                    self.logger.debug(f"Селектор {selector} не спрацював: {e}")
                    continue
            
            if not password_input:
                self.logger.warning("Не знайдено поле password в старій версії")
                return False
            
            # Очищення полів перед введенням
            try:
                username_input.clear()
                password_input.clear()
            except:
                pass
            
            # Введення username з фокусом
            self.logger.info("Введення username (стара версія)...")
            try:
                username_input.click()  # Клік для фокусу
                self.human_like_delay(0.5, 1)
                self.anti_detection.human_typing(username_input, self.username)
            except Exception as e:
                self.logger.warning(f"Помилка при введенні username: {e}")
                username_input.send_keys(self.username)
            
            self.human_like_delay(1, 2)
                
            # Введення password з фокусом
            self.logger.info("Введення password (стара версія)...")
            try:
                password_input.click()  # Клік для фокусу
                self.human_like_delay(0.5, 1)
                self.anti_detection.human_typing(password_input, self.password)
            except Exception as e:
                self.logger.warning(f"Помилка при введенні password: {e}")
                password_input.send_keys(self.password)
            
            self.human_like_delay(1, 2)
            
            # Покращений пошук кнопки входу для старої версії з виключенням кнопок пароля
            login_selectors = [
                # Точні селектори для кнопки "Log in"
                "//div[@role='button' and normalize-space(text())='Log in']",
                "//div[@role='button' and normalize-space(text())='Log In']",
                "//button[normalize-space(text())='Log in']",
                "//button[normalize-space(text())='Log In']",
                "//div[@role='button' and normalize-space(text())='Увійти']",
                "//button[normalize-space(text())='Увійти']",
                
                # Селектори по структурі кнопки
                "div[role='button'][tabindex='0']:has(div[dir='auto'])",
                "button[type='submit']",
                
                # Селектори по позиції (кнопка входу зазвичай після полів)
                "form div[role='button']:last-of-type",
                "div[role='button'][tabindex='0']:last-of-type"
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if not element.is_displayed() or not element.is_enabled():
                            continue
                            
                        element_text = element.get_attribute('textContent') or element.text or ""
                        aria_label = element.get_attribute('aria-label') or ""
                        
                        # Виключаємо кнопки пароля
                        password_keywords = ['show', 'hide', 'показати', 'приховати', 'password', 'пароль']
                        if any(keyword.lower() in (element_text + aria_label).lower() for keyword in password_keywords):
                            self.logger.debug(f"❌ Пропускаємо кнопку пароля: {element_text}")
                            continue
                        
                        # Фільтруємо кнопки по довжині тексту та змісту
                        if len(element_text.strip()) < 50:  # Коротший текст
                            if any(keyword in element_text.lower() for keyword in ['log in', 'log', 'sign in', 'enter', 'увійти']):
                                login_button = element
                                self.logger.info(f"✅ Знайдено кнопку входу: {selector}, текст: '{element_text.strip()}'")
                                break
                            elif element_text.strip() == "":  # Кнопка без тексту, але з role='button'
                                # Додаткова перевірка що це не випадковий елемент
                                if element.get_attribute('tabindex') == '0':
                                    login_button = element
                                    self.logger.info(f"✅ Знайдено кнопку входу без тексту: {selector}")
                                    break
                    
                    if login_button:
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Помилка з селектором {selector}: {e}")
                    continue
            
            # Спроба входу з покращеними методами
            if login_button:
                self.logger.info("Натискання кнопки входу (стара версія)...")
                try:
                    # Спочатку перевіряємо чи кнопка активна
                    if login_button.is_enabled():
                        # Скролимо до кнопки якщо потрібно
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
                        self.human_like_delay(0.5, 1)
                        
                        # Пробуємо звичайний клік
                        login_button.click()
                        self.logger.info("✅ Використано звичайний клік")
                    else:
                        self.logger.warning("Кнопка не активна, використовуємо Enter")
                        password_input.send_keys(Keys.RETURN)
                        
                except Exception as e:
                    self.logger.warning(f"Звичайний клік не спрацював: {e}")
                    try:
                        # Пробуємо JavaScript клік
                        self.driver.execute_script("arguments[0].click();", login_button)
                        self.logger.info("✅ Використано JavaScript клік")
                    except Exception as e2:
                        self.logger.warning(f"JavaScript клік не спрацював: {e2}")
                        # Останній варіант - Enter
                        password_input.send_keys(Keys.RETURN)
                        self.logger.info("✅ Використано Enter як останній варіант")
            else:
                self.logger.info("Кнопка входу взагалі не знайдена, використовуємо прямий Enter...")
                password_input.send_keys(Keys.RETURN)
            
            return self.wait_for_login_result()
                
        except Exception as e:
            self.logger.error(f"❌ Помилка в старій версії входу: {e}")
            return False
            
    def wait_for_login_result(self):
        """Очікування результату входу (універсальний метод)"""
        try:
            self.logger.info("Очікування результату входу...")
            
            start_time = time.time()
            timeout = 30
            
            while time.time() - start_time < timeout:
                current_url = self.driver.current_url
                
                # Перевірка на успішний вхід
                if current_url != "https://www.instagram.com/accounts/login/" and "login" not in current_url:
                    self.logger.info(f"URL змінився на: {current_url}")
                    
                    if "challenge" in current_url:
                        self.logger.warning("Потрібно пройти challenge вручну в браузері...")
                        try:
                            WebDriverWait(self.driver, 300).until(
                                lambda d: "challenge" not in d.current_url and "login" not in d.current_url
                            )
                            self.logger.info("Challenge пройдено вручну")
                            self.handle_post_login_dialogs()
                            self.logged_in = True
                            return True
                        except:
                            self.logger.error("Challenge не пройдено вчасно")
                            return False
                    
                    if "two_factor" in current_url or "2fa" in current_url:
                        self.logger.warning("Потрібна двофакторна автентифікація. Введіть код вручну...")
                        try:
                            WebDriverWait(self.driver, 180).until(
                                lambda d: "two_factor" not in d.current_url and "login" not in d.current_url
                            )
                            self.logger.info("2FA пройдено вручну")
                            self.handle_post_login_dialogs()
                            self.logged_in = True
                            return True
                        except:
                            self.logger.error("2FA не пройдено вчасно")
                            return False
                        
                    # Успішний вхід
                    self.handle_post_login_dialogs()
                    self.logged_in = True
                    self.logger.info(f"✅ Успішний вхід для {self.username}")
                    return True
                
                # Перевірка на помилки входу
                error_selectors = [
                    "div[role='alert']", 
                    "#slfErrorAlert", 
                    "div[data-testid='login-error']",
                    "p[data-testid='login-error-message']",
                    "div[id*='error']",
                    "div[class*='error']", 
                    "div[class*='Alert']", 
                    "div[class*='-message']", 
                    "span[class*='error']",
                    "span[data-testid='login-error-message']"
                ]
                
                for selector in error_selectors:
                    try:
                        error_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for error_el in error_elements:
                            if error_el.is_displayed() and error_el.text.strip():
                                error_text = error_el.text.strip()
                                self.logger.error(f"❌ Помилка входу: {error_text}")
                                return False
                    except:
                        continue
                
                # Перевірка на наявність Home іконки
                home_selectors = [
                    "svg[aria-label='Home']", 
                    "a[href='/']",
                    "div[data-testid='mobile-nav-home']",
                    "a[aria-label='Home']"
                ]
                
                for selector in home_selectors:
                    try:
                        home_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for home_el in home_elements:
                            if home_el.is_displayed():
                                self.logger.info("Знайдено Home елемент - успішний вхід")
                                self.handle_post_login_dialogs()
                                self.logged_in = True
                                self.logger.info(f"✅ Успішний вхід для {self.username}")
                                return True
                    except:
                        continue
                
                time.sleep(1)
            
            # Timeout
            current_url = self.driver.current_url
            self.logger.error(f"Timeout при вході. Фінальний URL: {current_url}")
            
            # Остання спроба перевірки
            if "login" not in current_url:
                self.logger.info("Можливо вхід все ж таки успішний, перевіряємо...")
                home_elements = self.driver.find_elements(By.CSS_SELECTOR, "svg[aria-label='Home'], a[href='/']")
                if home_elements and any(el.is_displayed() for el in home_elements):
                    self.handle_post_login_dialogs()
                    self.logged_in = True
                    self.logger.info(f"✅ Успішний вхід для {self.username} (затримана перевірка)")
                    return True
            
            return False
                
        except Exception as e:
            self.logger.error(f"❌ Помилка при очікуванні результату: {e}")
            return False
            
    def handle_post_login_dialogs(self):
        """Обробка діалогів після входу"""
        dialogs_handled = 0
        max_dialogs = 5
        
        self.logger.info("Початок обробки діалогів після входу...")
        
        while dialogs_handled < max_dialogs:
            self.human_like_delay(1, 2)
            dialog_found = False
            
            # Селектори для закриття діалогів
            close_selectors = [
                "//button[contains(text(), 'Not Now')]",
                "//button[contains(text(), 'Не зараз')]",
                "//button[@aria-label='Close']",
                "svg[aria-label='Close']",
                "//button[contains(text(), 'Skip')]",
                "//button[contains(text(), 'Cancel')]"
            ]
            
            for selector in close_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            try:
                                element.click()
                                self.logger.info(f"Закрито діалог: {selector}")
                                dialog_found = True
                                self.human_like_delay(1, 2)
                                break
                            except:
                                continue
                    
                    if dialog_found:
                        break
                        
                except:
                    continue
            
            if dialog_found:
                dialogs_handled += 1
            else:
                break
            
        self.logger.info(f"Обробка діалогів завершена. Закрито {dialogs_handled} діалогів")
        
        # Фінальне закриття через Escape
        try:
            remaining_dialogs = self.driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']")
            if remaining_dialogs:
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        except:
            pass

    def like_recent_posts(self, target_username, count=2):
        """Лайк останніх постів користувача"""
        try:
            profile_url = f"https://www.instagram.com/{target_username}/"
            self.driver.get(profile_url)
            self.logger.info(f"📍 Перехід на профіль {target_username}")
            self.human_like_delay(3, 5)
            
            # Пошук постів на профілі
            post_selectors = [
                "article a[href*='/p/']",
                "div[style*='padding-bottom'] a[href*='/p/']",
                "a[href*='/p/']"
            ]
            
            posts = []
            for selector in post_selectors:
                try:
                    found_posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if found_posts:
                        posts = found_posts[:count]
                        self.logger.info(f"📸 Знайдено {len(posts)} постів для лайку")
                        break
                except:
                    continue
            
            if not posts:
                self.logger.warning(f"❌ Не знайдено постів у профілі {target_username}")
                return False
            
            # Збереження посилань на пости
            post_links = []
            for post in posts:
                try:
                    href = post.get_attribute('href')
                    if href:
                        post_links.append(href)
                except:
                    continue
            
            if not post_links:
                self.logger.warning("❌ Не вдалося отримати посилання на пости")
                return False
            
            self.logger.info(f"🔗 Отримано {len(post_links)} посилань на пости")
            liked_count = 0
            
            # Лайк кожного поста з поверненням до профілю
            for i, post_url in enumerate(post_links):
                try:
                    self.logger.info(f"📸 Відкриваємо пост {i+1}/{len(post_links)}")
                    
                    # Перехід до поста
                    self.driver.get(post_url)
                    self.human_like_delay(3, 5)
                    
                    # Очікування завантаження поста
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
                        )
                    except:
                        self.logger.warning(f"⚠️ Пост {i+1} не завантажився")
                        continue
                    
                    # Пошук кнопки лайка
                    like_selectors = [
                        "svg[aria-label='Like']",
                        "svg[aria-label='Подобається']", 
                        "button svg[aria-label*='Like']",
                        "span[role='button'] svg[aria-label='Like']"
                    ]
                    
                    like_button = None
                    for selector in like_selectors:
                        try:
                            like_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for like_el in like_elements:
                                if like_el.is_displayed():
                                    like_button = like_el
                                    break
                            if like_button:
                                break
                        except:
                            continue
                    
                    if like_button:
                        # Перевірка чи пост вже лайкнутий
                        aria_label = like_button.get_attribute('aria-label') or ""
                        
                        if 'Unlike' in aria_label or 'Не подобається' in aria_label:
                            self.logger.info(f"ℹ️ Пост {i+1} вже лайкнутий, пропускаємо")
                        else:
                            # Спроба лайку
                            try:
                                parent_button = like_button.find_element(By.XPATH, "./ancestor::*[@role='button' or @tabindex='0'][1]")
                                parent_button.click()
                                self.logger.info(f"❤️ Лайк поста {i+1} користувача {target_username}")
                                liked_count += 1
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", like_button)
                                    self.logger.info(f"❤️ Лайк поста {i+1} користувача {target_username} (JS)")
                                    liked_count += 1
                                except:
                                    self.logger.warning(f"❌ Не вдалося поставити лайк на пост {i+1}")
                        
                        # Затримка після лайка
                        self.human_like_delay(2, 4)
                    else:
                        self.logger.warning(f"❌ Не знайдено кнопку лайка для поста {i+1}")
                    
                    # Повернення до профілю (завжди після кожного поста)
                    self.logger.info(f"🔙 Повертаємося до профілю після поста {i+1}")
                    self.driver.get(profile_url)
                    self.human_like_delay(2, 3)
                    
                except Exception as e:
                    self.logger.error(f"❌ Помилка при обробці поста {i+1}: {e}")
                    # При помилці також повертаємося до профілю
                    try:
                        self.driver.get(profile_url)
                        self.human_like_delay(2, 3)
                    except:
                        pass
                    continue
                    
            self.logger.info(f"✅ Завершено лайки постів: {liked_count}/{len(post_links)} успішно")
            return liked_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ Критична помилка при лайку постів: {e}")
            return False

    def _send_story_reply(self, reply_input, message):
        """Надійний метод відправки повідомлення в сторіс"""
        try:
            # Очищаємо поле і вводимо повідомлення
            reply_input.clear()
            reply_input.send_keys(message)
            self.logger.info(f"💬 Введено повідомлення: {message}")
            
            # Чекаємо щоб кнопка Send стала активною (з'являється після введення тексту)
            self.human_like_delay(1, 2)
            
            # Метод 1: Пошук кнопки Send з текстом "Send"
            try:
                # Шукаємо кнопки з текстом "Send"
                send_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Send')] | //div[@role='button'][contains(text(), 'Send')]")
                
                for btn in send_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        try:
                            btn.click()
                            self.logger.info("📤 Повідомлення відправлено (пошук по тексту Send)")
                            return True
                        except Exception as e:
                            self.logger.debug(f"Помилка кліку: {e}")
                            continue
                            
            except Exception as e:
                self.logger.debug(f"Метод 1 не спрацював: {e}")
            
            # Метод 2: Пошук через JavaScript з точним пошуком кнопки "Send"
            try:
                sent = self.driver.execute_script("""
                    const input = arguments[0];
                    const inputRect = input.getBoundingClientRect();
                    
                    // Шукаємо всі кнопки на сторінці
                    const allButtons = document.querySelectorAll('button, div[role="button"]');
                    
                    for (let btn of allButtons) {
                        const btnRect = btn.getBoundingClientRect();
                        
                        // Перевіряємо видимість
                        if (btnRect.width === 0 || btnRect.height === 0) continue;
                        
                        // Перевіряємо текст кнопки
                        const btnText = btn.textContent || btn.innerText || '';
                        
                        if (btnText.includes('Send')) {
                            // Кнопка має бути в правому нижньому куті від поля вводу
                            if (btnRect.left >= inputRect.right - 100 && 
                                btnRect.top >= inputRect.bottom - 50) {
                                
                                console.log('Знайшли кнопку Send:', btnText, btnRect);
                                
                                try {
                                    btn.click();
                                    return true;
                                } catch (e) {
                                    console.log('Click failed:', e);
                                }
                            }
                        }
                    }
                    return false;
                """, reply_input)
                
                if sent:
                    self.logger.info("📤 Повідомлення відправлено (JavaScript пошук)")
                    return True
                    
            except Exception as e:
                self.logger.debug(f"Метод 2 не спрацював: {e}")
            
            # Метод 3: Пошук кнопки в контейнері поля вводу
            try:
                # Знаходимо батьківський контейнер поля вводу
                parent_container = reply_input.find_element(By.XPATH, "./ancestor::div[contains(@class, '') or contains(@style, '')]")
                
                # Шукаємо кнопки в контейнері
                buttons = parent_container.find_elements(By.CSS_SELECTOR, "button, div[role='button']")
                
                for btn in buttons:
                    if not btn.is_displayed() or not btn.is_enabled():
                        continue
                    
                    btn_text = btn.text or btn.get_attribute('innerText') or ''
                    
                    if 'Send' in btn_text:
                        try:
                            btn.click()
                            self.logger.info("📤 Повідомлення відправлено (пошук в контейнері)")
                            return True
                        except Exception as e:
                            self.logger.debug(f"Помилка кліку: {e}")
                            continue
                            
            except Exception as e:
                self.logger.debug(f"Метод 3 не спрацював: {e}")
            
            # Метод 4: Універсальний пошук всіх кнопок з перевіркою позиції
            try:
                all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, div[role='button']")
                input_rect = reply_input.rect
                
                for btn in all_buttons:
                    if not btn.is_displayed():
                        continue
                    
                    btn_rect = btn.rect
                    btn_text = btn.text or ''
                    
                    # Перевіряємо що кнопка знаходиться в правому нижньому куті від поля вводу
                    if (btn_rect['x'] >= input_rect['x'] + input_rect['width'] - 100 and
                        btn_rect['y'] >= input_rect['y'] + input_rect['height'] - 50 and
                        'Send' in btn_text):
                        
                        try:
                            btn.click()
                            self.logger.info("📤 Повідомлення відправлено (універсальний пошук)")
                            return True
                        except Exception as e:
                            self.logger.debug(f"Помилка кліку: {e}")
                            continue
                            
            except Exception as e:
                self.logger.debug(f"Метод 4 не спрацював: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Помилка відправки повідомлення: {e}")
            return False

    def process_story(self, target_username, messages):
        """Покращена версія відповіді на сторіс"""
        try:
            # Перехід на профіль
            self.driver.get(f"https://www.instagram.com/{target_username}/")
            self.logger.info(f"📍 Перехід на профіль {target_username}")
            self.human_like_delay(2, 3)

            # Пошук сторіс
            story_selectors = [
                "button canvas[style*='border']",
                "div[style*='border'] button",
                "img[style*='border']",
                "button[aria-label*='story']",
                "div[role='button'][tabindex='0']"
            ]
            
            story_found = False
            for selector in story_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            self.logger.info(f"📱 Сторіс відкрита через: {selector}")
                            story_found = True
                            break
                    if story_found:
                        break
                except Exception as e:
                    self.logger.debug(f"Помилка з селектором {selector}: {e}")
                    continue

            if not story_found:
                self.logger.info("📭 Активних сторіс не знайдено")
                return False

            self.human_like_delay(1, 2)

            # Лайк сторіс
            like_success = False
            like_selectors = [
                "svg[aria-label='Like']",
                "svg[aria-label='Подобається']",
                "button[aria-label*='Like']"
            ]
            
            for selector in like_selectors:
                try:
                    like_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if 'Unlike' not in (like_btn.get_attribute('aria-label') or ''):
                        like_btn.click()
                        self.logger.info("❤️ Лайк поставлено")
                        like_success = True
                        break
                except:
                    continue

            # Відповідь на сторіс
            reply_success = False
            reply_selectors = [
                "textarea[placeholder*='Send message']",
                "textarea[placeholder*='Reply']",
                "textarea[placeholder*='Відповісти']",
                "div[contenteditable='true']"
            ]
            
            for selector in reply_selectors:
                try:
                    reply_input = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    message = random.choice(messages)
                    reply_input.click()
                    self.human_like_delay(0.5, 1)
                    
                    # Використовуємо новий метод відправки
                    if self._send_story_reply(reply_input, message):
                        reply_success = True
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Помилка з полем вводу {selector}: {e}")
                    continue

            if not reply_success:
                self.logger.warning("⚠️ Не вдалося відправити повідомлення")

            # ВАЖЛИВО: ЧЕКАЄМО 5 СЕКУНД ПІСЛЯ ВСІХ ДІЙ (НЕЗАЛЕЖНО ВІД РЕЗУЛЬТАТУ)
            self.logger.info("⏳ Обов'язкове очікування 5 секунд після всіх дій в сторіс...")
            time.sleep(5)
            self.logger.info("✅ Очікування завершено")

            # Тільки після очікування закриваємо сторіс
            self._close_story()
            
            self.logger.info("✅ Операція завершена")
            return like_success or reply_success

        except Exception as e:
            self.logger.error(f"❌ Помилка обробки сторіс: {e}")
            return False

    def _close_story(self):
        """Універсальне закриття сторіс"""
        try:
            close_methods = [
                lambda: self.driver.find_element(By.CSS_SELECTOR, "svg[aria-label='Close']").click(),
                lambda: self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close']").click(),
                lambda: ActionChains(self.driver).send_keys(Keys.ESCAPE).perform(),
                lambda: ActionChains(self.driver).move_by_offset(50, 50).click().perform()
            ]
            
            for method in close_methods:
                try:
                    method()
                    self.human_like_delay(1, 2)
                    self.logger.info("📱 Сторіс закрита")
                    return True
                except:
                    continue
                    
            self.logger.warning("⚠️ Не вдалося закрити сторіс стандартними методами")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Помилка при закритті сторіс: {e}")
            return False
    
    def send_direct_message(self, target_username, messages):
        """Fallback: якщо сторіс немає → Direct Messages → Next → повідомлення"""
        try:
            self.logger.info(f"💬 Відправка Direct Message для {target_username}")
            
            # Перехід до Direct Messages
            dm_url = "https://www.instagram.com/direct/new/"
            self.driver.get(dm_url)
            self.human_like_delay(3, 5)
            
            # Якщо direct/new не працює, пробуємо через inbox
            if "direct/new" not in self.driver.current_url:
                self.logger.info("💬 Перехід через inbox")
                dm_url = "https://www.instagram.com/direct/inbox/"
                self.driver.get(dm_url)
                self.human_like_delay(3, 5)
                
                # Пошук кнопки нового повідомлення
                new_message_selectors = [
                    "svg[aria-label='New message']",
                    "button[aria-label='New message']",
                    "//div[contains(text(), 'New message')]",
                    "//button[contains(text(), 'New message')]"
                ]
                
                for selector in new_message_selectors:
                    try:
                        if selector.startswith("//"):
                            new_message_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            new_message_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        new_message_button.click()
                        self.human_like_delay(2, 3)
                        break
                    except:
                        continue
            
            # Пошук поля для введення імені користувача
            search_selectors = [
                "input[placeholder*='Search']",
                "input[name='queryBox']",
                "input[aria-label*='Search']",
                "div[contenteditable='true']",
                "input[placeholder*='search']",
                "input[type='text']"
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not search_input:
                self.logger.error("❌ Не знайдено поле пошуку користувачів")
                return False
            
            # Введення імені користувача
            self.logger.info(f"🔍 Пошук користувача: {target_username}")
            search_input.clear()
            self.anti_detection.human_typing(search_input, target_username)
            self.human_like_delay(2, 3)
            
            # Пошук користувача в результатах
            user_found = False
            
            # Спочатку точний збіг
            try:
                exact_user = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//span[text()='{target_username}']"))
                )
                exact_user.click()
                user_found = True
                self.logger.info(f"✅ Знайдено користувача: {target_username}")
            except:
                # Частковий збіг 
                try:
                    user_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button'] span")
                    for element in user_elements:
                        if element.text and target_username.lower() in element.text.lower():
                            parent = element.find_element(By.XPATH, "./ancestor::div[@role='button'][1]")
                            parent.click()
                            user_found = True
                            self.logger.info(f"✅ Знайдено користувача: {element.text}")
                            break
                except:
                    pass
            
            if not user_found:
                self.logger.error(f"❌ Користувач {target_username} не знайдений")
                return False
            
            self.human_like_delay(2, 3)
            
            # ПОКРАЩЕНИЙ ПОШУК КНОПКИ "NEXT"
            next_button_found = False
            
            # Метод 1: Пошук кнопки Next відносно поля пошуку
            try:
                search_container = search_input.find_element(By.XPATH, "./ancestor::div[3]")
                next_selectors_relative = [
                    ".//button[contains(text(), 'Next')]",
                    ".//div[@role='button'][contains(text(), 'Next')]",
                    ".//button[contains(text(), 'Далі')]",
                    ".//div[@role='button'][contains(text(), 'Далі')]"
                ]
                
                for selector in next_selectors_relative:
                    try:
                        next_button = search_container.find_element(By.XPATH, selector)
                        if next_button.is_displayed() and next_button.is_enabled():
                            next_button.click()
                            next_button_found = True
                            self.logger.info("✅ Натиснуто кнопку Next (відносний пошук)")
                            break
                    except:
                        continue
                        
            except Exception as e:
                self.logger.debug(f"Помилка відносного пошуку Next: {e}")
            
            # Метод 2: Глобальний пошук кнопки Next
            if not next_button_found:
                next_selectors_global = [
                    "//div[@role='button'][contains(text(), 'Next')]",
                    "//button[contains(text(), 'Next')]",
                    "//div[@role='button'][contains(text(), 'Далі')]",
                    "//button[contains(text(), 'Далі')]"
                ]
                
                for selector in next_selectors_global:
                    try:
                        next_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        if next_button.is_displayed():
                            next_button.click()
                            next_button_found = True
                            self.logger.info("✅ Натиснуто кнопку Next (глобальний пошук)")
                            break
                    except:
                        continue
            
            # Обробка вікна, що може з'явитися після Next
            if next_button_found:
                self.human_like_delay(2, 3)
                try:
                    # Спроба знайти і закрити вікно "Not Now"
                    not_now_buttons = [
                        "//button[contains(text(), 'Not Now')]",
                        "//div[@role='button'][contains(text(), 'Not Now')]",
                        "//button[contains(text(), 'Не зараз')]",
                        "//div[@role='button'][contains(text(), 'Не зараз')]"
                    ]
                    
                    for selector in not_now_buttons:
                        try:
                            not_now_btn = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            if not_now_btn.is_displayed():
                                not_now_btn.click()
                                self.logger.info("✅ Закрито вікно 'Not Now'")
                                self.human_like_delay(1, 2)
                                break
                        except:
                            continue
                except Exception as e:
                    self.logger.debug(f"Не знайдено вікна для закриття: {e}")
            
            # Пошук поля для повідомлення
            message_selectors = [
                "textarea[placeholder*='Message']",
                "div[contenteditable='true'][aria-label*='Message']",
                "div[contenteditable='true']",
                "textarea[aria-label*='Message']"
            ]
            
            message_input = None
            for selector in message_selectors:
                try:
                    message_input = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not message_input:
                self.logger.error("❌ Не знайдено поле для введення повідомлення")
                return False
            
            message = random.choice(messages)
            self.logger.info(f"💬 Вибрано повідомлення ({len(message.splitlines())} рядків):")
            for i, line in enumerate(message.splitlines()):
                self.logger.info(f"   Рядок {i+1}: {line}")

            # Введення повідомлення
            self.logger.info(f"💬 Введення повідомлення: {message}")

            message_input.clear()
            self.fast_typing(message_input, message)
            self.human_like_delay(0.5, 1)

            # Відправка повідомлення
            try:
                message_input.send_keys(Keys.RETURN)
                self.logger.info(f"✅ Direct Message відправлено для {target_username}")
                return True
            except:
                try:
                    send_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    send_button.click()
                    self.logger.info(f"✅ Direct Message відправлено для {target_username}")
                    return True
                except:
                    self.logger.error("❌ Не вдалося відправити повідомлення")
                    return False

        except Exception as e:
            self.logger.error(f"❌ Помилка при відправці Direct Message: {e}")
            return False

    # === НОВИЙ МЕТОД: БАГАТОКОРИСТУВАЦЬКА АВТОМАТИЗАЦІЯ ===
    def run_automation_multiple_users(self, target_users_input, messages, actions_config=None):
        """Запуск автоматизації для багатьох користувачів ПОСЛІДОВНО"""
        try:
            self.logger.info(f"🚀 Початок багатокористувацької автоматизації")
            
            # Парсинг списку користувачів
            if isinstance(target_users_input, list):
                # Якщо вже список - використовуємо його
                target_users = target_users_input
            else:
                # Якщо рядок - парсимо
                target_users = self.parse_target_users(target_users_input)
            
            if not target_users:
                self.logger.error("❌ Не знайдено валідних користувачів")
                return False
            
            # Налаштування дій за замовчуванням
            if actions_config is None:
                actions_config = {
                    'like_posts': True,
                    'like_stories': True, 
                    'reply_stories': True,
                    'send_direct_message': True,
                    'posts_count': 2
                }
            
            # Вхід в систему (ОДИН РАЗ для всіх користувачів)
            if not self.login():
                self.logger.error("❌ Помилка входу в систему")
                return False
            
            total_users = len(target_users)
            successful_users = 0
            failed_users = []
            
            self.logger.info("=" * 60)
            self.logger.info(f"📋 ПЛАН: Обробити {total_users} користувачів послідовно")
            self.logger.info(f"🎯 Список: {', '.join(target_users)}")
            self.logger.info("📋 Для кожного користувача:")
            self.logger.info("  1. 📸 Лайк останніх постів (профіль → пост → лайк → назад)")
            self.logger.info("  2. 📱 Сторіс (аватарка → лайк → відповідь)")
            self.logger.info("  3. 💬 Fallback DM (якщо сторіс немає)")
            self.logger.info("=" * 60)
            
            # Обробка кожного користувача ПОСЛІДОВНО
            for user_index, target_user in enumerate(target_users, 1):
                try:
                    self.logger.info("")
                    self.logger.info("🔹" * 60)
                    self.logger.info(f"👤 КОРИСТУВАЧ {user_index}/{total_users}: @{target_user}")
                    self.logger.info("🔹" * 60)
                    
                    # Виконуємо ВСІ дії для цього користувача
                    user_success = self.run_single_user_automation(target_user, messages, actions_config)
                    
                    if user_success:
                        successful_users += 1
                        self.logger.info(f"✅ Користувач @{target_user} оброблений УСПІШНО!")
                    else:
                        failed_users.append(target_user)
                        self.logger.warning(f"❌ Помилка при обробці @{target_user}")
                    
                    # Затримка між користувачами (крім останнього)
                    if user_index < total_users:
                        delay_time = random.uniform(30, 60)  # 30-60 секунд між користувачами
                        self.logger.info(f"⏳ Затримка {delay_time:.1f} сек. перед наступним користувачем...")
                        time.sleep(delay_time)
                    
                except Exception as e:
                    self.logger.error(f"❌ Критична помилка при обробці @{target_user}: {e}")
                    failed_users.append(target_user)
                    continue
            
            # Підсумок роботи
            success_rate = (successful_users / total_users) * 100
            
            self.logger.info("")
            self.logger.info("🔸" * 60)
            self.logger.info("📊 === ЗАГАЛЬНИЙ ПІДСУМОК БАГАТОКОРИСТУВАЦЬКОЇ АВТОМАТИЗАЦІЇ ===")
            self.logger.info("🔸" * 60)
            self.logger.info(f"👥 Всього користувачів: {total_users}")
            self.logger.info(f"✅ Успішно оброблено: {successful_users}")
            self.logger.info(f"❌ Помилки: {len(failed_users)}")
            self.logger.info(f"📈 Успішність: {success_rate:.1f}%")
            
            if failed_users:
                self.logger.info(f"❌ Користувачі з помилками: {', '.join(failed_users)}")
            
            if success_rate == 100:
                self.logger.info("🎉 ВІДМІННО! Всі користувачі оброблені успішно!")
            elif success_rate >= 80:
                self.logger.info("👍 ДОБРЕ! Більшість користувачів оброблено успішно!")
            elif success_rate >= 50:
                self.logger.info("⚠️ ЗАДОВІЛЬНО! Половина користувачів оброблена!")
            else:
                self.logger.info("😞 ПОТРІБНО ПОКРАЩЕННЯ! Багато помилок!")
            
            self.logger.info("🔸" * 60)
            
            return successful_users > 0
            
        except Exception as e:
            self.logger.error(f"❌ Критична помилка при багатокористувацькій автоматизації: {e}")
            return False

    def run_single_user_automation(self, target_username, messages, actions_config=None):
        """Виконання повного циклу дій для ОДНОГО користувача"""
        try:
            self.logger.info(f"🎯 Початок повного циклу для @{target_username}")
            
            # Налаштування дій за замовчуванням
            if actions_config is None:
                actions_config = {
                    'like_posts': True,
                    'like_stories': True,
                    'reply_stories': True, 
                    'send_direct_message': True,
                    'posts_count': 2
                }
            
            success_count = 0
            total_actions = 3
            
            # 1. ЕТАП 1: Лайк постів (якщо увімкнено)
            if actions_config.get('like_posts', True):
                self.logger.info("📸 === ЕТАП 1: ЛАЙК ПОСТІВ ===")
                try:
                    posts_count = actions_config.get('posts_count', 2)
                    if self.like_recent_posts(target_username, posts_count):
                        success_count += 1
                        self.logger.info("✅ Лайки постів виконано успішно")
                    else:
                        self.logger.warning("❌ Лайки постів не виконано")
                except Exception as e:
                    self.logger.error(f"❌ Помилка при лайку постів: {e}")
                    
                # Затримка між етапами
                self.logger.info("⏳ Затримка між етапами...")
                self.human_like_delay(15, 25)
            
            # 2. ЕТАП 2: Сторіс (якщо увімкнено)
            story_success = False
            if actions_config.get('like_stories', True) or actions_config.get('reply_stories', True):
                self.logger.info("📱 === ЕТАП 2: СТОРІС (ЛАЙК + ВІДПОВІДЬ) ===")
                try:
                    story_success = self.process_story_with_config(target_username, messages, actions_config)
                    if story_success:
                        success_count += 1
                        self.logger.info("✅ Сторіс успішно оброблена")
                    else:
                        self.logger.warning("❌ Сторіс не оброблена або не знайдена")
                except Exception as e:
                    self.logger.error(f"❌ Помилка при роботі зі сторіс: {e}")
                    
            # 3. ЕТАП 3: Fallback - Direct Message (якщо увімкнено і сторіс не спрацювала)
            if not story_success and actions_config.get('send_direct_message', True):
                self.logger.info("💬 === ЕТАП 3: FALLBACK - DIRECT MESSAGE ===")
                self.human_like_delay(10, 15)
                
                try:
                    if self.send_direct_message(target_username, messages):
                        success_count += 1
                        self.logger.info("✅ Direct Message відправлено успішно")
                    else:
                        self.logger.warning("❌ Direct Message не відправлено")
                except Exception as e:
                    self.logger.error(f"❌ Помилка при відправці Direct Message: {e}")
            
            # Підсумок для цього користувача
            success_rate = (success_count / total_actions) * 100
            
            self.logger.info("📊 === ПІДСУМОК ДЛЯ КОРИСТУВАЧА ===")
            
            if success_count == total_actions:
                self.logger.info(f"🎉 Користувач @{target_username} - ПОВНІСТЮ завершено: {success_count}/{total_actions} дій ({success_rate:.1f}%)")
            elif success_count > 0:
                self.logger.info(f"⚠️ Користувач @{target_username} - ЧАСТКОВО завершено: {success_count}/{total_actions} дій ({success_rate:.1f}%)")
            else:
                self.logger.error(f"❌ Користувач @{target_username} - НЕ ВИКОНАНО: {success_count}/{total_actions} дій ({success_rate:.1f}%)")
            
            # Детальна статистика
            actions_status = {
                "📸 Лайк постів": "✅" if actions_config.get('like_posts', True) and success_count >= 1 else "❌",
                "📱 Сторіс": "✅" if story_success else "❌", 
                "💬 Повідомлення": "✅" if not story_success and success_count >= 2 else "❌"
            }
            
            self.logger.info("📋 Детальна статистика:")
            for action, status in actions_status.items():
                self.logger.info(f"  {status} {action}")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ Критична помилка для користувача @{target_username}: {e}")
            return False

    def process_story_with_config(self, target_username, messages, actions_config):
        """Обробка сторіс з урахуванням конфігурації"""
        try:
            # Прямий перехід на профіль цільового користувача
            profile_url = f"https://www.instagram.com/{target_username}/"
            self.driver.get(profile_url)
            self.logger.info(f"📍 Прямий перехід на профіль {target_username}")
            self.human_like_delay(2, 3)

            # Пошук аватара зі сторіс
            story_avatar_selectors = [
                "button canvas[style*='border']",
                "div[style*='border'] button", 
                "img[style*='border']",
                "button[aria-label*='story']",
                "div[role='button'][tabindex='0']"
            ]
            
            story_avatar = None
            for selector in story_avatar_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            story_avatar = element
                            self.logger.info(f"📱 Знайдено аватар зі сторіс: {selector}")
                            break
                    if story_avatar:
                        break
                except Exception as e:
                    self.logger.debug(f"Помилка пошуку сторіс через селектор {selector}: {e}")
                    continue
            
            if not story_avatar:
                self.logger.info(f"📭 Активних сторіс у {target_username} не знайдено")
                return False
                
            # Відкриття сторіс
            self.logger.info(f"🎬 Відкриття сторіс {target_username}")
            try:
                story_avatar.click()
            except:
                self.driver.execute_script("arguments[0].click();", story_avatar)
            self.human_like_delay(1, 2)

            story_actions_completed = 0

            # Лайк сторіс (якщо увімкнено)
            if actions_config.get('like_stories', True):
                story_liked = False
                like_selectors = [
                    "svg[aria-label='Like']",
                    "svg[aria-label='Подобається']",
                    "button[aria-label*='Like']",
                    "span[role='button'] svg[aria-label*='Like']"
                ]
                
                for selector in like_selectors:
                    try:
                        like_button = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if 'Unlike' not in (like_button.get_attribute('aria-label') or ''):
                            like_button.click()
                            story_liked = True
                            story_actions_completed += 1
                            self.logger.info("❤️ Поставлено лайк сторіс")
                            break
                    except:
                        continue

                if not story_liked:
                    self.logger.warning("⚠️ Не вдалося поставити лайк сторіс")

            # Відповідь на сторіс (якщо увімкнено)
            if actions_config.get('reply_stories', True):
                story_replied = False
                reply_selectors = [
                    "textarea[placeholder*='Send message']",
                    "textarea[placeholder*='Reply']",
                    "div[contenteditable='true'][aria-label*='Message']",
                    "textarea[placeholder*='Надіслати повідомлення']"
                ]
                
                for selector in reply_selectors:
                    try:
                        reply_input = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        message = random.choice(messages)
                        reply_input.clear()
                        
                        # ШВИДКЕ введення повідомлення для сторіс
                        self.fast_typing(reply_input, message)
                        self.logger.info(f"💬 Введено відповідь: {message}")
                        
                        # Пошук кнопки Send (знаходиться справа від поля вводу) - ОРИГІНАЛЬНА ЛОГІКА
                        send_button_found = False
                        
                        # Спочатку шукаємо кнопку відносно поля вводу
                        try:
                            # Знаходимо батьківський контейнер поля вводу
                            parent_container = reply_input.find_element(By.XPATH, "./..")
                            
                            # Шукаємо кнопку Send в тому ж контейнері
                            send_selectors_relative = [
                                ".//button[contains(@aria-label, 'Send')]",
                                ".//button[contains(@aria-label, 'Надіслати')]",
                                ".//div[@role='button'][contains(@tabindex, '0')]//svg",
                                ".//button[contains(@type, 'submit')]",
                                ".//button[.//*[name()='svg']]"
                            ]
                            
                            for selector in send_selectors_relative:
                                try:
                                    send_button = parent_container.find_element(By.XPATH, selector)
                                    if send_button.is_displayed():
                                        send_button.click()
                                        send_button_found = True
                                        self.logger.info("📤 Натиснуто кнопку Send (відносний пошук)")
                                        break
                                except:
                                    continue
                                    
                        except Exception as e:
                            self.logger.debug(f"Помилка відносного пошуку: {e}")
                        
                        # Якщо відносний пошук не спрацював, шукаємо глобально
                        if not send_button_found:
                            send_selectors = [
                                "button[aria-label*='Send']",
                                "button[aria-label*='Надіслати']",
                                "div[role='button'][tabindex='0'] svg[aria-label*='Send']",
                                "div[role='button'][tabindex='0'] svg[aria-label*='Надіслати']",
                                "button[type='submit']",
                                "svg[aria-label*='Send']",
                                "svg[aria-label*='Надіслати']",
                                "button:has(svg[aria-label*='Send'])",
                                "button:has(svg[aria-label*='Надіслати'])",
                                # Додаткові селектори для кнопки Send
                                "button svg[viewBox*='24'][fill*='#']",  # Типова іконка відправки
                                "div[role='button'] svg[d*='M1.101']",   # Специфічна іконка Send Instagram
                                "button[style*='cursor: pointer']",      # Активна кнопка
                            ]
                            
                            for send_selector in send_selectors:
                                try:
                                    send_button = WebDriverWait(self.driver, 2).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, send_selector))
                                    )
                                    if send_button.is_displayed():
                                        send_button.click()
                                        send_button_found = True
                                        self.logger.info("📤 Натиснуто кнопку Send (глобальний пошук)")
                                        break
                                except:
                                    continue
                        
                        # Якщо кнопка Send не знайдена, шукаємо наступний елемент після поля вводу
                        if not send_button_found:
                            try:
                                # Шукаємо наступний сусідній елемент
                                next_sibling = reply_input.find_element(By.XPATH, "./following-sibling::*[1]")
                                if next_sibling.tag_name in ['button', 'div'] and next_sibling.is_displayed():
                                    next_sibling.click()
                                    send_button_found = True
                                    self.logger.info("📤 Натиснуто сусідній елемент (кнопка Send)")
                            except:
                                pass
                        
                        # Останній варіант - Ctrl+Enter для відправки
                        if not send_button_found:
                            reply_input.send_keys(Keys.TAB + Keys.RETURN)
                            self.logger.info("📤 Відправлено через Ctrl+Enter")
                        
                        story_replied = True
                        story_actions_completed += 1
                        self.logger.info(f"✅ Відправлено відповідь на сторіс: {message}")
                        break
                        
                    except Exception as e:
                        continue

                if not story_replied:
                    self.logger.warning("⚠️ Не вдалося відправити відповідь на сторіс")

            # ВАЖЛИВО: ЧЕКАЄМО 5 СЕКУНД ПІСЛЯ ВСІХ ДІЙ
            self.logger.info("⏳ Обов'язкове очікування 5 секунд після всіх дій в сторіс...")
            time.sleep(5)
            self.logger.info("✅ Очікування завершено")

            # Закриття сторіс (тільки після очікування)
            close_selectors = [
                "svg[aria-label='Close']",
                "button[aria-label='Close']",
                "div[role='button'][tabindex='0']"
            ]
            
            for selector in close_selectors:
                try:
                    close_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    close_button.click()
                    self.logger.info("🚪 Сторіс закрита")
                    break
                except:
                    continue
            else:
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                self.logger.info("🚪 Сторіс закрита через ESC")

            return story_actions_completed > 0

        except Exception as e:
            self.logger.error(f"❌ Помилка при обробці сторіс: {str(e)}")
            return False

    # Підтримка старого API для зворотної сумісності
    def run_automation(self, target_username, messages):
        """Запуск автоматизації з оптимізованою логікою (старий API)"""
        try:
            # Якщо передано один користувач як рядок
            if isinstance(target_username, str) and ',' not in target_username and ';' not in target_username and '\n' not in target_username:
                self.logger.info(f"🚀 Початок автоматизації для {target_username}")
                
                # Вхід в систему
                if not self.login():
                    self.logger.error("❌ Помилка входу в систему")
                    return False
                
                # Виконуємо для одного користувача
                return self.run_single_user_automation(target_username, messages)
            else:
                # Якщо передано багато користувачів, використовуємо новий метод  
                return self.run_automation_multiple_users(target_username, messages)
                
        except Exception as e:
            self.logger.error(f"❌ Критична помилка при автоматизації: {e}")
            return False
        finally:
            # Завершальні дії
            try:
                self.logger.info("🔚 Завершення сесії...")
                self.human_like_delay(2, 5)
            except:
                pass
            
    def close(self):
        """Закриття драйвера та профілю"""
        if hasattr(self, "driver") and self.driver:
            self.driver.quit()
            self.driver = None
        
        # Закриття Dolphin профілю
        if self.dolphin_manager and self.browser_type == "dolphin anty":
            try:
                self.dolphin_manager.stop_profile(self.username)
                self.logger.info(f"🐬 Dolphin профіль {self.username} зупинено")
            except Exception as e:
                self.logger.error(f"Помилка закриття Dolphin профілю: {e}")

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass  # Ігноруємо будь-які помилки при знищенні об'єкта


# Приклад використання з багатьма користувачами
if __name__ == "__main__":
    # Налаштування для роботи
    USERNAME = "your_username"
    PASSWORD = "your_password"
    
    # === ПРИКЛАДИ РІЗНИХ СПОСОБІВ ВВЕДЕННЯ КОРИСТУВАЧІВ ===
    
    # Варіант 1: Один користувач (старий спосіб)
    SINGLE_USER = "target_username"
    
    # Варіант 2: Багато користувачів через кому
    MULTIPLE_USERS_COMMA = "user1, user2, user3, user4, user5"
    
    # Варіант 3: Багато користувачів через крапку з комою
    MULTIPLE_USERS_SEMICOLON = "user1; user2; user3; user4; user5"
    
    # Варіант 4: Багато користувачів кожен з нового рядка
    MULTIPLE_USERS_NEWLINE = """user1
user2
user3
user4
user5"""
    
    # Варіант 5: Багато користувачів через пробіл
    MULTIPLE_USERS_SPACE = "user1 user2 user3 user4 user5"
    
    # Варіант 6: З символами @ (будуть видалені автоматично)
    MULTIPLE_USERS_AT = "@user1, @user2, @user3, @user4, @user5"
    
    # Виберіть потрібний варіант
    TARGET_USERS = MULTIPLE_USERS_COMMA  # Змініть на потрібний варіант
    
    MESSAGES = [
        "Привіт! Як справи? 😊",
        "Гарний пост! 👍",
        "Дякую за цікавий контент! 🙏",
        "Супер фото! 📸",
        "Вітаю! 🎉",
        "Класно! 🔥",
        "Дуже круто! ⭐",
        "Чудово! 💫",
        # Багаторядкові повідомлення з гарним форматуванням:
        """Привіт! 😊
Дуже сподобався твій пост!
Продовжуй у тому ж дусі! 👍""",
        
        """Класний контент! 🔥
Чекаю на нові пости
Так тримати! ⭐""",
        
        """Wow! Amazing content! 🤩
Keep up the great work
Looking forward to more! 💯""",
        
        """Супер! 
Дуже цікаво! 
Дякую за натхнення! ✨"""
    ]
    
    # Створення та запуск бота
    bot = InstagramBot(USERNAME, PASSWORD)
    
    try:
        print("🚀 ПОВНІСТЮ ОНОВЛЕНИЙ Instagram Bot з підтримкою ВСІХ типів сторінок входу")
        print("=" * 80)
        print("🔧 НОВІ МОЖЛИВОСТІ:")
        print("✅ Третій тип сторінки входу (Bloks UI) з aria-label='Увійти'")
        print("✅ Розумне виключення кнопок 'показати пароль'")
        print("✅ Потрійний fallback механізм для входу")
        print("✅ Покращена надійність входу")
        print("=" * 80)
        print("📋 Підтримувані типи сторінок входу:")
        print("  🎯 Тип 1: Нова версія (input[name='username'] + button[type='submit'])")
        print("  🎯 Тип 2: Стара версія (aria-label + div[role='button'])")
        print("  🎯 Тип 3: Bloks UI (data-bloks-name + aria-label='Увійти') ← НОВИЙ!")
        print("=" * 80)
        print("📋 Багатокористувацькі можливості:")
        print("✅ Один користувач: просто вкажіть ім'я")
        print("✅ Багато користувачів: через кому, крапку з комою, пробіл або новий рядок")
        print("✅ Автоматичне видалення символів @ з імен")
        print("✅ Послідовна обробка: користувач1 (всі дії) → користувач2 (всі дії) → ...")
        print("✅ Детальні логи для кожного користувача")
        print("✅ Безпечні затримки між користувачами")
        print("=" * 80)
        print("📋 План дій для кожного користувача:")
        print("1. 📸 Лайк постів: профіль → пост1 → лайк → назад → пост2 → лайк → назад")
        print("2. 📱 Сторіс: на профілі натиснути аватарку → лайк → відповідь")
        print("3. 💬 Fallback: якщо сторіс немає → Direct Messages → Next → повідомлення")
        print("=" * 80)
        
        # Запуск автоматизації
        success = bot.run_automation(TARGET_USERS, MESSAGES)
        
        print("=" * 80)
        if success:
            print("🎉 Автоматизація завершена успішно! Перевірте деталі в логах.")
            print("✅ Всі типи сторінок входу підтримуються!")
        else:
            print("❌ Автоматизація завершена з помилками!")
            print("💡 Спробуйте ще раз - бот автоматично визначить тип сторінки")
        print("=" * 80)
            
    except KeyboardInterrupt:
        print("\n⚠️ Автоматизацію перервано користувачем")
        
    except Exception as e:
        print(f"❌ Помилка при запуску бота: {e}")
        
    finally:
        bot.close()
        print("🔚 Бот закрито")
