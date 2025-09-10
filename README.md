# RAS Room Manager

A command-line tool for managing chat rooms on [Retro AIM Server](https://github.com/mk6i/retro-aim-server). This tool provides an easy way to list, create, and delete both public and private chat rooms.

## Features

- List chat rooms - View all public or private chat rooms with participant details
- Create public rooms - Add new public chat rooms via API
- Delete rooms - Remove both public and private rooms (direct database access)
- Configurable - Use custom config files for different server environments
- Permission checking - Validates database access before operations
- Error handling - Clear error messages and troubleshooting guidance

## Prerequisites

- Python 3.6 or higher
- `requests` library (`pip install requests`)
- Running [Retro AIM Server](https://github.com/mk6i/retro-aim-server) instance
- For delete operations: SQLite3 command-line tool and database access

## Installation

1. Clone or download the script:
   ```bash
   wget https://raw.githubusercontent.com/your-repo/ras-room-mgr/main/ras-room-mgr.py
   chmod +x ras-room-mgr.py
   ```

2. Install dependencies:
   ```bash
   pip install requests
   ```

3. Create a configuration file (optional):
   ```bash
   echo "[server]" > config.ini
   echo "base_url = http://localhost:8080" >> config.ini
   ```

## Usage

### Basic Commands

```bash
# List all public chat rooms
./ras-room-mgr.py get public

# List all private chat rooms  
./ras-room-mgr.py get private

# Create a new public chat room
./ras-room-mgr.py create public "General Discussion"

# Delete a chat room (works for both public and private)
./ras-room-mgr.py delete public "Old Room"
./ras-room-mgr.py delete private "Secret Meeting"
```

### Configuration File

Use a custom configuration file for different environments:

```bash
# Use a different server
./ras-room-mgr.py --config-file production.ini get public

# Example config file (myserver.ini):
[server]
base_url = http://192.168.1.100:8080
```

### Help

```bash
./ras-room-mgr.py --help
```

## Configuration

The tool looks for a `config.ini` file in the current directory by default. If not found, it defaults to `http://localhost:8080`.

**Example config.ini:**
```ini
[server]
base_url = http://localhost:8080
# Change this to your retro AIM server URL
```

## API Limitations

- **Creating private rooms**: Not supported by the Retro AIM Server API (405 Method Not Allowed)
- **Deleting rooms**: No API endpoint available, so direct SQLite database manipulation is used

## Database Operations

Room deletion bypasses the API and directly modifies the SQLite database at `/usr/local/ras/oscar.sqlite`. This requires:

- Read/write access to the database file
- SQLite3 command-line tool at `/usr/bin/sqlite3`

### Permission Issues

If you encounter permission errors:

```bash
# Option 1: Run with sudo
sudo ./ras-room-mgr.py delete public "Room Name"

# Option 2: Fix file permissions  
sudo chmod 666 /usr/local/ras/oscar.sqlite

# Option 3: Add user to appropriate group
sudo usermod -a -G ras-group $USER
```

## Examples

### Managing Public Rooms
```bash
# List current public rooms
./ras-room-mgr.py get public

# Create a new public room
./ras-room-mgr.py create public "Tech Support"

# Delete an old public room
./ras-room-mgr.py delete public "Outdated Room"
```

### Managing Private Rooms
```bash
# List private rooms
./ras-room-mgr.py get private

# Delete a private room (creation not supported)
./ras-room-mgr.py delete private "Old Private Room"
```

### Multiple Environments
```bash
# Development
./ras-room-mgr.py get public

# Production  
./ras-room-mgr.py --config-file production.ini get public

# Testing
./ras-room-mgr.py --config-file test.ini create public "Test Room"
```

## Output Examples

### Listing Rooms
```
RAS Room Manager - Retro AIM Server Room Management
=======================================================
Loaded server URL from config: http://localhost:8080
Connecting to: http://localhost:8080/chat/room/public

Found 2 public chat room(s):

--------------------------------------------------------------------------------
Room 1: General Chat
  Created: 2024-01-15 14:30:22 UTC
  Participants (3):
    - user123 (ID: abc123)
    - alice (ID: def456)
    - bob (ID: ghi789)
--------------------------------------------------------------------------------
Room 2: Tech Support
  Created: 2024-01-15 15:45:11 UTC
  Participants (0):
    - No participants
--------------------------------------------------------------------------------

Successfully retrieved 2 public chat room(s).
```

### Creating Rooms
```
Creating public chat room: 'New Discussion'
Sending POST request to: http://localhost:8080/chat/room/public
Public chat room 'New Discussion' created successfully!

Successfully created public chat room: 'New Discussion'
```

### Deleting Rooms
```
Deleting public chat room: 'Old Room'
Executing direct database deletion...
Public chat room 'Old Room' deleted successfully!

Successfully deleted public chat room: 'Old Room'
```

## Error Handling

The tool provides clear error messages for common issues:

- **Server not running**: Connection refused errors with troubleshooting tips
- **Permission issues**: Detailed permission analysis and fix suggestions  
- **Invalid room names**: Validation error messages
- **API limitations**: Clear explanations when operations aren't supported

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Standards

- Code follows PEP 8 Python style guidelines
- All functions include comprehensive docstrings
- Changes should include appropriate test coverage
- Run the regression test suite before submitting changes

### Running Tests

```bash
# Validate your changes
./test.py --script ./ras-room-mgr.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Related Projects

- [Retro AIM Server](https://github.com/mk6i/retro-aim-server) - The AIM server this tool manages
- [AIM Client Setup Guide](https://github.com/mk6i/retro-aim-server/blob/main/docs/CLIENT.md) - Setting up AIM clients

## Acknowledgments

- Thanks to the [Retro AIM Server](https://github.com/mk6i/retro-aim-server) project for making classic AIM possible again
- Built for the retro computing and instant messaging community