from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color, Line
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from kivy.uix.floatlayout import FloatLayout
from kivy.animation import Animation
from random import randint
from kivy.core.audio import SoundLoader
from random import randint
import os
Window.clearcolor = (0, 0, 0, 1)
Window.fullscreen = True

class SnakeGame(Widget):
    def __init__(self, score_label, highscore_label, state_label, **kwargs):
        super().__init__(**kwargs)
        self.cell_size = 60
        self.snake = [(5, 5)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = (10, 10)
        self.score = 0
        self.running = False
        self.paused = False
        self._touch_start = None
        self.score_label = score_label
        self.highscore_label = highscore_label
        self.state_label = state_label

        
        highscore_path = os.path.join(App.get_running_app().user_data_dir, 'highscore.json')
        self.store = JsonStore(highscore_path)
        if not self.store.exists('score'):
            self.store.put('score', highscore=0)

        self.highscore_label.text = f"High Score: {self.store.get('score')['highscore']}"

        self.draw_border()
        self.bind(size=self.update_canvas, pos=self.update_canvas)

        
        self.bg_sound = SoundLoader.load('audios/bg_music.mp3')
        self.start_sound = SoundLoader.load('audios/start.mp3')
        self.hiss_sound = SoundLoader.load('audios/hiss.wav')
        self.chew_sound = SoundLoader.load('audios/chew.wav')
        self.death_sound = SoundLoader.load('audios/death.wav')

        if self.hiss_sound:
            self.hiss_sound.loop = True
            self.hiss_sound.volume = 0.4
        if self.bg_sound:
            self.bg_sound.loop = True
            self.bg_sound.volume = 0.2

    def fade_state_label(self, text):
        self.state_label.text = text
        self.state_label.opacity = 0
        anim = Animation(opacity=1, duration=0.5)
        anim.start(self.state_label)
        
    def start_game(self):
        if self.running:
            return
        self.snake = [(5, 5)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = (randint(0, (Window.width // self.cell_size) - 1),
                     randint(10, (Window.height // self.cell_size) - 1))
        self.score = 0
        self.running = True
        self.paused = False
        self.fade_state_label("")
        self.highscore_label.text = ""

        if self.start_sound:
            self.start_sound.play()
        if self.hiss_sound:
            self.hiss_sound.play()
        if self.bg_sound:
            self.bg_sound.play()

        Clock.unschedule(self.update)
        Clock.schedule_interval(self.update, 0.2)
        self.update_labels()

    def pause_game(self):
        if not self.running:
            return
        self.paused = not self.paused
        self.fade_state_label("PAUSE") if self.paused else self.fade_state_label("")
        self.highscore_label.text = f"High Score: {self.store.get('score')['highscore']}" if self.paused else ""
        if self.paused:
            if self.hiss_sound:
                self.hiss_sound.stop()
            if self.bg_sound:
                self.bg_sound.stop()
        else:
            if self.hiss_sound:
                self.hiss_sound.play()
            if self.bg_sound:
                self.bg_sound.play()

    def draw_border(self):
        with self.canvas.before:
            self.canvas.before.clear()
            Color(1, 1, 1)
            Line(rectangle=(0, 0, Window.width, Window.height), width=4)

    def update_canvas(self, *args):
        self.draw_border()

    def on_touch_down(self, touch):
        self._touch_start = touch.pos

    def on_touch_up(self, touch):
        if not self._touch_start:
            return

        dx = touch.pos[0] - self._touch_start[0]
        dy = touch.pos[1] - self._touch_start[1]

        if abs(dx) > abs(dy):
            if dx > 50 and self.direction != (-1, 0):
                self.next_direction = (1, 0)
            elif dx < -50 and self.direction != (1, 0):
                self.next_direction = (-1, 0)
        else:
            if dy > 50 and self.direction != (0, -1):
                self.next_direction = (0, 1)
            elif dy < -50 and self.direction != (0, 1):
                self.next_direction = (0, -1)

        if touch.pos[1] > Window.height * 0.9:
            self.start_game()
       
        elif touch.pos[1] < Window.height * 0.1:
            self.pause_game()

    def update(self, dt):
        if not self.running or self.paused:
            return

        self.direction = self.next_direction
        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])

        if (new_head in self.snake or
            new_head[0] < 0 or new_head[1] < 0 or
            new_head[0] * self.cell_size >= Window.width or
            new_head[1] * self.cell_size >= Window.height):
            self.running = False
            self.fade_state_label("RESTART")
            self.highscore_label.text = f"High Score: {self.store.get('score')['highscore']}"
            Clock.unschedule(self.update)
            if self.hiss_sound:
                self.hiss_sound.stop()
            if self.bg_sound:
                self.bg_sound.stop()
            if self.death_sound:
                self.death_sound.play()
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 1
            if self.chew_sound:
                self.chew_sound.play()
            while True:
                self.food = (randint(0, (Window.width // self.cell_size) - 1),
                             randint(0, (Window.height // self.cell_size) - 1))
                if self.food not in self.snake:
                    break
        else:
            self.snake.pop()

        if self.score > self.store.get('score')['highscore']:
            self.store.put('score', highscore=self.score)
            
        self.update_labels()
        self.draw()

    def update_labels(self):
        self.score_label.text = f"Score: {self.score}"

    def draw(self):
        self.canvas.clear()
        self.draw_border()
        with self.canvas:
            Color(0, 1, 0)
            for x, y in self.snake:
                Rectangle(pos=(x * self.cell_size, y * self.cell_size), size=(self.cell_size, self.cell_size))
            Color(1, 0, 0)
            fx, fy = self.food
            Rectangle(pos=(fx * self.cell_size, fy * self.cell_size), size=(self.cell_size, self.cell_size))


class SnakeApp(App):
    def build(self):
        self.layout = FloatLayout()
        self.score_label = Label(text="", size_hint=(None, None),
                            pos_hint={"center_x": 0.5, "center_y": 0.95}, font_size='20sp', color=(1, 1, 1, 1))
        self.highscore_label = Label(text="", size_hint=(None, None),
                                pos_hint={"center_x": 0.5, "center_y": 0.4}, font_size='20sp', color=(1, 1, 1, 1))
        self.state_label = Label(text="START", size_hint=(None, None),
                            pos_hint={"center_x": 0.5, "center_y": 0.5}, font_size='50sp', color=(1, 0, 0, 1))

        self.game = SnakeGame(self.score_label, self.highscore_label, self.state_label)

        self.layout.add_widget(self.game)
        self.layout.add_widget(self.score_label)
        self.layout.add_widget(self.highscore_label)
        self.layout.add_widget(self.state_label)

        # Schedule a frame update right after build
        Clock.schedule_once(self.force_redraw, 0.1)

        return self.layout

    def force_redraw(self, dt):
        self.game.draw()

if __name__ == '__main__':
    SnakeApp().run()
