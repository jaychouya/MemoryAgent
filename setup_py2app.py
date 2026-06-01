"""Setup script for MemoryAgent macOS app."""

from setuptools import setup

APP = ['src/main.py']
DATA_FILES = [
    ('', ['requirements.txt']),
    ('backend', ['src/backend/main.py']),
]

OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'uvicorn',
        'fastapi',
        'pydantic',
        'openai',
        'anthropic',
        'httpx',
        'tiktoken',
    ],
    'includes': [
        'src.backend.main',
        'src.agent.loop',
        'src.memory.tree',
    ],
    'excludes': ['tkinter'],
    'iconfile': 'assets/icon.icns',
    'plist': {
        'CFBundleName': 'MemoryAgent',
        'CFBundleDisplayName': 'MemoryAgent',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    }
}

setup(
    name='MemoryAgent',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
