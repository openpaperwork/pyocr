"""
Builders: Each builder specifies the expected output format

raw text : TextBuilder
word + boxes : WordBoxBuilder
"""

from HTMLParser import HTMLParser
import re
import xml

__all__ = [
    'Box',
    'TextBuilder',
    'WordBoxBuilder',
]


class Box(object):
    """
    Boxes are rectangles around each individual element recognized in the
    image. Elements are either char or word depending of the builder that
    was used.
    """

    def __init__(self, content, position):
        """
        Arguments:
            content --- a single string
            position --- the position of the box on the image. Given as a
                tuple of tuple:
                ((width_pt_x, height_pt_x), (width_pt_y, height_pt_y))
        """
        self.content = unicode(content)
        self.position = position

    def get_unicode_string(self):
        """
        Return the string corresponding to the box, in unicode (utf8).
        This string can be stored in a file as-is (see write_box_file())
        and reread using read_box_file().
        """
        return u"%s %d %d %d %d" % (
            self.content,
            self.position[0][0],
            self.position[0][1],
            self.position[1][0],
            self.position[1][1],
        )

    def get_xml_tag(self):
        span_tag = xml.dom.minidom.Element("span")
        span_tag.setAttribute("class", "ocr_word")
        span_tag.setAttribute("title", ("bbox %d %d %d %d" % (
                (self.position[0][0], self.position[0][1],
                 self.position[1][0], self.position[1][1]))))
        txt = xml.dom.minidom.Text()
        txt.data = self.content.encode('utf-8')
        span_tag.appendChild(txt)
        return span_tag

    def __str__(self):
        return self.get_unicode_string().encode('utf-8')

    def __box_cmp(self, other):
        """
        Comparison function.
        """
        if other == None:
            return -1
        for cmp_result in (cmp(self.position[0][1], other.position[0][1]),
                           cmp(self.position[1][1], other.position[1][1]),
                           cmp(self.position[0][0], other.position[0][0]),
                           cmp(self.position[1][0], other.position[1][0])):
            if cmp_result != 0:
                return cmp_result
        return 0

    def __lt__(self, other):
        return self.__box_cmp(other) < 0

    def __gt__(self, other):
        return self.__box_cmp(other) > 0

    def __eq__(self, other):
        return self.__box_cmp(other) == 0

    def __le__(self, other):
        return self.__box_cmp(other) <= 0

    def __ge__(self, other):
        return self.__box_cmp(other) >= 0

    def __ne__(self, other):
        return self.__box_cmp(other) != 0

    def __hash__(self):
        position_hash = 0
        position_hash += ((self.position[0][0] & 0xFF) << 0)
        position_hash += ((self.position[0][1] & 0xFF) << 8)
        position_hash += ((self.position[1][0] & 0xFF) << 16)
        position_hash += ((self.position[1][1] & 0xFF) << 24)
        return (position_hash ^ hash(self.content) ^ hash(self.content))


class TextBuilder(object):
    """
    If passed to image_to_string(), image_to_string() will return a simple
    string. This string will be the output of the OCR tool, as-is. In other
    words, the raw text as produced by the tool.

    Warning:
        The returned string is encoded in UTF-8
    """

    file_extension = "txt"
    tesseract_configs = []
    cuneiform_args = ["-f", "text"]

    def __init__(self):
        pass

    @staticmethod
    def read_file(file_descriptor):
        """
        Read a file and extract the content as a string
        """
        return file_descriptor.read().strip()

    @staticmethod
    def write_file(file_descriptor, text):
        """
        Write a string in a file
        """
        file_descriptor.write(text)

    @staticmethod
    def __str__():
        return "Raw text"


class WordBoxBuilder(object):
    """
    If passed to image_to_string(), image_to_string() will return an array of
    Box. Each box contains a word recognized in the image.
    """

    file_extension = "html"
    tesseract_configs = ['hocr']
    cuneiform_args = ["-f", "hocr"]

    def __init__(self):
        pass

    class WordHTMLParser(HTMLParser):
        """
        Tesseract style: Tesseract provides handy but non-standard hOCR tags:
        ocr_word
        """
        def __init__(self):
            HTMLParser.__init__(self)
            self.__current_box_position = None
            self.__current_box_text = None
            self.boxes = []

        @staticmethod
        def __parse_position(title):
            title = title.split("; ")
            title = title[-1]
            title = title.split(" ")
            position = ((int(title[1]), int(title[2])),
                        (int(title[3]), int(title[4])))
            return position

        def handle_starttag(self, tag, attrs):
            if (tag != "span"):
                return
            position = None
            for attr in attrs:
                if (attr[0] == 'class'
                    and (attr[1] != 'ocr_word')):
                    return
                if attr[0] == 'title':
                    position = attr[1]
            if position == None:
                return
            self.__current_box_position = self.__parse_position(position)
            self.__current_box_text = u""

        def handle_data(self, data):
            if self.__current_box_text == None:
                return
            self.__current_box_text += data

        def handle_endtag(self, tag):
            if (self.__current_box_text == None):
                return
            box_position = self.__current_box_position
            box = Box(self.__current_box_text, box_position)
            self.boxes.append(box)
            self.__current_box_text = None

        @staticmethod
        def __str__():
            return "WordHTMLParser"

    class LineHTMLParser(HTMLParser):
        """
        Cuneiform style: Cuneiform provides the OCR line by line, and for each
        line, the position of all its characters.
        Spaces have "-1 -1 -1 -1" for position".
        """
        def __init__(self):
            HTMLParser.__init__(self)
            self.boxes = []
            self.__line_text = None
            self.__char_positions = None

        def handle_starttag(self, tag, attrs):
            TAG_TYPE_CONTENT = 0
            TAG_TYPE_POSITIONS = 1

            if (tag != "span"):
                return
            tag_type = -1
            for attr in attrs:
                if attr[0] == 'class':
                    if attr[1] == 'ocr_line':
                        tag_type = TAG_TYPE_CONTENT
                    elif attr[1] == 'ocr_cinfo':
                        tag_type = TAG_TYPE_POSITIONS

            if tag_type == TAG_TYPE_CONTENT:
                self.__line_text = u""
                self.__char_positions = []
                return
            elif tag_type == TAG_TYPE_POSITIONS:
                for attr in attrs:
                    if attr[0] == 'title':
                        self.__char_positions = attr[1].split(" ")
                # strip x_bboxes
                self.__char_positions = self.__char_positions[1:]
                if self.__char_positions[-1] == "":
                    self.__char_positions[:-1]
                try:
                    while True:
                        self.__char_positions.remove("-1")
                except ValueError:
                    pass

        def handle_data(self, data):
            if self.__line_text == None:
                return
            self.__line_text += data

        def handle_endtag(self, tag):
            if self.__line_text == None or self.__char_positions == []:
                return
            words = self.__line_text.split(" ")
            for word in words:
                if word == "":
                    continue
                positions = self.__char_positions[0:4 * len(word)]
                self.__char_positions = self.__char_positions[4 * len(word):]

                left_pos = min([int(positions[x])
                                for x in range(0, 4 * len(word), 4)])
                top_pos = min([int(positions[x])
                               for x in range(1, 4 * len(word), 4)])
                right_pos = max([int(positions[x])
                                 for x in range(2, 4 * len(word), 4)])
                bottom_pos = max([int(positions[x])
                                  for x in range(3, 4 * len(word), 4)])

                box_pos = ((left_pos, top_pos), (right_pos, bottom_pos))
                box = Box(word, box_pos)
                self.boxes.append(box)
            self.__line_text = None

        @staticmethod
        def __str__():
            return "LineHTMLParser"

    def read_file(self, file_descriptor):
        """
        Extract of set of Box from the lines of 'file_descriptor'

        Return:
            An array of Box.
        """
        parsers = [self.WordHTMLParser(), self.LineHTMLParser()]
        html_str = file_descriptor.read()

        for p in parsers:
            p.feed(html_str)
            if len(p.boxes) > 0:
                return p.boxes
        return []

    @staticmethod
    def write_file(file_descriptor, boxes):
        """
        Write boxes in a box file. Output is a *very* *simplified* version
        of hOCR.

        Warning:
            The file_descriptor must support UTF-8 ! (see module 'codecs')
        """
        file_descriptor.write(u"<body>\n")
        for box in boxes:
            xml_str = box.get_xml_tag().toxml()
            xml_utf = xml_str.decode('utf-8')
            file_descriptor.write(xml_utf + u"\n")
        file_descriptor.write(u"</body>\n")

    @staticmethod
    def __str__():
        return "Word boxes"
