from ebooklib import epub
from bs4 import BeautifulSoup
from googletrans import Translator
import re

translator = Translator()

def clean_text(text):
    return (
        text
        .replace('"', '—')   # comillas dobles
        .replace("'", '—')   # comillas simples
        .replace('“', '—')   # comillas tipográficas izquierda
        .replace('”.', '—')   # comillas tipográficas derecha
        .replace('‘', '—')   # comillas simples tipográficas izquierda
        .replace('’.', '—')   # comillas simples tipográficas derecha
    )

def translate_text(text):
    if not text.strip():
        return text
    detected = translator.detect(text)
    translated = translator.translate(text, src=detected.lang, dest='es')
    return translated.text

def extract_text_from_epub(epub_path):
    book = epub.read_epub(epub_path)
    chapters = []

    for item in book.items:
        if item.get_type() == 9:  # ITEM_DOCUMENT
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            text = soup.get_text()
            chapters.append((item.get_id(), text))
    
    return chapters, book

def translate_epub(input_path, output_path, progress_callback=lambda c, t: None):
    chapters, original_book = extract_text_from_epub(input_path)
    translated_book = epub.EpubBook()

    translated_book.set_identifier('translated-book')
    translated_book.set_title('Libro traducido')
    translated_book.set_language('es')
    translated_book.add_author('Traductor Automático')

    translated_items = []
    total = len(chapters)

    for i, (chap_id, chapter_text) in enumerate(chapters):
        translated = translate_text(chapter_text)
        translated = replace_quotes_with_dashes(translated)

        html_body = "<html><body><p>{}</p></body></html>".format(translated.replace('\n', '<br/>'))
        c = epub.EpubHtml(title=f'Capítulo {i+1}', file_name=f'chap_{i+1}.xhtml', lang='es')
        c.content = html_body
        translated_book.add_item(c)
        translated_items.append(c)

        progress_callback(i + 1, total)

    translated_book.toc = tuple(translated_items)
    translated_book.spine = ['nav'] + translated_items
    translated_book.add_item(epub.EpubNcx())
    translated_book.add_item(epub.EpubNav())

    epub.write_epub(output_path, translated_book)
