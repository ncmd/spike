try:
    from urlparse import parse_qs
except ImportError:  # python3
    from urllib.parse import parse_qs
import logging
from time import time

from flask import Blueprint, render_template, request, redirect, flash, Response, url_for

from spike.model import db
from spike.model.naxsi_whitelist import NaxsiWhitelist
from spike.model.naxsi_whitelistsets import NaxsiWhitelistSets
from spike.model import naxsi_mz

whitelists = Blueprint('whitelists', __name__)


@whitelists.route("/")
def index():
    _wlist = NaxsiWhitelist.query.order_by(NaxsiWhitelist.wl.desc()).all()
    if not _wlist:
        flash("No whitelist found, please create one", "success")
        return redirect(url_for('whitelists.new'))
    return render_template("whitelists/index.html", whitelists=_wlist)


@whitelists.route("/plain/<string:wid>", methods=["GET"])
def plain(wid):
    _wlist = NaxsiWhitelist.query.filter(NaxsiWhitelist.id == wid).first()
    if not _wlist:
        flash("No rules found, please create one", "error")
        return redirect(url_for('whitelists.index'))
    return Response(str(_wlist), mimetype='text/plain')


@whitelists.route("/view/<int:wid>", methods=["GET"])
def view(wid):
    _wlist = NaxsiWhitelist.query.filter(NaxsiWhitelist.id == wid).first()
    if _wlist is None:
        flash("The whitelist %d was not found." % wid, "error")
        return redirect(url_for('whitelists.index'))
    return render_template("whitelists/view.html", whitelist=_wlist)


@whitelists.route("/edit/<string:wid>", methods=["GET"])
def edit(wid):
    return redirect(url_for('whitelists.new'))


@whitelists.route("/del/<string:wid>", methods=["GET"])
def del_sid(wid):
    _wlist = NaxsiWhitelist.query.filter(NaxsiWhitelist.id == wid).first()
    if not _wlist:
        return redirect(url_for('whitelists.index'))

    db.session.delete(_wlist)
    db.session.commit()

    flash("Successfully deleted %s" % wid, "success")
    return redirect(url_for('whitelists.index'))


@whitelists.route("/generate", methods=["GET", "POST"])
def generate():
    if request.method == "GET":
        return render_template("misc/whitelist_generator.html")
    nxlogs = request.form.get('nxlogs', '')

    if not nxlogs:
        flash('Please input nxlogs')
        return render_template("misc/whitelist_generator.html")

    whitelist = set()
    for nxlog in nxlogs.split('\n'):
        nxlog = nxlog.strip()
        if not nxlog:
            continue
        start = nxlog.find("ip=")
        if start < 0:
            flash('{} is an invalid extlog, string "ip=" not found.'.format(nxlog))
            return render_template("misc/whitelist_generator.html", nxlogs=nxlogs)

        end = nxlog.find(", ")
        if end < 0:
            flash('{} is an invalid extlog, string "," not found.'.format(nxlog))
            return render_template("misc/whitelist_generator.html", nxlogs=nxlogs)

        # Flatten the dict, since parse_qs is a bit annoying
        nxdic = parse_qs(nxlog[start:end])
        for key, value in nxdic.items():
            nxdic[key] = value[0]

        cpt = 0
        while "id{}".format(cpt) in nxdic:
            _id = "id{}".format(cpt)
            _var_name = "var_name{}".format(cpt)
            _zone = "zone{}".format(cpt)
            if nxdic[_zone].endswith('|NAME'):
                if "var_name{}".format(cpt) in nxdic:
                    whitelist.add('BasicRule wl:{} "mz:${}_VAR:{}|NAME"'.format(nxdic[_id], nxdic[_zone][:4], nxdic[_var_name]))
                else:
                    whitelist.add('BasicRule wl:{} "mz:{}"'.format(nxdic[_id], nxdic[_zone]))
            elif "var_name{}".format(cpt) in nxdic:
                whitelist.add('BasicRule wl:{} "mz:{}:{}"'.format(nxdic[_id], "$"+nxdic[_zone]+"_VAR", nxdic[_var_name]))
            else:
                whitelist.add('BasicRule wl:{} "mz:{}"'.format(nxdic[_id], nxdic[_zone]))
            cpt += 1
    return render_template("misc/whitelist_generator.html", whitelist='<br>'.join(whitelist) + ';', nxlogs=nxlogs)


@whitelists.route('/new', methods=["GET", "POST"])
def new():
    if request.method == "GET":
        _whitelistesets = NaxsiWhitelistSets.query.all()
        return render_template('whitelists/new.html', matchzones=naxsi_mz, whitelistsets=_whitelistesets)

    logging.debug('Posted new request: %s', request.form)

    mz = request.form.getlist("mz") + request.form.getlist("custom_mz_val")
    wid = request.form.get('wl', '')
    whitelistset = request.form.get("whitelistset", '')

    if not wid:
        flash('Please enter a wl', category='error')
        return render_template('whitelists/new.html')
    elif not whitelistset:
        flash('Please enter a whitelistset', category='error')
        return render_template('whitelists/new.html')

    wlist = NaxsiWhitelist(wl=wid, timestamp=int(time()),
                           whitelistset=whitelistset, mz=mz, active=1,
                           negative=request.form.get("negative", "") == 'checked')
    errors, warnings = wlist.validate()

    if errors:
        flash(",".join(errors), 'error')
        return redirect(url_for('whitelists.new'))
    elif warnings:
        flash(",".join(warnings), 'warning')

    wlist.mz = '|'.join(wlist.mz)
    db.session.add(wlist)
    db.session.commit()

    return render_template('whitelists/index.html')
