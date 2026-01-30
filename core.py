from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import sys
import time
from typing import Iterable, Optional

import discord

DEFAULT_OUTPUT_DIR = "output"


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def default_output_path() -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), DEFAULT_OUTPUT_DIR)


def normalize_output_path(path: Optional[str]) -> str:
    if not path:
        path = default_output_path()
    return os.path.abspath(os.path.expanduser(path))


def _resolve_intents_class():
    intents_cls = getattr(discord, "Intents", None)
    if intents_cls is not None:
        return intents_cls
    try:
        from discord import flags  # type: ignore
    except Exception:
        return None
    return getattr(flags, "Intents", None)


def build_intents():
    intents_cls = _resolve_intents_class()
    if intents_cls is None:
        return None
    intents = intents_cls.default()
    if hasattr(intents, "guilds"):
        intents.guilds = True
    if hasattr(intents, "members"):
        intents.members = True
    if hasattr(intents, "presences"):
        intents.presences = True
    return intents


def _client_supports_intents() -> bool:
    try:
        return "intents" in inspect.signature(discord.Client.__init__).parameters
    except Exception:
        return False


class MyClient(discord.Client):
    def __init__(
        self,
        sleep_time: float,
        output_verbosity: int,
        print_info: bool,
        write_to_json: bool,
        output_path: str,
        include_servers: Iterable[str],
        include_channels: Iterable[str],
        max_members: int,
        period_max_members: int,
        pause_duration: int,
        member_fetch_timeout: Optional[float] = None,
        intents: Optional[object] = None,
    ) -> None:
        resolved_intents = intents or build_intents()
        if _client_supports_intents() and resolved_intents is not None:
            super().__init__(intents=resolved_intents)
        else:
            super().__init__()
        self.sleep_time = sleep_time
        self.output_verbosity = output_verbosity
        self.print_info = print_info
        self.write_to_json = write_to_json
        self.output_path = output_path
        self.include_servers = set(include_servers)
        self.include_channels = set(include_channels)
        self.max_members = max_members
        self.period_max_members = period_max_members
        self.pause_duration = pause_duration
        self.member_fetch_timeout = (
            member_fetch_timeout if member_fetch_timeout and member_fetch_timeout > 0 else None
        )

    async def on_ready(self) -> None:
        logging.info("Client ready as %s", self.user)
        if self.include_servers:
            logging.info(
                "Server filter enabled (%s): %s",
                len(self.include_servers),
                sorted(self.include_servers),
            )
        if self.include_channels:
            logging.info(
                "Channel filter enabled (%s): %s",
                len(self.include_channels),
                sorted(self.include_channels),
            )
        logging.info(
            "Starting scan: sleep_time=%s, max_members=%s, period_max_members=%s, pause_duration=%s",
            self.sleep_time,
            self.max_members,
            self.period_max_members,
            self.pause_duration,
        )
        if self.member_fetch_timeout:
            logging.info(
                "Member fetch timeout enabled: %ss", self.member_fetch_timeout
            )
        else:
            logging.info("Member fetch timeout disabled (will wait indefinitely)")
        friend_ids = self.get_friend_ids(self)
        server_info = await self.get_server_info(
            self,
            friend_ids,
            self.sleep_time,
            self.include_servers,
            self.include_channels,
            self.max_members,
            self.period_max_members,
            self.pause_duration,
            self.member_fetch_timeout,
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
                mutual_friends[server] = [
                    (member, -mutual_friends_count)
                    for mutual_friends_count, member, mutual_friends_list in mutual_friends[
                        server
                    ]
                ]
            elif output_verbosity == 3:
                mutual_friends[server] = [
                    (member, -mutual_friends_count, mutual_friends_list)
                    for mutual_friends_count, member, mutual_friends_list in mutual_friends[
                        server
                    ]
                ]
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
                mutual_servers[server] = [
                    (member, -mutual_servers_count)
                    for mutual_servers_count, member, mutual_servers_list in mutual_servers[
                        server
                    ]
                ]
            elif output_verbosity == 3:
                mutual_servers[server] = [
                    (member, -mutual_servers_count, mutual_servers_list)
                    for mutual_servers_count, member, mutual_servers_list in mutual_servers[
                        server
                    ]
                ]
        return mutual_servers

    def print_client_info(self, server_info, friends, mutual_friends, mutual_servers) -> None:
        print("Server Info:")
        print(json.dumps(server_info, indent=4))
        print("\nFriends:")
        print(json.dumps(friends, indent=4))
        print("\nMutual Friends:")
        print(json.dumps(mutual_friends, indent=4))
        print("\nMutual Servers:")
        print(json.dumps(mutual_servers, indent=4))

    def write_data_to_json(
        self, server_info, friends, mutual_friends, mutual_servers, output_path
    ) -> None:
        resolved_output_path = normalize_output_path(output_path)
        os.makedirs(resolved_output_path, exist_ok=True)
        with open(os.path.join(resolved_output_path, "server_info.json"), "w") as f:
            json.dump(server_info, f, indent=4)
        with open(os.path.join(resolved_output_path, "friends.json"), "w") as f:
            json.dump(friends, f, indent=4)
        with open(os.path.join(resolved_output_path, "mutual_friends.json"), "w") as f:
            json.dump(mutual_friends, f, indent=4)
        with open(os.path.join(resolved_output_path, "mutual_servers.json"), "w") as f:
            json.dump(mutual_servers, f, indent=4)

    async def get_server_info(
        self,
        client: discord.Client,
        friend_ids: set,
        sleep_time: float,
        include_servers: set,
        include_channels: set,
        max_members: int,
        period_max_members: int,
        pause_duration: int,
        member_fetch_timeout: Optional[float],
    ) -> dict:
        async def maybe_wait_for(coro, timeout: Optional[float], label: str):
            if not timeout:
                return await coro
            try:
                return await asyncio.wait_for(coro, timeout=timeout)
            except asyncio.TimeoutError:
                logging.warning("%s timed out after %ss", label, timeout)
                return None

        async def fetch_members_with_retry(server, channels=None):
            try:
                if channels:
                    return set(await server.fetch_members(channels=channels))
                return set(await server.fetch_members())
            except discord.HTTPException as e:
                if e.status == 429:
                    retry_after = int(e.response.headers.get("Retry-After", 1))
                    logging.warning(
                        f"Rate limited. Retrying after {retry_after} seconds."
                    )
                    await asyncio.sleep(retry_after)
                    return await fetch_members_with_retry(server, channels)
                logging.error(f"Failed to fetch members: {e}")
                return set()
            except RuntimeError as e:
                logging.warning(f"Cannot fetch members for {server.name}: {e}")
                return set()

        logging.info("Fetching guild list...")
        user_servers = await client.fetch_guilds()
        servers_count = len(user_servers)
        logging.info("Found %s guilds", servers_count)
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
                matched_servers.add(server_name)
                specific_server_count += 1
            logging.info(
                "Fetching members for server %s (%s/%s)",
                server_name,
                server_idx + 1,
                servers_count,
            )

            if include_channels:
                channels = [
                    discord.utils.get(server.channels, name=channel)
                    for channel in include_channels
                ]
                logging.info(
                    "Starting fetch_members for %s with channels filter (%s)",
                    server_name,
                    len(channels),
                )
                fetch_start = time.monotonic()
                fetch_server_members = await maybe_wait_for(
                    fetch_members_with_retry(server, channels),
                    member_fetch_timeout,
                    f"fetch_members for {server_name}",
                )
            else:
                logging.info("Starting fetch_members for %s (no channel filter)", server_name)
                fetch_start = time.monotonic()
                fetch_server_members = await maybe_wait_for(
                    fetch_members_with_retry(server),
                    member_fetch_timeout,
                    f"fetch_members for {server_name}",
                )
            if fetch_server_members is None:
                fetch_server_members = set()
            logging.info(
                "fetch_members returned %s members for %s in %.1fs",
                len(fetch_server_members),
                server_name,
                time.monotonic() - fetch_start,
            )

            chunk_start = time.monotonic()
            logging.info("Starting chunk() for %s", server_name)
            try:
                chunk_result = await maybe_wait_for(
                    server.chunk(),
                    member_fetch_timeout,
                    f"chunk() for {server_name}",
                )
                chunked_server_members = set(chunk_result or [])
                logging.info(
                    "chunk() returned %s members for %s in %.1fs",
                    len(chunked_server_members),
                    server_name,
                    time.monotonic() - chunk_start,
                )
            except Exception as e:
                logging.warning(
                    "chunk() failed for %s after %.1fs: %s",
                    server_name,
                    time.monotonic() - chunk_start,
                    e,
                )
                chunked_server_members = set()
            guild_server_members = set(server.members)
            logging.info(
                "guild.members has %s members for %s", len(guild_server_members), server_name
            )
            server_members = list(
                fetch_server_members.union(guild_server_members).union(
                    chunked_server_members
                )
            )

            server_member_count = len(server_members)
            logging.info(
                "Server %s has %s members (processing up to %s)",
                server_name,
                server_member_count,
                max_members,
            )
            if server_member_count > max_members:
                logging.info(
                    "The server member count of %s is greater than the max member count "
                    "of %s, selecting only the first %s members",
                    server_member_count,
                    max_members,
                    max_members,
                )

            selected_server_member_count = min(server_member_count, max_members)

            server_info[server_name] = dict()

            for start_idx in range(0, selected_server_member_count, period_max_members):
                end_idx = min(
                    start_idx + period_max_members, selected_server_member_count
                )
                for member_idx in range(start_idx, end_idx):
                    member = server_members[member_idx]

                    if include_servers:
                        logging.info(
                            "Processing %s server, progress = %s/%s servers %s/%s members",
                            server.name,
                            specific_server_count,
                            len(include_servers),
                            member_idx + 1,
                            selected_server_member_count,
                        )
                    else:
                        logging.info(
                            "Processing %s server, progress = %s/%s servers %s/%s members",
                            server.name,
                            server_idx + 1,
                            servers_count,
                            member_idx + 1,
                            selected_server_member_count,
                        )
                    if member.id == client.user.id:
                        continue

                    member_name = f"{member.name}#{member.discriminator}"

                    if member_name in seen_members:
                        server_info[server_name][member_name] = dict()
                        server_info[server_name][member_name]["is_friend"] = (
                            seen_members[member_name]["is_friend"]
                        )
                        server_info[server_name][member_name]["mutual_friends"] = (
                            seen_members[member_name]["mutual_friends"]
                        )

                        server_info[server_name][member_name]["mutual_servers"] = (
                            seen_members[member_name]["mutual_servers"]
                        )
                        continue
                    seen_members[member_name] = dict()

                    try:
                        member_profile = await server.fetch_member_profile(
                            member.id,
                            with_mutual_guilds=True,
                            with_mutual_friends=True,
                        )
                    except (discord.errors.NotFound, discord.errors.InvalidData):
                        logging.warning(
                            "Member %s not found or invalid. Skipping.", member_name
                        )
                        continue
                    except discord.errors.HTTPException as e:
                        logging.warning(
                            "HTTP error fetching profile for %s: %s. Skipping.",
                            member_name,
                            e,
                        )
                        continue
                    except Exception as e:
                        logging.error(
                            "Unexpected error fetching profile for %s: %s.",
                            member_name,
                            e,
                        )
                        continue

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

                    await asyncio.sleep(sleep_time)

                if end_idx < selected_server_member_count and pause_duration > 0:
                    logging.info("Pausing for %s seconds...", pause_duration)
                    await asyncio.sleep(pause_duration)

        unmatched_servers = include_servers.difference(matched_servers)
        if unmatched_servers:
            logging.warning(
                "Did not find the following servers: %s consider choosing from the following servers: %s",
                unmatched_servers,
                seen_servers,
            )
        return server_info


def run_client(*, token: str, **kwargs) -> None:
    if not token:
        raise ValueError("Discord token is required.")
    client = MyClient(**kwargs)
    client.run(token)
