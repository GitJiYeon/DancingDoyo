import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import sqlite3

# DB 연결
conn = sqlite3.connect('signUp.db')

# 커서 연결
cursor = conn.cursor()


# 창 크기
WIDTH = 900
HEIGHT = 600

root = tk.Tk()
root.title("로그인 - Dancing Doyo")
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

# 배경
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, highlightthickness=0, bg="#1a1a2e")
canvas.pack(fill="both", expand=True)

# 로그인 프레임
login_frame = tk.Frame(canvas, bg="#2d2d44", padx=40, pady=40)
canvas.create_window(WIDTH // 2, HEIGHT // 2, window=login_frame, anchor="center")

# 제목
title_label = tk.Label(login_frame, text="로그인",
                       font=("맑은 고딕", 32, "bold"),
                       fg="#ffffff", bg="#2d2d44")
title_label.pack(pady=(0, 30))

# 아이디 입력
id_label = tk.Label(login_frame, text="아이디",
                    font=("맑은 고딕", 12),
                    fg="#ffffff", bg="#2d2d44")
id_label.pack(anchor="w", pady=(0, 5))

id_entry = tk.Entry(login_frame, font=("맑은 고딕", 12), width=30)
id_entry.pack(pady=(0, 20), ipady=8)

# 비밀번호 입력
pw_label = tk.Label(login_frame, text="비밀번호",
                    font=("맑은 고딕", 12),
                    fg="#ffffff", bg="#2d2d44")
pw_label.pack(anchor="w", pady=(0, 5))

pw_entry = tk.Entry(login_frame, font=("맑은 고딕", 12), width=30, show="●")
pw_entry.pack(pady=(0, 30), ipady=8)

# 버튼 스타일
style = ttk.Style()
style.theme_use('clam')
style.configure('Login.TButton',
                background='#6c5ce7',
                foreground='white',
                borderwidth=0,
                focuscolor='none',
                font=('맑은 고딕', 12, 'bold'),
                padding=10)
style.map('Login.TButton',
          background=[('active', '#5f4dd1')])

style.configure('Back.TButton',
                background='#4a4a5e',
                foreground='white',
                borderwidth=0,
                focuscolor='none',
                font=('맑은 고딕', 10),
                padding=8)
style.map('Back.TButton',
          background=[('active', '#3a3a4e')])


def login():
    """로그인 처리"""
    userId = id_entry.get()
    password = pw_entry.get()

    if not userId or not password:
        messagebox.showwarning("경고", "아이디와 비밀번호를 입력해주세요.")
        return

    # 로그인
    cursor.execute("SELECT userId, password FROM users WHERE userId = ? AND password = ?", (userId, password))
    conn.commit()
    result = cursor.fetchone() # 없으면 None 반환

    if result:
        messagebox.showinfo("성공", "로그인 성공!")
        start_pressed()
    else:
        messagebox.showerror("실패", "아이디 또는 비밀번호가 틀렸습니다.")


def signUp():
    """회원가입 메뉴로 이동"""
    root.destroy()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_path = os.path.join(script_dir, "signUp.py")
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    subprocess.Popen([pythonw, main_path])


def go_back():
    """메인 메뉴로 돌아가기"""
    root.destroy()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_path = os.path.join(script_dir, "main.py")
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    subprocess.Popen([pythonw, main_path])

def start_pressed():
    """게임 시작"""
    # 버튼 비활성화
    login_button.config(state='disabled')

    # 페이드아웃 효과
    fade_out_and_start()

def fade_out_and_start(volume=0.5):
    userId = id_entry.get()
    """페이드아웃 후 게임 시작"""
    root.destroy()

    # 잠깐 대기 후 게임 실행
    import time
    time.sleep(0.1)

    # 사용자 이름 전달
    cursor.execute("SELECT userName FROM users WHERE userId = ?", (userId,))
    conn.commit()
    name = cursor.fetchone()[0]

    import game
    game.main("login", name)


# 로그인 버튼
login_button = ttk.Button(login_frame, text="로그인",
                          command=login,
                          style='Login.TButton')
login_button.pack(ipadx=40, ipady=5)

# 회원가입 버튼
signUp_button = ttk.Button(login_frame, text="→ 회원가입",
                         command=signUp,
                         style='Back.TButton')
signUp_button.pack(pady=(20, 0), ipadx=20)

# 돌아가기 버튼
back_button = ttk.Button(login_frame, text="← 돌아가기",
                         command=go_back,
                         style='Back.TButton')
back_button.pack(pady=(10, 0), ipadx=20)

# Enter 키로 로그인
pw_entry.bind('<Return>', lambda e: login())

# ESC 키로 돌아가기
root.bind('<Escape>', lambda e: go_back())
root.mainloop()

# DB 연결 종료
conn.close()