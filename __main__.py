import sys

sys.path.append('.')

if __name__ == '__main__':
    from custom import CustomBot
    bot = CustomBot(sys.argv[1:])
