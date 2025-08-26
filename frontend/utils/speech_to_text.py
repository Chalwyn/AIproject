import speech_recognition as sr
from pydub import AudioSegment
import io

def audio_to_text(audio_file):
    recognizer = sr.Recognizer()

    # 使用pydub加载音频文件
    audio = AudioSegment.from_file(audio_file)

    # 将音频转为 wav 格式（SpeechRecognition库需要wav格式）
    audio_wav = io.BytesIO()
    audio.export(audio_wav, format="wav")
    audio_wav.seek(0)

    with sr.AudioFile(audio_wav) as source:
        audio_data = recognizer.record(source)
        try:
            # 语音识别并返回文本
            text = recognizer.recognize_google(audio_data, language='zh-CN')
            return text
        except sr.UnknownValueError:
            return "语音无法识别"
        except sr.RequestError:
            return "服务请求失败"
