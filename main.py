import argparse
import json
import logging
import os
from time import sleep
import sys

import discord
from dotenv import load_dotenv

from get_token import get_token


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MyClient(discord.Client):
    def __init__(
        self,
        sleep_time,
        output_verbosity,
        print_info,
        write_to_json,
        output_path,
        include_servers,
        include_channels,
        max_members,
    ):
        super().__init__()
        self.sleep_time = sleep_time
        self.output_verbosity = output_verbosity
        self.print_info = print_info
        self.write_to_json = write_to_json
        self.output_path = output_path
        self.include_servers = set(include_servers)
        self.include_channels = set(include_channels)
        self.max_members = max_members

    async def on_ready(self) -> None:
        friend_ids = self.get_friend_ids(self)
        server_info = await self.get_server_info(
            self,
            friend_ids,
            self.sleep_time,
            self.include_servers,
            self.include_channels,
            self.max_members,
        )
        friends = self.get_friends(server_info)
        mutual_friends = self.get_mutual_friends(server_info, self.output_verbosity)
        mutual_servers = self.get_mutual_servers(server_info, self.output_verbosity)

        if self.print_info:
            self.print_client_info(server_info, friends, mutual_friends, mutual_servers)

        if self.write_to_json:
            self.write_data_to_json(
                server_info, friends, mutual_friends, mutual_servers, self.output_path
            )

        await self.close()

    def get_friend_ids(self, client: discord.Client) -> set:
        friend_ids = set()
        for friend in self.friends:
            friend_ids.add(friend.user.id)
        return friend_ids

    def get_friends(self, server_info: dict) -> dict:
        friends = dict()
        for server in server_info:
            friends[server] = list()
            for member in server_info[server]:
                if server_info[server][member]["is_friend"]:
                    friends[server].append(member)
        return friends

    def get_mutual_friends(self, server_info: dict, output_verbosity: int) -> dict:
        mutual_friends = dict()
        for server in server_info:
            mutual_friends[server] = list()
            for member in server_info[server]:
                if server_info[server][member]["mutual_friends"]:
                    mutual_friends[server].append(
                        (
                            -len(server_info[server][member]["mutual_friends"]),
                            member,
                            server_info[server][member]["mutual_friends"],
                        )
                    )
            mutual_friends[server].sort()
            if output_verbosity == 1:
                mutual_friends[server] = [
                    member
                    for mutual_friends_count, member, mutual_friends_list in mutual_friends[
                        server
                    ]
                ]
            elif output_verbosity == 2:
                mutual_friends[server] = {
                    member: -mutual_friends_count
                    for mutual_friends_count, member, mutual_friends_list in mutual_friends[
                        server
                    ]
                }
            else:
                mutual_friends[server] = {
                    member: mutual_friends_list
                    for mutual_friends_count, member, mutual_friends_list in mutual_friends[
                        server
                    ]
                }
        return mutual_friends

    def get_mutual_servers(self, server_info: dict, output_verbosity: int) -> dict:
        mutual_servers = dict()
        for server in server_info:
            mutual_servers[server] = list()
            for member in server_info[server]:
                if server_info[server][member]["mutual_servers"]:
                    mutual_servers[server].append(
                        (
                            -len(server_info[server][member]["mutual_servers"]),
                            member,
                            server_info[server][member]["mutual_servers"],
                        )
                    )
            mutual_servers[server].sort()
            if output_verbosity == 1:
                mutual_servers[server] = [
                    member
                    for mutual_servers_count, member, mutual_servers_list in mutual_servers[
                        server
                    ]
                ]
            elif output_verbosity == 2:
                mutual_servers[server] = {
                    member: -mutual_servers_count
                    for mutual_servers_count, member, mutual_servers_list in mutual_servers[
                        server
                    ]
                }
            else:
                mutual_servers[server] = {
                    member: mutual_servers_list
                    for mutual_servers_count, member, mutual_servers_list in mutual_servers[
                        server
                    ]
                }
        return mutual_servers

    def write_data_to_json(
        self,
        server_info: dict,
        friends: dict,
        mutual_friends: dict,
        mutual_servers: dict,
        output_path: str,
    ) -> None:
        resolved_output_path = resource_path(output_path)
        os.makedirs(
            resolved_output_path, exist_ok=True
        )  # Ensure the directory is created at the resolved path

        file_names = [
            (server_info, "server_info.json"),
            (friends, "friends.json"),
            (mutual_friends, "mutual_friends.json"),
            (mutual_servers, "mutual_servers.json"),
        ]

        for input_dictionary, file_name in file_names:
            file_path = os.path.join(
                resolved_output_path, file_name
            )  # Resolve each file's path
            with open(file_path, "w") as fp:
                json.dump(input_dictionary, fp, indent=4)

    def print_client_info(
        self,
        server_info: dict,
        friends: dict,
        mutual_friends: dict,
        mutual_servers: dict,
    ) -> None:
        print("\nServer Info\n")
        print(json.dumps(server_info, indent=4))
        print("\nFriends\n")
        print(json.dumps(friends, indent=4))
        print("\nMutual Friends\n")
        print(json.dumps(mutual_friends, indent=4))
        print("\nMutual Servers\n")
        print(json.dumps(mutual_servers, indent=4))

    async def get_server_info(
        self,
        client: discord.Client,
        friend_ids: set,
        sleep_time: float,
        include_servers: set,
        include_channels: set,
        max_members: int,
    ) -> dict:
        user_servers = await client.fetch_guilds()
        servers_count = len(user_servers)
        server_info = dict()
        seen_members = dict()
        include_servers = set(include_servers)
        include_channels = set(include_channels)
        specific_server_count = 0
        matched_servers = set()
        seen_servers = set()

        for server_idx, user_server in enumerate(user_servers):
            server = client.get_guild(user_server.id)
            server_name = server.name
            seen_servers.add(server_name)
            if include_servers:
                if server_name not in include_servers:
                    continue
                else:
                    matched_servers.add(server_name)
                    specific_server_count += 1

            if include_channels:
                channels = [
                    discord.utils.get(server.channels, name=channel)
                    for channel in include_channels
                ]
                try:
                    fetch_server_members = set(
                        await server.fetch_members(channels=channels)
                    )
                except discord.ClientException:
                    logging.info("server.fetch_members() failed")
                    fetch_server_members = set()
            else:
                try:
                    fetch_server_members = set(await server.fetch_members())
                except discord.ClientException:
                    logging.info(
                        "server.fetch_members() failed, please try specifying a 1-5 channels to fetch channels from with the -c flag"
                    )
                    fetch_server_members = set()
            try:
                chunked_server_members = set(await server.chunk())
            except Exception:
                logging.info("server.fetch_members() failed")
                chunked_server_members = set()
            guild_server_members = set(server.members)
            server_members = list(
                fetch_server_members.union(guild_server_members).union(
                    chunked_server_members
                )
            )

            print(f"fetch_server_members: {len(fetch_server_members)}")
            print(f"guild_server_members: {len(guild_server_members)}")
            print(f"chunked_server_members: {len(chunked_server_members)}")

            server_member_count = len(server_members)
            if server_member_count > max_members:
                logging.info(
                    f"The server member count of {(server_member_count)} is greater than the max member count of {(max_members)}, selecting only the first {(max_members)} members"
                )

            selected_server_member_count = min(server_member_count, max_members)

            server_info[server_name] = dict()

            for member_idx in range(selected_server_member_count):
                member = server_members[member_idx]

                if include_servers:
                    logging.info(
                        f"Processing {server.name} server, progress = {specific_server_count}/{len(include_servers)} servers {member_idx+1}/{selected_server_member_count} members"
                    )
                else:
                    logging.info(
                        f"Processing {server.name} server, progress = {server_idx+1}/{servers_count} servers {member_idx+1}/{selected_server_member_count} members"
                    )
                if member.id == client.user.id:
                    continue

                member_name = f"{member.name}#{member.discriminator}"

                if member_name in seen_members:
                    server_info[server_name][member_name] = dict()
                    server_info[server_name][member_name]["is_friend"] = seen_members[
                        member_name
                    ]["is_friend"]
                    server_info[server_name][member_name]["mutual_friends"] = (
                        seen_members[member_name]["mutual_friends"]
                    )

                    server_info[server_name][member_name]["mutual_servers"] = (
                        seen_members[member_name]["mutual_servers"]
                    )
                    continue
                else:
                    seen_members[member_name] = dict()

                member_profile = await server.fetch_member_profile(
                    member.id,
                    with_mutual_guilds=True,
                    with_mutual_friends=True,
                )

                server_info[server_name][member_name] = dict()

                mutual_friend_names = []
                mutual_server_names = []
                mutual_friends = member_profile.mutual_friends
                mutual_servers = member_profile.mutual_guilds

                if member.id in friend_ids:
                    server_info[server_name][member_name]["is_friend"] = True
                    seen_members[member_name]["is_friend"] = True
                else:
                    server_info[server_name][member_name]["is_friend"] = False
                    seen_members[member_name]["is_friend"] = False

                for friend in mutual_friends:
                    friend_name = f"{friend.name}#{friend.discriminator}"
                    mutual_friend_names.append(friend_name)

                server_info[server_name][member_name]["mutual_friends"] = (
                    mutual_friend_names
                )
                seen_members[member_name]["mutual_friends"] = mutual_friend_names

                for mutual_server in mutual_servers:
                    if mutual_server.id != server.id:
                        mutual_server_names.append(mutual_server.guild.name)

                server_info[server_name][member_name]["mutual_servers"] = (
                    mutual_server_names
                )

                seen_members[member_name]["mutual_servers"] = mutual_server_names

                sleep(sleep_time)

        unmatched_servers = include_servers.difference(matched_servers)
        if unmatched_servers:
            logging.warning(
                f"Did not find the following servers: {unmatched_servers} consider choosing from the following servers: {seen_servers}"
            )
        sleep(sleep_time)
        return server_info


def check_positive_float(original_value):
    try:
        value = float(original_value)
        if value <= 0:
            raise argparse.ArgumentTypeError(f"{original_value} is not a positive")
    except ValueError:
        raise Exception(f"{original_value} is not an float")
    return value


def add_arguments(parser: argparse.ArgumentParser, output_path=str):
    parser.add_argument(
        "-s",
        "--sleep_time",
        default=3.0,
        type=check_positive_float,
        help="How long to sleep between each member request. With values lower than 3, rate limits tend to be hit, which may lead to a ban. Increase if you hit a rate limit. Example --sleep_time 4, default=3",
    )

    parser.add_argument(
        "-l",
        "--loglevel",
        default="info",
        choices=["debug", "info", "warn", "warning", "error", "critical"],
        help="Provide logging level. Example --loglevel debug, default=info",
    )

    parser.add_argument(
        "-v",
        "--output_verbosity",
        default=2,
        type=int,
        choices=[1, 2, 3],
        help="How much information to be included in the mutual friends and mutual servers files. 1 means just the member name. 2 means the member name and a count the member's of mutual friends or mutual servers. 3 means the member name and a list of the member's mutual friends or mutual servers. Example --output_verbosity 3, default=2",
    )

    parser.add_argument(
        "-p",
        "--print_info",
        default=True,
        help="If true, the server info, mutual friends, and mutual servers are printed to the command line. Example --print_info False, default=True",
    )

    parser.add_argument(
        "-j",
        "--write_to_json",
        default=True,
        help="If true, the server info, mutual friends, and mutual servers are written to json files. Example --write_to_json False, default=True",
    )

    parser.add_argument(
        "-o",
        "--output_path",
        default=output_path,
        help="Location for output files. Example --output_path some_directory/some_subdirectory/, default=pwd+'output'",
    )

    parser.add_argument(
        "-i",
        "--include_servers",
        default="",
        nargs="+",
        help="Only process servers whose names are in this list. If not specified, process all servers. Put server names with mutltiple words in quotes. Example --include_servers 'server 1' 'server2' 'server3', default=''",
    )

    parser.add_argument(
        "-c",
        "--include_channels",
        default="",
        nargs="+",
        help="Only process the members who are in the provided channels. If not specified, tries to retrieve all server members if you have the appropriate permissions, otherwise attempts to scrape the member sidebar. Example --include_channels 'channel-1' 'channel-2' 'channel-3', default=''",
    )

    parser.add_argument(
        "-g",
        "--get_token",
        action="store_true",
        help="If set, will run the get_token script to get a token",
    )

    parser.add_argument(
        "-m",
        "--max_members",
        type=int,
        default=sys.maxsize,
        help="Maximum number of members to process. Example --max_members 100, default=no limit",
    )


if __name__ == "__main__":
    # Set the default output path to the current working directory + /output/
    output_path = os.path.dirname(os.path.realpath(__file__)) + "/output/"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    parser = argparse.ArgumentParser()
    add_arguments(parser, output_path)
    args = parser.parse_args()
    if args.get_token:
        get_token()
    logging.basicConfig(level=args.loglevel.upper())

    key = "TOKEN"
    if key in os.environ:
        del os.environ[key]

    load_dotenv(verbose=True)
    token = os.getenv(key)

    client = MyClient(
        sleep_time=args.sleep_time,
        output_verbosity=args.output_verbosity,
        print_info=args.print_info,
        write_to_json=args.write_to_json,
        output_path=args.output_path,
        include_servers=args.include_servers,
        include_channels=args.include_channels,
        max_members=args.max_members,
    )
    client.run(token)
