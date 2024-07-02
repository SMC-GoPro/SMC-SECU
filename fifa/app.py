from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from collections import Counter

app = Flask(__name__)

def fetch_user_profiles(team_name):
    driver_path = r'D:\fifa\chromedriver-win64\chromedriver.exe'
    options = Options()
    options.add_argument('--headless')
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get('https://fconline.nexon.com/datacenter/rank')

        team_color_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'tc_01_view'))
        )
        team_color_button.click()

        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'search_tc'))
        )
        search_input.send_keys(team_name)
        search_input.send_keys(Keys.RETURN)

        time.sleep(1)

        search_results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='search_result']/button"))
        )
        first_result_button = search_results[0]
        first_result_button.click()

        complete_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'btn_teamcolor_complete'))
        )
        complete_button.click()

        time.sleep(1)

        detail_search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn_search') and contains(text(), '상세 검색')]"))
        )
        detail_search_button.click()

        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        user_profiles = []
        formations = []
        current_page = 1
        max_pages = 5
        
        while current_page <= max_pages:
            user_elements = soup.select('div.tbody > div.tr')
            for user_elem in user_elements:
                try:
                    nickname_elem = user_elem.find('span', {'class': 'name profile_pointer'})
                    rank_elem = user_elem.find('span', {'class': 'td rank_no'})
                    formation_elem = user_elem.find('span', {'class': 'td formation'})

                    if nickname_elem and rank_elem and formation_elem:
                        nickname = nickname_elem.text.strip()
                        rank = rank_elem.text.strip()
                        formation = formation_elem.text.strip()

                        user_profiles.append({
                            'nickname': nickname,
                            'rank': rank,
                            'formation': formation
                        })
                        
                        formations.append(formation)

                except Exception as e:
                    print(f"유저 정보를 가져오는 중 에러 발생: {e}")
                    continue
            
            current_page += 1
            if current_page <= max_pages:
                try:
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//a[contains(@class, 'btn_num') and text()='{current_page}']"))
                    )
                    next_button.click()
                    time.sleep(2)

                    soup = BeautifulSoup(driver.page_source, 'html.parser')

                except Exception as e:
                    print(f"다음 페이지로 이동하는 중 에러 발생: {e}")
                    break
        
        formation_counts = Counter(formations)
        most_common_formations = formation_counts.most_common()
        total_other_formations = sum(count for formation, count in most_common_formations[10:])

        return user_profiles, most_common_formations[:10], total_other_formations

    finally:
        driver.quit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        team_name = request.form['team_name']
        user_profiles, most_common_formations, total_other_formations = fetch_user_profiles(team_name)
        return render_template('result.html', team_name=team_name, user_profiles=user_profiles, most_common_formations=most_common_formations, total_other_formations=total_other_formations)
    return render_template('index.html')

# enumerate를 Jinja2 템플릿에서 사용할 수 있도록 추가
app.jinja_env.globals.update(enumerate=enumerate)

if __name__ == "__main__":
    app.run(debug=True)
