import znc
import re

class admin_control(znc.Module):
    description = "Provides admin commands via hostmask authentication (PM and Channel)"

    # Define your allowed hostmask(s) here
    ALLOWED_HOSTMASKS = [
        '*!*@Janroe.org',
        '*!*@ddoser.org',
        '*!*@nothingisharmexceptyourpri.de',
	'*!*@debian.debian.debian.ph',
	'*!*@*.debian.ph',
        # Add more hostmasks as needed:
        # 'YourName!*@some.isp.com',
        # '*!yourusername@192.168.1.*',
    ]

    def OnLoad(self, args, message):
        self.debug_mode = False  # Set to True to enable debug logging
        if self.debug_mode:
            self.PutModule("Admin Control module loaded. Ready for commands in PM and channels.")
        return True

    def _is_user_admin(self, nick):
        """Check if the user's hostmask matches any of the allowed hostmasks."""
        user_hostmask = nick.GetHostMask()
        for allowed_mask in self.ALLOWED_HOSTMASKS:
            # Convert the allowed mask pattern to a regex
            regex_pattern = allowed_mask.replace('.', r'\.').replace('*', '.*').replace('?', '.')
            if re.match(regex_pattern, user_hostmask, re.IGNORECASE):
                return True
        return False

    def _send_notice_to_user(self, nick_name, message):
        """Helper function to send NOTICE response directly to the user"""
        self.GetNetwork().PutIRC(f"NOTICE {nick_name} :{message}")

    def _handle_command(self, nick, channel, message):
        """Handle admin commands from both PM and channel messages"""
        msg_text = message.s
        sender_nick = nick.GetNick()
        sender_hostmask = nick.GetHostMask()
        is_channel = channel is not None
        channel_name = channel.GetName() if is_channel else None

        # Check if the user is an admin
        if not self._is_user_admin(nick):
            # Silently ignore non-admins for security
            return znc.CONTINUE

        # Log the command (only if debug mode is enabled)
        if self.debug_mode:
            location = f"channel {channel_name}" if is_channel else "PM"
            self.PutModule(f"Received command '{msg_text}' from admin {sender_hostmask} in {location}")

        # Parse the command
        parts = msg_text.strip().split()
        if not parts:
            return znc.CONTINUE

        command = parts[0].lower()
        args = parts[1:]

        # Handle the !join command
        if command == "!join" and len(args) >= 1:
            channel_to_join = args[0]
            key = args[1] if len(args) > 1 else None
            if key:
                self.GetNetwork().PutIRC(f"JOIN {channel_to_join} {key}")
            else:
                self.GetNetwork().PutIRC(f"JOIN {channel_to_join}")
            self._send_notice_to_user(sender_nick, f"Joining channel: {channel_to_join}")

        # Handle the !part command
        elif command == "!part" and len(args) >= 1:
            channel_to_part = args[0]
            reason = " ".join(args[1:]) if len(args) > 1 else "Requested by admin"
            self.GetNetwork().PutIRC(f"PART {channel_to_part} :{reason}")
            self._send_notice_to_user(sender_nick, f"Parting channel: {channel_to_part}")

        # Handle the !msg command
        elif command == "!msg" and len(args) >= 2:
            target = args[0]
            message_to_send = " ".join(args[1:])
            self.GetNetwork().PutIRC(f"PRIVMSG {target} :{message_to_send}")
            self._send_notice_to_user(sender_nick, f"Message sent to {target}")

        # Handle the !op command
        elif command == "!op" and len(args) >= 1:
            target_nick = args[0]
            target_channel = channel_name if is_channel else (args[1] if len(args) > 1 else None)
            if target_channel:
                self.GetNetwork().PutIRC(f"MODE {target_channel} +o {target_nick}")
                self._send_notice_to_user(sender_nick, f"Opping {target_nick} on {target_channel}")
            else:
                self._send_notice_to_user(sender_nick, "Error: Specify a channel for !op command")

        # Handle the !deop command
        elif command == "!deop" and len(args) >= 1:
            target_nick = args[0]
            target_channel = channel_name if is_channel else (args[1] if len(args) > 1 else None)
            if target_channel:
                self.GetNetwork().PutIRC(f"MODE {target_channel} -o {target_nick}")
                self._send_notice_to_user(sender_nick, f"De-opping {target_nick} on {target_channel}")
            else:
                self._send_notice_to_user(sender_nick, "Error: Specify a channel for !deop command")

        # Handle the !voice command
        elif command == "!voice" and len(args) >= 1:
            target_nick = args[0]
            target_channel = channel_name if is_channel else (args[1] if len(args) > 1 else None)
            if target_channel:
                self.GetNetwork().PutIRC(f"MODE {target_channel} +v {target_nick}")
                self._send_notice_to_user(sender_nick, f"Voicing {target_nick} on {target_channel}")
            else:
                self._send_notice_to_user(sender_nick, "Error: Specify a channel for !voice command")

        # Handle the !devoice command
        elif command == "!devoice" and len(args) >= 1:
            target_nick = args[0]
            target_channel = channel_name if is_channel else (args[1] if len(args) > 1 else None)
            if target_channel:
                self.GetNetwork().PutIRC(f"MODE {target_channel} -v {target_nick}")
                self._send_notice_to_user(sender_nick, f"De-voicing {target_nick} on {target_channel}")
            else:
                self._send_notice_to_user(sender_nick, "Error: Specify a channel for !devoice command")

        # Handle the !raw command (DANGEROUS, use with caution)
        elif command == "!raw" and len(args) >= 1:
            raw_command = " ".join(args)
            self.GetNetwork().PutIRC(raw_command)
            self._send_notice_to_user(sender_nick, f"Sent raw: {raw_command}")

        # Handle the !help command
        elif command == "!help":
            help_text = [
                "Admin Commands (PM or Channel):",
                "!join <channel> [key] - Join a channel",
                "!part <channel> [reason] - Part a channel", 
                "!msg <nick/channel> <message> - Send a message",
                "",
                "Channel Management (in channel or specify channel):",
                "!op <nick> [channel] - Op a user",
                "!deop <nick> [channel] - Deop a user",
                "!voice <nick> [channel] - Voice a user", 
                "!devoice <nick> [channel] - Devoice a user",
                "",
                "Advanced:",
                "!raw <irc command> - Send a raw IRC command (USE WITH CAUTION)",
                "!debug [on|off] - Toggle debug logging",
                "!help - Show this help",
                "",
                "Note: In PM, specify channel for management commands.",
                "Example: !op SomeNick #mychannel"
            ]
            # Send help as NOTICE to the user
            for line in help_text:
                if line.strip():
                    self._send_notice_to_user(sender_nick, line)

        # Handle the !debug command
        elif command == "!debug":
            if len(args) >= 1:
                if args[0].lower() == "on":
                    self.debug_mode = True
                    self._send_notice_to_user(sender_nick, "Debug logging enabled")
                elif args[0].lower() == "off":
                    self.debug_mode = False
                    self._send_notice_to_user(sender_nick, "Debug logging disabled")
                else:
                    self._send_notice_to_user(sender_nick, f"Debug logging is {'on' if self.debug_mode else 'off'}")
            else:
                self._send_notice_to_user(sender_nick, f"Debug logging is {'on' if self.debug_mode else 'off'}")

        # Command not found
        else:
            self._send_notice_to_user(sender_nick, "")

        return znc.CONTINUE

    def OnPrivMsg(self, nick, message):
        """Handle private messages"""
        return self._handle_command(nick, None, message)

    def OnChanMsg(self, nick, channel, message):
        """Handle channel messages"""  
        return self._handle_command(nick, channel, message)

