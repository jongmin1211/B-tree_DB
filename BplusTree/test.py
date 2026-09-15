import os
import subprocess
import sys

# bptree.py parses sys.argv at module level, so it cannot be imported without
# running main(). every test drives it as a subprocess instead.

HERE        = os.path.dirname(os.path.abspath(__file__))
BPTREE      = os.path.join(HERE, 'bptree.py')
INDEX       = os.path.join(HERE, 'test_index.dat')
INPUT_CSV   = os.path.join(HERE, 'data', 'input.csv')
DELETE_CSV  = os.path.join(HERE, 'data', 'delete.csv')

DEGREE  = 4                 # N, number of children
DEGREES = [3, 4, 5]         # runAll() repeats every test for each degree
TIMEOUT = 10                # seconds. guards against infinite loops in the tree code


# helpers
def run(*args) -> tuple[int, str, str]:
    # returns (returncode, stdout, stderr). a timeout is reported as returncode -1.
    try:
        r = subprocess.run([sys.executable, BPTREE, *map(str, args)],
                           capture_output=True, text=True, timeout=TIMEOUT)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, '', f'timeout after {TIMEOUT}s'

def readInput() -> list[tuple[str, str]]:
    pairs = []
    with open(INPUT_CSV) as f:
        for line in f:
            line = line.strip()
            if line:
                key, value = line.split(',')
                pairs.append((key, value))
    return pairs

def readDelete() -> list[str]:
    with open(DELETE_CSV) as f:
        return [line.strip() for line in f if line.strip()]

def freshIndex(degree) -> list:
    # remove any index left by a previous run, then create an empty one.
    # returns a list of failure messages (empty means ok).
    if os.path.exists(INDEX):
        os.remove(INDEX)
    code, out, err = run('-c', INDEX, degree)
    if code != 0:
        return [f'create failed (exit {code}): {err.strip() or out.strip()}']
    if not os.path.exists(INDEX):
        return ['create did not produce an index file']
    return []

def searchOut(key) -> tuple[int, str, str]:
    return run('-s', INDEX, key)


# tests. each returns a list of failure messages, empty means pass.
def insertTest(degree = DEGREE) -> list:
    pairs = readInput()
    fails = freshIndex(degree)
    if fails:
        return fails

    code, out, err = run('-i', INDEX, INPUT_CSV)
    if code != 0:
        return [f'insert failed (exit {code}): {err.strip() or out.strip()}']

    # every inserted key must now be searchable, with the value it was given
    for key, value in pairs:
        code, out, err = searchOut(key)
        if code != 0:
            fails.append(f'search({key}) failed after insert (exit {code}): {err.strip()}')
        elif 'NOT FOUND' in out:
            fails.append(f'key {key} was inserted but search says NOT FOUND')
        elif value not in out.split():
            fails.append(f'key {key} : expected value {value}, got {out.strip()!r}')

    # a duplicate insert must be rejected, not stored twice
    dupKey, dupValue = pairs[0]
    code, out, err = run('-i', INDEX, INPUT_CSV)
    if code == 0 and 'duplicated' not in out.lower():
        fails.append(f'reinserting {INPUT_CSV} was accepted without a duplicate-key message')

    return fails

def deleteTest(degree = DEGREE) -> list:
    pairs = readInput()
    targets = readDelete()
    survivors = [(k, v) for k, v in pairs if k not in targets]

    fails = freshIndex(degree)
    if fails:
        return fails

    code, out, err = run('-i', INDEX, INPUT_CSV)
    if code != 0:
        return [f'insert (setup for delete) failed (exit {code}): {err.strip() or out.strip()}']

    code, out, err = run('-d', INDEX, DELETE_CSV)
    if code != 0:
        return [f'delete failed (exit {code}): {err.strip() or out.strip()}']

    # deleted keys must be gone
    for key in targets:
        code, out, err = searchOut(key)
        if code != 0:
            fails.append(f'search({key}) failed after delete (exit {code}): {err.strip()}')
        elif 'NOT FOUND' not in out:
            fails.append(f'key {key} was deleted but search still returns {out.strip()!r}')

    # untouched keys must survive
    for key, value in survivors:
        code, out, err = searchOut(key)
        if code != 0:
            fails.append(f'search({key}) failed after delete (exit {code}): {err.strip()}')
        elif 'NOT FOUND' in out:
            fails.append(f'key {key} was not deleted but search says NOT FOUND')
        elif value not in out.split():
            fails.append(f'key {key} : expected value {value} to survive, got {out.strip()!r}')

    return fails

def searchTest(degree = DEGREE) -> list:
    pairs = readInput()
    fails = freshIndex(degree)
    if fails:
        return fails

    code, out, err = run('-i', INDEX, INPUT_CSV)
    if code != 0:
        return [f'insert (setup for search) failed (exit {code}): {err.strip() or out.strip()}']

    keys = sorted(int(k) for k, v in pairs)

    # single key search : a key that exists
    key, value = pairs[0]
    code, out, err = searchOut(key)
    if code != 0:
        fails.append(f'single search({key}) failed (exit {code}): {err.strip()}')
    elif value not in out.split():
        fails.append(f'single search({key}) : expected value {value}, got {out.strip()!r}')

    # single key search : a key that does not exist
    missing = keys[-1] + 1
    code, out, err = searchOut(missing)
    if code != 0:
        fails.append(f'single search({missing}) failed (exit {code}): {err.strip()}')
    elif 'NOT FOUND' not in out:
        fails.append(f'search({missing}) should be NOT FOUND, got {out.strip()!r}')

    # ranged search : a window that covers part of the tree
    start, end = keys[1], keys[-2]
    expected = {str(k) for k in keys if start <= k <= end}
    code, out, err = run('-r', INDEX, start, end)
    if code != 0:
        fails.append(f'ranged search({start},{end}) failed (exit {code}): {err.strip()}')
    else:
        found = set()
        for line in out.splitlines():
            if ',' in line:
                found.add(line.split(',')[0].strip())
        for k in sorted(expected, key=int):
            if k not in found:
                fails.append(f'ranged search({start},{end}) is missing key {k}')
        for k in sorted(found - expected, key=int):
            fails.append(f'ranged search({start},{end}) returned key {k}, which is out of range')

    return fails


# runner
TESTS = {'insert': insertTest, 'delete': deleteTest, 'search': searchTest}

def report(name, degree, fails) -> bool:
    label = f'{name}Test(N={degree})'
    if not fails:
        print(f'  PASS  {label}')
        return True
    print(f'  FAIL  {label}')
    for msg in fails:
        print(f'          {msg}')
    return False

def runAll(names = None, degrees = None):
    names = names or list(TESTS)
    degrees = degrees or DEGREES
    passed = failed = 0

    for degree in degrees:
        print(f'degree N = {degree}')
        for name in names:
            if report(name, degree, TESTS[name](degree)):
                passed += 1
            else:
                failed += 1

    print(f'\n{passed} passed, {failed} failed')
    if os.path.exists(INDEX):
        os.remove(INDEX)
    return failed == 0


if __name__ == '__main__':
    # test.py                -> every test, every degree in DEGREES
    # test.py insert          -> insertTest only
    # test.py search 5        -> searchTest at N=5
    names   = [a for a in sys.argv[1:] if not a.isdigit()]
    degrees = [int(a) for a in sys.argv[1:] if a.isdigit()]

    unknown = [n for n in names if n not in TESTS]
    if unknown:
        print(f'unknown test(s): {", ".join(unknown)}. choose from {", ".join(TESTS)}')
        sys.exit(2)

    sys.exit(0 if runAll(names, degrees) else 1)
