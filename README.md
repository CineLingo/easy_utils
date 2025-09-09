### Installation

```bash
pip install -e .
```

### Usage

#### PRINT with line
```python
from easy_utils import printline as print
print("Hello, World!", string_color='your_color')  # You can use any color from the colorama library
# result:
# [README.md, line: 12] Hello, World!
```
- default string_color is system default terminal color
- you can use 'red', 'green', 'yellow', 'blue', 'purple', 'cyan', 'white', 'gray'
- if you want to add more colors, you can modify the `COLORS` in `easy_utils/log_utils.py`

#### extlist
Simple function to get a list of files with a given extension in a folder and its subfolders.
- input: folder path, extension (single or list or tuple)
- output: list of files with the given extension in the folder and its subfolders (abs path)

```python
from easy_utils import extlist

# test_files_os_utils
# ├── .scret_sub_folder
# │   └── scret_sub_folder_test_txt.txt
# ├── sub_folder
# │   └── sub_test_txt.txt
# ├── .scret_test_txt.txt
# ├─- test_txt.txt
# └─- test_csv.csv

print(extlist('test_files_os_utils', '.txt')) 
# ['test_files_os_utils/sub_folder/sub_test_txt.txt', 'test_files_os_utils/test_txt.txt']

print(extlist('test_files_os_utils', '.txt', exclude_hidden_folders=False))
# previous + ['test_files_os_utils/.scret_sub_folder/scret_sub_folder_test_txt.txt']

print(extlist('test_files_os_utils', '.txt', exclude_hidden_folders=False, exclude_hidden_files=False))
# previous + ['test_files_os_utils/.scret_test_txt.txt']

print(extlist('test_files_os_utils', '.txt', sort=True)) # default sort=False
# it will sort the previous list as natural sort 

print(extlist('test_files_os_utils', ('.txt', '.csv'), exclude_hidden_folders=False, exclude_hidden_files=False, sort=True))
# previous + ['test_files_os_utils/test_csv.csv']
```

#### os_utils
```python
from easy_utils import change_suffix, suffix, prefix, prefix_basename, remove_suffix

print(change_suffix('file.txt', '.csv'))  # file.csv
print(suffix('file.txt'))  # .txt
print(prefix('file.txt'))  # file
print(prefix_basename('/path/to/file.txt'))  # file
print(remove_suffix('file.txt'))  # file
```

