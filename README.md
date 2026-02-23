## Full Project Demo:
https://youtu.be/Jq-79XXTvu4

this project won't be actively maintained due to time commitments, but I will try to fix issues if you request them.


## More API documentation:
https://docs.elephantrobotics.com/docs/mycobot_280_pi_en/3-FunctionsAndApplications/6.developmentGuide/python/2_API.html?h=set_vision
https://github.dev/elephantrobotics/pymycobot

look for:
`generate.py`
`mycobot.py`


## Xpra display forwarding
```
#On raspi
sudo apt-get update
sudo apt-get install xpra

xpra start :99 --start=xterm
xpra start :99 --opengl=yes

export QT_X11_NO_MITSHM=1
export LIBGL_ALWAYS_INDIRECT=1
export DISPLAY=:99
export DISPLAY=:0 # side note this is for display to show up on the monitor

#On host (MacOS)
# INSTALL XPRA FROM: https://xpra.org/index.html, find the xpra pkg
# DON"T USE BREW
xpra attach ssh://er@er/:99  # go to privacy & settings select open anyway for xpra
```

## Speed up Raspi with adding swap
```
free -h # verify 

# sudo dd if=/dev/zero of=/swapfile bs=1024 count=1048576 #adds 1G
sudo dd if=/dev/zero of=/swapfile bs=1024 count=4194304  # 4GB
sudo chmod 600 /swapfile # set correct permission
sudo mkswap /swapfile # format as swap
sudo swapon /swapfile # enable swap

free -h

# to turn off
sudo swapoff /swapfile
```

## Try Xpra again
```
# first copy my public key from macbook...
cat ~/.ssh/id_ed25519.pub

# copy output to pi
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "PASTE_YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# then try
xpra attach ssh://er@192.168.1.169/99

# test on pi
xpra start :99 --bind-tcp=0.0.0.0:10000 --start=xeyes

```

## Try X11
```
brew install --cask xquartz

# check if it's installed
 ls /Applications/Utilities/XQuartz.app
Contents

ssh -Y er@192.168.1.169 #X11 forwarding

# try xeyes on mac
xeyes


# if not working then do the following
# on pi
grep X11 /etc/ssh/sshd_config

"X11Forwarding yes
#X11DisplayOffset 10
#X11UseLocalhost yes
#X11Forwarding no"

# need to set X11Forwarding to yes, uncomment them too
sudo nano /etc/ssh/sshd_config

sudo systemctl restart ssh


# if cv2 images are black try:
pip install --upgrade opencv-python

```
