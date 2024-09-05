
Lỗi FileNotFoundError trong môi trường Streamlit Cloud có thể xảy ra do một số vấn đề liên quan đến việc tải và sử dụng chromedriver. Dưới đây là một số cách giải quyết và hướng dẫn cụ thể để khắc phục vấn đề này:

1. Đảm bảo chromedriver Được Tải Về Đúng Cách
Trước tiên, hãy kiểm tra lại đoạn mã tải về chromedriver để đảm bảo rằng nó hoạt động đúng trong môi trường của bạn. Hãy chắc chắn rằng chromedriver được tải về và lưu đúng đường dẫn.

python
Sao chép mã
def download_chromedriver():
    url = 'https://github.com/nguynquangnhat3424/App-scrape-data-youtube/raw/main/drivers/chromedriver.exe'
    response = requests.get(url)
    if response.status_code == 200:
        with open('/tmp/chromedriver', 'wb') as file:  # Lưu vào thư mục tạm thời
            file.write(response.content)
        return '/tmp/chromedriver'
    else:
        raise Exception("Failed to download chromedriver")
2. Sử Dụng Đường Dẫn Chính Xác
Đảm bảo rằng đường dẫn đến chromedriver là chính xác và có quyền thực thi trong môi trường Streamlit Cloud. Sử dụng đường dẫn /tmp/chromedriver hoặc đường dẫn phù hợp với môi trường mà bạn đang chạy.

3. Thiết Lập Quyền Thực Thi
Sau khi tải về chromedriver, bạn cần đảm bảo rằng nó có quyền thực thi. Trong mã của bạn, hãy thêm đoạn mã để thay đổi quyền:

python
Sao chép mã
import os

def download_chromedriver():
    url = 'https://github.com/nguynquangnhat3424/App-scrape-data-youtube/raw/main/drivers/chromedriver.exe'
    response = requests.get(url)
    if response.status_code == 200:
        path = '/tmp/chromedriver'
        with open(path, 'wb') as file:
            file.write(response.content)
        os.chmod(path, 0o755)  # Cấp quyền thực thi
        return path
    else:
        raise Exception("Failed to download chromedriver")
4. Sử Dụng headless Mode
Đảm bảo rằng bạn đang sử dụng chế độ headless để tránh việc giao diện đồ họa không hoạt động trong môi trường máy chủ.

python
Sao chép mã
options = webdriver.ChromeOptions()
options.add_argument("disable-extensions")
options.add_argument("headless")
options.add_argument("--mute-audio")
5. Kiểm Tra Phiên Bản chromedriver và Chrome
Đảm bảo rằng phiên bản của chromedriver và trình duyệt Chrome tương thích. Bạn có thể cần cập nhật chromedriver hoặc sử dụng một phiên bản khác của Chrome nếu cần.

6. Kiểm Tra Log Chi Tiết
Xem chi tiết log lỗi trong Streamlit Cloud để xác định nguyên nhân cụ thể của lỗi. Truy cập vào phần "Manage app" và xem log để biết thêm thông tin về vấn đề gặp phải.

7. Tạo Một Tệp requirements.txt
Đảm bảo rằng bạn có tệp requirements.txt để cài đặt các thư viện cần thiết, bao gồm selenium và requests:

makefile
Sao chép mã
selenium==4.8.0
requests==2.28.2
Ví dụ Code Đã Cập Nhật
Dưới đây là ví dụ code đã cập nhật với các bước trên:

python
Sao chép mã
import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import urllib.parse
import time
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled, VideoUnavailable
import re
import requests
import os

def download_chromedriver():
    url = 'https://github.com/nguynquangnhat3424/App-scrape-data-youtube/raw/main/drivers/chromedriver.exe'
    response = requests.get(url)
    if response.status_code == 200:
        path = '/tmp/chromedriver'
        with open(path, 'wb') as file:
            file.write(response.content)
        os.chmod(path, 0o755)
        return path
    else:
        raise Exception("Failed to download chromedriver")

def layscript(browser, url):
    print("Initiating scrape for youtube transcript")
    
    def extract_video_id(url):
        match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid YouTube URL")

    video_id = extract_video_id(url)

    languages_priority = ['vi', 'en', 'fr', 'es']

    transcript = None

    try:
        for language in languages_priority:
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
                transcript = ' '.join([item['text'] for item in transcript_list])
                print(f"Transcript found in language: {language}")
                break
            except NoTranscriptFound:
                print(f"No transcript found in language: {language}")
        if not transcript:
            transcript = "video không tìm thấy script"
    except (TranscriptsDisabled, VideoUnavailable, Exception) as e:
        print(f"An error occurred: {e}")
        transcript = "video không tìm thấy script"
    
    transcript = transcript.replace("[âm nhạc]", "") if transcript else "video không tìm thấy script"
    
    return transcript

def generate_youtube_search_url(search_query):
    encoded_query = urllib.parse.quote(search_query)
    base_url = "https://www.youtube.com/results?search_query="
    sp_param = "&sp=EgYIBBABGAM%253D"
    full_url = f"{base_url}{encoded_query}{sp_param}"
    return full_url

def layscript_theo_keyword(search_query, so_video):
    url = generate_youtube_search_url(search_query)

    video_data = []

    # Tải về và thiết lập chromedriver
    chromedriver_path = download_chromedriver()
    service = Service(chromedriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("disable-extensions")
    options.add_argument("headless")
    options.add_argument("--mute-audio")
    
    browser = webdriver.Chrome(service=service, options=options)
    print("Browser started successfully")

    browser.get(url)
    print("Youtube search page loaded successfully")

    time.sleep(4)
    
    last_height = browser.execute_script("return document.documentElement.scrollHeight")

    while len(browser.find_elements(By.CSS_SELECTOR, 'ytd-video-renderer')) < so_video:
        browser.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(2)

        new_height = browser.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    videos = browser.find_elements(By.CSS_SELECTOR, 'ytd-video-renderer')[:so_video]

    progress_bar = st.progress(0)
    step = 1 / so_video

    for index, video in enumerate(videos):
        title_element = video.find_element(By.CSS_SELECTOR, 'yt-formatted-string[aria-label]')
        title = title_element.text

        video_url_element = video.find_element(By.CSS_SELECTOR, 'a#thumbnail')
        video_url = video_url_element.get_attribute('href')

        metadata_elements = video.find_elements(By.CSS_SELECTOR, 'span.inline-metadata-item.style-scope.ytd-video-meta-block')
        
        if len(metadata_elements) >= 2:
            views = metadata_elements[0].text
            upload_date = metadata_elements[1].text
        else:
            views = 'N/A'
            upload_date = 'N/A'

        video_data.append({
            'Tiêu đề': title,
            'Ngày đăng': upload_date,
            'Lượt xem': views,
            'url': video_url
        })

        transcript = layscript(browser, video_url)
        video_data[index]['Transcript'] = transcript

        progress_bar.progress(min((index + 1) * step, 1))

    df = pd.DataFrame(video_data, columns=['Tiêu đề', 'Ngày đăng', 'Lượt xem', 'url', 'Transcript'])

    browser.quit()

    return df

def main():
    st.title("YouTube Data Scraper")

    search_query = st.text_input("Nhập từ khóa:")
    so_video = st.number_input("Số lượng video muốn cào:", min_value=1, max_value=50, value=1)

    if st.button("Chạy"):
        with st.spinner("Đang cào dữ liệu..."):
            df = layscript_theo_keyword(search_query, so_video)
        
        st.success("Cào dữ liệu hoàn tất!")
        
        st.dataframe(df)

        excel_filename = f"youtube_data.xlsx"
        df.to_excel(excel_filename, index=False)
        
        with open(excel_filename, "rb") as file:
            st.download_button(
                label="Tải về file Excel",
                data=file,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
