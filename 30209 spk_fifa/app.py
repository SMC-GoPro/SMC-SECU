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
    # ChromeDriver 경로 설정
    driver_path = r'D:\fifa\chromedriver-win64\chromedriver.exe'

    # ChromeOptions 설정
    options = Options()
    # options.add_argument('--headless')  # headless 모드 설정 제거

    # ChromeDriver 서비스 설정
    service = Service(executable_path=driver_path)

    # WebDriver 초기화
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # 넥슨 피파 온라인 4 데이터 센터 페이지 열기
        driver.get('https://fconline.nexon.com/datacenter/rank')

        # 팀컬러 1 선택 버튼 클릭
        team_color_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'tc_01_view'))
        )
        team_color_button.click()

        # 팀컬러 검색 입력
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'search_tc'))
        )
        search_input.send_keys(team_name)  # 입력 받은 팀 이름 입력
        search_input.send_keys(Keys.RETURN)

        # 대기 시간 추가
        time.sleep(1)

        # 첫 번째 검색 결과 버튼 클릭
        search_results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='search_result']/button"))
        )
        first_result_button = search_results[0]  # 첫 번째 결과 버튼 선택
        first_result_button.click()

        # 팀컬러 선택 완료 버튼 클릭
        complete_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'btn_teamcolor_complete'))
        )
        complete_button.click()

        # <span>닫기</span> 요소 클릭
        try:
            close_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='닫기']"))
            )
            close_button.click()
        except Exception as e:
            print(f"닫기 버튼을 클릭하는 중 에러 발생: {e}")

        # 대기 시간 추가
        time.sleep(3)

        # 상세 검색 버튼 클릭
        detail_search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn_search') and contains(text(), '상세 검색')]"))
        )
        detail_search_button.click()

        # HTML 파싱
        time.sleep(1)  # 페이지 로드 대기
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 상위 20명의 유저 정보 수집
        user_profiles = []
        formations = []  # 포메이션 리스트 초기화
        current_page = 1
        max_pages = 5  # 최대 5페이지까지 조회
        
        while current_page <= max_pages:
            user_elements = soup.select('div.tbody > div.tr')
            for user_elem in user_elements:
                try:
                    nickname_elem = user_elem.find('span', {'class': 'name profile_pointer'})
                    rank_elem = user_elem.find('span', {'class': 'td rank_no'})
                    formation_elem = user_elem.find('span', {'class': 'td formation'})
                    win_rate_elem = user_elem.find('span', {'class': 'td rank_before'})  # 승률 요소 추가

                    if nickname_elem and rank_elem and formation_elem and win_rate_elem:
                        nickname = nickname_elem.text.strip()
                        rank = rank_elem.text.strip()
                        formation = formation_elem.text.strip()
                        win_rate = win_rate_elem.find('span', {'class': 'top'}).text.strip()  # 승률 값 추출

                        user_profiles.append({
                            'nickname': nickname,
                            'rank': rank,
                            'formation': formation,
                            'win_rate': win_rate  # 사용자 정보 객체에 승률 추가
                        })
                        
                        formations.append(formation)  # 포메이션 추가

                except Exception as e:
                    print(f"유저 정보를 가져오는 중 에러 발생: {e}")
                    continue
                
            # 다음 페이지로 이동
            current_page += 1
            if current_page <= max_pages:
                try:
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//a[contains(@class, 'btn_num') and text()='{current_page}']"))
                    )
                    next_button.click()
                    time.sleep(2)  # 페이지 로드 대기

                    # 새로운 페이지의 HTML 파싱
                    soup = BeautifulSoup(driver.page_source, 'html.parser')

                except Exception as e:
                    print(f"다음 페이지로 이동하는 중 에러 발생: {e}")
                    break
        
        # 포메이션 빈도 계산
        formation_counts = Counter(formations)
        most_common_formations = formation_counts.most_common()

        return user_profiles, most_common_formations

    finally:
        # 드라이버 종료
        driver.quit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        team_name = request.form['team_name']
        user_profiles, most_common_formations = fetch_user_profiles(team_name)
        
        # 가장 많이 사용하는 포메이션 순서대로 정렬
        most_common_formations_sorted = sorted(most_common_formations, key=lambda x: x[1], reverse=True)
        top_10_formations = most_common_formations_sorted[:10]
        remaining_count = sum(count for _, count in most_common_formations_sorted[10:])

        # 포메이션 리스트에 등수를 추가하여 정리
        ranked_formations = []
        for index, (formation, count) in enumerate(top_10_formations, 1):
            ranked_formations.append(f"{index}등 {formation} ({count}명)")
        if remaining_count > 0:
            ranked_formations.append(f"기타 {remaining_count}명")

        return render_template('result.html', team_name=team_name, user_profiles=user_profiles, 
                               top_10_formations=ranked_formations)
    
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
