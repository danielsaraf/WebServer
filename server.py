import socket
import sys
import os


def find_path(s):  # get the text between GET and HTTP/1.1 - that's the path
    first = "GET "
    last = " HTTP/1.1"
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ValueError


def get_file_content(path):  # get path of exists file and return its content in bytes or binary image data
    if path.endswith(".jpg") or path.endswith(".ico"):
        with open(path, "rb") as f:
            return f.read()
    else:
        with open(path) as f:
            return f.read()


# find the line in the request that contains the Connection field and extract the connection type from it
def find_conn(request_arr):
    for line in request_arr:
        if "Connection:" in line:
            connection = line[12:]
            if connection == "close" or connection == "keep-alive":
                return connection
            else:
                return ValueError
    return ValueError


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = sys.argv[1]
    server.bind(('', int(port)))
    BUFFER_SIZE = 1024
    server.listen(10)

    while True:
        client_socket, client_address = server.accept()
        client_socket.settimeout(1)
        conn = ""  # reset the connection status each iterate
        start_of_req = ""
        while conn != "close":  # take request from client until connection status change to 'close'
            request = start_of_req
            start_of_req = ""
            valid_msg = True
            while "\r\n\r\n" not in request:  # read in BUFFER_SIZE len until gets "\r\n\r\n" from client
                try:
                    request += client_socket.recv(BUFFER_SIZE).decode("utf-8")
                    if request == "":  # make sure what empty msg means?
                        valid_msg = False
                        break
                except:  # timeout
                    valid_msg = False
                    break
            if not valid_msg:  # in case of empty message or timeout, close the connection and move to next client
                break
            # if the request contains more than one message content, keep the rest for next iterate
            if len(request.split("\r\n\r\n")) > 1:
                start_of_req = request[request.index("\r\n\r\n") + 4:]
            request = request.split("\r\n\r\n")[0]  # cut the request from the start of the str to the first "\r\n\r\n"

            print(request)
            request_arr = request.split("\r\n")
            path = find_path(request_arr[0])  # extract the path
            conn = find_conn(request_arr)  # extract the connection type

            # in this case, the request is invalid because the address is not in the first line
            # there is no reference for this issue in the assigment file so i guess i should return 404
            if path == ValueError or conn == ValueError:
                response_msg = "HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n"
                try:
                    client_socket.send(response_msg.encode('utf-8'))
                except:  # connection lost
                    conn = "close"
                conn = "close"
                break



            if path == "/redirect":  # special treatment for '/redirect' path
                response_msg = "HTTP/1.1 301 Moved Permanently\r\nConnection: close\r\nLocation: /result.html\r\n\r\n"
                try:
                    client_socket.send(response_msg.encode('utf-8'))
                except:  # connection lost
                    conn = "close"
                conn = "close"
            else:
                if path == "/":  # special treatment for "/" path. and also, chain "files" at the beginning of path
                    path = "files/index.html"
                else:
                    path = "files" + path

                if os.path.exists(path) and not os.path.isdir(path):  # make sure the file is exists and not a directory
                    file_content = get_file_content(path)
                    length = len(file_content)
                    response_msg = ("HTTP/1.1 200 OK\r\nConnection: " + conn + "\r\nContent-Length: " + str(
                        length) + "\r\n\r\n").encode('utf-8')
                    if type(file_content) is str:  # in case of html/js/css files, file_content will be in string format
                        file_content = file_content.encode('utf-8')
                    try:
                        client_socket.send(response_msg + file_content)
                    except:  # connection lost
                        conn = "close"
                else:  # file doesnt exists
                    response_msg = "HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n"
                    try:
                        client_socket.send(response_msg.encode('utf-8'))
                    except:  # connection lost
                        conn = "close"
                    conn = "close"
        client_socket.close()


main()
