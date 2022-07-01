import os


def create_dir(path):
    if os.path.isdir(path):
        return True
    if os.path.isfile(path):
        return True
    os.makedirs(path)
    return False

if __name__ == '__main__':
    path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # f"{path}\\form"
    rs = create_dir(f"{path}\\form")
    print(rs)