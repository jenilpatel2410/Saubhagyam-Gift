from googletrans import Translator
translator = Translator()

def translate_text(text, lang="en"):
    if lang == "en":
        return text
    try:
        return translator.translate(text, src='en', dest=lang).text
    except Exception:
        return text


def get_lang_code(request):
    try:
        lang = request.headers.get('lang', 'en')
        return lang.lower()
    except:
        return 'en'
    