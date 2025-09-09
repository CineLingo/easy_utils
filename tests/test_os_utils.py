from easy_utils.os_utils import extlist, change_suffix, suffix, prefix, prefix_basename, remove_suffix
from easy_utils import find_package_path

from natsort import natsorted
import os

ABS_PACKAGE_PATH = find_package_path('easy_utils') # root/src/easy_utils
PARENT_PATH = os.path.dirname(ABS_PACKAGE_PATH) # src folder
ROOT_PATH = os.path.dirname(PARENT_PATH) # package_root folder

TEST_FOLDER = os.path.join(ROOT_PATH, 'assets', 'test_files_os_utils')

# test_files_os_utils
# ├── .scret_sub_folder
# │   └── scret_sub_folder_test_txt.txt
# ├── sub_folder
# │   └── sub_test_txt.txt
# ├── .scret_test_txt.txt
# ├─- test_txt.txt
# └─- test_csv.csv

def test_extlist():
    test_folder = TEST_FOLDER
    
    all_txts_gt = [
        os.path.join(test_folder, 'test_txt.txt'),
        os.path.join(test_folder, '.scret_test_txt.txt'),
        os.path.join(test_folder, 'sub_folder', 'sub_test_txt.txt'),
        os.path.join(test_folder, '.scret_sub_folder', 'scret_sub_folder_test_txt.txt'),
    ]
    
    # Test single extension
    txt_files = extlist(test_folder, 'txt', sort=True, exclude_hidden_files=False, exclude_hidden_folders=False)
    assert txt_files == natsorted(all_txts_gt)
    
    exclude_hidden_txts_gt = [
        os.path.join(test_folder, 'test_txt.txt'),
        os.path.join(test_folder, 'sub_folder', 'sub_test_txt.txt'),
        os.path.join(test_folder, '.scret_sub_folder', 'scret_sub_folder_test_txt.txt'),
    ]
    txt_files = extlist(test_folder, 'txt', sort=True, exclude_hidden_files=True, exclude_hidden_folders=False)
    assert txt_files == natsorted(exclude_hidden_txts_gt)
    
    exclude_hidden_folders_txts_gt = [
        os.path.join(test_folder, 'test_txt.txt'),
        os.path.join(test_folder, '.scret_test_txt.txt'),
        os.path.join(test_folder, 'sub_folder', 'sub_test_txt.txt'),
    ]
    txt_files = extlist(test_folder, 'txt', sort=True, exclude_hidden_files=False, exclude_hidden_folders=True)
    assert txt_files == natsorted(exclude_hidden_folders_txts_gt)
    
    exclude_all_hidden_txts_gt = [
        os.path.join(test_folder, 'test_txt.txt'),
        os.path.join(test_folder, 'sub_folder', 'sub_test_txt.txt'),
    ]
    txt_files = extlist(test_folder, 'txt', sort=True, exclude_hidden_files=True, exclude_hidden_folders=True)
    assert txt_files == natsorted(exclude_all_hidden_txts_gt)
    
    # Test multiple extensions
    all_exts_gt = all_txts_gt + [os.path.join(test_folder, 'test_csv.csv')]
    exts_files = extlist(test_folder, ['txt', 'csv'], sort=True, exclude_hidden_files=False, exclude_hidden_folders=False)
    assert exts_files == natsorted(all_exts_gt)
    
    exts_files = extlist(test_folder, ('txt', 'csv'), sort=True, exclude_hidden_files=False, exclude_hidden_folders=False)
    assert exts_files == natsorted(all_exts_gt)

def test_suffix():
    assert suffix('path/to/file.txt') == 'txt'
    assert suffix('path/to/file') == ''
    assert suffix('path/to/file.tar.gz') == 'gz'
    assert suffix('path/to/.hiddenfile.ext') == 'ext'
    assert suffix('no_extension.') == ''
    
def test_prefix():
    assert prefix('path/to/file.txt') == 'path/to/file'
    assert prefix('path/to/file') == 'path/to/file'
    assert prefix('path/to/file.tar.gz') == 'path/to/file.tar'
    assert prefix('path/to/.hiddenfile.ext') == 'path/to/.hiddenfile'
    assert prefix('no_extension.') == 'no_extension'
    
def test_prefix_basename():
    assert prefix_basename('path/to/file.txt') == 'file'
    assert prefix_basename('path/to/file') == 'file'
    assert prefix_basename('path/to/file.tar.gz') == 'file.tar'
    assert prefix_basename('path/to/.hiddenfile.ext') == '.hiddenfile'
    assert prefix_basename('no_extension.') == 'no_extension'
    assert prefix_basename('just_a_file') == 'just_a_file'
    
def test_remove_suffix():
    assert remove_suffix('path/to/file.txt') == 'path/to/file'
    assert remove_suffix('path/to/file') == 'path/to/file'
    assert remove_suffix('path/to/file.tar.gz') == 'path/to/file.tar'
    assert remove_suffix('path/to/.hiddenfile.ext') == 'path/to/.hiddenfile'
    assert remove_suffix('no_extension.') == 'no_extension'
    assert remove_suffix('just_a_file') == 'just_a_file'
    
def test_change_suffix():
    assert change_suffix('path/to/file.txt', 'md') == 'path/to/file.md'
    assert change_suffix('path/to/file', 'md') == 'path/to/file.md'
    assert change_suffix('path/to/file.tar.gz', 'zip') == 'path/to/file.tar.zip'
    assert change_suffix('path/to/.hiddenfile.ext', 'txt') == 'path/to/.hiddenfile.txt'
    assert change_suffix('no_extension.', 'txt') == 'no_extension.txt'
    assert change_suffix('just_a_file', 'txt') == 'just_a_file.txt'
    assert change_suffix('file.old', '.new') == 'file.new'
    assert change_suffix('file', '.new') == 'file.new'
    assert change_suffix('file', 'new') == 'file.new'