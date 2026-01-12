import os
import time
import shutil
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from datetime import datetime

# ============ ユーザーが事前に設定する =============
EXCEL_FILE = "E:/ファイル/ドキュメント/x_auto_post_bot/post_data.xlsx"
IMAGE_FOLDER = "E:/ファイル/ドキュメント/x_auto_post_bot/images"
POSTED_FOLDER = os.path.join(IMAGE_FOLDER, "投稿済み")
CHROME_BINARY = "E:/ファイル/ドキュメント/x_auto_post_bot/chrome-win64/chrome.exe"
CHROMEDRIVER = "E:/ファイル/ドキュメント/x_auto_post_bot/chromedriver.exe"  # 未使用でもOK

# ============ Xのログイン情報（アカウントは固定で良いならここに直接記載） =============
USERNAME = "YOUR_X_USERNAME"
PASSWORD = "YOUR_X_PASSWORD"

# ==================================================

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def wait_mask_gone(wait):
    try:
        wait_short = WebDriverWait(wait._driver, 10)
        wait_short.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='mask']")))
    except Exception:
        pass

def dismiss_sheet_with_escape(driver):
    try:
        if driver.find_elements(By.CSS_SELECTOR, "[data-testid='mask']"):
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='mask']")))
    except Exception:
        pass

def focus_and_type(driver, element, text):
    driver.execute_script("arguments[0].focus();", element)
    time.sleep(0.2)
    element.clear()
    element.send_keys(text)

def send_ctrl_enter(driver, retries=3, wait_sec=1.0):
    actions = ActionChains(driver)
    for i in range(retries):
        actions.key_down(Keys.CONTROL).send_keys(Keys.RETURN).key_up(Keys.CONTROL).perform()
        time.sleep(wait_sec)

def post_to_x(image_filename, caption):
    driver = None
    try:
        log_message(f"投稿開始: {image_filename}")
        
        chrome_options = Options()
        chrome_options.binary_location = CHROME_BINARY
        chrome_options.add_argument("--disable-gpu")
        #chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # ドライバは自動解決（Selenium Manager）
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 30)

        # ログイン
        log_message("Xにログイン中...")
        driver.get("https://x.com/login")
        wait_mask_gone(wait); dismiss_sheet_with_escape(driver)

        username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']")))
        username_input.clear(); username_input.send_keys(USERNAME)
        time.sleep(0.5)

        next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next' or text()='次へ']")))
        next_button.click()
        wait_mask_gone(wait); time.sleep(0.5)

        password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']")))
        password_input.clear(); password_input.send_keys(PASSWORD)
        time.sleep(0.3)

        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in' or text()='ログイン']")))
        login_button.click()

        wait.until(lambda d: "/home" in d.current_url or "/compose" in d.current_url)
        time.sleep(1.0)
        log_message("ログイン完了")

        # 直接コンポーザーへ
        driver.get("https://x.com/compose/post")
        wait_mask_gone(wait); dismiss_sheet_with_escape(driver)
        log_message("投稿準備中...")

        # テキストエリア
        textarea = None
        for sel in [
            "div[role='textbox'][data-testid^='tweetTextarea']",
            "div[role='textbox'][data-testid='tweetTextarea_0']",
        ]:
            try:
                textarea = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                break
            except Exception:
                continue
        if textarea is None:
            raise Exception("投稿テキストエリアが見つかりませんでした。UI変更の可能性。")

        # クリックを避けて JS focus → 入力
        focus_and_type(driver, textarea, caption)
        time.sleep(0.5)

        # 画像アップロード
        log_message("画像アップロード中...")
        image_path = os.path.abspath(os.path.join(IMAGE_FOLDER, image_filename))
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")

        upload_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file' and @accept]")))
        upload_input.send_keys(image_path)
        time.sleep(4)

        # ★ 常に Ctrl+Enter で投稿（ボタンは探さない）
        log_message("投稿実行中...(Ctrl+Enter)")
        send_ctrl_enter(driver, retries=2, wait_sec=1.2)

        time.sleep(5)
        log_message(f"投稿完了: {image_filename}")
        return True

    except Exception as e:
        log_message(f"投稿エラー - {image_filename}: {str(e)}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def move_image_to_posted(image_filename):
    try:
        src = os.path.join(IMAGE_FOLDER, image_filename)
        dst = os.path.join(POSTED_FOLDER, image_filename)
        if os.path.exists(dst):
            name, ext = os.path.splitext(image_filename)
            counter = 1
            while os.path.exists(dst):
                new_filename = f"{name}_{counter}{ext}"
                dst = os.path.join(POSTED_FOLDER, new_filename)
                counter += 1
        shutil.move(src, dst)
        log_message(f"画像移動完了: {image_filename} → 投稿済みフォルダ")
        return True
    except Exception as e:
        log_message(f"画像移動エラー - {image_filename}: {str(e)}")
        return False

def remove_excel_row(row_index):
    try:
        df = pd.read_excel(EXCEL_FILE)
        if row_index < len(df):
            df = df.drop(df.index[row_index]).reset_index(drop=True)
            df.to_excel(EXCEL_FILE, index=False)
            log_message(f"Excel行削除完了: 行{row_index + 1}")
            return True
        else:
            log_message(f"Excel行削除エラー: 行{row_index + 1}が存在しません")
            return False
    except Exception as e:
        log_message(f"Excel行削除エラー: {str(e)}")
        return False

def main():
    try:
        log_message("プログラム開始")
        if not os.path.exists(POSTED_FOLDER):
            os.makedirs(POSTED_FOLDER)
            log_message("投稿済みフォルダを作成しました")
        if not os.path.exists(EXCEL_FILE):
            log_message(f"エラー: Excelファイルが見つかりません - {EXCEL_FILE}")
            return
        df = pd.read_excel(EXCEL_FILE)
        if df.empty:
            log_message("投稿データがありません")
            return
        required_columns = ["画像ファイル名", "キャプション"]
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            log_message(f"エラー: 必要な列が不足しています - {missing}")
            return
        row = df.iloc[0]
        image_filename = str(row["画像ファイル名"]).strip()
        caption = str(row["キャプション"]).strip()
        log_message(f"処理対象 - 画像: {image_filename}, キャプション: {caption[:30]}...")
        image_path = os.path.join(IMAGE_FOLDER, image_filename)
        if not os.path.exists(image_path):
            log_message(f"エラー: 画像ファイルが見つかりません - {image_path}")
            return

        if post_to_x(image_filename, caption):
            log_message("投稿成功 - 後処理を実行中...")
            excel_success = remove_excel_row(0)
            move_success = move_image_to_posted(image_filename)
            if excel_success and move_success:
                log_message("全ての処理が完了しました")
            else:
                log_message("一部の後処理でエラーが発生しました")
        else:
            log_message("投稿に失敗しました")
    except Exception as e:
        log_message(f"プログラム実行エラー: {str(e)}")

if __name__ == "__main__":
    main()
