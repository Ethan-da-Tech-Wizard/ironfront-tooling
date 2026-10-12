# Iron Front Playtest Input

A small Linux uinput helper that sends timed keyboard and mouse actions to a focused playtest window.

**Status:** Development helper  
**Built with:** Python, python-evdev, Linux uinput

[Project guide](docs/PROJECT_GUIDE.md) · [Every file explained](docs/FILE_GUIDE.md) · [Licenses and dependencies](docs/LICENSE_REVIEW.md)

## Start here

- [playtest_input.py](playtest_input.py) — Send short test inputs to the focused Unreal playtest through Linux uinput. Connects `sys`, `time`, `subprocess`, `json`.

## Repository layout

| Path | Role |
| --- | --- |

## Scope and current limits

This repository contains the input helper only. It requires evdev and permission to access uinput; invoking it sends real input to the focused window.

## License

Original project code retains **MIT** terms in [LICENSE](LICENSE). Third-party libraries, media, data, models, and tools retain their own terms. See the [license review](docs/LICENSE_REVIEW.md) and [dependency inventory](docs/DEPENDENCIES.csv).
