"""Test fixtures containing realistic raw error outputs across various ecosystems."""

PYTHON_MODULE_NOT_FOUND_PANDAS = """
Traceback (most recent call last):
  File "app.py", line 15, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
"""

PYTHON_MODULE_NOT_FOUND_SUBMODULE = """
Traceback (most recent call last):
  File "src/server.py", line 8, in <module>
    from torch.utils.data import DataLoader
ModuleNotFoundError: No module named 'torch'
"""

NODE_MODULE_NOT_FOUND_EXPRESS = """
node:internal/modules/cjs/loader:1080
  throw err;
  ^

Error: Cannot find module 'express'
Require stack:
- /Users/developer/project/server.js
- /Users/developer/project/index.js
    at Module._resolveFilename (node:internal/modules/cjs/loader:1077:15)
    at Module._load (node:internal/modules/cjs/loader:922:27)
    at Function.executeUserEntryPoint [as runMain] (node:internal/modules/run_main:81:12)
    at node:internal/main/run_main_module:17:47 {
  code: 'MODULE_NOT_FOUND',
  requireStack: [
    '/Users/developer/project/server.js',
    '/Users/developer/project/index.js'
  ]
}
"""

NODE_PORT_IN_USE = """
node:events:491
      throw er; // Unhandled 'error' event
      ^

Error: listen EADDRINUSE: address already in use :::3000
    at Server.setupListenHandle [as _listen2] (node:net:1740:16)
    at listenInCluster (node:net:1788:12)
    at Server.listen (node:net:1876:7)
    at Object.<anonymous> (/home/user/app/server.js:24:8)
Emitted 'error' event on Server instance at:
    at emitErrorNT (node:net:1767:8)
    at process.processTicksAndRejections (node:internal/process/task_queues:82:21) {
  code: 'EADDRINUSE',
  errno: -98,
  syscall: 'listen',
  address: '::',
  port: 3000
}
"""

PYTHON_PORT_IN_USE = """
Traceback (most recent call last):
  File "manage.py", line 22, in <module>
    main()
  File "manage.py", line 18, in main
    execute_from_command_line(sys.argv)
  File "/venv/lib/python3.10/site-packages/django/core/management/__init__.py", line 446, in execute_from_command_line
    utility.execute()
OSError: [Errno 98] Address already in use
"""

COMMAND_NOT_FOUND_POWERSHELL = """
pnpm : The term 'pnpm' is not recognized as the name of a cmdlet, function, script file, or operable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:1 char:1
+ pnpm dev
+ ~~~~
    + CategoryInfo          : ObjectNotFound: (pnpm:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
"""

COMMAND_NOT_FOUND_BASH = """
bash: docker-compose: command not found
"""

COMMAND_NOT_FOUND_WINDOWS_CMD = """
'mvn' is not recognized as an internal or external command,
operable program or batch file.
"""

PERMISSION_DENIED_NODE = """
npm ERR! code EACCES
npm ERR! syscall mkdir
npm ERR! path /usr/local/lib/node_modules
npm ERR! errno -13
npm ERR! Error: EACCES: permission denied, mkdir '/usr/local/lib/node_modules'
"""

PERMISSION_DENIED_PYTHON = """
Traceback (most recent call last):
  File "backup.py", line 42, in <module>
    with open('/etc/config.json', 'w') as f:
PermissionError: [Errno 13] Permission denied: '/etc/config.json'
"""

FILE_NOT_FOUND_NODE = """
Error: ENOENT: no such file or directory, open './config/settings.json'
    at Object.openSync (node:fs:585:3)
    at Object.readFileSync (node:fs:453:35)
    at Object.<anonymous> (/workspace/src/config.js:5:19)
"""

FILE_NOT_FOUND_PYTHON = """
Traceback (most recent call last):
  File "main.py", line 12, in <module>
    data = open("dataset/train.csv").read()
FileNotFoundError: [Errno 2] No such file or directory: 'dataset/train.csv'
"""

CONNECTION_REFUSED_POSTGRES = """
Error: connect ECONNREFUSED 127.0.0.1:5432
    at TCPConnectWrap.afterConnect [as oncomplete] (node:net:1494:16)
    at TCPConnectWrap.callbackTrampoline (node:internal/async_hooks:130:17) {
  errno: -111,
  code: 'ECONNREFUSED',
  syscall: 'connect',
  address: '127.0.0.1',
  port: 5432
}
"""

CONNECTION_REFUSED_PYTHON = """
Traceback (most recent call last):
  File "/venv/lib/python3.10/site-packages/urllib3/connection.py", line 174, in _new_conn
    conn = connection.create_connection(
  File "/venv/lib/python3.10/site-packages/urllib3/util/connection.py", line 95, in create_connection
    raise err
ConnectionRefusedError: [Errno 111] Connection refused
"""

NPM_DEPENDENCY_CONFLICT = """
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
npm ERR! 
npm ERR! While resolving: my-app@0.1.0
npm ERR! Found: react@18.2.0
npm ERR! node_modules/react
npm ERR!   react@"^18.2.0" from the root project
npm ERR! 
npm ERR! Could not resolve dependency:
npm ERR! peer react@"^16.8.0 || ^17.0.0" from legacy-ui-lib@1.2.0
npm ERR! node_modules/legacy-ui-lib
npm ERR!   legacy-ui-lib@"*" from the root project
npm ERR! 
npm ERR! Fix the upstream dependency conflict, or retry
npm ERR! this command with --force, or --legacy-peer-deps
"""

PYTHON_SYNTAX_ERROR = """
  File "utils.py", line 33
    def process_data(items)
                           ^
SyntaxError: expected ':'
"""

PYTHON_INDENTATION_ERROR = """
  File "calculator.py", line 10
    total = a + b
    ^
IndentationError: unexpected indent
"""

GIT_NOT_A_REPO = """
fatal: not a git repository (or any of the parent directories): .git
"""

GIT_REFUSING_UNRELATED = """
fatal: refusing to merge unrelated histories
"""

GIT_PUSH_REJECTED = """
To github.com:owner/repo.git
 ! [rejected]        main -> main (fetch first)
error: failed to push some refs to 'github.com:owner/repo.git'
hint: Updates were rejected because the remote contains work that you do
hint: not have locally. This is usually caused by another repository pushing
hint: to the same ref. You may want to first integrate the remote changes
hint: (e.g., 'git pull ...') before pushing again.
"""

UNKNOWN_EXOTIC_ERROR = """
KernelPanicException: 0xDEADBEEF in segment 0x0040 at 0x8892110
Unhandled interrupt at 0xFFFA3B
"""

ANSI_COLORED_ERROR = """
\x1b[31m\x1b[1mError:\x1b[0m \x1b[33mCannot find module 'chalk'\x1b[0m
\x1b[90m    at Function.Module._resolveFilename (node:internal/modules/cjs/loader:1077:15)\x1b[0m
\x1b[90m    at /home/user/app/index.js:4:1\x1b[0m
"""
