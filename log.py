from datetime import datetime, timezone

def log(prefix, text):
    message = '[' + str(datetime.now()) + '] ' + prefix + ': ' + str(text)
    with open('log.txt', 'a') as log_file:
        log_file.write(message + '\n')
    print(message)


def log_error(text):
    log('ERROR', text)


def log_info(text):
    log('INFO', text)