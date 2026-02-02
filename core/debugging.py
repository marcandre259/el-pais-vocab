from core import db
from core import audio

if __name__ == "__main__":
    words = db.get_all_words()

    audio.generate_audio()
