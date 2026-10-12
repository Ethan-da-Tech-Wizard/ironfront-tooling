# Iron Front Playtest Input

A small Linux uinput helper that sends timed keyboard and mouse actions to a focused playtest window.

**Status:** Development helper  
**Built with:** Python, python-evdev, Linux uinput

## Reading order

1. Read the root README for project purpose and setup navigation.
2. Follow the entry points below to find the implementation.
3. Use the file guide to locate individual modules, tests, assets, and configuration.
4. Check component licenses before redistributing dependencies or assets.

## Important paths

- [playtest_input.py](../playtest_input.py) — Send short test inputs to the focused Unreal playtest through Linux uinput. Connects `sys`, `time`, `subprocess`, `json`.

## Structure

| Path | Role |
| --- | --- |
| [docs/](../docs/) | Project documentation, decisions, and reference material (5 tracked entries). |

## Scope

This repository contains the input helper only. It requires evdev and permission to access uinput; invoking it sends real input to the focused window.

## Maintaining the guide

The file catalog is a source-inspection snapshot, not proof that every runtime path works. Update it when moving files or changing module responsibilities. The 2026-10-12 documentation review did not run every application, deploy services, or validate all historical performance claims.
