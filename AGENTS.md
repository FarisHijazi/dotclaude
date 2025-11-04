Always test before delivering or saying that it's done, nothing is done unless it's tested and works.

NEVER reboot or shutdown the machine, NEVER restart the docker runtime or mess with system internals.

Unless absolutely necessary, do not use `python -c "..."` or `exec()`, `bash -c ` for running large chunks of code (large means more than 3 lines). Instead write the code to a file and execute it

Use something that already exists, avoid implementing from scratch unless absolutely necessary
