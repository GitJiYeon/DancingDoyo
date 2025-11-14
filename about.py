import tkinter as tk
from PIL import Image, ImageTk
import subprocess
import sys
import os

# 창 크기
WIDTH = 900
HEIGHT = 600

root = tk.Tk()
root.title("About Game - Dancing Doyo")
root.resizable(False, False)

# 화면 중앙 배치
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
center_x = int((screen_width - WIDTH) / 2)
center_y = int((screen_height - HEIGHT) / 2)
root.geometry(f'{WIDTH}x{HEIGHT}+{center_x}+{center_y}')

# 창을 맨 앞으로
root.lift()
root.attributes('-topmost', True)
root.after_idle(root.attributes, '-topmost', False)
root.focus_force()

# Canvas
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, highlightthickness=0)
canvas.pack(fill="both", expand=True)

try:
    about_image = Image.open("./images/background/abouDoyo.png").resize((WIDTH, HEIGHT))
    about_photo = ImageTk.PhotoImage(about_image)
    canvas.create_image(0, 0, anchor="nw", image=about_photo)
except:
    # 이미지 없으면 기본 배경
    canvas.configure(bg="#1a1a2e")

    # 텍스트로 대체
    canvas.create_text(WIDTH // 2, HEIGHT // 2 - 100,
                       text="이 글이 정말 안뜨면 좋겠지만 떴다면 파일이 없나본데요......",
                       font=("맑은 고딕", 20, "bold"),
                       fill="#ffffff")

# X 버튼 (우측 상단)
def close_window():
    """창 닫기"""
    root.destroy()

    # 메인으로 돌아가기
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_path = os.path.join(script_dir, "main.py")
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    subprocess.Popen([pythonw, main_path])


# X 버튼 생성
close_button = tk.Button(canvas, text="✕",
                         font=("맑은 고딕", 16, "bold"),
                         bg="#ff4757", fg="white",
                         bd=0, padx=15, pady=5,
                         cursor="hand2",
                         command=close_window)
canvas.create_window(WIDTH - 30, 30, window=close_button, anchor="center")

# ESC 키로도 닫기
root.bind('<Escape>', lambda e: close_window())

root.mainloop()