import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
import urllib.parse
import time
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled, VideoUnavailable
import re

def layscript(page, url):
    print("Initiating scrape for YouTube transcript")

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
            transcript = "Video không tìm thấy transcript"
    except (TranscriptsDisabled, VideoUnavailable, Exception) as e:
        print(f"An error occurred: {e}")
        transcript = "Video không tìm thấy transcript"
    
    # Loại bỏ "[âm nhạc]" khỏi transcript nếu tìm thấy
    transcript = transcript.replace("[âm nhạc]", "") if transcript else "Video không tìm thấy transcript"
    
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

    # Khởi tạo Playwright
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--mute-audio"])
            page = browser.new_page()
            page.goto(url)
            print("YouTube search page loaded successfully")

            time.sleep(4)

            last_height = page.evaluate("document.documentElement.scrollHeight")

            while len(page.query_selector_all('ytd-video-renderer')) < so_video:
                page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(2)

                new_height = page.evaluate("document.documentElement.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            videos = page.query_selector_all('ytd-video-renderer')[:so_video]

            if not videos:
                print("No videos found on the page.")
            
            # Cập nhật thanh tiến độ
            progress_bar = st.progress(0)
            step = 1 / so_video

            for index, video in enumerate(videos):
                title_element = video.query_selector('yt-formatted-string[aria-label]')
                title = title_element.inner_text() if title_element else "No title"

                video_url_element = video.query_selector('a#thumbnail')
                video_url = video_url_element.get_attribute('href') if video_url_element else "No URL"

                metadata_elements = video.query_selector_all('span.inline-metadata-item.style-scope.ytd-video-meta-block')

                if len(metadata_elements) >= 2:
                    views = metadata_elements[0].inner_text()
                    upload_date = metadata_elements[1].inner_text()
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
                transcript = layscript(page, video_url)
                video_data[index]['Transcript'] = transcript

                # Cập nhật thanh tiến độ sau mỗi lần duyệt xong một video (giá trị từ 0 đến 1)
                progress_bar.progress(min((index + 1) * step, 1))

            # Tạo DataFrame
            df = pd.DataFrame(video_data, columns=['Tiêu đề', 'Ngày đăng', 'Lượt xem', 'url', 'Transcript'])

            browser.close()

        return df

    except Exception as e:
        print(f"An error occurred during Playwright operations: {e}")
        return pd.DataFrame()  # Trả về DataFrame rỗng nếu gặp lỗi

def main():
    st.title("YouTube Data Scraper")

    search_query = st.text_input("Nhập từ khóa:")
    so_video = st.number_input("Số lượng video muốn cào:", min_value=1, max_value=50, value=1)

    if st.button("Chạy"):
        with st.spinner("Đang cào dữ liệu..."):
            df = layscript_theo_keyword(search_query, so_video)
        
        st.success("Cào dữ liệu hoàn tất!")
        
        if not df.empty:
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
        else:
            st.warning("Không có dữ liệu để hiển thị.")

if __name__ == "__main__":
    main()
