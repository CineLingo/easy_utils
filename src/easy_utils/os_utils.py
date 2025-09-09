import os
from natsort import natsorted

def suffix(filename):
    """a.jpg -> jpg"""
    pos = filename.rfind(".")
    if pos == -1:
        return ""
    return filename[pos + 1:]

def prefix(filename):
    """
    a.jpg -> a
    a/b/c.jpg -> a/b/c
    """
    pos = filename.rfind(".")
    if pos == -1:
        return filename
    return filename[:pos]

def prefix_basename(filename):
    """a/b/c.jpg -> c"""
    return prefix(os.path.basename(filename))

def remove_suffix(filepath):
    """a/b/c.jpg -> a/b/c"""
    return os.path.join(os.path.dirname(filepath), prefix_basename(filepath))

def change_suffix(filepath, new_suffix):
    """a/b/c.jpg -> a/b/c.new_suffix"""
    if '.' not in new_suffix:
        new_suffix = '.' + new_suffix
    return remove_suffix(filepath) + new_suffix

def extlist(path, 
            ext, # single extension or list/tuple of extensions
            exclude_hidden_folders=True, # skip hidden dirs (starting with '.')
            exclude_hidden_files=True, # skip hidden files (starting with '.')
            ignore_case=True, # case-insensitive match (.JPG == .jpg if True)
            sort=False,
            ):
    """
    Get all files with given extension(s) under `path`.
    - Skips hidden directories if pass_hidden_folders=True.
    - If `ext` is a list/tuple, unions results across all.
    - Case-insensitive match if ignore_case=True.
    - Optionally exclude hidden files (starting with '.') too.
    """
    def _norm_ext(e):
        e = e if e.startswith('.') else ('.' + e)
        return e.lower() if ignore_case else e

    # handle list/tuple of extensions
    if isinstance(ext, (list, tuple)):
        files = []
        for e in ext:
            files.extend(extlist(path, e, exclude_hidden_folders, False, ignore_case, exclude_hidden_files))
        # de-duplicate
        files = list(set(files))
        return natsorted(files) if sort else files

    ext = _norm_ext(ext)

    # path is a single file
    if os.path.isfile(path):
        name = path.lower() if ignore_case else path
        if name.endswith(ext):
            if exclude_hidden_files and os.path.basename(path).startswith('.'):
                return []
            return [path]
        return []

    results = []
    for root, dirs, files in os.walk(path):
        if exclude_hidden_folders:
            # filter out hidden dirs in-place so os.walk doesn't descend into them
            dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in files:
            if exclude_hidden_files and fname.startswith('.'):
                continue
            name_cmp = fname.lower() if ignore_case else fname
            if name_cmp.endswith(ext):
                results.append(os.path.join(root, fname))

    return natsorted(results) if sort else results


if __name__ == "__main__":
    # Example usage
    test_dir = "/mnt/CINELINGO_BACKUP/CineLingo/easy_utils/assets/test_files"
    files = extlist(test_dir, ext=['.txt'], sort=True, exclude_hidden_files=True)
    print(files)