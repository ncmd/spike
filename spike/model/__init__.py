from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

naxsi_score = ["$SQL", "$RFI", "$TRAVERSAL", "$EVADE", "$XSS", "$UWA", "$ATTACK"]
rulesets_seeds = {'WEB_SERVER', 'APP_SERVER', 'WEB_APPS', 'SCANNER', 'MALWARE'}
naxsi_mz = ["BODY", "ARGS", "HEADERS", "FILE_EXT", "$HEADERS_VAR:Cookie", "$HEADERS_VAR:Content-Type",
            "$HEADERS_VAR:User-Agent", "$HEADERS_VAR:Accept-Encoding", "$HEADERS_VAR:Connection"]
