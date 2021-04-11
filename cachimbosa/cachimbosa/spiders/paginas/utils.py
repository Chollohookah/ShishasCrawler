import re
import unidecode

class Utils(object):

    def removeSpecificWordsFromString(self, string, wordsToDelete):
        if string is not None:
            edit_string_as_list = string.lower().split()
            final_list = [
                word for word in edit_string_as_list if word not in wordsToDelete]
            final_string = ' '.join(final_list)
            return final_string
        else:
            return ""

    def flattenString(self, string):
        string = string.upper()
        string = string.replace(".", " ")
        string = string.replace(",", " ")
        string = string.replace("-", " ")
        string = string.replace(" ", "")
        string = string.strip()
        string = unidecode.unidecode(string)
        return string

    def cleanhtml(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext