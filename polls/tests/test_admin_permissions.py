# polls/tests/test_admin_permissions.py
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User, Group, Permission
from django.urls import reverse
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import shutil, os


def _find_chromium_binary():
    candidates = [
        os.environ.get("CHROMIUM_BIN"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


class ReadOnlyStaffPollsTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chromium_bin = _find_chromium_binary()
        if not chromium_bin:
            raise RuntimeError(
                "No se encontró Chromium. Instala 'chromium' (o 'chromium-browser') "
                "y 'chromium-driver'. Ej.: sudo apt-get install -y chromium chromium-driver"
            )

        opts = ChromeOptions()
        opts.binary_location = chromium_bin
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1280,900")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        cls.selenium = Chrome(options=opts)
        cls.wait = WebDriverWait(cls.selenium, 20)

        # Superusuario
        su = User.objects.create_user("isard", "isard@isardvdi.com", "pirineus")
        su.is_superuser = True
        su.is_staff = True
        su.save()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.selenium.quit()
        finally:
            super().tearDownClass()

    
    def admin_login(self, username, password):
        self.selenium.get(f"{self.live_server_url}{reverse('admin:login')}")
        self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
        self.selenium.find_element(By.NAME, "username").clear()
        self.selenium.find_element(By.NAME, "username").send_keys(username)
        self.selenium.find_element(By.NAME, "password").clear()
        self.selenium.find_element(By.NAME, "password").send_keys(password)
        self.selenium.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

        def logged_in_or_error(driver):
            if driver.find_elements(By.CSS_SELECTOR, 'a[href*="logout"]'):
                return True
            if driver.find_elements(By.CSS_SELECTOR, "#user-tools"):
                return True
            if driver.title.lower().startswith("site administration"):
                return True
            if driver.find_elements(By.CSS_SELECTOR, ".errornote, ul.errorlist"):
                raise AssertionError("Error de login: credenciales incorrectas.")
            return False

        self.wait.until(logged_in_or_error)

    def admin_logout(self):
        """Salir del admin y garantizar que terminamos en la pantalla de login."""
        self.selenium.get(f"{self.live_server_url}/admin/logout/")

        try:
            self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            return
        except Exception:
            pass

        links = self.selenium.find_elements(By.CSS_SELECTOR, 'a[href$="/admin/login/"]')
        if links:
            links[0].click()

        if "/admin/login/" not in self.selenium.current_url:
            self.selenium.get(f"{self.live_server_url}/admin/login/")

        self.wait.until(EC.presence_of_element_located((By.NAME, "username")))

    def open_questions_changelist(self):
        """Abre la lista de Questions (relogin si hace falta)."""
        self.selenium.get(f"{self.live_server_url}/admin/polls/question/")
        if "/admin/login/" in self.selenium.current_url:
            self.admin_login("isard", "pirineus")
            self.selenium.get(f"{self.live_server_url}/admin/polls/question/")
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#changelist")))

    def open_question_add_form(self, as_user="isard", pwd="pirineus"):
        """Abre directamente el formulario de creación de Question."""
        self.selenium.get(f"{self.live_server_url}/admin/polls/question/add/")
        if "/admin/login/" in self.selenium.current_url:
            self.admin_login(as_user, pwd)
            self.selenium.get(f"{self.live_server_url}/admin/polls/question/add/")
        self.wait.until(EC.presence_of_element_located((By.NAME, "question_text")))

    # ---------- test principal ----------
    def test_staff_read_only_flow(self):
        # 1) Superusuario crea 2 Questions con 2 Choices
        self.admin_login("isard", "pirineus")

        # --- Question 1 ---
        self.open_questions_changelist()
        self.open_question_add_form()
        self.selenium.find_element(By.NAME, "question_text").send_keys("¿Color favorito?")
        self.selenium.find_element(By.NAME, "pub_date_0").clear()
        self.selenium.find_element(By.NAME, "pub_date_0").send_keys("2025-10-29")
        self.selenium.find_element(By.NAME, "pub_date_1").clear()
        self.selenium.find_element(By.NAME, "pub_date_1").send_keys("12:00:00")
        self.selenium.find_element(By.NAME, "choice_set-0-choice_text").send_keys("Azul")
        self.selenium.find_element(By.NAME, "choice_set-1-choice_text").send_keys("Verde")
        self.selenium.find_element(By.NAME, "_save").click()
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.success")))

        # --- Question 2 ---
        self.open_questions_changelist()
        self.open_question_add_form()
        self.selenium.find_element(By.NAME, "question_text").send_keys("¿Comida favorita?")
        self.selenium.find_element(By.NAME, "pub_date_0").clear()
        self.selenium.find_element(By.NAME, "pub_date_0").send_keys("2025-10-29")
        self.selenium.find_element(By.NAME, "pub_date_1").clear()
        self.selenium.find_element(By.NAME, "pub_date_1").send_keys("12:05:00")
        self.selenium.find_element(By.NAME, "choice_set-0-choice_text").send_keys("Pasta")
        self.selenium.find_element(By.NAME, "choice_set-1-choice_text").send_keys("Pizza")
        self.selenium.find_element(By.NAME, "_save").click()
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.success")))

        # 2) Grupo + usuario staff 
        viewers, _ = Group.objects.get_or_create(name="Polls Viewers")
        viewers.permissions.add(
            Permission.objects.get(codename="view_question"),
            Permission.objects.get(codename="view_choice"),
        )
        lector = User.objects.create_user("lector", "lector@example.com", "LectorSegur0!")
        lector.is_staff = True
        lector.is_superuser = False
        lector.save()
        lector.groups.add(viewers)

        # 3) Login como lector y verificaciones
        self.admin_logout()
        self.admin_login("lector", "LectorSegur0!")
        self.open_questions_changelist()

        rows = self.selenium.find_elements(By.CSS_SELECTOR, "#changelist-form tbody tr")
        assert len(rows) >= 2, "El usuario lector debería ver al menos 2 Questions."

        assert not self.selenium.find_elements(By.CSS_SELECTOR, "a.addlink"), \
            "lector no debería ver el botón Add."

        rows[0].find_element(By.CSS_SELECTOR, "th a").click()
        for name in ["_save", "_addanother", "_continue"]:
            assert not self.selenium.find_elements(By.NAME, name), \
                f"Botón {name} no debería aparecer para lector."
