# Documentation Documentation

Documentation for Just-another Walk-ER is built using `sphinx`:

## Building a Local Copy

Building documentation locally:

```bash
cd documentation
pip install -r documentation_requirements.txt
```

Once dependencies are installed: the documentation may be 
built using the `Makefile` in the same directory:

```bash
make html
```

The landing page of the documentation should be written 
to `build/html/index.html`.

```bash
open -a "Firefox" build/html/index.html     # MacOS
xdg-open build/html/index.html              # Linux
```

## Further Reading

- ["Sphinx Getting Started Guide"](https://www.sphinx-doc.org/en/master/usage/quickstart.html)
