# Discord Mutual Friends and Servers

This is a simple Discord bot that allows you to gather a list of server members who are your friends, along with those you share mutual servers or mutual friends with.

**Note:**
This project is a proof of concept. Please be aware that the use of self bots is against Discord's terms of service. Engaging with this code is at your own risk, and any potential consequences, including account suspension, are your responsibility.

## Features

- List friends present in a server.
- List server members with mutual friends.
- List server members with mutual servers.

## Coming Soon

- Windows .exe and Mac .app
- Connections graph

## Building Windows .exe and Max .app from Source

```bash
pyinstaller --noconfirm main.spec
```

## Limitations

- If a server has more than 1000 members, this program is only able to retrieve
  the currently online members (unless you have the required permissions to
  request all server members)

## Requirements

- [Git](https://git-scm.com/downloads)
- [Python](https://www.python.org/downloads/)

## Usage

1. Install all project [Requirements](#requirements)
2. Get your Discord token using the steps in the [How to Get Your Token](#how-to-get-your-token) section
3. Put your Discord token into `.env.sample` file
4. Rename the file `.env.sample` to `.env`
5. Install the requirements using the following command:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

6. Run the main Python file with the command below, or customize the command with the options in the [Command-line Options](#command-line-options) section:

   ```bash
   python3 main.py
   ```

## How to Get Your Token

### Primary Method

If you are comfortable running JavaScript in the Developer Tools Console, the following method is the easiest:

1. Login to Discord's web app: [Discord](https://discordapp.com/)
2. Go to your browser's Developer Tools. In most browsers this can be done by pressing `⌘ + Option + I` on macOS or `CTRL+ Shift + I` on Windows or Linux. `F12` may also work.
3. Paste the code snippet below. If this is your first time using the Developer Tools, you may need to type `allow pasting` first.

   ```javascript
     (webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()
   ```

### Other Methods

Other methods that don't involve running JavaScript in the console:

- [From the requests tab](https://gist.github.com/MarvNC/e601f3603df22f36ebd3102c501116c6)
- [From local storage](https://www.androidauthority.com/get-discord-token-3149920/)

## Command-line Options

| Long Flag            | Flag | Default      | Description                                                                                                                                                                                                                                                                                  | Example                                            |
| -------------------- | ---- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `--get_token`        | `-g` | False        | If set, will run the get_token script to get a token                                                                                                                                                                                                                                     | `--get_token`                                      |
| `-help`              | `-h` | None         | Show the help message                                                                                                                                                                                                                                                                        | `--help`                                           |
| `--sleep_time`       | `-s` | 2            | How long to sleep between each member request. With values lower than 2, rate limits tend to be hit, which may lead to a ban. Increase if you hit a rate limit.                                                                                                                              | `--sleep_time 3`                                   |
| `--loglevel`         | `-l` | info         | Provide logging level.                                                                                                                                                                                                                                                                       | `--loglevel debug`                                 |
| `--output_verbosity` | `-v` | 2            | How much information to be included in the mutual friends and mutual servers files. 1 means just the member name. 2 means the member name and a count the member's of mutual friends or mutual servers. 3 means the member name and a list of the member's mutual friends or mutual servers. | `--output_verbosity 3`                             |
| `--print_info`       | `-p` | True         | If true, the server info, mutual friends, and mutual servers are printed to the command line.                                                                                                                                                                                                | `--print_info False`                               |
| `--write_to_json`    | `-j` | True         | If true, the server info, mutual friends, and mutual servers are written to json files.                                                                                                                                                                                                      | `--write_to_json False`                            |
| `--output_path`      | `-o` | pwd+'output' | Location for output files.                                                                                                                                                                                                                                                                   | `--output_path some_directory/some_subdirectory/`  |
| `--include_servers`  | `-i` | ""           | Only process servers whose names are in this list. If not specified, process all servers. Put server names with mutltiple words in quotes.                                                                                                                                                   | `--include_servers 'server 1' 'server2' 'server3'` |
