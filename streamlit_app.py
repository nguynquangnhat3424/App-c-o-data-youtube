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
import shutil

def download_chromedriver(url, local_path):
    # Tải xuống chromedriver từ URL và lưu vào đường dẫn cục bộ
    response = requests.get(url, stream=True)
    with open(local_path, 'wb') as file:
        shutil.copyfileobj(response.raw, file)
    del response

def layscript(browser, url):
    print("Initiating scrape for youtube transcript")
    
    def extract_video_id(url):
        # Sử dụng regex để tìm video ID
        match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid YouTube URL")

    # Trích xuất video ID từ URL
    video_id = extract_video_id(url)

    # Danh sách các ngôn ngữ ưu tiên
    languages_priority = ['vi', 'en', 'fr', 'es']  # Thử tiếng Việt, Anh, Pháp, Tây Ban Nha

    transcript = None

    # Thử lấy transcript với từng ngôn ngữ trong danh sách
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
    
    # Loại bỏ "[âm nhạc]" khỏi transcript nếu tìm thấy
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

    # Tải chromedriver từ GitHub
    chromedriver_url = "https://raw.githubusercontent.com/nguynquangnhat3424/App-scrape-data-youtube/main/drivers/chromedriver.exe"
    local_chromedriver_path = "chromedriver.exe"
    download_chromedriver(chromedriver_url, local_chromedriver_path)

    # Khởi tạo trình duyệt
    service = Service(local_chromedriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("disable-extensions")
    options.add_argument("headless")
    options.add_argument("--mute-audio")
    
    browser = webdriver.Chrome(service=service, options=options)
    print("Browser started successfully")

    # Mở trang youtube
    browser.get(url)
    print("Youtube search page loaded successfully")

    time.sleep(4)
    
    # Scroll trang xuống để tải thêm video
    last_height = browser.execute_script("return document.documentElement.scrollHeight")

    while len(browser.find_elements(By.CSS_SELECTOR, 'ytd-video-renderer')) < so_video:
        browser.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(2)  # Chờ một chút để trang tải thêm nội dung

        new_height = browser.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            break  # Nếu không có thêm nội dung mới thì dừng lại
        last_height = new_height

    videos = browser.find_elements(By.CSS_SELECTOR, 'ytd-video-renderer')[:so_video]

    # Cập nhật thanh tiến độ
    progress_bar = st.progress(0)

    # Tính tỷ lệ mỗi khi duyệt một video (0 đến 1)
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

        # Lấy transcript sau khi xử lý URL
        transcript = layscript(browser, video_url)
        video_data[index]['Transcript'] = transcript

        # Cập nhật thanh tiến độ sau mỗi lần duyệt xong một video (giá trị từ 0 đến 1)
        progress_bar.progress(min((index + 1) * step, 1))

    # Tạo DataFrame
    df = pd.DataFrame(video_data, columns=['Tiêu đề', 'Ngày đăng', 'Lượt xem', 'url', 'Transcript'])

    # Đóng trình duyệt
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
        
        # Hiển thị DataFrame trên giao diện web
        st.dataframe(df)

        # Tạo file Excel và cung cấp link tải về
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
