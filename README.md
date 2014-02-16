inscode
==========
Runtime Objective-C Code Insertion Tool for iOS Debugging.

See video: [https://vimeo.com/86823475](https://vimeo.com/86823475)

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

1. Import `inscode.py` into a LLDB debug session by below command.  
    You may execute this command just one time within same debug session.

    ![img3](https://raw.github.com/addsict/inscode/master/img/img3.png)

1. Then, insert an Objective-C code anywhere you want.  
    format: `inscode <file name>:<line number> '<code>'`

    ![img4](https://raw.github.com/addsict/inscode/master/img/img4.png)
