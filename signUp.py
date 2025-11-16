import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import sqlite3


# DB 파일 연결 (없으면 생성)
conn = sqlite3.connect('signUp.db')

# 커서 연결
cursor = conn.cursor()

# 회원 테이블 생성
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        userName TEXT NOT NULL,
        userId TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        score INTEGER DEFAULT 0
    )
''')
conn.commit()


# 창 크기
WIDTH = 900
HEIGHT = 600

root = tk.Tk()
root.title("회원가입 - Dancing Doyo")
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

# 회원가입 프레임
signUp_frame = tk.Frame(canvas, bg="#2d2d44", padx=40, pady=40)
canvas.create_window(WIDTH // 2, HEIGHT // 2, window=signUp_frame, anchor="center")

# 제목
title_label = tk.Label(signUp_frame, text="회원가입",
                       font=("맑은 고딕", 32, "bold"),
                       fg="#ffffff", bg="#2d2d44")
title_label.pack(pady=(0, 30))

# 닉네임 입력
name_label = tk.Label(signUp_frame, text="닉네임",
                    font=("맑은 고딕", 12),
                    fg="#ffffff", bg="#2d2d44")
name_label.pack(anchor="w", pady=(0, 5))

name_entry = tk.Entry(signUp_frame, font=("맑은 고딕", 12), width=30)
name_entry.pack(pady=(0, 10), ipady=8)

# 아이디 입력
id_label = tk.Label(signUp_frame, text="아이디",
                    font=("맑은 고딕", 12),
                    fg="#ffffff", bg="#2d2d44")
id_label.pack(anchor="w", pady=(0, 5))

id_entry = tk.Entry(signUp_frame, font=("맑은 고딕", 12), width=30)
id_entry.pack(pady=(0, 20), ipady=8)

# 비밀번호 입력
pw_label = tk.Label(signUp_frame, text="비밀번호",
                    font=("맑은 고딕", 12),
                    fg="#ffffff", bg="#2d2d44")
pw_label.pack(anchor="w", pady=(0, 5))

pw_entry = tk.Entry(signUp_frame, font=("맑은 고딕", 12), width=30, show="●")
pw_entry.pack(pady=(0, 30), ipady=8)

# 버튼 스타일
style = ttk.Style()
style.theme_use('clam')
style.configure('SignUp.TButton',
                background='#6c5ce7',
                foreground='white',
                borderwidth=0,
                focuscolor='none',
                font=('맑은 고딕', 12, 'bold'),
                padding=10)
style.map('SignUp.TButton',
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


def signUp():
    """회원가입 처리"""
    userName = name_entry.get()
    userId = id_entry.get()
    password = pw_entry.get()

    # 유효성 검사
    if not userName:
        messagebox.showwarning("경고", "닉네임을 입력해주세요.")
        return
    
    if not userId:
        messagebox.showwarning("경고", "아이디를 입력해주세요.")
        return
    
    if not password:
        messagebox.showwarning("경고", "비밀번호를 입력해주세요.")
        return
    
    # 닉네임 중복 검사
    cursor.execute('SELECT * FROM users WHERE userName = ?', (userName,))
    if cursor.fetchone():
        messagebox.showerror("실패", "이미 존재하는 닉네임입니다.")
        return
    
    else:
        # 회원가입 처리
        try:
            cursor.execute('INSERT INTO users (userName, userId, password) VALUES (?, ?, ?)', (userName, userId, password))
            conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror("실패", "이미 존재하는 아이디입니다.")
            return
        messagebox.showinfo("성공", "회원가입이 완료되었습니다!")
        go_login()


def go_login():
    """로그인 메뉴로 돌아가기"""
    root.destroy()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_path = os.path.join(script_dir, "login.py")
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    subprocess.Popen([pythonw, main_path])




# 로그인 버튼
signUp_button = ttk.Button(signUp_frame, text="가입하기",
                          command=signUp,
                          style='SignUp.TButton')
signUp_button.pack(ipadx=40, ipady=5)


# Enter 키로 로그인
pw_entry.bind('<Return>', lambda e: signUp())

# ESC 키로 돌아가기
root.bind('<Escape>', lambda e: go_login())

root.mainloop()

# DB 연결 종료
conn.close()
