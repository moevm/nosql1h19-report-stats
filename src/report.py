from docx import Document

class Report:
    def __init__(self, docx_text, meta, text_processor):
        self.document = Document(docx_text)
        
        self.date = self.document.core_properties.modified
        self.title = meta['title']
        self.author = meta['author']
        self.group = meta['group']
        self.department = meta['department']
        self.course = meta['course']
        self.faculty = meta['faculty']
        
        raw_text = ' '.join([par.text for par in self.document.paragraphs])
        processed_text = text_processor.process(raw_text)

        self.text = processed_text['text']
        self.text.pop('clean_text', None) # Не храним очищенный текст

        self.words = processed_text['words']
        self.words.pop('words', None) # Не храним все слова

        self.symbols = processed_text['symbols']

    def serialize_db(self):
        serialized_document = {
            'title': self.title,
            'date': self.date,
            'author': self.author,
            'group': self.group,
            'department': self.department,
            'course': self.course,
            'faculty': self.faculty,
            'text': self.text,
            'words': self.words,
            'symbols': self.symbols
        }

        return serialized_document
