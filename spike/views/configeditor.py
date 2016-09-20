try:
    from urlparse import parse_qs
except ImportError:  # python3
    from urllib.parse import parse_qs

from flask import Blueprint, render_template, current_app, request, flash, redirect
import json
import pprint
import re
from spike.lib.pynaxsiconfig import NginxNaxsiConfig

configeditor = Blueprint('configeditor', __name__)


def load_fqdn_from_file(rfqdn, ssl="on"):
    cfg_dump = current_app.config["NGINX_CFG_DUMP"]
    x = open(cfg_dump, 'r')
    js = json.loads(x.read())
    for group in js.keys():
        for dict in js[group]:
            if rfqdn in dict.keys() and dict[rfqdn]["summary"]["ssl"] == ssl:
                return dict[rfqdn]
    return {}

def load_location_from_fqdn(location, fqdn_data):
    if fqdn_data is None:
        return None
    for t in fqdn_data["locations"].keys():
        if t == location:
            return fqdn_data["locations"][location]
    return None


def apply_change(old_rx, newline, filename, append=None):
    print "apply change : replace {0} by {1} in {2} (or append {3})".format(old_rx, newline, filename, append)
    if filename is None:
        newtext = "#No config file to edit"
        return newtext
    fd = open(filename, "r")
    newtext = "#Suggested diff for : {0}\n".format(filename)
    edited_lines = 0
    if not fd:
        return -1
    for line in fd:
        if old_rx is not None and re.match(old_rx, line):
            print "found/replace line {0}".format(line)
            newtext += "#" + line
            newtext += newline + "\n"
            edited_lines += 1
        else:
            newtext += line
    fd.close()
    if append is not None:
        newtext += "\n#automatically append\n{0}\n".format(append)
    return newtext


@configeditor.route("/write/", methods=["POST"])
def write():
    fqdn = request.form["fqdn"]
    loc_name = request.form["location"]

    location = load_location_from_fqdn(loc_name, load_fqdn_from_file(fqdn))
    if location is None:
        flash("Unable to load fqdn/location.")
        return "bad fqdn."

    txt = ""
    # check if checkrules changed
    for key in request.form.keys():
        val = request.form[key]
        print "checking key/val : {0} / {1}".format(key, val)
        # recreate checkrule label
        if key.startswith("checkrule"):
            label = "_".join(key.split("_")[1:-1])
            for orig_cr in location["checkrules"]:
                if orig_cr["label"] == label:
                    if orig_cr["action"] != val:
                        newline = "CheckRule '{0} {1} {2}' {3};".format(orig_cr["label"], orig_cr["operator"],
                                                                        orig_cr["score"], val)
                        find_rx = r"^\s*CheckRule\s+(['\"])\s*({0})\s*({1})\s*({2})\s*\\1\s*({3})\s*;.*$".format(
                                    orig_cr["label"].replace("$", "\$"),
                                    orig_cr["operator"],
                                    orig_cr["score"],
                                    orig_cr["action"])
                        txt = apply_change(find_rx, newline, orig_cr["fname"])
        elif key == "naxsi" and location["summary"]["naxsi"] != val:
            #off -> on (absent, or SecRulesDisabled)
            if val == "on":
                find_rx = r"^\s*SecRulesDisabled\s*;.*$"
                newline = "#"
                append = "SecRulesEnabled;"
            #on -> off ()
            elif val == "off":
                find_rx = r"^\s*SecRulesEnabled\s*;.*$"
                newline = "SecRulesDisabled;"
                append = ""
            txt = apply_change(find_rx, newline, location["summary"].get("naxsi_path"))
        elif key == "learning" and location["summary"]["naxsi_learning"] != val:
            #off -> on
            if val == "on":
                find_rx = None
                newline = None
                append = "LearningMode;"
            #on -> off
            elif val == "off":
                find_rx = r"^\s*LearningMode\s*;.*$"
                newline = ""
                append = None
            txt = apply_change(find_rx, newline, location["summary"].get("naxsi_path"), append=append)
        elif key not in ["location", "fqdn"]:
            flash("unexpected data : {0} - {1}".format(key, val))
    if txt is not "":
        return txt
    return "ok."


@configeditor.route("/force-load", methods=["GET"])
def force_load():
    print "forcing load ..."
    cfg = NginxNaxsiConfig()
    cfg.process_arbo()
    flash("Loaded configuration")
    return redirect("/configeditor")
    pass

@configeditor.route("/", methods=["GET"])
@configeditor.route("/<fqdn>", methods=["GET"])
@configeditor.route("/<fqdn>/<ssl>", methods=["GET"])
def index(fqdn=None, ssl="on"):
    cfg = NginxNaxsiConfig()

    if fqdn is None:
        all = cfg.load_current_config()
        return render_template("configeditor/fqdn-list.html", all=all, nginx_dir=current_app.config["NGINX_CFG_DIR"])

    datas = load_fqdn_from_file(fqdn, ssl)
    pprint.pprint(datas)
    return render_template("configeditor/index.html", fqdn=fqdn,
                           data=datas)
