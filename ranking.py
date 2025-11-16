import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import sqlite3
import subprocess
import sys

# 3:2 비율 창
WIDTH = 900
HEIGHT = 600

# 이미지 경로
BACKGROUND_PATH = "./images/menuBackground.png"

root = tk.Tk()
root.title("Ranking - Dancing Doyo")

# 창 크기 설정
root.geometry(f"{WIDTH}x{HEIGHT}")
root.resizable(False, False)

# 창을 맨 앞으로
root.lift()
root.attributes('-topmost', True)
root.after_idle(root.attributes, '-topmost', False)
root.focus_force()

# 창을 화면 중앙에 배치
root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = (screen_width - WIDTH) // 2
y = (screen_height - HEIGHT) // 2

root.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")

# ----------------------------
# Canvas 위에 배경 이미지
# ----------------------------
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, highlightthickness=0)
canvas.pack(fill="both", expand=True)

try:
    bg_image = Image.open(BACKGROUND_PATH).resize((WIDTH, HEIGHT))
    bg_photo = ImageTk.PhotoImage(bg_image)
    canvas.create_image(0, 0, anchor="nw", image=bg_photo)
except:
    canvas.configure(bg="#1a1a2e")
    print("배경 이미지를 찾을 수 없습니다.")

# ----------------------------
# 스타일 설정
# ----------------------------
style = ttk.Style()
style.theme_use('clam')

# 상단 버튼 스타일
style.configure('TopMenu.TButton',
                background='#2d2d44',
                foreground='white',
                borderwidth=0,
                focuscolor='none',
                font=('맑은 고딕', 10))
style.map('TopMenu.TButton',
          background=[('active', '#3d3d54')])

# 뒤로가기 버튼 스타일
style.configure('Back.TButton',
                background='#6c5ce7',
                foreground='white',
                borderwidth=0,
                focuscolor='none',
                font=('맑은 고딕', 12, 'bold'),
                padding=8)
style.map('Back.TButton',
          background=[('active', '#5f4dd1')])

# ----------------------------
# 데이터베이스에서 랭킹 가져오기
# ----------------------------
def get_rankings():
    """DB에서 상위 10명의 랭킹 가져오기"""
    try:
        conn = sqlite3.connect('signUp.db')
        cursor = conn.cursor()
        
        # score 기준 내림차순, 동점시 id 오름차순
        cursor.execute("""
            SELECT userName, score 
            FROM users 
            ORDER BY score DESC, id ASC 
            LIMIT 10
        """)
        
        rankings = cursor.fetchall()
        conn.close()
        return rankings
    except Exception as e:
        print(f"DB 오류: {e}")
        return []

# ----------------------------
# 메인 메뉴로 돌아가기
# ----------------------------
def go_back():
    # 두가지 경우 존재
    """선택 메뉴로 돌아가기"""
    root.destroy()
    subprocess.Popen([sys.executable, "choose.py"])

# ----------------------------
# 상단 타이틀
# ----------------------------
title_text = canvas.create_text(WIDTH//2, 60,
                                text="🏆 RANKING 🏆",
                                font=("맑은 고딕", 36, "bold"),
                                fill="#ffd700")

# ----------------------------
# 랭킹 표시 프레임
# ----------------------------
ranking_frame = tk.Frame(canvas, bg="#2d2d44", bd=2, relief="solid")
ranking_frame_window = canvas.create_window(WIDTH//2, HEIGHT//2 + 20,
                                           window=ranking_frame,
                                           width=700,
                                           height=380)

# 랭킹 데이터 표시
rankings = get_rankings()

# 스크롤 가능한 영역
scroll_frame = tk.Frame(ranking_frame, bg="#2d2d44")
scroll_frame.pack(fill="both", expand=True, padx=10, pady=(10, 10))

if rankings:
    for idx, (username, score) in enumerate(rankings, 1):
        # 순위별 색상
        if idx == 1:
            rank_color = "#ffd700"  # 금색
            rank_emoji = "🥇"
        elif idx == 2:
            rank_color = "#c0c0c0"  # 은색
            rank_emoji = "🥈"
        elif idx == 3:
            rank_color = "#cd7f32"  # 동색
            rank_emoji = "🥉"
        else:
            rank_color = "#ffffff"
            rank_emoji = ""
        
        # 각 랭킹 행
        row_frame = tk.Frame(scroll_frame, bg="#3d3d54", height=40)
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)
        
        tk.Label(row_frame, text=f"{rank_emoji} {idx}",
                font=("맑은 고딕", 12, "bold"),
                bg="#3d3d54", fg=rank_color, width=8).pack(side="left", padx=10)
        
        tk.Label(row_frame, text=username,
                font=("맑은 고딕", 12),
                bg="#3d3d54", fg="#ffffff", width=30, anchor="w").pack(side="left", padx=10)
        
        tk.Label(row_frame, text=f"{score:,}점",
                font=("맑은 고딕", 12, "bold"),
                bg="#3d3d54", fg="#00ff00", width=15).pack(side="left", padx=10)
else:
    # 데이터가 없을 때
    no_data_label = tk.Label(scroll_frame,
                            text="아직 등록된 기록이 없습니다.",
                            font=("맑은 고딕", 16),
                            bg="#2d2d44",
                            fg="#888888")
    no_data_label.pack(expand=True)

# ----------------------------
# 뒤로가기 버튼
# ----------------------------
back_button = ttk.Button(canvas, text="← 돌아가기",
                        command=go_back,
                        style='Back.TButton')
back_button_window = canvas.create_window(WIDTH//2, HEIGHT - 50,
                                         window=back_button)

# ----------------------------
# 페이드인 효과
# ----------------------------
alpha = 0.0

def fade_in_ui():
    """UI 페이드인 효과"""
    global alpha
    if alpha < 1.0:
        alpha += 0.05
        y_offset = int((1.0 - alpha) * 30)
        canvas.coords(title_text, WIDTH//2, 60 + y_offset)
        canvas.coords(ranking_frame_window, WIDTH//2, HEIGHT//2 + 20 + y_offset)
        canvas.coords(back_button_window, WIDTH//2, HEIGHT - 50 + y_offset)
        root.after(30, fade_in_ui)

root.after(200, fade_in_ui)

# ----------------------------
# ESC 키로 메인 메뉴로
# ----------------------------
def on_escape(event):
    go_back()

root.bind('<Escape>', on_escape)

root.mainloop()