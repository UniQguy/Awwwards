import subprocess

def main():
    stat = subprocess.check_output(['git', 'diff', '--stat', 'pre-r6'], text=True)
    with open('docs/phase-r6-report.md', 'r', encoding='utf-8') as f:
        c = f.read()

    target = '## 11. Exact Git Difference Statistics'
    sec_idx = c.find(target)
    if sec_idx == -1:
        print('Target not found')
        return

    cb_start = c.find('```text\n', sec_idx) + len('```text\n')
    cb_end = c.find('```\n\n---', cb_start)
    if cb_end == -1:
        print('Closing block not found')
        return

    new_c = c[:cb_start] + stat + c[cb_end:]
    with open('docs/phase-r6-report.md', 'w', encoding='utf-8') as f:
        f.write(new_c)
    print('Updated phase-r6-report.md successfully')

if __name__ == '__main__':
    main()
