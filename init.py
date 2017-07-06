import json
import wave
import pyaudio
from tkinter import *
from tkinter import ttk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from watson_developer_cloud import TextToSpeechV1, SpeechToTextV1, LanguageTranslatorV2

RATE = 44100
CHANNELS = 2
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "file.wav"

translator_models = ['es-en', 'en-es']
translator_voices = ["es-LA_SofiaVoice", "en-US_MichaelVoice"]
broadbands = ["en-US_BroadbandModel", "es-ES_BroadbandModel"]

text_to_speech = TextToSpeechV1(
    username="af9aa8f2-e1c3-41ca-b6fa-8f234d41a276",
    password="FmHKZtWx2neA",
    x_watson_learning_opt_out=True
)

language_translator = LanguageTranslatorV2(
    username="7ae5c091-59c1-4d18-bc72-8e0a21638298",
    password="1WJS8Js68MJ2",
    x_watson_learning_opt_out=True
)

speech_to_text = SpeechToTextV1(
    username="026021fe-0067-4611-bbe0-1d7d53133060",
    password="TMbL6YDJblB8",
    x_watson_learning_opt_out=True
)

class Application(Frame):

    def play_wav(self, filename, chunk_size = CHUNK_SIZE):
        try:
            wf = wave.open(filename, 'rb')
        except IOError as ioe:
            sys.stderr.write('IOError on file ' + filename + '\n' + str(ioe) + '. Skipping.\n')
            return
        except EOFError as eofe:
            sys.stderr.write('EOFError on file ' + filename + '\n' + str(eofe) + '. Skipping.\n')
            return
        p = pyaudio.PyAudio()
        stream = p.open(format= p.get_format_from_width(wf.getsampwidth()),
                        channels= wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        data = wf.readframes(chunk_size)
        while len(data) > 0:
            stream.write(data)
            data =  wf.readframes(chunk_size)
        stream.stop_stream()
        stream.close()
        p.terminate()

    def load_file(self):
        self.input_fname = filedialog.askopenfilename(filetypes=(("Windows Audio", "*.wav"), ("All files", "*.*")))
        print(self.input_fname)

    def save_file(self):
        fname = filedialog.asksaveasfile(mode='w', defaultextension='.wav')
        if fname:
            try:
                print("%s" % fname)
                with open(fname, "wb") as audio_file:
                    audio_file.write(
                        text_to_speech.synthesize(self.text_translated, accept="audio/wav",
                                                  voice="es-LA_SofiaVoice"))
            except:
                messagebox.showerror("File path invalid", "Failed to save file\n '%s'" % fname)
            return

    def translate(self, translate_from='es-ES_BroadbandModel', translate_to='en-US_MichaelVoice'):
        translate_model = translate_from[0:2] + '-' + translate_to[0:2]
        print(translate_model)
        #Read input file
        print(self.input_fname)
        input_audio = open(self.input_fname, 'rb')
        #Convert to text and write transcript
        with open('transcript.json', 'w') as fp:
            result = speech_to_text.recognize(input_audio, content_type='audio/wav', model=translate_from, continuous=True, timestamps=False, max_alternatives=1)
            json.dump(result, fp, indent=2)
            self.text_to_translate = result['results'][0]['alternatives'][0]['transcript']
            print(self.text_to_translate)

        self.box_text_to_translate.delete(0, END)
        self.box_text_to_translate.insert(END, self.text_to_translate)
        # Translate text
        self.text_translated = language_translator.translate(self.text_to_translate, model_id=translate_model)

        self.box_text_translated.delete(0, END)
        self.box_text_translated.insert(END, self.text_translated)

        #Synthesize and write output to file
        with open('output.wav', "wb") as audio_file:
            audio_file.write(
                text_to_speech.synthesize(self.text_translated, accept="audio/wav",
                                          voice=translate_to))
        #Play output
        self.play_wav('output.wav')

    def change_language(self, event):
        current = self.input_language.current()
        print(translator_models[current])
        if translator_models[current] == "en-es":
            self.translate_to = translator_voices[0]
            self.translate_from = broadbands[0]
        else:
            self.translate_to = translator_voices[1]
            self.translate_from = broadbands[1]
        return

    def record(self):
        audio = pyaudio.PyAudio()
        #Crear stream de microfono
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK_SIZE)
        #Grabar
        print("Grabando")
        frames = []

        for i in range(0, int(RATE / CHUNK_SIZE * RECORD_SECONDS)):
            data = stream.read(CHUNK_SIZE)
            frames.append(data)

        print("Grabacion terminada")

        #Guardar grabacion
        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()
        self.input_fname = WAVE_OUTPUT_FILENAME
        return

    def createWidgets(self):

        button_frame = Frame(self)
        button_frame.pack(expand=True, fill=X)

        self.recordButton = Button(button_frame)
        self.recordButton["text"] = "Record"
        self.recordButton["command"] = self.record
        self.recordButton.grid(row=1, column=0, stick=W + E)

        self.inputButton = Button(button_frame)
        self.inputButton["text"] = "Input"
        self.inputButton["command"] = self.load_file
        self.inputButton.grid(row=0, column=0, stick=W+E)

        self.file_text = Label(button_frame, text=self.input_fname)
        self.file_text.grid(row=1, column=0, sticky=W)

        self.input_language = ttk.Combobox(button_frame, values=["ES to EN", "EN to ES"])
        self.input_language.current(0)
        self.input_language.grid(row=2, column=0)
        self.input_language.bind("<<ComboboxSelected>>", self.change_language)

        self.audioButton= Button(button_frame)
        self.audioButton["text"] = "Translate"
        self.audioButton["command"] = lambda: self.translate(self.translate_from, self.translate_to)
        self.audioButton.grid(row=0, column=1, sticky=W+E)

        self.QUIT = Button(button_frame)
        self.QUIT["text"] = "QUIT"
        self.QUIT["fg"] = "red"
        self.QUIT["command"] = self.quit
        self.QUIT.grid(row=0, column=2, sticky=W+E)


        Label(text="Recognised Text").pack(side=LEFT)
        self.box_text_to_translate = Listbox(self)
        self.box_text_to_translate["textvariable"] = self.text_to_translate
        self.box_text_to_translate.pack(side=LEFT)

        Label(text="Translated Text").pack(side=RIGHT)
        self.box_text_translated = Listbox(self)
        self.box_text_translated["textvariable"] = self.text_to_translate
        self.box_text_translated.pack(side=RIGHT)


    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.translate_to = translator_voices[0]
        self.translate_from = broadbands[0]
        self.input_fname = None
        self.text_translated = None
        self.text_to_translate = None
        self.output_audio = None
        #print(json.dumps(text_to_speech.voices(), indent=2))
        #print(json.dumps(language_translator.get_models(), indent=2))
        #print(json.dumps(speech_to_text.models(), indent=2))
        self.pack()
        self.createWidgets()

if __name__ == "__main__":
    root = Tk()
    app = Application(master=root)
    app.mainloop()
    if root:
        try:
            root.destroy()
        except:
            print("Application Root already Destroyed")


# print(json.dumps(text_to_speech.voices(), indent=2))
# print(json.dumps(speech_to_text.models(), indent=2))

# print(json.dumps(language_translator.translate()))

''''
with open(join(dirname(__file__), "output.wav"),
          "rb") as audio_file:
    text_result = json.dumps(speech_to_text.recognize(
        audio_file, content_type="audio/wav", timestamps=True,
        word_confidence=True, model="es-ES_BroadbandModel"), indent=2
    )
    print(text_result)

with open(join(dirname(__file__), "output.wav"),
          "wb") as audio_file:
    audio_file.write(
        text_to_speech.synthesize("Hola Mundo", accept="audio/wav",
                                   voice="es-LA_SofiaVoice"))

print(json.dumps(text_to_speech.pronunciation("Watson", pronunciation_format="spr"), indent=2))
'''
