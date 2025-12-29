## Things to NEVER do

IMPORTANT: NEVER reboot or shutdown the machine, NEVER restart the docker runtime or mess with system internals.

## Tool calling and specifics

- Unless absolutely necessary, do not use `python -c "..."` or `exec()`, `bash -c ` for running large chunks of code (large means more than 3 lines). Instead write the code to a file and execute it
- When files are not meant to be modified directly, avoid modifying them directly, and instead use an appropriate CLI tool or conversion script. For example, to create a pyproject.toml, use `uv init` and update it, rather than writing it manually from scratch. likewise with `uv.lock`. Another example: to write a jupyter notebook, do NOT write the raw JSON content to a ipynb file, instead write to an intermediate format that's more human readable and less likely to cause mistakes such as a .py file with #%% or anything else, and then use a conversion script/command.
- When asked to create/write large generic boilerplate files, download them from the internet when possible, such as a .gitignore for Python, download it from https://github.com/github/gitignore/blob/main/Python.gitignore . and so on... when asking you to write the latest state of the art pre-commit-config.yaml, instead of doing so with memory, search the internet for the different hooks I asked for and combine them. If needed, use a ./tmp/ dir to download stuff and then combine them manually.
- In python, always keep the __init__.py files totally empty as using them can be confusing

## Documentation

- Document whatever you do before you stop coding, write it in `./docs/devlog/claude_{DATETIME}-{DESCRIPTION}.md`. You might also want to read the devlog folder to see if any other devs left any important notes.
- Always update CLAUDE.md before git commit. If you are in a monorepo or folder with multiple projects or even sub or sub sub projects, make a CLAUDE.md that is separate for the root and separate for each project as seen fit.

# Development Workflow

- Think step-by-step before coding, you may write 2-3 reasoning paragraphs outlining your approach.
- Create pseudocode/plan before implementation.
- Test after every meaningful change.
- Focus on complete core functionality first (zero TODOs/placeholders).
- Optimize only after achieving core functionality.

## Coding practices

Always test before delivering or saying that it's done, nothing is done unless it's tested and works.

Use something that already exists, avoid implementing from scratch unless absolutely necessary

When I ask you to configure a project/repo from scratch, I expect you to not do the minimum and to properly configure it. If it's a configuration/deployment/setup task I expect you to configure and not to code or develop.
I expect it to be properly setup and working and configured, for example if it's possible to configure the database or set an APIkey in the env vars, then I'd expect you to do that, I shouldn't have to open the UI and do it myself. You should carefully search and read the docs and set it up and configure it properly with whatever environment variables possible, then in the case it can't be configured in env vars and without writing code, then report to me at the end what I need to do

follow these principles:

### KISS (Keep It Simple, Stupid)

- write straightforward, uncomplicated solutions
- Avoid over-engineering and unnecessary complexity
- code must be readable and maintainable

### YAGNI (You Aren't Gonna Need It)

- do not add speculative features
- Focuses on implementing only what's currently needed
- Absolutely avoid code bloat and maintenance overhead

### SOLID Principles

- Single Responsibility Principle
- Open-Closed Principle
- Liskov Substitution Principle
- Interface Segregation Principle
- Dependency Inversion Principle

---

Act as a senior staff software engineer.

Always update CLAUDE.md before every git commit.

Always ask clarifying questions in planning / thinking mode.

## Skills

### tests skill

Python testing skill located at `skills/tests/`. Use for creating comprehensive test suites.

Key conventions:
- File naming: `<name>_test.py` (not `test_<name>.py`)
- Tests in `tests/` folder at project root
- Functional style (no test classes)
- Dual-mode: direct ASGI testing (default) or live server via `TEST_SERVER_URL`
- Categories: unit, integration, e2e, flow tests
