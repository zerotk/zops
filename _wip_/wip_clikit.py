from zerotk.clikit.app import App
import sys

app = App('hello')

@app
def greeting(console_, person="world"):
    '''
    Greetings from clikit.
    '''
    console_.Print(f"Hello, {person}!")

if __name__ == '__main__':
    sys.exit(app.Main())
