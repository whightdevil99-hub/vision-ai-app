from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.properties import StringProperty
from gtts import gTTS
import threading
import os
import tempfile
import vosk
import json

class VisionApp(App):
    status_text = StringProperty("Ready")
    language = 'hi'

    def build(self):
        self.title = "Vision AI (Offline)"
        layout = BoxLayout(orientation='vertical', padding=20)
        self.status_label = Label(text="Vision: Ready...", size_hint_y=0.2, font_size=20)
        layout.add_widget(self.status_label)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        btn_hindi = Button(text="Hindi", on_press=self.set_hindi)
        btn_guj = Button(text="Gujarati", on_press=self.set_gujarati)
        btn_layout.add_widget(btn_hindi)
        btn_layout.add_widget(btn_guj)
        layout.add_widget(btn_layout)
        
        self.output_text = TextInput(text="...", multiline=True, readonly=True, size_hint_y=0.4)
        layout.add_widget(self.output_text)
        
        btn_start = Button(text="Start Listening", on_press=self.start_listening, size_hint_y=0.2)
        layout.add_widget(btn_start)
        
        self.load_vosk_model()
        return layout

    def load_vosk_model(self):
        try:
            model_path = f"models/vosk-model-small-{self.language}"
            if os.path.exists(model_path):
                self.recognizer = vosk.KaldiModel(model_path)
                self.stt = vosk.Stt(self.recognizer, 16000)
                self.status_label.text = "Model loaded."
            else:
                self.status_label.text = "Model missing! Check 'models' folder."
        except Exception as e:
            self.status_label.text = f"Error: {e}"

    def set_hindi(self, instance):
        self.language = 'hi'
        self.speak_text("Hindi chun li gayi hai")
        self.load_vosk_model()

    def set_gujarati(self, instance):
        self.language = 'gu'
        self.speak_text("Gujarati chun li gayi hai")
        self.load_vosk_model()

    def start_listening(self, instance):
        self.status_label.text = "Sun raha hoon..."
        threading.Thread(target=self.listen_offline, daemon=True).start()

    def listen_offline(self):
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True)
            self.stt.Reset()
            while True:
                data = stream.read(4000, exception_on_overflow=False)
                if len(data) == 0: break
                result = self.stt.AcceptWaveform(data)
                res_json = json.loads(result)
                if "text" in res_json and res_json["text"]:
                    text = res_json["text"]
                    Clock.schedule_once(lambda dt: setattr(self.output_text, 'text', f"Aap: {text}"), 0)
                    response = f"Aapne kaha: {text}. Main madad kar sakta hoon?"
                    Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', "Bol raha hoon..."), 0)
                    self.speak_text(response)
                    break
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f"Error: {e}"), 0)

    def speak_text(self, text):
        def play():
            try:
                tts = gTTS(text=text, lang=self.language)
                f = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                tts.save(f.name)
                from kivy.core.audio import SoundLoader
                sound = SoundLoader.load(f.name)
                if sound: sound.play()
                import time
                time.sleep(3)
                os.remove(f.name)
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', "Ready"), 0)
            except Exception as e:
                print(e)
        threading.Thread(target=play, daemon=True).start()

if __name__ == '__main__':
    VisionApp().run()
