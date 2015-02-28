from eleven.tasks import generateSpritesheets


if __name__ == '__main__':
    generateSpritesheets.delay('TSID', {'key': 'val'})
