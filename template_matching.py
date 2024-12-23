import glob
import os
import threading
import tkinter.messagebox
import cv2
import numpy as np
import fitz
from PIL import Image
import random
import csv
from datetime import datetime
import time
import shutil
import matplotlib.pyplot as plt

# 各種フォルダおよびファイルの設定
main_folder = r"受信フォルダ"  # 処理対象の受信フォルダ
temp_folder = r"temp_folder"  # 一時保存フォルダ
temp_pics = r"template_pics"  # テンプレート画像フォルダ
sample_pic = r"sample_pic.png"  # サンプル画像の保存パス
matching_sheet = r"matching_sheet.csv"  # マッチングデータを保持するCSV
stop_event = threading.Event()  # スレッド停止用のイベントオブジェクト


def template_pic_to_gray():
    """
    テンプレート画像フォルダ内の全画像をグレースケールに変換する。
    元の画像ファイルに上書き保存。
    """
    template_pics = glob.glob(f"{temp_pics}/*.png")  # フォルダ内の全PNG画像を取得
    for pic in template_pics:
        img = Image.open(pic)
        gray = img.convert("L")  # グレースケール化
        gray.save(pic)  # 元の画像に上書き保存
    print("テンプレート画像のグレースケール化完了。マッチングを開始します。")


def matching_failed():
    """
    テンプレートマッチングに失敗した場合に、ファイル名を変更して失敗フォルダに移動する。
    """
    now = datetime.now()
    formatted_time = now.strftime("%Y%m%d%H%M%S")  # タイムスタンプの生成
    failed_file = f"{main_folder}\\▼登録名称不明-{formatted_time}.pdf"
    try:
        os.rename(file, failed_file)  # ファイル名を変更
        print("受信フォルダをサーチ中、、、")
    except Exception:
        pass  # エラー時には何もしない


max_val_dict = {}  # 各テンプレートの最大マッチング値を格納する辞書
dts = ""  # デバッグ用の一時変数
top_val = ""  # 最も高いマッチング率のテンプレート名


def template_matching(pic):
    """
    受信した画像とテンプレート画像をマッチングする。
    テンプレートごとのマッチング結果を記録し、最大値を更新する。

    Args:
        pic (str): マッチング対象のテンプレート画像のパス。
    """
    global top_val, dts, max_val_dict
    renamed_pic = pic.split("/")[-1].replace(".png", "")  # テンプレート画像の名前を抽出
    templ = cv2.imread(fr"{pic}")  # テンプレート画像を読み込む
    print(f"Matching to : <<{renamed_pic}>>")

    # 画像マッチングの実行（テンプレートマッチング）
    result = cv2.matchTemplate(img, templ, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    thrshold = 0.72  # マッチング判定の閾値

    match_y, match_x = np.where(result >= thrshold)

    if max_val >= thrshold:
        for x, y in zip(match_x, match_y):
            if x:
                if max_val == 1.0:  # 完全一致の場合
                    print(f"""
                    {renamed_pic}が100%マッチしました！
                    """)
                    max_val_dict[pic] = max_val
                    top_val = max(max_val_dict, key=max_val_dict.get).split("/")[-1].replace(".png", "")
                    stop_event.set()  # マッチング成功を通知
                else:
                    print(f"""
                    {renamed_pic}がマッチしました！
                    """)
                    max_val_dict[pic] = max_val
                    top_val = max(max_val_dict, key=max_val_dict.get).split("/")[-1].replace(".png", "")

                # マッチング結果を画像上に矩形として表示
                h, w = templ.shape[:2]
                top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                cv2.rectangle(img, top_left, bottom_right, (0, 0, 255), 2)
                plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                plt.title(f"Match: {renamed_pic} with value: {max_val:.2f}")
                plt.show()
                break


def change_title():
    """
    最もマッチング率が高いテンプレートに基づいてPDFファイルの名前を変更し、
    保存先フォルダに移動する。
    """
    global top_val, dts, max_val_dict
    now = datetime.now()
    formatted_time = now.strftime("%Y%m%d%H%M%S")  # タイムスタンプの生成
    print(f"{top_val}が最も高いマッチング率でした")
    with open(matching_sheet, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if top_val in row["キーワード"]:  # マッチング結果とCSVデータを照合
                new_pdf = f"{temp_folder}/{row['会社名']}-{formatted_time}.pdf"
                f.close()
                try:
                    os.rename(file, new_pdf)  # ファイル名を変更
                    shutil.move(new_pdf, main_folder)  # 保存先フォルダに移動
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
    """
    PDF解析に失敗したファイルを監視し、一時フォルダに移動する。
    """
    while True:
        files = glob.glob(f"{main_folder}/*.pdf")  # フォルダ内のPDFファイルを監視
        for file in files:
            if "変換失敗" in file:  # ファイル名に「変換失敗」を含む場合
                print("変換失敗を発見しました！rename_folderへ移動します。")
                shutil.move(file, temp_folder)  # ファイルを移動
        t = 2
        while t > 0:  # 2秒間スリープ
            time.sleep(1)
            t -= 1


if __name__ == "__main__":
    # 常駐スレッドの開始
    in_progress_thread = threading.Thread(target=run_in_progress_to_convert, daemon=True)
    in_progress_thread.start()
    print("受信フォルダをサーチ中、、、")
    
    while True:
        # 一時フォルダ内のPDFを処理
        files = glob.glob(rf"{temp_folder}/*.pdf")
        for file in files:
            print(f"{file}のリネームを開始します。")
            try:
                doc = fitz.open(file)  # PDFファイルを開く
            except fitz.fitz.FileDataError as e:
                print(e)
                continue
            
            # PDFを画像化
            page = doc[0]
            zoom = 400 / 72
            mat = fitz.Matrix(zoom, zoom)
            image = page.get_pixmap(matrix=mat)
            image.save(sample_pic)

            # 画像をグレースケール化
            PIL_img = Image.open(sample_pic)
            gray_img = PIL_img.convert("L")
            gray_img.save(sample_pic)
            doc.close()

            img = cv2.imread(sample_pic)  # 画像を読み込む
            template_pic_to_gray()  # テンプレート画像をグレースケール化
            pics = glob.glob(f"{temp_pics}/*.png")
            pics = random.sample(pics, len(pics))  # テンプレート画像をランダムな順序で処理
            for pic in pics:
                template_matching(pic)  # テンプレートマッチングの実行
                change_title()  # ファイル名を変更
        t = 2
        while t > 0:  # 2秒間スリープ
            time.sleep(1)
            t -= 1
