import sys


def prompt_yn(stmt):
    '''Prints the statement stmt to the terminal and wait for a Y or N answer.
       Returns True for 'Y', False for 'N'.'''
    print(stmt)
    answer = ''
    while answer not in ['Y', 'N']:
        sys.stdout.write("$ ")
        answer = sys.stdin.readline().upper().strip()
    return answer == 'Y'