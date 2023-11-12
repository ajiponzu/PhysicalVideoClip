import time

import cv2
import os
import sys
import re
import ffmpeg
from datetime import datetime, timedelta


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
CLIP_IMG = ord('x')
MODE = ord('m')


#
def skip_frame(v_cap, input_key, frame_count, max_frame_num) -> (int, int):
    print("skipping process..................")
    cv2.destroyAllWindows()

    _frame_count = frame_count
    _cur_frame_count = 0
    front_flag = True
    if (input_key == PREV or input_key == PREV_FAST
            or input_key == PREV_FASTER or input_key == PREV_FASTEST):
        _frame_count -= 1
        front_flag = False
    else:
        _frame_count += 1

    while input_key is not None and 0 <= _frame_count <= max_frame_num:
        v_cap.set(cv2.CAP_PROP_POS_FRAMES, _frame_count)
        _cur_frame_count = int(v_cap.get(cv2.CAP_PROP_POS_FRAMES))
        ret, frame = v_cap.read()

        if ret and _cur_frame_count == _frame_count:
            print("next frame is found")
            print(f"go to count[{_cur_frame_count}]")
            return _frame_count, _cur_frame_count
        else:
            if front_flag:
                _frame_count += 1
            else:
                _frame_count -= 1

    frame_count = max_frame_num + 1
    return _frame_count, _cur_frame_count


#
def visualize_time(view, timestamp_str):
    cv2.rectangle(view, [0, 0, 650, 50], [255, 255, 255], -1)
    cv2.putText(view,
                text=timestamp_str,
                org=(10, 40),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=1.0,
                color=(0, 0, 0),
                thickness=2,
                lineType=cv2.LINE_4)


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
            フレーム画像切り抜き:
                x:  画像切り抜き・保存
            モード切替
                m: 経過フレーム<->タイムスタンプ表示
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

    video_start_time = ffmpeg.probe(
        i_path)["streams"][0]["tags"]["creation_time"]
    video_start_time = datetime.strptime(
        video_start_time, '%Y-%m-%dT%H:%M:%S.%fZ') + timedelta()

    passed_time_mode = True

    if max_frame_num < 0:
        print("[Oops] video path can't be recognized")
        return

    # 動画読み込みループ
    input_key = None
    frame_count = 0  # 現在フレーム位置(読み込み前基準)
    clip_start_frame = 0  # 切り抜き開始位置
    clip_end_frame = 0  # 切り抜き終端位置
    clip_start_time = "None"
    clip_end_time = "None"
    clip_start_datetime = "None"
    clip_end_datetime = "None"
    cur_frame_count = 0  # タイムスタンプに基づいたフレーム位置
    prev_frame_count = 0
    while True:
        # usage outputs
        print(
            "◀◀◀◀[H]\t◀◀◀[h]\t◀◀[J]\t◀[j]\t■[q]\t▶[k]\t▶▶[K]\t▶▶▶[l]\t▶▶▶▶[L]")
        print("clip image [x]")
        print("EXIT [Q]")
        # clip_info outputs
        print(f"clip_start_pos: {clip_start_time} - {clip_start_datetime}")
        print(f"clip_end_pos: {clip_end_time} - {clip_end_datetime}")
        # video_start_time
        print(video_start_time.strftime(
            'start_time: [Day] %Y-%m-%d, [Time] %H:%M:%S, .%f'))

        # seek and read
        v_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        cur_frame_count = int(v_cap.get(cv2.CAP_PROP_POS_FRAMES))
        print(f"frame_count: {frame_count}")
        print(f"cur_frame_count: {cur_frame_count}")
        ret, frame = v_cap.read()

        # 読み込みに失敗（精確にはフレームが欠損）している場合，またはタイムスタンプが変わらない場合
        if not ret or frame_count != cur_frame_count:
            frame_count, cur_frame_count = (
                skip_frame(v_cap, input_key, frame_count, max_frame_num))

        if frame_count > max_frame_num:
            print("frame is empty")
            break

        # GUI
        # ウィンドウ
        view = cv2.resize(frame, (1280, 720))
        timestamp_str = ""
        cur_passed_time = timedelta(
            milliseconds=v_cap.get(cv2.CAP_PROP_POS_MSEC))
        cur_datetime = video_start_time + timedelta(milliseconds=v_cap.get(
            cv2.CAP_PROP_POS_MSEC))
        if passed_time_mode:
            timestamp_str = str(cur_passed_time)
        else:
            timestamp_str = cur_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        visualize_time(view, timestamp_str)
        cv2.imshow("view", view)

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
            clip_start_frame = cur_frame_count
            clip_start_time = cur_passed_time
            clip_start_datetime = cur_datetime
        elif input_key == CLIP_END:
            clip_end_frame = cur_frame_count
            clip_end_time = cur_passed_time
            clip_end_datetime = cur_datetime
        elif input_key == CLIP_IMG:
            cv2.imwrite("frame.jpg", frame)
            cv2.imwrite("frame_timestamp.jpg", view)
        elif input_key == MODE:
            passed_time_mode = not passed_time_mode
        else:
            continue

    # 終了処理・クリップ動画書き出し処理
    cv2.destroyAllWindows()
    print("try to export..........................")

    timestamp_json = dict()

    v_writer = cv2.VideoWriter(o_path, fmt, fps, (v_wid, v_high))
    frame_count = clip_start_frame
    new_video_frame_count = 0
    while True:
        v_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        cur_frame_count = int(v_cap.get(cv2.CAP_PROP_POS_FRAMES))
        ret, frame = v_cap.read()

        if not ret or cur_frame_count != frame_count:
            frame_count, cur_frame_count = (
                skip_frame(v_cap, NEXT, frame_count, clip_end_frame))

        if cur_frame_count > clip_end_frame:
            break

        cur_datetime = video_start_time + \
            timedelta(milliseconds=v_cap.get(cv2.CAP_PROP_POS_MSEC))
        cur_datetime += timedelta(hours=9)
        timestamp_json[f"Frame{new_video_frame_count}"] = cur_datetime.strftime(
            '%Y-%m-%dT%H:%M:%S.%fZ')

        v_writer.write(frame)
        new_video_frame_count += 1
        frame_count += 1

    with open('timestamp.json', 'w') as fp:
        print(timestamp_json, file=fp)

    v_writer.release()
    v_cap.release()
    print("done!")


def main():
    exe_args = sys.argv
    video_path = ''
    base_path = ''
    path_ext = '.'
    if len(exe_args) <= 1:
        video_path = input("input video_path: ")
    else:
        video_path = exe_args[1]
    video_path = re.sub('"', '', repr(video_path)[1:-1])  # reprによる''を取り除く
    base_path, path_ext = video_path.split('.')
    path_ext = '.' + path_ext

    app(base_path, path_ext)


if __name__ == "__main__":
    main()
