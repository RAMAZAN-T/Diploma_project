from urllib.parse import urlparse

def url_validator(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

import openpyxl

class WriteExcel:
    def __init__(self, filename):
        self.filename = filename
        self.workbook = openpyxl.Workbook()
        self.sheet = self.workbook.active
    
    def write(self, data):
        for row_index, (exploit_name, result, status) in enumerate(data, start=1):
            self.sheet.append([exploit_name, result, status])
        self.workbook.save(self.filename)
