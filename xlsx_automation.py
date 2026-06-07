import ctypes
ctypes.windll.user32.SetProcessDPIAware()

import time
import pythoncom
import win32com.client as win32
import pyautogui
import pygetwindow as gw

FILE_PATH = r"C:\Users\admin\Desktop\factor-platform\更新因子_test_copy.xlsx"
SAVE_COPY_PATH = r"C:\Users\admin\Desktop\factor-platform\更新因子.xlsx"

# 先填「增益集分頁」座標
ADDIN_TAB_X = 1333
ADDIN_TAB_Y = 155

# 再填「真正更新按鈕」座標
UPDATE_BTN_X = 547
UPDATE_BTN_Y = 226

WAIT_AFTER_OPEN = 8
WAIT_AFTER_TAB_CLICK = 2
WAIT_AFTER_UPDATE_CLICK = 100

def focus_excel_window(part_of_title="更新因子"):
    windows = gw.getWindowsWithTitle(part_of_title)
    if not windows:
        raise RuntimeError(f"找不到 Excel 視窗，標題包含：{part_of_title}")
    win = windows[0]
    if win.isMinimized:
        win.restore()
    win.activate()
    time.sleep(1)
    win.maximize()
    time.sleep(2)
    return win

def safe_click(x, y, label):
    pyautogui.moveTo(x, y, duration=1)
    time.sleep(0.5)
    pyautogui.click(x, y)
    print(f"已點擊 {label}: ({x}, {y})")

def main():
    pythoncom.CoInitialize()
    excel = win32.DispatchEx("Excel.Application")
    excel.Visible = True
    excel.DisplayAlerts = False

    wb = None
    try:
        wb = excel.Workbooks.Open(FILE_PATH)
        print("已開啟 Excel")

        time.sleep(WAIT_AFTER_OPEN)
        focus_excel_window("更新因子")
        print("已切到 Excel 視窗")

        # 先點增益集分頁
        safe_click(ADDIN_TAB_X, ADDIN_TAB_Y, "增益集分頁")
        time.sleep(WAIT_AFTER_TAB_CLICK)

        # 再點更新按鈕
        safe_click(UPDATE_BTN_X, UPDATE_BTN_Y, "更新按鈕")

        print(f"等待更新完成 {WAIT_AFTER_UPDATE_CLICK} 秒...")
        time.sleep(WAIT_AFTER_UPDATE_CLICK)

        # 先存副本，避免動到原檔
        wb.SaveCopyAs(SAVE_COPY_PATH)
        print(f"已另存副本：{SAVE_COPY_PATH}")

        wb.Close(SaveChanges=False)
        print("已關閉活頁簿")

    finally:
        excel.Quit()
        pythoncom.CoUninitialize()
        print("Excel 已關閉")

if __name__ == "__main__":
    main()