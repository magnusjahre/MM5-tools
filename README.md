# MM5 Tools

This repository contains scripts for analyzing the output of the MM5 simulator. The plotting scripts in this repository are deprecated. For plotting, use [calplot](https://github.com/magnusjahre/calplot).

## Setup

The first step is to add the root folder of MM5-tools to your systems PYTHONPATH. If you cloned MM5-tools in your home directory, adding the following to your .bashrc will be sufficient:

```
export PYTHONPATH=$PYTHONPATH:$HOME/MM5-tools
```

It is also useful to be run the scripts without providing the full path. To do this, first make sure there is a bin folder in your home directory. Then, add this to the path by adding the following to .bashrc:
```
export PATH=$PATH:$HOME/bin
```

Then, you can add symlinks for all runnable scripts in MM5-tools to your bin folder by running:
```
cd MM5-tools/
./install.py $HOME/bin/
```
