inscode
==========
Runtime Objective-C Code Insertion Tool for iOS Debugging.

Install
-------------
```sh
$ git clone https://github.com/addsict/inscode.git
```

How to use
------------
1. Run your iOS app from Xcode on either the iOS simulator or the iOS device.
    ![img1](https://raw.github.com/addsict/inscode/master/img/img1.png)

1. Pause program execution by clicking a pause button at debug area or keyboard shortcut `^⌘Y`.
    ![img2](https://raw.github.com/addsict/inscode/master/img/img2.png)

1. Import `inscode.py` into LLDB debug session by below command.  
    You may execute this command just one time within same debug session.

    ```
    (lldb) command script import /path/to/inscode.py
    ```
1. Then, insert an Objective-C code anywhere you want.  
    format: `inscode <file name>:<line number> '<code>'`

    ```
    (lldb) inscode ViewController.m:45 'NSLog(@"%s", self);'
    ```
