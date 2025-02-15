import crawler
import time

def get_login_info(file_path):
    id = None
    pw = None
    
    f = open(file_path, "r")
    lines = f.readlines()

    id = lines[0].strip()
    pw = lines[1].strip()
    
    if id is not None and pw is not None:
        return id, pw
    else:
        print("id, pw 정보가 없습니다.")
        exit()
    
if __name__ == "__main__":
    id, pw = get_login_info("login_info.txt")
    crawler = crawling.Crawler(login_id = id, login_pw = pw)
    crawler.start_driver()
    crawler.login_univstore()
    time.sleep(1)
    crawler.get_macbook_info_in_univstore()
    crawler.quit_driver()