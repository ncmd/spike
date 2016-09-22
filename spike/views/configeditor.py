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



#todo : fix the fact that main_file points to the previous one rather than the current one ^^



def apply_change(old_rx, newline, filename, append=None):
    print "apply change : replace {0} by {1} in {2} (or append {3})".format(old_rx, newline, filename, append)
    if filename is None:
        newtext = "#No config file to edit<br>\n"
        return newtext
    fd = open(filename, "r")
    newtext = "#Suggested diff for : {0}<br>\n<br>".format(filename)
    edited_lines = 0
    if not fd:
        return -1
    for line in fd:
        if old_rx is not None and re.match(old_rx, line):
            print "found/replace line {0}".format(line)
            newtext += "#" + line + "<br>\n"
            newtext += newline + "<br>\n"
            edited_lines += 1
        else:
            newtext += line + "<br>\n"
    fd.close()
    if append is not None:
        newtext += "\n#automatically append<br>\n{0}<br>\n".format(append)
    return newtext


@configeditor.route("/write/", methods=["POST"])
def write():
    fqdn = request.form["fqdn"]
    loc_name = request.form["location"]
    ssl = request.form["ssl"]
    nx = NginxNaxsiConfig()
    append = ""

    location = nx.load_location_from_fqdn(loc_name, nx.load_fqdn_from_file(fqdn, ssl))
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
                append = ""
            txt = apply_change(find_rx, newline, location["summary"].get("naxsi_learning_path"), append=append)
        elif key not in ["location", "fqdn"]:
            flash("unexpected data : {0} - {1}".format(key, val))
    if append is not "":
        txt += "#Append this line :<br>\n{0}<br>\n".format(append)
    if txt is not "":
        #location
        txt = "#Included from {0}<br>\n".format(location["summary"]["main_file"]) + txt
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

@configeditor.route("/<fqdn>/<ssl>", methods=["GET"])
@configeditor.route("/<fqdn>", methods=["GET"])
@configeditor.route("/", methods=["GET"])
def index(fqdn=None, ssl="on"):
    cfg = NginxNaxsiConfig()
    if fqdn is None:
        all = cfg.load_current_config()
        return render_template("configeditor/fqdn-list.html", all=all, nginx_dir=current_app.config["NGINX_CFG_DIR"])

    nx = NginxNaxsiConfig()
    datas = nx.load_fqdn_from_file(fqdn, ssl)
    return render_template("configeditor/index.html", fqdn=fqdn,
                           data=datas)
