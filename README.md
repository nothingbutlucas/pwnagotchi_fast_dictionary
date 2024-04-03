# pwnagotchi_fast_dictionary

Improved version of quickdic.py + aircrackonly - For pwnagotchi's devices

---

## Why improved?

* Use the quickdic code as a base
* Use of scapy to see if there is any handshake in the pcap file
* Delete the pcap file automatically if there is no handshake or bssid or ssid (Like aircrackonly)
* Timeout between each wordlist (Avoids the pwnagotchi to freeze or hang on one pcap)
* Defensive programming filosophy
* More logs

## Where can I find wordlists?

[Seclists](https://github.com/danielmiessler/SecLists)

## Installation

### Installation via script

On your pwnagotchi, go to your home directory and clone the repository:

```bash
git clone https://github.com/nothingbutlucas/pwnagotchi_fast_dictionary fast_dictionary
cd fast_dictionary
chmod 744 install.sh
sudo ./install.sh
```
Then, just follow the installation script instructions.

### Manual installation

Basically, you can read the install.sh file and do the same thing manually.
1. Clone the repository (`git clone https://github.com/nothingbutlucas/pwnagotchi_fast_dictionary fast_dictionary`)
2. Move or symlink (recommended) fast_dictionary.py to your custom plugins directory (Usually `/usr/local/share/pwnagotchi/custom-plugins`)
3. Edit your config file (`/etc/pwnagotchi/config.toml`) and add the following lines:
```toml
main.plugins.fast_dictionary.enable = true
main.plugins.fast_dictionary.wordlist_folder = "/usr/share/wordlists" # This is the folder where your wordlists are
main.plugins.fast_dictionary.time_per_wordlist = 5 # This is the timeout between each wordlist
```
4. Restart your pwnagotchi (At least, the daemon): `sudo systemctl restart pwnagotchi`

## Usage

After properly installation the `fast_dictionary` plugin is going to execute when you capture a handshake.

### See a cracked password

If you succeed in cracking the password, it will leave it on the following file: `/root/handshakes/fast_dictionary_cracked.potfile`
You could use the [display-password-plugin](https://github.com/nothingbutlucas/pwnagotchi-display-password-plugin) in order to display the password on the screen of the pwnagotchi.
Also can be retrieved with the [telegram.py](https://github.com/wpa-2/telegram.py) bot.

