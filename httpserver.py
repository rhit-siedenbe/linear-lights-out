import socket
import traceback
import random
from datetime import date

current_game_state = {
    "active": False,
    "player_name": None,
    "lights": [],
    "num_lights": 0,
    "moves": 0,
}
best_scores = {}

def get_requested_filename(request_line):
    parts = request_line.split()
    path = parts[1]
    if not path.startswith("."):
        return "./public" + path
    return path

def get_requested_method(request_line):
    parts = request_line.split()
    method = parts[0]
    return method

def get_file_type(file_name):
    return "." + file_name.split(".")[-1]

def get_content_type(file_extension):
    if file_extension == ".html" or file_extension == ".htm":
        return "text/html; charset=utf-8"
    elif file_extension == ".txt":
        return "text/plain; charset=utf-8"
    elif file_extension == ".jpg" or file_extension == ".jpeg":
        return "image/jpeg"
    elif file_extension == ".png":
        return "image/png"
    elif file_extension == ".css":
        return "text/css; charset=utf-8"
    elif file_extension == ".ico":
        return "image/x-icon"
    elif file_extension == ".js":
        return "text/javascript; charset=utf-8"
    else:
        return "application/octet-stream"

# This function (and the following) was moved here for clarity,
# but is the same thing we have done in the
# past to handle special routes like /shutdown and getting request bodies
def handle_special_routes(requested_filename, connection_to_browser):
    if requested_filename == "./public/shutdown":
        print("Server shutting down")
        shutdown_connection(connection_to_browser)
        exit()

def get_file_body_in_bytes(requested_filename):
    with open(requested_filename, "rb") as fd:
        return fd.read()
    
def parse_headers(reader_from_browser):
    headers = {}
    header_line = reader_from_browser.readline().decode("utf-8")
    while(True):
        if(header_line == "\r\n"):
            break
        pairs = header_line.split(": ")
        headers[pairs[0]] = pairs[1].strip()
        header_line = reader_from_browser.readline().decode("utf-8")
    return headers

def parse_post_request_form_fields(headers, reader_from_browser):
    content_length = int(headers["Content-Length"])
    content_type = headers["Content-Type"]
    form_fields = {}
    post_body = reader_from_browser.read(content_length).decode("utf-8")
    if content_type == "text/plain":
        post_lines = post_body.split("\r\n")
    else:
        post_lines = post_body.split("&")
    for line in post_lines:
        if line == "":
            continue
        pair = line.split("=")
        form_fields[pair[0]] = pair[1].replace("+", " ")
    return form_fields



def main(testing_flags=None):
    # Do not change the following code. This is here to allow us to manage part of your server
    # during testing.
    flags = initialize_flags(testing_flags)

    server = create_connection(port = 8080)

    while flags["continue"]:
        # Wait for the browser to send a HTTP Request
        connection_to_browser = accept_browser_connection_to(server)

        # Read the HTTP Request from the browser
        reader_from_browser = connection_to_browser.makefile(mode='rb')
        try:
            request_line = reader_from_browser.readline().decode("utf-8") # decode converts from bytes to text
            print()
            print('Request:')
            print(request_line)
        except Exception as e:
            print("Error while reading HTTP Request:", e)
            traceback.print_exc() # Print what line the server crashed on.
            shutdown_connection(connection_to_browser)
            continue

        # Gets the requested filename, extension, and file type
        print(request_line)
        requested_filename = get_requested_filename(request_line)
        file_extension = get_file_type(requested_filename)
        content_type = get_content_type(file_extension)

        # DONE: Get the requested HTTP Method
        # Implement a new get_requested_method function, which takes the
        # request line, and then call it here
        request_method = get_requested_method(request_line)

        # NOT DONE: Print requested method
        print("Requested file:", requested_filename)
        print("Extension:", file_extension)

        # DONE: Read all Headers into a Dictionary
        # Implement a new parse_headers function, which takes the
        # browser stream (called reader_from_browser),
        # and then call it here
        headers = parse_headers(reader_from_browser)


        # Move handling shutdown to a new function for clarity
        handle_special_routes(requested_filename, connection_to_browser)

        # Write the HTTP Response back to the browser
        writer_to_browser = connection_to_browser.makefile(mode='wb')
        try:
            # DONE: Handle GET and POST requests differently
            # The code below is what we did before to handle GET requests,
            # but it's been partially moved into a function for clarity.
            if request_method == "GET":
                if requested_filename == "./public/game.html":
                    if not current_game_state["active"]:
                        response_body = b"<h1>403 Forbidden</h1><p>No active game</p>"
                        response_headers = "\r\n".join([
                            'HTTP/1.1 403 Forbidden',
                            'Content-Type: text/html; charset=charset-utf8',
                            f'Content-Length: {len(response_body)}',
                            'Connection: close',
                            '\r\n'
                        ]).encode("utf-8")
                        writer_to_browser.write(response_headers)
                        writer_to_browser.write(response_headers)
                        writer_to_browser.flush()
                        shutdown_connection(connection_to_browser)
                        continue
                    else:
                        lights = current_game_state["lights"]
                        player_name = current_game_state["player_name"]

                        light_buttons_html = '<form method="POST" action="/toggle_light">'
                        for index, light in enumerate(lights):
                            button_class = "button_x" if light == "X" else "button_o"
                            light_buttons_html += f'<button type="submit" name="button_index" value="{index+1}" class="{button_class}">{light}</button>'
                        light_buttons_html += "</form>"


                        response_body = f"""
                            <html>
                            <head>
                            <title>Linear Lights Out</title>
                            <link rel="stylesheet" type="text/css" href="styles/styles.css">
                            </head>
                            <body>
                                <h1>Make the buttons all turn to Xs.</h1>
                                <div>{light_buttons_html}</div>
                            </body>
                            </html>
                        """.encode("utf-8")

                elif requested_filename == "./public/best_scores.html":
                    table_rows = ""
                    for num_lights in sorted(best_scores.keys()):
                        score_data = best_scores[num_lights]
                        table_rows += f"""
                            <tr>
                                <td>{num_lights}</td>
                                <td>{score_data['moves']}</td>
                                <td>{score_data['player_name']}</td>
                                <td>{score_data['date']}</td>
                            </tr>
                        """


                    response_body = f"""
                        <html lang="en">
                        <head>
                        <title>Best Scores - Linear Lights Out</title>
                        <link rel="stylesheet" type="text/css" href="styles/styles.css">
                        </head>
                        <body>
                            <table border="1">
                                <tr>
                                    <th>Number of Lights</th>
                                    <th>Lowest Number of Moves</th>
                                    <th>Player Name</th>
                                    <th>Date</th>
                                </tr>
                                {table_rows}
                            </table>
                            <br>
                        </body>
                        </html>
                    """.encode("utf-8")

                else:
                    response_body = get_file_body_in_bytes(requested_filename)
            
            elif request_method == "POST":

                
                if requested_filename == "./public/game.html":
                    post_form_fields = parse_post_request_form_fields(headers, reader_from_browser)
                    number_of_lights = int(post_form_fields.get("number_of_lights", "7"))
                    off_lights = int(post_form_fields.get("off_lights", "0"))
                    player_name = post_form_fields.get("player_name", "Unknown")


                    lights = ["O"] * number_of_lights
                    off_indices = random.sample(range(number_of_lights), min(off_lights, number_of_lights))

                    for k in off_indices:
                        lights[k] = "X"
                    
                    current_game_state.update({
                        "active": True,
                        "player_name": player_name,
                        "lights": lights,
                        "num_lights": number_of_lights,
                        "moves": 0
                    })

                    light_buttons_html = '<form method="POST" action="/toggle_light">'
                    for index, light, in enumerate(lights):
                        button_class = "button_x" if light == "X" else "button_o"
                        light_buttons_html += f'<button type="submit" name="button_index" value="{index+1}" class="{button_class}">{light}</button>'
                    light_buttons_html += '</form>'

                    response_body = f"""
                        <html lang="en">
                        <head>
                        <title>Linear Lights Out</title>
                        <link rel="stylesheet" type="text/css" href="styles/styles.css">
                        </head>
                        <body>
                            <h1>Make the buttons all turn to Xs.</h1>
                            <p>{light_buttons_html}</p>
                        </body>
                        </html>
                    """.encode("utf-8")
                    content_type = "text/html; charset=utf-8"

                
                elif requested_filename == "./public/toggle_light":
                    print("Handling toggle_light request")
                    post_form_fields = parse_post_request_form_fields(headers, reader_from_browser)

                    button_index_str = post_form_fields.get("button_index", "1")
                    button_index = int(button_index_str) - 1
                    print(f"Button clicked: {button_index}")

                    lights = current_game_state["lights"]

                    indices_to_toggle = [button_index]
                    if button_index > 0:
                        indices_to_toggle.append(button_index-1)
                    if button_index < len(lights) - 1:
                        indices_to_toggle.append(button_index + 1)

                    for i in indices_to_toggle:
                        if lights[i] == "X":
                            lights[i] = "O"
                        else:
                            lights[i] = "X"
                    current_game_state["moves"]+=1

                    if all(light == "X" for light in lights):
                        print(f"Game won in {current_game_state['moves']} moves!")
                        
                        num_lights = current_game_state["num_lights"]
                        moves = current_game_state["moves"]
                        player_name = current_game_state["player_name"]
                        
                        if num_lights not in best_scores or moves < best_scores[num_lights]["moves"]:
                            best_scores[num_lights] = {
                                "moves": moves,
                                "player_name": player_name,
                                "date": date.today().strftime("%Y-%m-%d")
                            }
                            print(f"New best score for {num_lights} lights!")
                        
                        current_game_state["active"] = False
                        
                        response_body = b""
                        response_headers = "\r\n".join([
                            'HTTP/1.1 303 See Other',
                            'Location: /best_scores.html',
                            'Content-Type: text/html; charset=utf-8',
                            'Content-Length: 0',
                            'Connection: close',
                            '\r\n'
                        ]).encode("utf-8")
                        writer_to_browser.write(response_headers)
                        writer_to_browser.write(response_body)
                        writer_to_browser.flush()
                    else:
                        light_buttons_html = '<form method="POST" action="/toggle_light">'
                        for index, light in enumerate(lights):
                            button_class = "button_x" if light == "X" else "button_o"
                            light_buttons_html += f'<button type="submit" name="button_index" value="{index+1}" class="{button_class}">{light}</button>'
                        light_buttons_html += '</form>'

                        response_body = f"""
                            <html lang="en">
                            <head>
                            <title>Linear Lights Out</title>
                            <link rel="stylesheet" type="text/css" href="styles/styles.css">
                            </head>
                            <body>
                                <h1>Make the buttons all turn to Xs.</h1>
                                {light_buttons_html}
                            </body>
                            </html>
                        """.encode("utf-8")
                        content_type = "text/html; charset=utf-8"





            # DONE: Implement a new function called parse_post_request_form_fields.
            # It should have the following signature:
            #   parse_post_request_form_fields(headers, reader_from_browser)
            #
            # It should return a dictionary of the form fields and their values.
            # Then, call the parse_post_request_form_fields function here to get the
            # form field values.
            # Then print the fields for debugging.

            # TODO: Decide what to do with the data.

            response_headers = "\r\n".join([
                'HTTP/1.1 200 OK',
                f'Content-Type: {content_type}',
                f'Content-length: {len(response_body)}',
                'Connection: close',
                '\r\n'
            ]).encode("utf-8")

            # These lines just PRINT the HTTP Response to your Terminal.
            print()
            print('Response headers:')
            print(response_headers)
            print()
            print('Response body:')
            print(response_body)
            print()

            # These lines do the real work; they write the HTTP Response to the Browser.
            writer_to_browser.write(response_headers)
            writer_to_browser.write(response_body)
            writer_to_browser.flush()
        except Exception as e:
            print("Error while writing HTTP Response:", e)
            flags["exceptions"].append(e)
            traceback.print_exc() # print what line the server crashed on
    
        shutdown_connection(connection_to_browser)



# Don't worry about the details of the rest of the code below.
# It is VERY low-level code for creating the underlying connection to the browser.

def create_connection(port):
    addr = ("", port)  # "" = all network adapters; usually what you want.
    server = socket.create_server(addr, family=socket.AF_INET6, dualstack_ipv6=True) # prevent rare IPV6 softlock on localhost connections
    server.settimeout(2)
    print(f'Server started on port {port}. Try: http://localhost:{port}/startgame.html')
    return server

def accept_browser_connection_to(server):
    while True:
        try:
            (conn, address) = server.accept()
            conn.settimeout(2)
            return conn
        except socket.timeout:
            print(".", end="", flush=True)
        except KeyboardInterrupt:
            exit(0)

def shutdown_connection(connection_to_browser):
    connection_to_browser.shutdown(socket.SHUT_RDWR)
    connection_to_browser.close()

def initialize_flags(testing_flags):
    flags = testing_flags if testing_flags is not None else {}
    if "continue" not in flags:
        flags["continue"] = True
    if "exceptions" not in flags:
        flags["exceptions"] = []
    return flags

if __name__ == "__main__":
    main()
