# doudough
*Sounds like 'dough-dough', spoken quickly!*

Doudough is an alternative web interface for the double-entry bookkeeping
software [Beancount](https://beancount.github.io/docs/).  It replaces or supplements [fava](https://beancount.github.io/fava/)
as a frontend, and currently leverages fava backend logic wherever possible.

## Why an alternative web ui?
Beancount is a python program, and I am a python programmer!  Fava makes the "right"
decision and is a purposely-build web frontend using lots of javascript.  As a
data scientist and developer, I wanted a more python-friendly way to visualize and
analyze my personal finances, and so I leveraged the excellent dashboarding
environment [plotly dash](https://dash.plotly.com/) to create a similar experience - 
which should be much easier for python natives like myself to tweak.

Doudough is a way to rapidly develop your own financial dashboards with all the power
of python!

## Installation

Doudough is not yet released into pypi, so installing in editable mode
is recommended.

Pick your favorite installation method!  Doudough can be installed
directly into an existing beancount or fava environment with `pip install`,
or you can install into a dedicated environment using a tool like `pipx`
or `uv`:

```bash
git clone https://github.com/gorlins/doudough.git
pipx install -e ./doudough
```

(I believe `uv` does not fully support editable installs from gh yet,
I have not tested this)
```bash
uv tool install ...
```


If you want to edit and
```bash
pipx install -e ./pidoudough
```

## What's in a name?

"Dou" (豆) is Chinese for 'bean.'  In Chinese, diminutives are created by repeating
the word - 'doudou' means 'little beans,' like peas, or - in my family in particular -
edamame.

*(The first name for this project was "edamoney," which doesn't have the same ring)*

Keeping with the 'bean' theme in the beancount fan multiverse, and green is the color of
$$$, and dough... I mean... I rest my case.
