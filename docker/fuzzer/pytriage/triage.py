# @param stderr is assumed to be a Python string (i.e., already decoded from utf-8 or whatever)
def triage_err_msg(stderr):
    if 'sysmalloc: Assertion `(old_top == initial_top (av) && old_size == 0) || ((unsigned long) (old_size) >= MINSIZE' in stderr:
        return 'Know error: Malloc assertion'
    return f"Unknown error: {stderr}"
