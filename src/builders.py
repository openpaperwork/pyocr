import xml

__all__ = [
    'Box',
    'TextBuilder',
    'WordBoxBuilder',
]


class Box(object):
    """
    Boxes are rectangles around each individual element recognized in the image.
    Elements are either char or word depending of the builder that was used.
    """

    def __init__(self, content, position):
        """
        Arguments:
            content --- a single string
            position --- the position of the box on the image. Given as a
                tuple of tuple:
                ((width_pt_x, height_pt_x), (width_pt_y, height_pt_y))
        """
        self.content = content
        self.position = position

    def get_unicode_string(self):
        """
        Return the string corresponding to the box, in unicode (utf8).
        This string can be stored in a file as-is (see write_box_file())
        and reread using read_box_file().
        """
        return "%s %d %d %d %d" % (
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
        txt.data = self.content
        span_tag.appendChild(txt)
        return span_tag

    def __str__(self):
        return self.get_unicode_string().encode('ascii', 'replace')

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

    def __init__(self):
        pass

    @staticmethod
    def __parse_position(xml_tag):
        title = xml_tag.getAttribute("title")
        title = title.split("; ")
        title = title[-1]
        title = title.split(" ")
        position = ((int(title[1]), int(title[2])),
                    (int(title[3]), int(title[4])))
        return position

    @staticmethod
    def __extract_txt(xml_tag):
        txt = u""
        for tag in xml_tag.childNodes:
            if tag.nodeType == tag.TEXT_NODE:
                txt += tag.wholeText
            else:
                txt += WordBoxBuilder.__extract_txt(tag)
        return txt

        element = elements[0]

    @staticmethod
    def read_file(file_descriptor):
        """
        Extract of set of Box from the lines of 'file_descriptor'

        Return:
            An array of Box.
        """
        xml_string = file_descriptor.read().encode("utf-8")
        xml_doc = xml.dom.minidom.parseString(xml_string)
        boxes = []
        for tag in xml_doc.getElementsByTagName("span"):
            if ("ocr_word" != tag.getAttribute("class")):
                continue
            txt = WordBoxBuilder.__extract_txt(tag)
            position = WordBoxBuilder.__parse_position(tag)
            box = Box(txt, position)
            boxes.append(box)
        return boxes

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
            file_descriptor.write(box.get_xml_tag().toxml() + u"\n")
        file_descriptor.write(u"</body>\n")

    @staticmethod
    def __str__():
        return "Word boxes"

