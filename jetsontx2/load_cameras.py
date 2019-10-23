import sys


def load_cameras_from_file():
    file = open('cameras.txt','r')
    info = eval(file.read())
    print(f'{info}')
    camera_list =  info['cameras']
    for cam in camera_list:
        print(f'{cam}')
    return camera_list

if __name__ == '__main__':
    load_cameras_from_file()