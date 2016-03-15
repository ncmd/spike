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

    warnings = []
    error = []
    mr_kw = ["MainRule", "BasicRule", "main_rule", "basic_rule"]
    static_mz = {"$ARGS_VAR", "$BODY_VAR", "$URL", "$HEADERS_VAR"}
    full_zones = {"ARGS", "BODY", "URL", "HEADERS", "FILE_EXT", "RAW_BODY"}
    rx_mz = {"$ARGS_VAR_X", "$BODY_VAR_X", "$URL_X", "$HEADERS_VAR_X"}
    sub_mz = list(static_mz) + list(full_zones) + list(rx_mz)

    def __init__(self, msg, detection, mz, score, sid, ruleset, rmks, active, negative, timestamp):
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

    def fullstr(self):
        rdate = strftime("%F - %H:%M", localtime(float(str(self.timestamp))))
        rmks = "# ".join(self.rmks.strip().split("\n"))
        return "#\n# sid: {0} | date: {1}\n#\n# {2}\n#\n{3}".format(self.sid, rdate, rmks, self.__str__())

    def __str__(self):
        negate = 'negative' if self.negative == 1 else ''
        return 'MainRule {} "{}" "msg:{}" "mz:{}" "s:{}" id:{} ;'.format(
            negate, self.detection, self.msg, self.mz, self.score, self.sid)

    def validate(self):
        self.p_mz(self.mz)
        self.p_id(self.sid)
        self.p_detection(self.detection)

        if not self.msg:
            self.warnings.append("Rule has no 'msg:'.")
        if not self.score:
            self.error.append("Rule has no score.")

    def fail(self, msg):
        self.error.append(msg)
        return False

    # Bellow are parsers for specific parts of a rule
    def p_dummy(self, s, assign=False):
        return True

    def p_detection(self, s, assign=False):
        if not s.startswith("str:") and not s.startswith("rx:"):
            self.fail("detection {} is neither rx: or str:".format(s))
        if not s.islower():
            self.warnings.append("detection {} is not lower-case. naxsi is case-insensitive".format(s))
        if assign is True:
            self.detection = s
        return True

    def p_genericstr(self, s, assign=False):
        if s and not s.islower():
            self.warnings.append("Pattern ({0}) is not lower-case.".format(s))
        return True

    def p_mz(self, s, assign=False):
        has_zone = False
        mz_state = set()
        locs = s.split('|')
        for loc in locs:
            kw = loc
            arg = None
            if loc.startswith("$"):
                try:
                    kw, arg = loc.split(":")
                except ValueError:
                    return self.fail("Missing 2nd part after ':' in {0}".format(loc))
            # check it is a valid keyword
            if kw not in self.sub_mz:
                return self.fail("'{0}' no a known sub-part of mz : {1}".format(kw, self.sub_mz))
            mz_state.add(kw)
            # verify the rule doesn't attempt to target REGEX and STATIC _VAR/URL at the same time
            if len(self.rx_mz & mz_state) and len(self.static_mz & mz_state):
                return self.fail("You can't mix static $* with regex $*_X ({})".format(str(mz_state)))
            # just a gentle reminder
            if arg and arg.islower() is False:
                self.warnings.append("{0} in {1} is not lowercase. naxsi is case-insensitive".format(arg, loc))
            # the rule targets an actual zone
            if kw not in ["$URL", "$URL_X"] and kw in (self.rx_mz | self.full_zones | self.static_mz):
                has_zone = True
        if has_zone is False:
            return self.fail("The rule/whitelist doesn't target any zone.")
        if assign is True:
            self.mz = s
        return True

    def p_id(self, s, assign=False):
        try:
            x = int(s)
            if x < 10000:
                self.warnings.append("rule IDs below 10k are reserved ({0})".format(x))
        except ValueError:
            self.error.append("id:{0} is not numeric".format(s))
            return False
        if assign is True:
            self.sid = x
        return True

    @staticmethod
    def splitter(s):
        lexer = shlex(s)
        lexer.quotes = '"\''
        lexer.whitespace_split = True
        items = list(iter(lexer.get_token, ''))
        return ([i for i in items if i[0] in "\"'"] +
                [i for i in items if i[0] not in "\"'"])

    def parse_rule(self, x):
        """
        Parse and validate a full naxsi rule
        :param x: raw rule
        :return: [True|False, dict]
        """
        xfrag_kw = {"id:": self.p_id, "str:": self.p_genericstr,
                    "rx:": self.p_genericstr, "msg:": self.p_dummy, "mz:": self.p_mz,
                    "negative": self.p_dummy, "s:": self.p_dummy}

        split = self.splitter(x)  # parse string


        sect = set(self.mr_kw) & set(split) # check if it's a MainRule/BasicRule, store&delete kw

        if len(sect) != 1:
            return self.fail("no (or multiple) mainrule/basicrule keyword.")

        split.remove(sect.pop())

        if ";" in split:
            split.remove(";")

        while True:  # iterate while there is data, as handlers can defer

            if not split: # we are done
                break

            for kw in split:
                okw = kw
                kw = kw.strip()

                # clean-up quotes or semicolon
                if kw.endswith(";"):
                    kw = kw[:-1]
                if kw.startswith(('"', "'")) and (kw[0] == kw[-1]):
                    kw = kw[1:-1]
                for frag_kw in xfrag_kw:
                    ret = False
                    if kw.startswith(frag_kw):
                        # parser funcs returns True/False
                        ret = xfrag_kw[frag_kw](kw[len(frag_kw):])
                        if ret is False:
                            return self.fail("parsing of element '{0}' failed.".format(kw))
                        if ret is True:
                            split.remove(okw)
                        break
                # we have an item that wasn't successfully parsed
                if okw in split and ret is not None:
                    return False
        return True
