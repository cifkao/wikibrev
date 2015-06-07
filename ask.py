def ask_yes_no(o, prompt):
    while True:
        o.write(prompt + " [y/n] ")
        choice = raw_input().lower()
        if choice in ['y', 'ye', 'yes']: return True
        if choice in ['n', 'no']: return False
