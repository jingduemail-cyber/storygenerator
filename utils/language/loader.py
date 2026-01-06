from .en import LANG as EN
from .zh import LANG as ZH

def get_language(lang: str):
    return EN if lang == "en" else ZH

