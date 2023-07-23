import cv2
import os
import sys


# キーコードエイリアス
EXIT = ord('Q')
SAVE_EXIT = ord('q')
NEXT = ord('k')
NEXT_FAST = ord('K')
NEXT_FASTER = ord('l')
NEXT_FASTEST = ord('L')
PREV = ord('j')
PREV_FAST = ord('J')
PREV_FASTER = ord('h')
PREV_FASTEST = ord('H')
CLIP_START = ord('a')
CLIP_END = ord('s')


#
def make_timestamp_string(milliseconds: float) -> str:
    """
    Description:
        ミリ秒時刻を 時間:分:秒:ミリ秒 の文字形式(str)に変換する
    Args:
        milliseconds: float
            浮動小数点型のミリ秒
    Returns:
        "{時間}[h] : {分}[m]: {秒}[s] : {ミリ秒}[ms]" 形式の文字列
    """
    hour = milliseconds / (3600 * 1000)
    hour_surplus = milliseconds % (3600 * 1000)
    minute = hour_surplus / (60 * 1000)
    minute_surplus = hour_surplus % (60 * 1000)
    second = minute_surplus / 1000
    millisecond = minute_surplus % 1000
    sign = "" if milliseconds >= 0 else "[err]"

    return f"{int(hour)}[h] : {int(minute)}[m] : {int(second)} [s] : {int(millisecond)} [ms] {sign}"


#
def app(base_path: str, path_ext: str):
    """
    Description:
        キー入力操作による解像度維持・fps維持可能な動画クリップアプリ:
            出力ファイルは動画
    Args:
        base_path: str
            拡張子を除いた相対パス
        path_ext: str
            拡張子
    Usage:
        受け付けるキー入力は以下:
            フレーム移動:
                H:  30秒早戻し
                h:  10秒早戻し
                J:  1秒早戻し
                j:  1コマ戻し
                k:  1コマ送り
                K:  1秒早送り
                l:  10秒早送り
                L:  30秒早送り
            切り抜き:
                a:  
                    開始位置設定
                s:  
                    終端位置設定
                q:  動画出力
            アプリ終了:
                Q
    """
    i_path = base_path + path_ext
    o_path = base_path + "_c.mp4"

    v_cap = cv2.VideoCapture(i_path)
    max_frame_num = int(v_cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
    v_wid = int(v_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    v_high = int(v_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = v_cap.get(cv2.CAP_PROP_FPS)
    fmt = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    if max_frame_num < 0:
        print("[Oops] video path can't be recognized")
        return

    # 動画読み込みループ
    frame_count = 0  # 現在フレーム位置(読み込み前基準)
    clip_start_frame = 0  # 切り抜き開始位置
    clip_end_frame = 0  # 切り抜き終了位置
    clip_start_time: str = "None"
    clip_end_time: str = "None"
    while True:
        # usage outputs
        print(
            "◀◀◀◀[H]\t◀◀◀[h]\t◀◀[J]\t◀[j]\t■[q]\t▶[k]\t▶▶[K]\t▶▶▶[l]\t▶▶▶▶[L]")
        print("EXIT [Q]")
        # clip_info outputs
        print(f"clip_start_pos: {clip_start_time}")
        print(f"clip_end_pos: {clip_end_time}")

        # seek and read
        v_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        ret, frame = v_cap.read()
        if ret is not True:
            print("frame is empty")
            break

        # GUI
        # ウィンドウ
        view = cv2.resize(frame, (1280, 720))
        timestamp_str = make_timestamp_string(v_cap.get(cv2.CAP_PROP_POS_MSEC))
        cv2.rectangle(view, [0, 0, 650, 50], [255, 255, 255], -1)
        cv2.putText(view,
                    text=timestamp_str,
                    org=(10, 40),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=1.0,
                    color=(0, 0, 0),
                    thickness=2,
                    lineType=cv2.LINE_4)
        cv2.imshow("frame", view)

        # キー受付
        input_key = cv2.waitKey(0)
        os.system("clear")  # ここでクリアをかませる

        if input_key == EXIT:
            print("goodbye!")
            return
        elif input_key == SAVE_EXIT:
            if clip_start_frame < clip_end_frame:
                break
            else:
                print("[Re:input] clip_start_frame must be less than clip_end_frame!")
        elif input_key == NEXT:
            frame_count = min(frame_count + 1, max_frame_num)
        elif input_key == NEXT_FAST:
            frame_count = min(frame_count + int(fps), max_frame_num)
        elif input_key == NEXT_FASTER:
            frame_count = min(frame_count + int(fps) * 10, max_frame_num)
        elif input_key == NEXT_FASTEST:
            frame_count = min(frame_count + int(fps) * 30, max_frame_num)
        elif input_key == PREV:
            frame_count = max(frame_count - 1, 0)
        elif input_key == PREV_FAST:
            frame_count = max(frame_count - int(fps), 0)
        elif input_key == PREV_FASTER:
            frame_count = max(frame_count - int(fps) * 10, 0)
        elif input_key == PREV_FASTEST:
            frame_count = max(frame_count - int(fps) * 30, 0)
        elif input_key == CLIP_START:
            clip_start_frame = frame_count
            clip_start_time = timestamp_str
        elif input_key == CLIP_END:
            clip_end_frame = frame_count
            clip_end_time = timestamp_str
        else:
            continue

    # 終了処理・クリップ動画書き出し処理
    cv2.destroyAllWindows()
    v_writer = cv2.VideoWriter(o_path, fmt, fps, (v_wid, v_high))
    print("try to export..........................")

    frame_count = clip_start_frame
    v_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
    while True:
        ret, frame = v_cap.read()
        if ret is not True:
            print("frame is empty")
            break
        elif frame_count > clip_end_frame:
            break

        v_writer.write(frame)
        frame_count += 1

    v_writer.release()
    v_cap.release()
    print("done!")


if __name__ == "__main__":
    exe_args = sys.argv
    base_path = ''
    path_ext = '.'
    if len(exe_args) <= 2:
        base_path = input("input video_path (** extension be not included **): ")
        path_ext += input("input path_extension: ")
    else:
        base_path = exe_args[1]
        path_ext += exe_args[2]

    app(base_path, path_ext)
