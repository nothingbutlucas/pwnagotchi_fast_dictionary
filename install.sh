#!/usr/bin/env bash

set -e

CONFIG_FILE="/etc/pwnagotchi/config.toml"

function user_sleep() {
	sleep 0.5
}

function check_toml_key_exists() {
	local key="$1"
	local config_file="$2"

	if grep -q "^${key}" "$config_file"; then
		echo "[ + ] The '$key' already exists on $config_file."
	else
		echo "[ ~ ] Creating '$key' on $config_file."
		echo "${key} = true " >>"$config_file"
	fi
}

function edit_configuration_values() {
	local key="$1"
	local value="$2"
	local config_file="$3"

	# Escape slashes and dots in the value to avoid issues with sed
	value=$(echo "$value" | sed 's/\//\\\//g')
	value=$(echo "$value" | sed 's/\./\\\./g')
	# If the value is true, replace it with the lowercase version and without quotes
	if [ "$value" = "true" ]; then
		sed -i "s/^${key} = .*/${key} = ${value}/" "$config_file"
	else
		# Use sed to insert or replace the configuration value
		sed -i "/^${key}/c ${key} = \"${value}\"" "$config_file"
	fi

}

function modify_config_files() {
	wordlist_folder="$1"
	# TODO If you know a simple method to write on toml files, please submit a change
	check_toml_key_exists "main.plugins.fast_dictionary.enabled" "$CONFIG_FILE"
	check_toml_key_exists "main.plugins.fast_dictionary.wordlist_folder" "$CONFIG_FILE"
	check_toml_key_exists "main.plugins.fast_dictionary.time_per_wordlist" "$CONFIG_FILE"

	# Set the configuration values
	edit_configuration_values "main.plugins.fast_dictionary.enabled" true "$CONFIG_FILE"
	edit_configuration_values "main.plugins.fast_dictionary.wordlist_folder" "$wordlist_folder" "$CONFIG_FILE"
	edit_configuration_values "main.plugins.fast_dictionary.time_per_wordlist" 5 "$CONFIG_FILE"
}

function get_installation_path() {
	check_toml_key_exists "main.custom_plugins" "$CONFIG_FILE"
	installation_dir=$(awk '/^main.custom_plugins = / {print $3}' "$CONFIG_FILE")
	if [ -z "${installation_dir//\"/}" ] || [ "$installation_dir" = true ]; then
		echo "[ ! ] The installation directory was not found in the configuration file"
		read -r -p "Please enter the installation directory, press Enter to set '/usr/local/share/pwnagotchi/custom-plugins' or specify yours with absolute path: " installation_dir
	fi
	if [ -z "${installation_dir//\"/}" ]; then
		installation_dir="/usr/local/share/pwnagotchi/custom-plugins"
	fi
	edit_configuration_values "main.custom_plugins" "${installation_dir}" "$CONFIG_FILE"
	installation_dir="${installation_dir//\"/}"
}

# Main

# Check that the script is running as root

if [ "$EUID" -ne 0 ]; then
	echo "[ ! ] This script need to be run as root"
	exit 0
fi
echo "[ + ] Getting installation path..."
get_installation_path
echo "[ + ] Creating symbolic link to ${installation_dir}"
ln -sf "$(pwd)/fast_dictionary.py" "${installation_dir}/fast_dictionary.py"
echo "[ + ] Backing up configuration files..."
cp "${CONFIG_FILE}" "${CONFIG_FILE}.bak"
read -r -p "Where do you have your wordlists folder? [Default: /usr/share/wordlists] " wordlist_folder
if [ -z "$wordlist_folder" ]; then
	wordlist_folder="/usr/share/wordlists"
fi
mkdir -p "$wordlist_folder"
echo "[ ~ ] Modifying configuration files..."
modify_config_files "$wordlist_folder"
echo "[ * ] Done! Please restart your pwnagotchi daemon to apply changes"
echo "[ * ] You can do so with"
echo "[ > ] sudo systemctl restart pwnagotchi"
