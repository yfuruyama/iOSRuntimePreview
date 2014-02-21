iOS Runtime Preview
======================
This tool enables an iOS app to sync with code modifications at runtime.

See video: [https://vimeo.com/87258262](https://vimeo.com/87258262)

Install
-------------
```sh
$ git clone https://github.com/addsict/iOSRuntimePreview.git
```

How to use
------------
1. Run your iOS app from Xcode on either the iOS simulator or the iOS device.

    ![img1](https://raw.github.com/addsict/iOSRuntimePreview/master/img/img1.png)

1. Pause program execution by clicking a pause button at debug area or keyboard shortcut `^⌘Y`.

    ![img2](https://raw.github.com/addsict/iOSRuntimePreview/master/img/img2.png)

1. Import `preview.py` into a LLDB debug session by below command.  
    You may execute this command just one time within same debug session.

    ![img3](https://raw.github.com/addsict/iOSRuntimePreview/master/img/img3.png)

1. Register a source file which you want to sync with running iOS app.  
    format: `preview <file path from project directory>`
