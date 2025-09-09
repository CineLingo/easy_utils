from inspect import currentframe, getframeinfo
import os
import shutil
import importlib.util

EXCEPTION_FOLDERS = [
    'checkpoints',
    'inputs',
    'outputs',
    'wandb',
    'debug',
    '__pycache__',
]
EXCEPTION_EXTENSIONS = [
    '.pth',
    '.png',
    '.jpg',
    '.jpeg',
    '.mp4',
    '.pyc',
    '.pt',
    '.wav',
]

COLORS={
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'cyan': '\033[96m',
    'blue': '\033[94m',
    'purple': '\033[95m',
    'white': '\033[97m',
    'gray': '\033[90m',
    'reset': '\033[0m'
}

def printline(*args, sep=' ', abs_path=False, prefix_color='gray', string_color=None):
    '''
    Print the current file and line number along with the given message.
    
    Parameters
    ----------
    *args : any
        Arguments to print (like built-in print).
    sep : str
        Separator between args.
    abs_path : bool
        Whether to show full file path.
    prefix_color : str
        Color for prefix [filename, line].
    string_color : str or None
        Color for the printed string.
    '''

    frameinfo = getframeinfo(currentframe().f_back)
    filename = frameinfo.filename if abs_path else frameinfo.filename.split('/')[-1]
    linenumber = frameinfo.lineno

    # ANSI escape code for colors
    if prefix_color in COLORS:
        pre_color = COLORS[prefix_color]
    else:
        pre_color = COLORS['gray']
    
    # Join all args into a single string
    string = sep.join(str(arg) for arg in args)
    
    if string_color is not None and string_color in COLORS:
        string = COLORS[string_color] + string + COLORS['reset']

    reset_color = '\033[0m'
    loc_str = f'{pre_color}[{filename}, line: {linenumber}]{reset_color}'

    print(f'{loc_str} {string}')


def find_package_path(package_name):
    # 패키지 로더 가져오기

    package_loader = importlib.util.find_spec(package_name)
    if package_loader is None or not hasattr(package_loader, 'submodule_search_locations'):
        raise ImportError(f"패키지 '{package_name}'의 경로를 찾을 수 없습니다.")
    
    # NamespaceLoader의 _path에서 첫 번째 경로 선택
    namespace_path = list(package_loader.submodule_search_locations)
    if not namespace_path:
        raise ImportError(f"패키지 '{package_name}'의 경로를 찾을 수 없습니다.")
    
    # 첫 번째 경로를 절대 경로로 반환
    return os.path.abspath(namespace_path[0])

def copy_all_files(src, dst):
    # copy all files from src to dst
    # except EXCEPTION_FOLDERS and EXCEPTION_EXTENSIONS
    if not os.path.exists(dst):
        os.makedirs(dst)


    for root, dirs, files in os.walk(src):
        # 제외할 폴더 필터링
        dirs[:] = [d for d in dirs if d not in EXCEPTION_FOLDERS]
        
        # 파일 복사
        for file in files:
            # 제외할 확장자 확인
            if any(file.endswith(ext) for ext in EXCEPTION_EXTENSIONS):
                continue
            
            src_file = os.path.join(root, file)
            # 대상 디렉토리 계산
            relative_path = os.path.relpath(root, src)
            dest_dir = os.path.join(dst, relative_path)
            
            # 대상 디렉토리 생성
            os.makedirs(dest_dir, exist_ok=True)
            
            # 파일 복사
            dest_file = os.path.join(dest_dir, file)
            shutil.copy2(src_file, dest_file)