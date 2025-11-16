import pygame
import random
import sys
import subprocess
from PIL import Image, ImageSequence
import os
import sqlite3

# DB 연결
conn = sqlite3.connect('signUp.db')
cursor = conn.cursor()

os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'  # 중앙 배치
os.environ['SDL_VIDEO_CENTERED'] = '1'

# 초기화
pygame.init()
pygame.mixer.init()

# 화면 설정
WIDTH = 900
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dancing Doyo")

# 강제로 포커스
#################################이거 리스타트 하면 창 맨 앞으로 가져오는건데 안됨;; 일단 기능은 있긴 하다 정도~ㅋ
pygame.event.pump()
pygame.display.flip()

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (100, 100, 255)
PURPLE = (200, 100, 255)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)
DARK_BG = (26, 26, 46)

# FPS
clock = pygame.time.Clock()
FPS = 60

# 화살표 키 매핑
ARROW_KEYS = {
    pygame.K_LEFT: 0,  # 왼쪽
    pygame.K_DOWN: 1,  # 아래
    pygame.K_UP: 2,  # 위
    pygame.K_RIGHT: 3  # 오른쪽
}

ARROW_NAMES = ['LEFT', 'DOWN', 'UP', 'RIGHT']
ARROW_COLORS = [PURPLE, BLUE, GREEN, RED]

# 노트 설정
NOTE_SIZE = 100  #100*100
NOTE_SPEED = 6
SPAWN_HEIGHT = HEIGHT + 50  # 아래에서 스폰

# 판정 라인 위치 (상단 3/4 지점)
JUDGMENT_Y = HEIGHT // 4

# 플레이어와 상대 위치
PLAYER_X_START = 100
OPPONENT_X_START = 550
ARROW_SPACING = 90

# 게임 상태
class GameState:
    PLAYING = "playing"
    GAME_OVER = "game_over"
    CLEAR = "clear"

# GIF 애니메이션 클래스
class AnimatedSprite:
    def __init__(self, gif_path, width, height):
        self.frames = []
        self.current_frame = 0
        self.animation_speed = 214  # 밀리초
        self.last_update = pygame.time.get_ticks()

        try:
            # PIL로 GIF 로드
            gif = Image.open(gif_path)
            for frame in ImageSequence.Iterator(gif):
                frame_rgba = frame.convert('RGBA')
                frame_resized = frame_rgba.resize((width, height))

                # PIL 이미지를 pygame surface로 변환
                mode = frame_resized.mode
                size = frame_resized.size
                data = frame_resized.tobytes()

                py_image = pygame.image.fromstring(data, size, mode)
                self.frames.append(py_image)

            self.is_loaded = True
        except:
            self.is_loaded = False
            print(f"GIF 로드 실패: {gif_path}")

    def update(self):
        if not self.is_loaded or len(self.frames) == 0:
            return

        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_update = now
    def get_current_frame(self):
        if self.is_loaded and len(self.frames) > 0:
            return self.frames[self.current_frame]
        return None


# 노트 클래스
class Note:
    def __init__(self, arrow_type, is_player, spawn_time, note_image):
        self.arrow_type = arrow_type  # 0~3
        self.is_player = is_player  # True: 플레이어, False: 상대
        self.spawn_time = spawn_time
        self.note_image = note_image  # 노트 이미지

        # X 위치 계산
        base_x = PLAYER_X_START if is_player else OPPONENT_X_START
        self.x = base_x + arrow_type * ARROW_SPACING
        self.y = SPAWN_HEIGHT

        self.hit = False
        self.missed = False

    def update(self):
        if not self.hit:
            self.y -= NOTE_SPEED  # 위로 이동

            # 화면 밖으로 나가면 miss 처리
            if self.y < -30:
                self.missed = True

    def draw(self, screen):
        if not self.hit:
            # 노트 이미지 그리기 (정사각형)
            screen.blit(self.note_image,
                        (self.x - NOTE_SIZE // 2, self.y - NOTE_SIZE // 2))

    def check_hit(self, judgment_y, tolerance=50):
        """판정 체크"""
        return abs(self.y - judgment_y) <= tolerance


# 게임 매니저
class RhythmGame:
    def __init__(self):
        self.state = GameState.PLAYING
        self.notes = []
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.miss_count = 0
        self.total_notes_hit = 0

        self.gif_change_time = 0
        self.gif_duration = 400  # 300ms동안 GIF 변경

        self.opponent_gif_change_time = 0
        self.opponent_gif_duration = 400  # 300ms동안 GIF 변경

        self.game_duration = 150000 - 3000

        # 디버그 디버깅 (True면 바로 끝)
        self.debug_mode = False  # 디버깅 : True, 일반 : False
        ###############이거 밑에 클리어로 끝내는거랑 게임오버로 끝내는거로 디버깅 설정 할 수 있음!!!!!!!!!!!!!!!!!

        # 카메라 줌 효과
        self.camera_x = 0
        self.camera_y = 0
        self.camera_zoom = 1.0
        self.target_camera_x = 0
        self.target_camera_y = 0
        self.target_zoom = 1.0
        self.camera_speed = 0.1  # 부드러운 전환 속도
        self.current_focus = None  # 'player' or 'opponent'

        # 배경 이미지 로드
        self.background = self.load_background()

        # 화살표 이미지 로드
        self.arrow_images = self.load_arrow_images()
        self.note_images = self.load_note_images()

        self.player_gif_normal = AnimatedSprite("./images/doyo.gif", 190, 190)
        self.player_gif_up = AnimatedSprite("./images/doyo_up.gif", 190, 190)
        self.player_gif_down = AnimatedSprite("./images/doyo_down.gif", 190, 190)
        self.player_gif_left = AnimatedSprite("./images/doyo_left.gif", 190, 190)
        self.player_gif_right = AnimatedSprite("./images/doyo_right.gif", 190, 190)
        self.player_gif = self.player_gif_normal  # 현재 사용 중인 GIF

        self.opponent_gif_normal = AnimatedSprite("./images/gugu.gif", 210, 210)
        self.opponent_gif_up = AnimatedSprite("./images/gugu_up.gif", 210, 210)
        self.opponent_gif_down = AnimatedSprite("./images/gugu_down.gif", 210, 210)
        self.opponent_gif_left = AnimatedSprite("./images/gugu_left.gif", 210, 210)
        self.opponent_gif_right = AnimatedSprite("./images/gugu_right.gif", 210, 210)
        self.opponent_gif = self.opponent_gif_normal

        self.opponent2_gif_normal = AnimatedSprite("./images/pla.gif", 210, 210)
        self.opponent2_gif_up = AnimatedSprite("./images/pla_up.gif", 210, 210)
        self.opponent2_gif_down = AnimatedSprite("./images/pla_down.gif", 210, 210)
        self.opponent2_gif_left = AnimatedSprite("./images/pla_left.gif", 210, 210)
        self.opponent2_gif_right = AnimatedSprite("./images/pla_right.gif", 210, 210)

        self.opponent3_gif_normal = AnimatedSprite("./images/peacock.gif", 210, 210)
        self.opponent3_gif_up = AnimatedSprite("./images/peacock_up.gif", 210, 210)
        self.opponent3_gif_down = AnimatedSprite("./images/peacock_down.gif", 210, 210)
        self.opponent3_gif_left = AnimatedSprite("./images/peacock_left.gif", 210, 210)
        self.opponent3_gif_right = AnimatedSprite("./images/peacock_right.gif", 210, 210)

        self.opponent4_gif_normal = AnimatedSprite("./images/ak.gif", 210, 210)
        self.opponent4_gif_up = AnimatedSprite("./images/ak_up.gif", 210, 210)
        self.opponent4_gif_down = AnimatedSprite("./images/ak_down.gif", 210, 210)
        self.opponent4_gif_left = AnimatedSprite("./images/ak_left.gif", 210, 210)
        self.opponent4_gif_right = AnimatedSprite("./images/ak_right.gif", 210, 210)

        # 판정 이미지
        self.judgment_perfect = pygame.image.load("./images/logo/perfect.png")
        self.judgment_perfect = pygame.transform.scale(self.judgment_perfect, (160, 80))
        self.judgment_great = pygame.image.load("./images/logo/great.png")
        self.judgment_great = pygame.transform.scale(self.judgment_great, (160, 80))
        self.judgment_good = pygame.image.load("./images/logo/good.png")
        self.judgment_good = pygame.transform.scale(self.judgment_good, (160, 80))
        self.judgment_normal = pygame.image.load("./images/logo/normal.png")
        self.judgment_normal = pygame.transform.scale(self.judgment_normal, (160, 80))

        # 엔딩 GIF
        self.ending_gif = AnimatedSprite("./images/background/ending.gif", 600, 400)
        self.ending_started = False
        self.ending_start_time = 0
        self.ending_duration = 5000

        # 판정 표시용 변수
        self.current_judgment = None
        self.judgment_time = 0
        self.judgment_duration = 500  # 0.5초 동안 표시

        # 차트 데이터 로드
        self.chart = self.create_chart()
        self.chart_index = 0

        # 배경음악 로드
        self.music_started = False
        self.music_delay = 1500  # 2초 딜레이

        try:
            pygame.mixer.music.load("./sounds/gameBGM1.mp3")
        except:
            print("음악 파일을 찾을 수 없습니다.")

        # 효과음 로드
        try:
            self.hit_sound = pygame.mixer.Sound("./sounds/clap1.mp3")
            self.hit_sound.set_volume(0.3)  # 볼륨 조절 (0.0~1.0)
        except:
            print("효과음 파일을 찾을 수 없습니다.")
            self.hit_sound = None

        #디버깅할때 하나만 켜서 확인 디버그
        if self.debug_mode:
            #gameOver (클리어 X)
            #self.start_ticks = pygame.time.get_ticks() - (150000 - 100000)
            #clear
            self.start_ticks = pygame.time.get_ticks() - (150000 - 5000)
        else:
            self.start_ticks = pygame.time.get_ticks()


    def load_background(self):
        """배경 이미지 로드"""
        try:
            bg = pygame.image.load("./images/street.png")
            bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
            return bg
        except:
            print("배경 이미지를 찾을 수 없습니다. 기본 배경 사용")
            return None

    def load_arrow_images(self):
        """판정선 화살표 이미지 로드"""
        arrow_images = []
        arrow_files = [
            "./images/arrow_left.png",
            "./images/arrow_down.png",
            "./images/arrow_up.png",
            "./images/arrow_right.png"
        ]

        for i, filepath in enumerate(arrow_files):
            try:
                img = pygame.image.load(filepath)
                img = pygame.transform.scale(img, (NOTE_SIZE, NOTE_SIZE))
                arrow_images.append(img)
            except:
                # 이미지가 없으면 기본 사각형 생성
                surface = pygame.Surface((NOTE_SIZE, NOTE_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(surface, ARROW_COLORS[i], (0, 0, NOTE_SIZE, NOTE_SIZE), 3)

                # 화살표 텍스트
                font = pygame.font.Font(None, 30)
                text = font.render(ARROW_NAMES[i], True, ARROW_COLORS[i])
                text_rect = text.get_rect(center=(NOTE_SIZE // 2, NOTE_SIZE // 2))
                surface.blit(text, text_rect)
                arrow_images.append(surface)

        return arrow_images

    def load_note_images(self):
        """노트 이미지 로드"""
        note_images = []
        note_files = [
            "./images/left.png",
            "./images/down.png",
            "./images/up.png",
            "./images/right.png"
        ]

        for i, filepath in enumerate(note_files):
            try:
                img = pygame.image.load(filepath)
                img = pygame.transform.scale(img, (NOTE_SIZE, NOTE_SIZE))
                note_images.append(img)
            except:
                # 이미지가 없으면 기본 사각형 생성
                surface = pygame.Surface((NOTE_SIZE, NOTE_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(surface, ARROW_COLORS[i], (5, 5, NOTE_SIZE - 10, NOTE_SIZE - 10))
                pygame.draw.rect(surface, WHITE, (0, 0, NOTE_SIZE, NOTE_SIZE), 2)

                # 화살표 텍스트
                font = pygame.font.Font(None, 36)
                text = font.render(ARROW_NAMES[i][0], True, WHITE)
                text_rect = text.get_rect(center=(NOTE_SIZE // 2, NOTE_SIZE // 2))
                surface.blit(text, text_rect)
                note_images.append(surface)

        return note_images

    def create_chart(self):
        try:
            return self.load_chart_from_file("chart.txt")
        except:
            pass  # 파일이 없으면 기본 차트 사용

        chart = []

        current_time = 300  # 음악 시작 시간에 맞춤

        BPM = 145
        beat = 60000 / BPM  # 4분음표 길이(ms)

        current_time += beat

        # 메인 파트 (반복 패턴)
        while current_time < (150000 - 3000):

            # 상대 턴
            for _ in range(16):
                arrow_type = random.randint(0, 3)
                chart.append({
                    'time': current_time,
                    'arrow': arrow_type,
                    'is_player': False
                })
                current_time += beat / 2

            current_time += 0  # 쉬는 시간

            # 플레이어 턴
            pattern = [0, 1, 2, 3, 2, 1, 0, 3]  # 원하는 패턴으로 변경
            #for arrow in pattern:
            for _ in range(16):
                arrow_type = random.randint(0, 3)
                chart.append({
                    'time': current_time,
                    'arrow': arrow_type,
                    'is_player': True
                })
                current_time += beat / 2 # 간격 조절



            current_time += beat

        # ===== 여기까지 =====

        return chart

    def load_chart_from_file(self, filename):
        """텍스트 파일에서 차트 로드"""
        chart = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):  # 빈 줄이나 주석 무시
                    continue

                parts = line.split(',')
                if len(parts) >= 3:
                    time = int(parts[0])
                    arrow = int(parts[1])
                    is_player = bool(int(parts[2]))

                    # arrow가 -2면 이벤트만 추가
                    if arrow == -2:
                        chart.append({
                            'time': time,
                            'event': 'change_opponent2',
                            'is_player': is_player
                        })
                    elif arrow == -3:
                        chart.append({
                            'time': time,
                            'event': 'change_opponent3',
                            'is_player': is_player
                        })
                    elif arrow == -4:
                        chart.append({
                            'time': time,
                            'event': 'change_opponent4',
                            'is_player': is_player
                        })
                    else:
                        # 일반 노트만 추가
                        chart.append({
                            'time': time,
                            'arrow': arrow,
                            'is_player': is_player
                        })

        return chart

    def update(self, dt):
        if self.state != GameState.PLAYING:
            return

        self.game_time = pygame.time.get_ticks() - self.start_ticks

        # 음악 시작 (2초 후)
        if not self.music_started and self.game_time >= self.music_delay:
            try:
                pygame.mixer.music.play()
                self.music_started = True
            except:
                print("음악 재생 실패")

        self.player_gif.update()
        self.opponent_gif.update()

        if self.player_gif != self.player_gif_normal:
            if pygame.time.get_ticks() - self.gif_change_time > self.gif_duration:
                self.player_gif = self.player_gif_normal

        if self.opponent_gif != self.opponent_gif_normal:
            if pygame.time.get_ticks() - self.opponent_gif_change_time > self.opponent_gif_duration:
                self.opponent_gif = self.opponent_gif_normal
        # 다가오는 노트 확인하여 카메라 포커스 결정
        self.update_camera_focus()

        # 카메라 부드럽게 이동
        self.camera_x += (self.target_camera_x - self.camera_x) * self.camera_speed
        self.camera_y += (self.target_camera_y - self.camera_y) * self.camera_speed
        self.camera_zoom += (self.target_zoom - self.camera_zoom) * self.camera_speed

        # 노트 스폰
        while (self.chart_index < len(self.chart) and
               self.chart[self.chart_index]['time'] <= self.game_time):
            note_data = self.chart[self.chart_index]

            if 'event' in note_data:
                if note_data['event'] == 'change_opponent2':
                    self.opponent_gif_normal = self.opponent2_gif_normal
                    self.opponent_gif_up = self.opponent2_gif_up
                    self.opponent_gif_down = self.opponent2_gif_down
                    self.opponent_gif_left = self.opponent2_gif_left
                    self.opponent_gif_right = self.opponent2_gif_right
                elif note_data['event'] == 'change_opponent3':
                    self.opponent_gif_normal = self.opponent3_gif_normal
                    self.opponent_gif_up = self.opponent3_gif_up
                    self.opponent_gif_down = self.opponent3_gif_down
                    self.opponent_gif_left = self.opponent3_gif_left
                    self.opponent_gif_right = self.opponent3_gif_right
                elif note_data['event'] == 'change_opponent4':
                    self.opponent_gif_normal = self.opponent4_gif_normal
                    self.opponent_gif_up = self.opponent4_gif_up
                    self.opponent_gif_down = self.opponent4_gif_down
                    self.opponent_gif_left = self.opponent4_gif_left
                    self.opponent_gif_right = self.opponent4_gif_right
            else:
                # 이벤트가 아닐 때만 노트 생성
                note = Note(note_data['arrow'], note_data['is_player'],
                            note_data['time'], self.note_images[note_data['arrow']])
                self.notes.append(note)

            self.chart_index += 1

        # 노트 업데이트
        for note in self.notes[:]:
            note.update()

            # 상대 노트 자동 처리
            if not note.is_player and not note.hit:
                if note.check_hit(JUDGMENT_Y, tolerance=20):
                    if self.hit_sound:
                        self.hit_sound.play()
                    note.hit = True

                    self.opponent_gif_change_time = pygame.time.get_ticks()
                    if note.arrow_type == 0:  # LEFT
                        self.opponent_gif = self.opponent_gif_left
                    elif note.arrow_type == 1:  # DOWN
                        self.opponent_gif = self.opponent_gif_down
                    elif note.arrow_type == 2:  # UP
                        self.opponent_gif = self.opponent_gif_up
                    elif note.arrow_type == 3:  # RIGHT
                        self.opponent_gif = self.opponent_gif_right

            # Miss 처리 (플레이어 노트만)
            if note.is_player and note.missed and not note.hit:
                self.miss_count += 1

                if self.combo > self.max_combo:
                    self.max_combo = self.combo

                self.combo = 0
                self.notes.remove(note)

                # 5번 이상 miss면 게임오버
                if self.miss_count >= 5:
                    self.state = GameState.GAME_OVER
                    pygame.mixer.music.stop()

            # 상대 노트 제거
            if not note.is_player and (note.hit or note.missed):
                if note in self.notes:
                    self.notes.remove(note)

        # 게임 클리어 체크
        if self.game_time >= self.game_duration:
            # 남은 노트 강제 제거
            if len(self.notes) > 0:
                self.notes.clear()

            if not self.ending_started:
                self.ending_started = True
                self.ending_start_time = pygame.time.get_ticks()
                pygame.mixer.music.stop()
                print("엔딩")
            elif pygame.time.get_ticks() - self.ending_start_time >= self.ending_duration:
                self.state = GameState.CLEAR
                print("결과 화면")

    def update_camera_focus(self):
        """판정선 근처의 노트를 확인하여 카메라 포커스 결정"""
        # 판정선 근처(±140픽셀 이내)에 있는 노트만 확인
        nearby_notes = []
        for note in self.notes:
            if not note.hit and abs(note.y - JUDGMENT_Y + 20) < 140:
                nearby_notes.append(note)

        if nearby_notes:
            # 판정선에 가장 가까운 노트 찾기
            closest_note = min(nearby_notes, key=lambda n: abs(n.y - JUDGMENT_Y))

            # 같은 시간대에 플레이어와 상대 노트가 동시에 있는지 확인
            has_player = any(n.is_player and abs(n.y - closest_note.y) < 100 for n in nearby_notes)
            has_opponent = any(not n.is_player and abs(n.y - closest_note.y) < 100 for n in nearby_notes)

            # 양쪽 동시에 있으면 중앙 유지
            if has_player and has_opponent:
                self.target_camera_x = 0
                self.target_camera_y = 0
                self.target_zoom = 1.0
                self.current_focus = None
            elif closest_note.is_player:
                # 플레이어 턴만 - 왼쪽으로 줌
                self.target_camera_x = 150
                self.target_camera_y = 0
                self.target_zoom = 1.15
                self.current_focus = 'player'
            else:
                # 상대 턴만 - 오른쪽으로 줌
                self.target_camera_x = -150
                self.target_camera_y = 0
                self.target_zoom = 1.15
                self.current_focus = 'opponent'
        else:
            # 판정선 근처에 노트가 없으면 중앙으로
            self.target_camera_x = 0
            self.target_camera_y = 0
            self.target_zoom = 1.0
            self.current_focus = None

    def handle_input(self, key):
        """키 입력 처리"""
        # handle_input에서 타이머 시작

        if key not in ARROW_KEYS:
            return

        arrow_type = ARROW_KEYS[key]
        self.gif_change_time = pygame.time.get_ticks()

        # 가장 가까운 플레이어 노트 찾기
        closest_note = None
        min_distance = float('inf')

        for note in self.notes:
            if note.is_player and not note.hit and note.arrow_type == arrow_type:
                distance = abs(note.y - JUDGMENT_Y)
                if distance < min_distance:
                    min_distance = distance
                    closest_note = note

        # 판정
        if closest_note and closest_note.check_hit(JUDGMENT_Y, tolerance=80):
            closest_note.hit = True
            self.notes.remove(closest_note)

            # 효과음 재생
            if self.hit_sound:
                self.hit_sound.play()

            # 콤보 증가
            self.combo += 1

            # 최대 콤보 갱신
            if self.combo > self.max_combo:
                self.max_combo = self.combo

            # 콤보 보너스 계산 (10콤보마다 1% 추가)
            combo_bonus = 1.0 + (self.combo // 10) * 0.01

            # 판정 계산
            if min_distance <= 15:
                base_score = 300
                self.current_judgment = self.judgment_perfect
                judgment = "PERFECT!"
            elif min_distance <= 30:
                base_score = 200
                self.current_judgment = self.judgment_great
                judgment = "GREAT!"
            elif min_distance <= 50:
                base_score = 100
                self.current_judgment = self.judgment_good
                judgment = "GOOD!"
            elif min_distance <= 100:
                base_score = 50
                self.current_judgment = self.judgment_normal
                judgment = "NORMAL!"
            else:
                base_score = 0

            # 콤보 보너스 적용
            final_score = int(base_score * combo_bonus)
            self.score += final_score

            # 판정 이미지 표시 시작
            self.judgment_time = pygame.time.get_ticks()

            self.total_notes_hit += 1

            # 플레이어 GIF 변경
            if arrow_type == 0:
                self.player_gif = self.player_gif_left
            elif arrow_type == 1:
                self.player_gif = self.player_gif_down
            elif arrow_type == 2:
                self.player_gif = self.player_gif_up
            elif arrow_type == 3:
                self.player_gif = self.player_gif_right

    def draw(self, screen):
        # 카메라 효과를 위한 임시 서피스
        game_surface = pygame.Surface((WIDTH, HEIGHT))

        # 배경
        if self.background:
            game_surface.blit(self.background, (0, 0))
        else:
            game_surface.fill(DARK_BG)

        # 판정 라인
        #pygame.draw.line(game_surface, WHITE, (0, JUDGMENT_Y), (WIDTH, JUDGMENT_Y), 3)

        # 화살표 가이드(플레이어) 판정선에 이미지 표시
        for i in range(4):
            x = PLAYER_X_START + i * ARROW_SPACING
            game_surface.blit(self.arrow_images[i],
                              (x - NOTE_SIZE // 2, JUDGMENT_Y - NOTE_SIZE // 2))

        # 화살표 가이드(상대 판정선에 이미지 표시
        for i in range(4):
            x = OPPONENT_X_START + i * ARROW_SPACING
            game_surface.blit(self.arrow_images[i],
                              (x - NOTE_SIZE // 2, JUDGMENT_Y - NOTE_SIZE // 2))

        # 노트 그리기
        for note in self.notes:
            note.draw(game_surface)

        # 캐릭터 GIF 애니메이션 (판정선 아래, y +110)
        # 플레이어 캐릭터
        player_frame = self.player_gif.get_current_frame()
        if player_frame:
            game_surface.blit(player_frame, (PLAYER_X_START - 75 + 120, JUDGMENT_Y + 190))
        else:
            # GIF 로드 실패시 임시 박스
            pygame.draw.rect(game_surface, GREEN,
                             (PLAYER_X_START + 20, JUDGMENT_Y + 160, 120, 120), 3)
            font = pygame.font.Font(None, 24)
            text = font.render("PLAYER", True, GREEN)
            game_surface.blit(text, (PLAYER_X_START + 35, JUDGMENT_Y + 200))

        # 상대 캐릭터
        opponent_frame = self.opponent_gif.get_current_frame()
        if opponent_frame:
            game_surface.blit(opponent_frame, (OPPONENT_X_START - 75 + 120, JUDGMENT_Y + 160))
        else:
            # GIF 로드 실패시 임시 박스
            pygame.draw.rect(game_surface, RED,
                             (OPPONENT_X_START + 20, JUDGMENT_Y + 160, 120, 120), 3)
            font = pygame.font.Font(None, 24)
            text = font.render("OPPONENT", True, RED)
            game_surface.blit(text, (OPPONENT_X_START + 15, JUDGMENT_Y + 210))

        # === 카메라 효과 적용 ===
        # 줌 및 이동 효과 (게임만)
        if self.camera_zoom != 1.0 or self.camera_x != 0 or self.camera_y != 0:
            # 줌 적용
            zoomed_width = int(WIDTH / self.camera_zoom)
            zoomed_height = int(HEIGHT / self.camera_zoom)

            # 카메라 중심점 계산
            camera_center_x = WIDTH // 2 - int(self.camera_x)
            camera_center_y = HEIGHT // 2 - int(self.camera_y)

            # 크롭 영역 계산
            crop_x = max(0, camera_center_x - zoomed_width // 2)
            crop_y = max(0, camera_center_y - zoomed_height // 2)
            crop_x = min(crop_x, WIDTH - zoomed_width)
            crop_y = min(crop_y, HEIGHT - zoomed_height)

            # 서피스 크롭 및 확대
            cropped = game_surface.subsurface((crop_x, crop_y, zoomed_width, zoomed_height))
            scaled = pygame.transform.scale(cropped, (WIDTH, HEIGHT))
            screen.blit(scaled, (0, 0))
        else:
            screen.blit(game_surface, (0, 0))

        # =========== UI (카메라 효과X 화면에 고정) ================
        font_large = pygame.font.Font(None, 48)
        font_medium = pygame.font.Font(None, 36)

        # 판정 이미지 표시 (중앙 유ㅣ쪽)
        if self.current_judgment and pygame.time.get_ticks() - self.judgment_time < self.judgment_duration:
            judgment_x = WIDTH // 2 - 75
            judgment_y = 30
            screen.blit(self.current_judgment, (judgment_x, judgment_y))

        # 점수 (상단 중앙)
        score_text = font_large.render(f"{self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH // 2, 30))
        screen.blit(score_text, score_rect)


        # Miss 카운트 (하단 중앙)
        miss_color = RED if self.miss_count >= 4 else WHITE
        miss_text = font_medium.render(f"Miss: {self.miss_count}/5", True, miss_color)
        miss_rect = miss_text.get_rect(center=(WIDTH // 2, HEIGHT - 30))
        screen.blit(miss_text, miss_rect)

        # 콤보 (상단 좌측) - 보너스 표시 추가
        if self.combo > 0:
            combo_bonus = (self.combo // 10) * 1
            if combo_bonus > 0:
                combo_text = font_medium.render(f"x{self.combo} (+{combo_bonus}%)", True, YELLOW)
            else:
                combo_text = font_medium.render(f"x{self.combo}", True, YELLOW)
            screen.blit(combo_text, (20, 20))

        # 남은 시간 (상단 우측)
        remaining = max(0, self.game_duration - self.game_time)
        minutes = remaining // 60000
        seconds = (remaining % 60000) // 1000
        time_text = font_medium.render(f"{minutes}:{seconds:02d}", True, WHITE)
        screen.blit(time_text, (WIDTH - 150, 20))

    def draw_ending(self, screen):
        """엔딩 GIF 화면"""
        screen.fill(BLACK)  # 검정 배경

        # GIF 애니메이션 업데이트
        self.ending_gif.update()

        # GIF 표시 (중앙)
        ending_frame = self.ending_gif.get_current_frame()
        if ending_frame:
            gif_x = WIDTH // 2 - 300
            gif_y = HEIGHT // 2 - 200
            screen.blit(ending_frame, (gif_x, gif_y))
        else:
            # GIF 로드 실패 시 텍스트
            font = pygame.font.Font(None, 72)
            text = font.render("CLEAR!", True, WHITE)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(text, text_rect)

    def draw_result(self, screen):
        """결과 화면"""
        if self.background:
            screen.blit(self.background, (0, 0))
            # 반투명 오버레이
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(100)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(DARK_BG)

        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)

        if self.state == GameState.GAME_OVER:
            title = font_large.render("GAME OVER", True, RED)
            title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
            screen.blit(title, title_rect)
        else:
            title = font_large.render("CLEAR!", True, GREEN)
            title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
            screen.blit(title, title_rect)

        # 결과 표시
        results = [
            f"Final Score: {self.score}",
            f"Total Hits: {self.total_notes_hit}",
            f"Max Combo: {self.max_combo}",
            f"Miss: {self.miss_count}"
        ]

        y_offset = HEIGHT // 2 - 50
        for result in results:
            text = font_medium.render(result, True, WHITE)
            text_rect = text.get_rect(center=(WIDTH // 2, y_offset))
            screen.blit(text, text_rect)
            y_offset += 60

        # 안내 메시지
        info1 = font_small.render("Press ESC to return to menu", True, GRAY)
        info1_rect = info1.get_rect(center=(WIDTH // 2, HEIGHT - 70))
        screen.blit(info1, info1_rect)

        info2 = font_small.render("Press R to restart", True, GRAY)
        info2_rect = info2.get_rect(center=(WIDTH // 2, HEIGHT - 30))
        screen.blit(info2, info2_rect)

    def save_score(self, player_name):
        cursor.execute('''UPDATE users SET score = ? WHERE userName = ?''', (self.score, player_name))
        conn.commit()


# 메인 게임 루프
def main(status, name):
    game = RhythmGame()
    running = True

    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # 결과 화면에서 ESC → 메뉴로
                    if game.state != GameState.PLAYING:
                        running = False
                        return_to_menu()
                        return
                    else:
                        running = False

                elif event.key == pygame.K_r and game.state != GameState.PLAYING:
                    # 결과 화면에서 R → 재시작
                    running = False
                    restart_game()
                    return
                elif game.state == GameState.PLAYING:
                    game.handle_input(event.key)

        # 업데이트
        if game.state == GameState.PLAYING:
            game.update(dt)

        # 그리기
        if game.state == GameState.PLAYING:
            if game.ending_started:
                game.draw_ending(screen)
            else:
                game.draw(screen)
        else:
            game.draw_result(screen)
            # 로그인 후 게임 종료 시 점수 저장
            if status == "login":
                game.save_score(name)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def restart_game():
    """게임 재시작"""
    import os

    pygame.mixer.quit()
    pygame.quit()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    game_path = os.path.join(script_dir, "game.py")

    # pythonw 사용
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    subprocess.Popen([pythonw, game_path])


def return_to_menu():
    """메인 메뉴로 돌아가기"""
    import os
    import platform

    pygame.mixer.quit()
    pygame.quit()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_path = os.path.join(script_dir, "main.py")

    if platform.system() == "Windows":
        # Windows: pythonw 사용
        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        subprocess.Popen([pythonw, main_path])
    else:
        # Mac/Linux
        subprocess.Popen([sys.executable, main_path])

if __name__ == "__main__":
    main()

