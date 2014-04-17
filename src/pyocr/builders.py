"""
Builders: Each builder specifies the expected output format

raw text : TextBuilder
words + boxes : WordBoxBuilder
lines + words + boxes : LineBoxBuilder
"""

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

import re
import xml

from .util import to_unicode

__all__ = [
    'Box',
    'TextBuilder',
    'WordBoxBuilder',
    'LineBoxBuilder',
]

_XHTML_HEADER = to_unicode("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
 "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<head>
\t<meta http-equiv="content-type" content="text/html; charset=utf-8" />
</head>
""")

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
        if hasattr(content, 'decode'):
            content = to_unicode("%s") % content
        self.content = content
        self.position = position

    def get_unicode_string(self):
        """
        Return the string corresponding to the box, in unicode (utf8).
        This string can be stored in a file as-is (see write_box_file())
        and reread using read_box_file().
        """
        return to_unicode("%s %d %d %d %d") % (
            self.content,
            self.position[0][0],
            self.position[0][1],
            self.position[1][0],
            self.position[1][1],
        )

    def get_xml_tag(self, parent_doc):
        span_tag = parent_doc.createElement("span")
        span_tag.setAttribute("class", "ocrx_word")
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
        for (x, y) in ((self.position[0][1], other.position[0][1]),
                           (self.position[1][1], other.position[1][1]),
                           (self.position[0][0], other.position[0][0]),
                           (self.position[1][0], other.position[1][0])):
            if x < y:
                return -1
            elif x > y:
                return 1
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


class LineBox(object):
    """
    Boxes are rectangles around each individual element recognized in the
    image. LineBox are boxes around lines. LineBox contains Box.
    """

    def __init__(self, word_boxes, position):
        """
        Arguments:
            word_boxes --- a single string
            position --- the position of the box on the image. Given as a
                tuple of tuple:
                ((width_pt_x, height_pt_x), (width_pt_y, height_pt_y))
        """
        self.word_boxes = word_boxes
        self.position = position

    def get_unicode_string(self):
        """
        Return the string corresponding to the box, in unicode (utf8).
        This string can be stored in a file as-is (see write_box_file())
        and reread using read_box_file().
        """
        txt = to_unicode("[\n")
        for box in self.word_boxes:
            txt += to_unicode("  %s\n") % box.get_unicode_string()
        return to_unicode("%s] %d %d %d %d") % (
            txt,
            self.position[0][0],
            self.position[0][1],
            self.position[1][0],
            self.position[1][1],
        )

    def __get_content(self):
        txt = to_unicode("")
        for box in self.word_boxes:
            txt += box.content + to_unicode(" ")
        txt = txt.strip()
        return txt

    content = property(__get_content)

    def get_xml_tag(self, parent_doc):
        span_tag = parent_doc.createElement("span")
        span_tag.setAttribute("class", "ocr_line")
        span_tag.setAttribute("title", ("bbox %d %d %d %d" % (
                (self.position[0][0], self.position[0][1],
                 self.position[1][0], self.position[1][1]))))
        for box in self.word_boxes:
            space = xml.dom.minidom.Text()
            space.data = " "
            span_tag.appendChild(space)
            box_xml = box.get_xml_tag(parent_doc)
            span_tag.appendChild(box_xml)
        return span_tag

    def __str__(self):
        return self.get_unicode_string().encode('utf-8')

    def __box_cmp(self, other):
        """
        Comparison function.
        """
        if other == None:
            return -1
        for (x, y) in ((self.position[0][1], other.position[0][1]),
                       (self.position[1][1], other.position[1][1]),
                       (self.position[0][0], other.position[0][0]),
                       (self.position[1][0], other.position[1][0])):
            if (x < y):
                return -1
            elif (x > y):
                return 1
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
        content = self.content
        position_hash = 0
        position_hash += ((self.position[0][0] & 0xFF) << 0)
        position_hash += ((self.position[0][1] & 0xFF) << 8)
        position_hash += ((self.position[1][0] & 0xFF) << 16)
        position_hash += ((self.position[1][1] & 0xFF) << 24)
        return (position_hash ^ hash(content) ^ hash(content))


class TextBuilder(object):
    """
    If passed to image_to_string(), image_to_string() will return a simple
    string. This string will be the output of the OCR tool, as-is. In other
    words, the raw text as produced by the tool.

    Warning:
        The returned string is encoded in UTF-8
    """

    file_extensions = ["txt"]
    tesseract_configs = []
    cuneiform_args = ["-f", "text"]

    def __init__(self, tesseract_layout=3):
        self.tesseract_configs = ["-psm", str(tesseract_layout)]
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


class _WordHTMLParser(HTMLParser):
    """
    Tesseract style: Tesseract provides handy but non-standard hOCR tags:
    ocrx_word
    """

    def __init__(self):
        HTMLParser.__init__(self)

        self.__tag_types = []

        self.__current_box_position = None
        self.__current_box_text = None
        self.boxes = []

        self.__current_line_position = None
        self.__current_line_content = []
        self.lines = []

    @staticmethod
    def __parse_position(title):
        for piece in title.split("; "):
            piece = piece.strip()
            if not piece.startswith("bbox"):
                continue
            piece = piece.split(" ")
            position = ((int(piece[1]), int(piece[2])),
                        (int(piece[3]), int(piece[4])))
            return position
        raise Exception("Invalid hocr position: %s" % title)

    def handle_starttag(self, tag, attrs):
        if (tag != "span"):
            return
        position = None
        tag_type = None
        for attr in attrs:
            if attr[0] == 'class':
                tag_type = attr[1]
            if attr[0] == 'title':
                position = attr[1]
        if position is None or tag_type is None:
            return
        if tag_type == 'ocr_word' or tag_type == 'ocrx_word':
            try:
                position = self.__parse_position(position)
                self.__current_box_position = position
            except Exception:
                # invalid position --> old format --> we ignore this tag
                self.__tag_types.append("ignore")
                return
            self.__current_box_text = to_unicode("")
        elif tag_type == 'ocr_line':
            self.__current_line_position = self.__parse_position(position)
            self.__current_line_content = []
        self.__tag_types.append(tag_type)

    def handle_data(self, data):
        if self.__current_box_text == None:
            return
        data = to_unicode("%s") % data
        self.__current_box_text += data

    def handle_endtag(self, tag):
        if tag != 'span':
            return
        tag_type = self.__tag_types.pop()
        if tag_type == 'ocr_word' or tag_type == 'ocrx_word':
            if (self.__current_box_text == None):
                return
            box_position = self.__current_box_position
            box = Box(self.__current_box_text, box_position)
            self.boxes.append(box)
            self.__current_line_content.append(box)
            self.__current_box_text = None
            return
        elif tag_type == 'ocr_line':
            line = LineBox(self.__current_line_content,
                           self.__current_line_position)
            self.lines.append(line)
            self.__current_line_content = []
            return

    @staticmethod
    def __str__():
        return "WordHTMLParser"


class _LineHTMLParser(HTMLParser):
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
            self.__line_text = to_unicode("")
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


class WordBoxBuilder(object):
    """
    If passed to image_to_string(), image_to_string() will return an array of
    Box. Each box contains a word recognized in the image.
    """

    file_extensions = ["html", "hocr"]
    tesseract_configs = ['hocr']
    cuneiform_args = ["-f", "hocr"]

    def __init__(self):
        pass

    def read_file(self, file_descriptor):
        """
        Extract of set of Box from the lines of 'file_descriptor'

        Return:
            An array of Box.
        """
        parsers = [_WordHTMLParser(), _LineHTMLParser()]
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
        global _XHTML_HEADER

        impl = xml.dom.minidom.getDOMImplementation()
        newdoc = impl.createDocument(None, "root", None)

        file_descriptor.write(_XHTML_HEADER)
        file_descriptor.write(to_unicode("<body>\n"))
        for box in boxes:
            xml_str = to_unicode("%s") % box.get_xml_tag(newdoc).toxml()
            file_descriptor.write(xml_str + to_unicode("<br/>\n"))
        file_descriptor.write(to_unicode("</body>\n"))

    @staticmethod
    def __str__():
        return "Word boxes"


class LineBoxBuilder(object):
    """
    If passed to image_to_string(), image_to_string() will return an array of
    LineBox. Each box contains a word recognized in the image.
    """

    file_extensions = ["html", "hocr"]
    tesseract_configs = ['hocr']
    cuneiform_args = ["-f", "hocr"]

    def __init__(self):
        pass

    def read_file(self, file_descriptor):
        """
        Extract of set of Box from the lines of 'file_descriptor'

        Return:
            An array of LineBox.
        """
        parsers = [
            (_WordHTMLParser(), lambda parser: parser.lines),
            (_LineHTMLParser(), lambda parser: [LineBox([box], box.position)
                                                for box in parser.boxes]),
        ]
        html_str = file_descriptor.read()

        for (parser, convertion) in parsers:
            parser.feed(html_str)
            if len(parser.boxes) > 0:
                return convertion(parser)
        return []

    @staticmethod
    def write_file(file_descriptor, boxes):
        """
        Write boxes in a box file. Output is a *very* *simplified* version
        of hOCR.

        Warning:
            The file_descriptor must support UTF-8 ! (see module 'codecs')
        """
        global _XHTML_HEADER

        impl = xml.dom.minidom.getDOMImplementation()
        newdoc = impl.createDocument(None, "root", None)

        file_descriptor.write(_XHTML_HEADER)
        file_descriptor.write(to_unicode("<body>\n"))
        for box in boxes:
            xml_str = box.get_xml_tag(newdoc).toxml()
            if hasattr(xml_str, 'decode'):
                xml_str = xml_str.decode('utf-8')
            file_descriptor.write(xml_str + to_unicode("<br/>\n"))
        file_descriptor.write(to_unicode("</body>\n"))

    @staticmethod
    def __str__():
        return "Line boxes"
