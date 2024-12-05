from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from io import StringIO
import os
import glob
import time
import csv
import shutil
import datetime
from dict import keywords
import random

main_folder = r"FAX受信フォルダ"
rename_csv = "rename_list.csv"


# タイトル変更を行う
def Rename():
    global fp
    """
    指定されたフォルダ内のPDFファイルを解析し、内容に基づいてファイル名を変更する。
    """
    # 現在時刻を取得して、ファイル名変更時に使用
    current_time = datetime.datetime.now()
    current_time = current_time.strftime("%Y%m%d%H%M%S")

    # フォルダ内のPDFファイルをリスト化
    files = glob.glob(f"{main_folder}//*.pdf")
    for file in files:
        file_name = os.path.basename(file)
        if "登録名称不明" in file:
            try:
                fp = open(file, "rb")
            except Exception:
                print("ファイルが見つかりません")
                continue

        # PDFからテキストを抽出
        outfp = StringIO()
        rmgr = PDFResourceManager()
        lprms = LAParams(
            line_overlap=0.5,
            word_margin=0,
            char_margin=2,
            line_margin=0.5,
            detect_vertical=False
        )
        device = TextConverter(rmgr, outfp, laparams=lprms)
        iprtr = PDFPageInterpreter(rmgr, device)

        try:
            for page in PDFPage.get_pages(fp):  # 各ページのテキストを解析
                iprtr.process_page(page)
            fp.close()
        except Exception:
            continue

        text = outfp.getvalue()  # テキスト抽出結果を取得
        outfp.close()
        device.close()

        # スペースを削除したテキストでキーワードを検索
        no_space_text = text.replace(" ", "")
        detected_keywords = ""

        # 定義されたキーワードでマッチングを実施
        for key, value in keywords.items():
            for values in value:
                if key in no_space_text:
                    if values in no_space_text:
                        detected_keywords = key + values
                        print(f"【{file_name}】から検出されたキーワード：{detected_keywords}")
                        break
                if detected_keywords:
                    break

        # キーワードが検出された場合、CSVリストを参照して会社名を取得
        try:
            with open(rename_csv, "r", encoding="utf-8_sig") as f:
                for row in csv.DictReader(f):
                    if row["キーワード"] in detected_keywords:
                        print(f"【{file_name}】を解析：合致する会社名は【{row["会社名"]}】です。")

                        if "登録名称不明" in file:
                            # 新しいファイル名を作成
                            new_file_name = f"{row["会社名"]}-{current_time}-{random.randrange(1000)}.pdf"
                            new_file = f"{os.path.dirname(file)}/{new_file_name}"
                            print(f"【{file_name}】を、【{new_file_name}】へPDFタイトルを変換します。")
                            os.rename(file, new_file)  # ファイル名を変更
                        break

                else:
                    # キーワードが見つからなかった場合の処理
                    print(f"【{file_name}】の変換に失敗しました。名称を【変換失敗】に変更します。")
                    failed_file_name = f"変換失敗.pdf"
                    failed_file = f"{os.path.dirname(file)}/{failed_file_name}"
                    os.rename(file, failed_file)

        except Exception as e:
            print(e)  # エラーを表示して次のファイルへ
            continue

# 定期的にRename関数を実行するループ
def rename_start():
    """
    フォルダ内のPDFファイルを一定間隔でチェックして、タイトル変更処理を繰り返す。
    """
    global flg3
    flg3 = False
    n = 0
    while True:
        t = 3
        while t > 0:
            t -= 1
            time.sleep(1) # 処理のインターバルを設定
        Rename()

# スクリプトのエントリーポイント
if __name__ == "__main__":
    print("フォルダをサーチ中"
          "\n")
    rename_start()
