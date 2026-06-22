#!/usr/bin/gawk -f

BEGIN {
    port = 8080
    print "DOOMLESS server starting on port " port
    server = "/inet/tcp/" port "/0/0"

    while (1) {
        body = ""
        method = ""
        path = ""
        content_length = 0

        while ((server |& getline line) > 0) {
            sub(/\r/, "", line)
            if (line == "") break

            if (method == "") {
                split(line, parts, " ")
                method = parts[1]
                path   = parts[2]
            }
            if (line ~ /^Content-Length:/) {
                split(line, cl, ": ")
                content_length = int(cl[2])
            }
        }

        if (content_length > 0) {
            for (i = 1; i <= content_length; i++) {
                server |& getline char
                body = body char
            }
        }

        if (path == "/" || path == "/index.html") {
            response = serve_file("frontend/index.html", "text/html")
        } else if (path == "/interests.html") {
            response = serve_file("frontend/interests.html", "text/html")
        } else if (path == "/history.html") {
            response = serve_file("frontend/history.html", "text/html")
        } else if (path == "/suggest" && method == "POST") {
            response = handle_suggest(body)
        } else if (path == "/log" && method == "POST") {
            response = handle_log(body)
        } else if (path == "/style.css") {
            response = serve_file("frontend/style.css", "text/css")
        } else {
            response = http_response(404, "text/plain", "404 not found")
        }

        print response |& server
        close(server)
    }
}

function serve_file(filepath, mimetype,    content, line) {
    content = ""
    while ((getline line < filepath) > 0) {
        content = content line "\n"
    }
    close(filepath)
    if (content == "") return http_response(404, "text/plain", "file not found")
    return http_response(200, mimetype, content)
}

function handle_suggest(body,    params, time_val, user_id, cmd, result, suggestion) {
    split(body, params, "&")
    time_val = "30"
    user_id  = "1"
    for (i in params) {
        split(params[i], kv, "=")
        if (kv[1] == "time")    time_val = kv[2]
        if (kv[1] == "user_id") user_id  = kv[2]
    }

    cmd = "sudo -u postgres psql -d doomless -t -c \"SELECT interest FROM interests WHERE user_id=" user_id ";\""
    interests = ""
    while ((cmd | getline line) > 0) {
        gsub(/^ +| +$/, "", line)
        if (line != "") interests = interests line ", "
    }
    close(cmd)

    suggestion = call_gemini(time_val, interests)

    html = "<html><body style='font-family:monospace;padding:2rem'>"
    html = html "<h2>your activity for the next " time_val " minutes</h2>"
    html = html "<p>" suggestion "</p>"
    html = html "<form method='POST' action='/log'>"
    html = html "<input type='hidden' name='user_id' value='" user_id "'>"
    html = html "<input type='hidden' name='activity' value='" suggestion "'>"
    html = html "<input type='hidden' name='time_spent' value='" time_val "'>"
    html = html "<button type='submit'>done, log this</button>"
    html = html "</form>"
    html = html "<br><a href='/'>back</a></body></html>"

    return http_response(200, "text/html", html)
}

function handle_log(body,    params, user_id, activity, time_spent, cmd) {
    split(body, params, "&")
    for (i in params) {
        split(params[i], kv, "=")
        if (kv[1] == "user_id")    user_id    = kv[2]
        if (kv[1] == "activity")   activity   = kv[2]
        if (kv[1] == "time_spent") time_spent = kv[2]
    }

    gsub(/\+/, " ", activity)
    gsub(/%20/, " ", activity)

    cmd = "sudo -u postgres psql -d doomless -c \"INSERT INTO activity_log (user_id, activity, time_spent) VALUES (" user_id ", '" activity "', " time_spent ");\""
    system(cmd)

    return http_response(302, "text/html", "", "Location: /history.html")
}

function call_gemini(time_val, interests,    api_key, prompt, payload, cmd, line, result) {
    api_key = ENVIRON["GEMINI_API_KEY"]
    prompt  = "Suggest one specific activity for someone who has " time_val " minutes free. Their interests are: " interests ". Give only the activity name and a one-line description. Be specific and creative. No lists, no markdown."

    gsub(/"/, "\\\"", prompt)

    payload = "{\"contents\":[{\"parts\":[{\"text\":\"" prompt "\"}]}]}"

    cmd = "curl -s -X POST 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" api_key "' -H 'Content-Type: application/json' -d '" payload "'"

    result = ""
    while ((cmd | getline line) > 0) {
        result = result line
    }
    close(cmd)

    if (match(result, /"text": *"([^"]+)"/, arr)) {
        return arr[1]
    }
    return "take a 5 minute walk and breathe"
}

function http_response(code, mimetype, body, extra_header,    status, response) {
    if (code == 200) status = "200 OK"
    else if (code == 302) status = "302 Found"
    else status = "404 Not Found"

    response = "HTTP/1.1 " status "\r\n"
    response = response "Content-Type: " mimetype "\r\n"
    if (extra_header != "") response = response extra_header "\r\n"
    response = response "Connection: close\r\n"
    response = response "Content-Length: " length(body) "\r\n"
    response = response "\r\n"
    response = response body
    return response
}
