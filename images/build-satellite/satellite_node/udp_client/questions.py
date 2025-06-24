QUESTION_FOR_PROTOCOL = [
    {
        "type": "list",
        "name": "protocol",
        "message": "Please select the network protocol: ",
        "choices": ["IP", "LIPSIN"]
    }
]

QUESTION_FOR_DESTINATION = [
    {
        "type": "list",
        "name": "destination",
        "message": "Please select the satellite you want to send data to: "
    }
]

QUESTION_FOR_PORT = [
    {
        "type": "input",
        "name": "port",
        "message": "Please input the destination port: ",
        "default": "31313"
    }
]
