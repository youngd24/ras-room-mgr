#!/usr/bin/env python3
"""
RAS Room Manager - Retro AIM Server Room Management Tool
Manages public chat rooms on a retro AIM server.
"""

import requests
import json
import sys
import argparse
import os
import subprocess
from datetime import datetime
from configparser import ConfigParser

class RASRoomManager:
    def __init__(self, config_file="config.ini"):
        self.base_url = self._load_config(config_file)
        self.sqlite_path = "/usr/local/ras/oscar.sqlite"
        self.sqlite_cmd = "/usr/bin/sqlite3"
    
    def _get_rooms_endpoint(self, room_type):
        """
        Get the appropriate endpoint for the room type.
        
        Args:
            room_type (str): Either 'public' or 'private'
            
        Returns:
            str: The full endpoint URL
        """
        return f"{self.base_url}/chat/room/{room_type}"
    
    def _load_config(self, config_file):
        """
        Load configuration from config file.
        
        Args:
            config_file (str): Path to configuration file
        
        Returns:
            str: Base URL from config file or default
        """
        default_url = "http://localhost:8080"
        
        # Check if config file exists
        if not os.path.exists(config_file):
            print(f"⚠ Config file {config_file} not found, using default URL: {default_url}")
            return default_url
        
        try:
            config = ConfigParser()
            config.read(config_file)
            
            if 'server' in config and 'base_url' in config['server']:
                url = config['server']['base_url']
                print(f"✓ Loaded server URL from config: {url}")
                return url
            else:
                print(f"⚠ Warning: Invalid config format in {config_file}, using default URL")
                return default_url
                
        except Exception as e:
            print(f"⚠ Warning: Error reading config file {config_file}: {e}")
            print(f"✓ Using default URL: {default_url}")
            return default_url

    def get_chat_rooms(self, room_type):
        """
        Retrieves and displays all chat rooms of the specified type.
        
        Args:
            room_type (str): Either 'public' or 'private'
        
        Returns:
            list: List of chat rooms, or None if error occurred
        """
        rooms_endpoint = self._get_rooms_endpoint(room_type)
        
        try:
            print(f"Connecting to: {rooms_endpoint}")
            response = requests.get(rooms_endpoint)
            response.raise_for_status()
            
            chat_rooms = response.json()
            
            print(f"\nFound {len(chat_rooms)} {room_type} chat room(s):\n")
            
            if not chat_rooms:
                print(f"No {room_type} chat rooms found.")
                return chat_rooms
            
            print("-" * 80)
            
            for i, room in enumerate(chat_rooms, 1):
                print(f"Room {i}: {room.get('name', 'Unknown')}")
                
                # Format and display creation time
                create_time = room.get('create_time')
                if create_time:
                    try:
                        dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                        print(f"  Created: {formatted_time}")
                    except ValueError:
                        print(f"  Created: {create_time}")
                
                # Display participants
                participants = room.get('participants', [])
                print(f"  Participants ({len(participants)}):")
                
                if participants:
                    for participant in participants:
                        screen_name = participant.get('screen_name', 'Unknown')
                        user_id = participant.get('id', 'Unknown')
                        print(f"    - {screen_name} (ID: {user_id})")
                else:
                    print("    - No participants")
                
                print("-" * 80)
            
            return chat_rooms
            
        except requests.exceptions.ConnectionError:
            print("✗ Error: Could not connect to the server.")
            print(f"  Make sure the retro AIM server is running at: {self.base_url}")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"✗ HTTP Error: {e}")
            print(f"  Status Code: {response.status_code}")
            if response.text:
                print(f"  Response: {response.text}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching {room_type} chat rooms: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"✗ Error parsing JSON response: {e}")
            print(f"  Raw response: {response.text}")
            return None

    def create_chat_room(self, room_name, room_type):
        """
        Creates a new chat room of the specified type.
        
        Args:
            room_name (str): Name of the chat room to create
            room_type (str): Either 'public' or 'private'
            
        Returns:
            bool: True if room was created successfully, False otherwise
        """
        # Check if trying to create private room (not supported)
        if room_type == "private":
            print("✗ Error: Creating private chat rooms is not supported by the server.")
            print("  Only public chat rooms can be created through the API.")
            return False
            
        # Validate room name
        if not self._validate_room_name(room_name):
            return False
        
        # Only proceed if room_type is public
        rooms_endpoint = self._get_rooms_endpoint(room_type)
        payload = {"name": room_name}
        headers = {"Content-Type": "application/json"}
        
        try:
            print(f"Creating {room_type} chat room: '{room_name}'")
            print(f"Sending POST request to: {rooms_endpoint}")
            
            response = requests.post(rooms_endpoint, json=payload, headers=headers)
            
            if response.status_code == 201:
                print(f"✓ {room_type.capitalize()} chat room '{room_name}' created successfully!")
                return True
            elif response.status_code == 400:
                print(f"✗ Bad request: Invalid input data.")
                if response.text:
                    print(f"  Server response: {response.text}")
                return False
            elif response.status_code == 409:
                print(f"✗ {room_type.capitalize()} chat room '{room_name}' already exists.")
                return False
            else:
                print(f"✗ Unexpected response status: {response.status_code}")
                if response.text:
                    print(f"  Server response: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("✗ Error: Could not connect to the server.")
            print(f"  Make sure the retro AIM server is running at: {self.base_url}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Error creating {room_type} chat room: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return False

    def delete_chat_room(self, room_name, room_type):
        """
        Deletes a chat room by directly removing it from the SQLite database.
        
        Args:
            room_name (str): Name of the chat room to delete
            room_type (str): Either 'public' or 'private' (for display purposes)
            
        Returns:
            bool: True if room was deleted successfully, False otherwise
        """
        if not self._validate_room_name(room_name):
            return False
        
        # Check if database file exists
        if not os.path.exists(self.sqlite_path):
            print(f"✗ Error: Database file not found at {self.sqlite_path}")
            return False
        
        # Check if sqlite3 command exists
        if not os.path.exists(self.sqlite_cmd):
            print(f"✗ Error: SQLite command not found at {self.sqlite_cmd}")
            return False
        
        # Check database file permissions
        if not self._check_database_permissions():
            return False
        
        try:
            print(f"Deleting {room_type} chat room: '{room_name}'")
            print(f"Executing direct database deletion...")
            
            # Escape single quotes for SQL safety
            escaped_name = room_name.replace("'", "''")
            sql_query = "DELETE FROM chatRoom WHERE name = '" + escaped_name + "'"
            
            # Execute the sqlite command
            result = subprocess.run(
                [self.sqlite_cmd, self.sqlite_path, sql_query],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Check if the room still exists to verify deletion
            check_query = "SELECT COUNT(*) FROM chatRoom WHERE name = '" + escaped_name + "'"
            check_result = subprocess.run(
                [self.sqlite_cmd, self.sqlite_path, check_query],
                capture_output=True,
                text=True,
                check=True
            )
            
            room_count = int(check_result.stdout.strip())
            
            if room_count == 0:
                print(f"✓ {room_type.capitalize()} chat room '{room_name}' deleted successfully!")
                return True
            else:
                print(f"⚠ Warning: Room '{room_name}' may not have existed or deletion failed.")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"✗ Error executing SQLite command: {e}")
            if e.stderr:
                print(f"  SQLite error: {e.stderr}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error during deletion: {e}")
            return False

    def _check_database_permissions(self):
        """
        Check if the current user has read/write permissions to the database file.
        
        Returns:
            bool: True if permissions are sufficient, False otherwise
        """
        import getpass
        import stat
        
        current_user = getpass.getuser()
        
        try:
            # Get file stats
            file_stat = os.stat(self.sqlite_path)
            file_mode = file_stat.st_mode
            
            # Check if file is readable and writable by current user
            is_readable = os.access(self.sqlite_path, os.R_OK)
            is_writable = os.access(self.sqlite_path, os.W_OK)
            
            if not is_readable or not is_writable:
                print(f"✗ Error: Insufficient permissions for database file.")
                print(f"  Current user: {current_user}")
                print(f"  Database file: {self.sqlite_path}")
                print(f"  File permissions: {stat.filemode(file_mode)}")
                print(f"  Read access: {'✓' if is_readable else '✗'}")
                print(f"  Write access: {'✓' if is_writable else '✗'}")
                print(f"")
                print(f"  Possible solutions:")
                print(f"  - Run the script as a user with database access (e.g., sudo)")
                print(f"  - Change file permissions: sudo chmod 666 {self.sqlite_path}")
                print(f"  - Add current user to the appropriate group")
                return False
            
            return True
            
        except OSError as e:
            print(f"✗ Error checking file permissions: {e}")
            return False

    def _validate_room_name(self, room_name):
        """
        Validates the chat room name.
        
        Args:
            room_name (str): Room name to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not room_name:
            print("✗ Error: Room name cannot be empty.")
            return False
        
        if not room_name.strip():
            print("✗ Error: Room name cannot be only whitespace.")
            return False
        
        return True

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="RAS Room Manager - Manage public chat rooms on retro AIM server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s get public                              # List all public chat rooms
  %(prog)s get private                             # List all private chat rooms
  %(prog)s create public "General Chat"           # Create a public room
  %(prog)s delete public "Old Room"               # Delete a public room
  %(prog)s delete private "Secret Room"           # Delete a private room
  %(prog)s --config-file myserver.ini              # Use custom config file
        """
    )
    
    parser.add_argument(
        "action",
        choices=["get", "create", "delete"],
        help="Action to perform: 'get' to list rooms, 'create' to create a new room, 'delete' to delete a room"
    )
    
    parser.add_argument(
        "room_type",
        choices=["public", "private"],
        help="Type of chat room: 'public' or 'private'"
    )
    
    parser.add_argument(
        "room_name",
        nargs="?",
        help="Name of the room to create or delete (required for 'create' and 'delete' actions)"
    )
    
    parser.add_argument(
        "--config-file",
        default="config.ini",
        help="Path to configuration file (default: config.ini)"
    )
    
    args = parser.parse_args()
    
    print("RAS Room Manager - Retro AIM Server Room Management")
    print("=" * 55)
    
    # Initialize the room manager
    room_manager = RASRoomManager(args.config_file)
    
    if args.action == "get":
        # List all chat rooms of the specified type
        rooms = room_manager.get_chat_rooms(args.room_type)
        if rooms is not None:
            print(f"\n✓ Successfully retrieved {len(rooms)} {args.room_type} chat room(s).")
            sys.exit(0)
        else:
            print(f"\n✗ Failed to retrieve {args.room_type} chat rooms.")
            sys.exit(1)
    
    elif args.action == "create":
        # Get room name from positional argument
        room_name = args.room_name
        
        if not room_name:
            print("✗ Error: Room name is required for 'create' action.")
            print("\nUsage examples:")
            print("  python ras-room-mgr.py create public \"My Public Room\"")
            sys.exit(1)
        
        # Create the chat room
        success = room_manager.create_chat_room(room_name, args.room_type)
        
        if success:
            print(f"\n🎉 Successfully created {args.room_type} chat room: '{room_name}'")
            print("\nYou can now:")
            print(f"- Run 'python ras-room-mgr.py get {args.room_type}' to verify the room was created")
            print("- Connect with an AIM client to join the room")
            sys.exit(0)
        else:
            print(f"\n❌ Failed to create {args.room_type} chat room: '{room_name}'")
            sys.exit(1)
    
    elif args.action == "delete":
        # Get room name from positional argument
        room_name = args.room_name
        
        if not room_name:
            print("✗ Error: Room name is required for 'delete' action.")
            print("\nUsage examples:")
            print("  python ras-room-mgr.py delete public \"Room to Delete\"")
            print("  python ras-room-mgr.py delete private \"Private Room to Delete\"")
            sys.exit(1)
        
        # Delete the chat room
        success = room_manager.delete_chat_room(room_name, args.room_type)
        
        if success:
            print(f"\n🗑️  Successfully deleted {args.room_type} chat room: '{room_name}'")
            print("\nYou can now:")
            print(f"- Run 'python ras-room-mgr.py get {args.room_type}' to verify the room was deleted")
            sys.exit(0)
        else:
            print(f"\n❌ Failed to delete {args.room_type} chat room: '{room_name}'")
            sys.exit(1)

if __name__ == "__main__":
    main()
