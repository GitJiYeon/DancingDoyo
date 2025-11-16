import pygame
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageSequence
import subprocess
import sys

# 3:2 비율 창
WIDTH = 900
HEIGHT = 600

# 이미지 경로
LEFT_IMAGE_PATH = "./images/doyo.gif"
RIGHT_IMAGE_PATH = "./images/peacock.gif"
BACKGROUND_PATH = "./images/menuBackground.png"

root = tk.Tk()
root.title("Dancing Doyo")

# 창 크기 설정 (먼저)
root.geometry(f"{WIDTH}x{HEIGHT}")
root.resizable(False, False)

# 창을 맨 앞으로
root.lift()
root.attributes('-topmost', True)
root.after_idle(root.attributes, '-topmost', False)
root.focus_force()

# 창을 화면 중앙에 배치
root.update_idletasks()  # 창 크기 업데이트
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = (screen_width - WIDTH) // 2
y = (screen_height - HEIGHT) // 2

root.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")



# 페이드인 효과를 위한 알파값
alpha = 0.0
# ----------------------------
# 🎨 Canvas 위에 배경 이미지
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


# 커스텀 버튼 스타일
style = ttk.Style()
style.theme_use('clam')
style.configure('TopMenu.TButton',
                background='#2d2d44',
                foreground='white',
                borderwidth=0,
                focuscolor='none',
                font=('맑은 고딕', 10))
style.map('TopMenu.TButton',
          background=[('active', '#3d3d54')])


def login_pressed():
    """로그인 화면"""
    # 버튼 비활성화
    login_button.config(state='disabled')

    # 페이드아웃 효과
    fade_out_and_login()

# ----------------------------
# 오른쪽 상단 버튼들
# ----------------------------

def open_about():
    """Ranking 화면 열기"""
    root.destroy()
    subprocess.Popen([sys.executable, "ranking.py"])


# 오른쪽 상단 프레임
top_right_frame = tk.Frame(canvas, bg="")
canvas.create_window(WIDTH - 20, 20, window=top_right_frame, anchor="ne")

# 커스텀 버튼 스타일
style = ttk.Style()
style.theme_use('clam')
style.configure('TopMenu.TButton',
                background='#2d2d44',
                foreground='white',
                borderwidth=0,
                focuscolor='none',
                font=('맑은 고딕', 10))
style.map('TopMenu.TButton',
          background=[('active', '#3d3d54')])

ranking_button = ttk.Button(top_right_frame, text="랭킹 보기",
                          command=open_about,
                          style='TopMenu.TButton')
ranking_button.pack(ipadx=15, ipady=5)

def start_pressed():
    """게임 시작"""
    # 버튼 비활성화
    login_button.config(state='disabled')

    # 페이드아웃 효과
    fade_out_and_start()


# ----------------------------
# 중앙 제목 + 버튼 (페이드인 효과)
# ----------------------------
try:
    # 로고 이미지 로드 (PNG 투명 배경)
    logo_image = Image.open("./images/logo.png")
    logo_photo = ImageTk.PhotoImage(logo_image)
    logo_img = canvas.create_image(WIDTH//2, HEIGHT//2 - 100,
                                   image=logo_photo,
                                   anchor="center")
    # 이미지 참조 유지
    canvas.logo_photo = logo_photo
except:
    # 이미지 없으면 텍스트로 대체
    logo_img = canvas.create_text(WIDTH//2, HEIGHT//2 - 100,
                                  text="Play Style",
                                  font=("맑은 고딕", 48, "bold"),
                                  fill="#ffffff")

# Login 버튼 스타일 
style.configure('Start.TButton',
                background='#6c5ce7',
                foreground='white',
                borderwidth=0,
                focuscolor='none',
                font=('맑은 고딕', 16, 'bold'),
                padding=10)
style.map('Start.TButton',
          background=[('active', '#5f4dd1')])

login_button = ttk.Button(canvas, text="Login",
                         command=login_pressed,
                         style='Start.TButton')
login_button_window = canvas.create_window(WIDTH//2, HEIGHT//2,
                                          window=login_button)

# Guest 버튼 스타일 
style.configure('Start.TButton',
                background='#6c5ce7',
                foreground='white',
                borderwidth=0,
                focuscolor='none',
                font=('맑은 고딕', 16, 'bold'),
                padding=10)
style.map('Start.TButton',
          background=[('active', '#5f4dd1')])

guest_button = ttk.Button(canvas, text="Guest",
                         command=start_pressed,
                         style='Start.TButton')
guest_button_window = canvas.create_window(WIDTH//2, HEIGHT//2+60,
                                          window=guest_button)



def fade_out_and_start(volume=0.5):
    """페이드아웃 후 게임 시작"""
    root.destroy()

    # 잠깐 대기 후 게임 실행
    import time
    time.sleep(0.1)

    import game
    game.main("guest", "Guest")


def fade_out_and_login(volume=0.5):
    """Login 화면 열기"""
    root.destroy()
    subprocess.Popen([sys.executable, "login.py"])

# 제목과 버튼 페이드인
center_frame_alpha = 0.0

# 페이드인 효과
def fade_in_ui():
    """UI 페이드인 효과"""
    global center_frame_alpha
    if center_frame_alpha < 1.0:
        center_frame_alpha += 0.05
        y_offset = int((1.0 - center_frame_alpha) * 30)
        canvas.coords(logo_img, WIDTH//2, HEIGHT//2 - 100 + y_offset)
        canvas.coords(login_button_window, WIDTH//2, HEIGHT//2 + y_offset)
        canvas.coords(guest_button_window, WIDTH//2, HEIGHT//2 + y_offset+60)
        root.after(30, fade_in_ui)

root.after(200, fade_in_ui)


root.after(200, fade_in_ui)


# ----------------------------
# GIF 움직이기 클래스
# ----------------------------
class AnimatedGIF:
    def __init__(self, canvas, path, x, y, width, height, delay=100):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.delay = delay
        self.frames = []

        try:
            im = Image.open(path)
            for frame in ImageSequence.Iterator(im):
                frame = frame.convert("RGBA").resize((width, height))
                self.frames.append(ImageTk.PhotoImage(frame))
        except Exception as e:
            print(f"GIF 로드 실패 ({path}): {e}")

        self.idx = 0
        self.image_obj = self.canvas.create_image(x, y, image=self.frames[0])
        self.animate()

    def animate(self):
        if self.frames:
            self.canvas.itemconfig(self.image_obj, image=self.frames[self.idx])
            self.idx = (self.idx + 1) % len(self.frames)
        self.canvas.after(self.delay, self.animate)


# ----------------------------
# 왼쪽 / 오른쪽 GIF
# ----------------------------
left_gif = AnimatedGIF(canvas, LEFT_IMAGE_PATH, 30 + 75, HEIGHT - 30 - 75, 200, 200)
right_gif = AnimatedGIF(canvas, RIGHT_IMAGE_PATH, WIDTH - 30 - 150, HEIGHT - 30 - 150, 300, 300)


# ----------------------------a
# ESC 키로 종료
# ----------------------------

def on_escape(event):
    root.destroy()


root.bind('<Escape>', on_escape)

root.mainloop()