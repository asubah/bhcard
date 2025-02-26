# BHIDCard
قراءة بيانات البطاقة الذكية البحرينية باستخدام البايثون

## Debian-based Systems
```
# PC/SC Smart Card middleware
sudo apt install pcscd
sudo apt install libpcsclite1
sudo apt install libpcsclite-dev

# For GUI support
sudo apt install python3-tk

# For image processing
sudo apt install python3-pil
sudo apt install python3-pil.imagetk
```

## RHEL-based Systems
```
# PC/SC Smart Card middleware
sudo dnf install pcsc-lite
sudo dnf install pcsc-lite-libs
sudo dnf install pcsc-lite-devel
sudo dnf install ccid

# For GUI support
sudo dnf install python3-tkinter

# For image processing
sudo dnf install python3-pillow
```
