vtemplate_seeds = {

    'naxsi_score': ["$SQL", "$RFI", "$TRAVERSAL", "$EVADE", "$XSS", "$UWA", "$ATTACK"],
    'naxsi_mz': ["BODY", "ARGS", "HEADERS", "FILE_EXT",
                 "$HEADERS_VAR:Cookie", "$HEADERS_VAR:Content-Type", "$HEADERS_VAR:User-Agent",
                 "$HEADERS_VAR:Accept-Encoding", "$HEADERS_VAR:Connection"],
}

rulesets_seeds = {
    'WEB_SERVER': 'web_server.rules',
    'APP_SERVER': 'app_server.rules',
    'WEB_APPS': 'web_apps.rules',
    'SCANNER': 'scanner.rules',
    'MALWARE': 'malware.rules',
}

settings_seeds = {

    'rules_offset': '200000',
}
