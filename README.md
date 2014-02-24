iOS Runtime Preview
======================
This tool enables a running iOS app to execute modified source codes without rebuilding them.

You can check instantly the result of modification to the source code as if you are using an interpreter.  
There is no need for compiling again after editing a source code with this tool!

![iOSRuntimePreviewDemo](https://raw.github.com/addsict/iOSRuntimePreview/master/img/iOSRuntimePreviewDemo.gif)

See video: [https://vimeo.com/87261099](https://vimeo.com/87261099)

Install
-------------
```sh
$ git clone https://github.com/addsict/iOSRuntimePreview.git
```

Requirements
-------------
The target iOS app must be compiled with a option `-O0`(default option for debug build).

How to use
------------
1. Run your iOS app from Xcode by either the iOS simulator or the iOS device.

    ![img1](https://raw.github.com/addsict/iOSRuntimePreview/master/img/img1.png)

1. Pause execution of running app by clicking a pause button at debug area or keyboard shortcut `^⌘Y`.

    ![img2](https://raw.github.com/addsict/iOSRuntimePreview/master/img/img2.png)

1. Import `preview.py` into a LLDB debug session by below command.  
    You may execute this command just one time within same debug session.

    ![img3](https://raw.github.com/addsict/iOSRuntimePreview/master/img/img3.png)

1. Register a source file which you'll edit in runtime by below command, then clicking a play button at debug area.  
    `Syntax: preview <file>`

    ![img4](https://raw.github.com/addsict/iOSRuntimePreview/master/img/img4.png)

1. It's all done! You can edit a source code and that modification will be appeared in running app without compiling again.

How it works
-------------
The key technique is LLDB breakpoints.  
Once you insert a new code into a source file, a breakpoint is set at the line of inserted code and LLDB debugger executes it when debugger hits the breakpoint.  
On the other hand, if the code is deleted from a source file, a breakpoint is set again, then LLDB debugger sets the address of next instruction to PC(Program Counter) to skip the deleted code when debugger hits the breakpoint.

Limitation
-----------
Currently, there exist some limitations for using this tool.

- Can't write control syntax like `if` or `for`.
- Can't write new methods.
- Can't declare new variables.
