"""Export the saved library; install the package first with pip install -e ."""
from amazing_tts.preview import build

if __name__ == '__main__':
    print(build())
