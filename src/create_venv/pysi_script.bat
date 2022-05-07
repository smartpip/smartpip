:: get Administrator permission
@echo off&color 17
if exist "%SystemRoot%\SysWOW64" path %path%;%windir%\SysNative;%SystemRoot%\SysWOW64;%~dp0
bcdedit >nul
if '%errorlevel%' NEQ '0' (goto UACPrompt) else (goto UACAdmin)
:UACPrompt
%1 start "" mshta vbscript:createobject("shell.application").shellexecute("""%~0""","::",,"runas",1)(window.close)&exit
exit /B
:UACAdmin
cd /d "%~dp0"


:: create soft link for file | target source
mklink  C:\\Users\DELL\AppData\Local\Programs\Python\Python39\Lib\site-packages\pipdeptree  C:\\Users\DELL\www\rep\pipdeptree

:: create soft link for dir | target source
mklink /J C:\\Users\DELL\AppData\Local\Programs\Python\Python39\Lib\site-packages\requests-2.26.0.dist-info C:\\Users\DELL\www\rep\requests-2.26.0.dist-info