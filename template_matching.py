import glob
import os
import threading
import tkinter.messagebox
import cv2
import numpy as np
import fitz
import concurrent.futures
from PIL import Image
import random
import csv
from datetime import datetime
import time
import shutil
import threading
import matplotlib.pyplot as plt

main_folder = r"受信フォルダ"
temp_folder = r"temp_folder"
temp_pics = r"template_pics"
sample_pic = r"sample_pic.png"
matching_sheet = r"matching_sheet.csv"
stop_event = threading.Event()


def template_pic_to_gray():
    template_pics = glob.glob(f"{temp_pics}*.png")
    for pic in template_pics:
        img = Image.open(pic)
        gray = img.convert("L")
        gray.save(pic)
    print("テンプレート画像のグレースケール化完了。マッチングを開始します。")


def matching_failed():
    now = datetime.now()
    formatted_time = now.strftime("%Y%m%d%H%M%S")
    failed_file = f"{main_folder}\\▼登録名称不明-{formatted_time}.pdf"
    try:
        os.rename(file, failed_file)
        print("受信フォルダをサーチ中、、、")
    except Exception:
        pass


max_val_dict = {}
dts = ""
top_val = ""


def template_matching(pic):
    global top_val, dts, max_val_dict
    renamed_pic = pic.split("/")
    renamed_pic = renamed_pic[-1].replace(".png", "")
    templ = cv2.imread(fr"{pic}")
    print(f"Matching to : <<{renamed_pic}>>")

    result = cv2.matchTemplate(img,
                               templ,
                               cv2.TM_CCOEFF_NORMED
                               )

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    thrshold = 0.72

    match_y, match_x = np.where(result >= thrshold)

    if max_val >= thrshold:
        for x, y in zip(match_x, match_y):
            if x:
                if max_val == 1.0:
                    print(f"""
                                    {renamed_pic}が100%マッチしました！
                                    """)
                    max_val_dict[pic] = max_val
                    top_val = max(max_val_dict, key=max_val_dict.get)
                    top_val = top_val.split("/")
                    top_val = top_val[7].replace(".png", "")
                    stop_event.set()
                else:
                    print(f"""
                    {renamed_pic}がマッチしました！
                    """)
                    max_val_dict[pic] = max_val
                    top_val = max(max_val_dict, key=max_val_dict.get)
                    top_val = top_val.split("/")
                    top_val = top_val[-1].replace(".png", "")

                h, w = templ.shape[:2]
                top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                cv2.rectangle(img, top_left, bottom_right, (0, 0, 255), 2)
                plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                plt.title(f"Match: {renamed_pic} with value: {max_val:.2f}")
                plt.show()
                break


def change_title():
    global top_val, dts, max_val_dict
    now = datetime.now()
    formatted_time = now.strftime("%Y%m%d%H%M%S")
    print(f"{top_val}が最も高いマッチング率でした")
    with open(matching_sheet, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if top_val in row["キーワード"]:
                new_pdf = f"{temp_folder}/{row['会社名']}-{formatted_time}.pdf"
                f.close()
                try:
                    os.rename(file, new_pdf)
                    shutil.move(new_pdf, main_folder)
                    top_val = ""
                    dts = ""
                    max_val_dict = {}
                    return
                except Exception:
                    top_val = ""
                    dts = ""
                    max_val_dict = {}
                    return


def run_in_progress_to_convert():
    while True:
        files = glob.glob(f"{main_folder}/*.pdf")
        for file in files:
            if "変換失敗" in file:
                print("変換失敗を発見しました！rename_folderへ移動します。")
                shutil.move(file, temp_folder)
        t = 2
        while t > 0:
            time.sleep(1)
            t -= 1


if __name__ == "__main__":
    in_progress_thread = threading.Thread(target=run_in_progress_to_convert, daemon=True)
    in_progress_thread.start()
    print("受信フォルダをサーチ中、、、")
    while True:
        files = glob.glob(rf"{temp_folder}/*.pdf")
        for file in files:
            print(f"{file}のリネームを開始します。")
            try:
                doc = fitz.open(file)
            except fitz.fitz.FileDataError as e:
                print(e)
                continue
            page = doc[0]
            zoom = 400 / 72
            mat = fitz.Matrix(zoom, zoom)

            image = page.get_pixmap(matrix=mat)
            image.save(sample_pic)

            PIL_img = Image.open(sample_pic)

            gray_img = PIL_img.convert("L")
            gray_img.save(sample_pic)
            doc.close()

            img = cv2.imread(sample_pic)
            template_pic_to_gray()
            pics = glob.glob(f"{temp_pics}/*.png")
            pics = random.sample(pics, len(pics))
            for pic in pics:
                template_matching(pic)
                change_title()
        t = 2
        while t > 0:
            time.sleep(1)
            t -= 1