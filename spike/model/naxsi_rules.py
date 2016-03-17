from time import strftime, localtime

from spike.model import db
from shlex import shlex


class NaxsiRules(db.Model):
    __bind_key__ = 'rules'
    __tablename__ = 'naxsi_rules'

    id = db.Column(db.Integer, primary_key=True)
    msg = db.Column(db.String(), nullable=False)
    detection = db.Column(db.String(1024), nullable=False)
    mz = db.Column(db.String(1024), nullable=False)
    score = db.Column(db.String(1024), nullable=False)
    sid = db.Column(db.Integer, nullable=False, unique=True)
    ruleset = db.Column(db.String(1024), nullable=False)
    rmks = db.Column(db.Text, nullable=True, server_default="")
    active = db.Column(db.Integer, nullable=False, server_default="1")
    negative = db.Column(db.Integer, nullable=False, server_default='0')
    timestamp = db.Column(db.Integer, nullable=False)

    mr_kw = ["MainRule", "BasicRule", "main_rule", "basic_rule"]
    static_mz = {"$ARGS_VAR", "$BODY_VAR", "$URL", "$HEADERS_VAR"}
    full_zones = {"ARGS", "BODY", "URL", "HEADERS", "FILE_EXT", "RAW_BODY"}
    rx_mz = {"$ARGS_VAR_X", "$BODY_VAR_X", "$URL_X", "$HEADERS_VAR_X"}
    sub_mz = list(static_mz) + list(full_zones) + list(rx_mz)

    def __init__(self, msg="", detection="", mz="", score="", sid=42000, ruleset="", rmks="", active=0, negative=0,
                 timestamp=0):
        self.msg = msg
        self.detection = detection
        self.mz = mz
        self.score = score
        self.sid = sid
        self.ruleset = ruleset
        self.rmks = rmks
        self.active = active
        self.negative = 1 if negative == 'checked' else 0
        self.timestamp = timestamp
        self.warnings = []
        self.error = []

    def fullstr(self):
        rdate = strftime("%F - %H:%M", localtime(float(str(self.timestamp))))
        rmks = "# ".join(self.rmks.strip().split("\n"))
        return "#\n# sid: {0} | date: {1}\n#\n# {2}\n#\n{3}".format(self.sid, rdate, rmks, self.__str__())

    def __str__(self):
        negate = 'negative' if self.negative == 1 else ''
        return 'MainRule {} "{}" "msg:{}" "mz:{}" "s:{}" id:{} ;'.format(
            negate, self.detection, self.msg, self.mz, self.score, self.sid)

    def explain(self):
        """ Return a string explaining the rule

         :return str: A textual explanation of the rule
         """
        translation = {'ARGS': 'argument', 'BODY': 'body', 'URL': 'url', 'HEADER': 'header'}
        explanation = 'The rule number <strong>%d</strong> is ' % self.sid
        if self.negative:
            explanation += '<strong>not</strong> '
        explanation += 'setting the '

        scores = []
        for score in self.score.split(','):
            scores.append('<strong>{0}</strong> to <strong>{1}</strong> '.format(*score.split(':', 1)))
        explanation += ', '.join(scores) + 'when it '
        if self.detection.startswith('str:'):
            explanation += 'finds the string <strong>{}</strong> '.format(self.detection[4:])
        else:
            explanation += 'matches the regexp <strong>{}</strong> '.format(self.detection[3:])

        zones = []
        for mz in self.mz.split('|'):
            if mz.startswith('$'):
                current_zone, arg = mz.split(":", 1)
                zone_name = "?"

                for translated_name in translation:  # translate zone names
                    if translated_name in current_zone:
                        zone_name = translation[translated_name]

                if "$URL" in current_zone:
                    regexp = "matching regex" if current_zone == "$URL_X" else ""
                    explanation += "on the URL {} '{}' ".format(regexp, arg)
                else:
                    regexp = "matching regex" if current_zone.endswith("_X") else ""
                    explanation += "in the var with name {} '{}' of {} ".format(regexp, arg, zone_name)
            else:
                zones.append('the <strong>{0}</strong>'.format(translation[mz]))
        return explanation

    def validate(self):
        self.__validate_matchzone(self.mz)
        self.__validate_id(self.sid)
        self.__validate_detection(self.detection)

        if not self.msg:
            self.warnings.append("Rule has no 'msg:'.")
        if not self.score:
            self.error.append("Rule has no score.")

    def __fail(self, msg):
        self.error.append(msg)
        return False

    # Bellow are parsers for specific parts of a rule

    def __validate_detection(self, p_str, label="", assign=False):
        p_str = label + p_str
        if not p_str.islower():
            self.warnings.append("detection {} is not lower-case. naxsi is case-insensitive".format(p_str))
        if p_str.startswith("str:") or p_str.startswith("rx:"):
            if assign is True:
                self.detection = p_str
        else:
            return self.__fail("detection {} is neither rx: or str:".format(p_str))
        return True

    def __validate_genericstr(self, p_str, label="", assign=False):
        if assign is False:
            return True
        if label == "s:":
            self.score = p_str
        elif label == "msg:":
            self.msg = p_str
        elif label == "negative":
            self.negative = 1
        elif label != "":
            return self.__fail("Unknown fragment {}".format(label+p_str))
        return True

    def __validate_matchzone(self, p_str, label="", assign=False):
        has_zone = False
        mz_state = set()
        for loc in p_str.split('|'):
            keyword, arg = loc, None
            if loc.startswith("$"):
                if loc.find(":") == -1:
                    return self.__fail("Missing 2nd part after ':' in {0}".format(loc))
                keyword, arg = loc.split(":")

            if keyword not in self.sub_mz:  # check if `keyword` is a valid keyword
                return self.__fail("'{0}' no a known sub-part of mz : {1}".format(keyword, self.sub_mz))

            mz_state.add(keyword)

            # verify that the rule doesn't attempt to target REGEX and STATIC _VAR/URL at the same time
            if len(self.rx_mz & mz_state) and len(self.static_mz & mz_state):
                return self.__fail("You can't mix static $* with regex $*_X ({})".format(', '.join(mz_state)))

            if arg and not arg.islower(): # just a gentle reminder
                self.warnings.append("{0} in {1} is not lowercase. naxsi is case-insensitive".format(arg, loc))

            # the rule targets an actual zone
            if keyword not in ["$URL", "$URL_X"] and keyword in (self.rx_mz | self.full_zones | self.static_mz):
                has_zone = True

        if has_zone is False:
            return self.__fail("The rule/whitelist doesn't target any zone.")

        if assign is True:
            self.mz = p_str

        return True

    def __validate_id(self, p_str, label="", assign=False):
        try:
            num = int(p_str)
            if num < 10000:
                self.warnings.append("rule IDs below 10k are reserved ({0})".format(num))
        except ValueError:
            self.error.append("id:{0} is not numeric".format(p_str))
            return False
        if assign is True:
            self.sid = num
        return True

    @staticmethod
    def splitter(s):
        lexer = shlex(s)
        lexer.whitespace_split = True
        return list(iter(lexer.get_token, ''))

    def parse_rule(self, full_str):
        """
        Parse and validate a full naxsi rule
        :param full_str: raw rule
        :return: [True|False, dict]
        """
        self.warnings = []
        self.error = []

        func_map = {"id:": self.__validate_id, "str:": self.__validate_detection,
                    "rx:": self.__validate_detection, "msg:": self.__validate_genericstr,
                    "mz:": self.__validate_matchzone, "negative": self.__validate_genericstr,
                    "s:": self.__validate_genericstr}
        ret = False
        split = self.splitter(full_str)  # parse string
        intersection = set(split).intersection(set(self.mr_kw))

        if not intersection:
            return self.__fail("No mainrule/basicrule keyword.")
        elif len(intersection) > 1:
            return self.__fail("Multiple mainrule/basicrule keywords.")

        split.remove(intersection.pop())  # remove the mainrule/basicrule keyword

        if ";" in split:
            split.remove(";")

        while split:  # iterate while there is data, as handlers can defer
            for keyword in split:
                orig_kw = keyword
                keyword = keyword.strip()

                if keyword.endswith(";"):  # remove semi-colons
                    keyword = keyword[:-1]
                if keyword.startswith(('"', "'")) and (keyword[0] == keyword[-1]):  # remove (double-)quotes
                    keyword = keyword[1:-1]

                for frag_kw in func_map:
                    ret = False
                    if keyword.startswith(frag_kw):
                        # parser funcs returns True/False
                        ret = func_map[frag_kw](keyword[len(frag_kw):], label=frag_kw, assign=True)
                        if ret is True:
                            split.remove(orig_kw)
                        else:
                            return self.__fail("parsing of element '{0}' failed.".format(keyword))
                        break

                if orig_kw in split and ret is not None:  # we have an item that wasn't successfully parsed
                    return False
        return True
