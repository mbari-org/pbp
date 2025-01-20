# README

This directory contains the sources for documenting the use of
[`mbari-org/pbp`](https://pypi.org/project/mbari-pbp/).

Merging changes in this directory into the main branch in the remote repo
will automatically trigger the update of the generated site at
<https://docs.mbari.org/pbp/>.

### Local doc development

The following commands assume `pbp-doc` is the current directory.

One-off setup:
```bash
just setup
```

Then:
```bash
just serve
```
and open the indicated URL in your browser.
