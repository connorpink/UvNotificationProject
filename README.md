## Prerequisites

- Docker and Docker Compose
- Discord Bot Token
- WeatherAPI.com API Key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/connorpink/UvNotificationProject
cd UvNotificationProject
```

2. Run the bot using Docker Compose, passing your credentials as environment variables:
```bash
DISCORD_TOKEN=your_discord_token_here \
WEATHER_API_KEY=your_weather_api_key_here \
docker-compose up --build -d
```

Alternatively, you can export the environment variables first:
```bash
export DISCORD_TOKEN=your_discord_token_here
export WEATHER_API_KEY=your_weather_api_key_here
docker-compose up --build -d
```

## Development

### Project Structure
```
UvNotificationProject/
├── UV_bot.py           # Main bot code
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
└── requirements.txt    # Python dependencies
```

## Bot Commands

### UV Index Commands
- `$uv <location>` - Get the current UV index for any location
  - Example: `$uv London` or `$uv "New York"`
  - Shows current UV index and risk level

- `$setlocation <location>` - Set your default location and notification preferences
  - Example: `$setlocation Sydney`
  - Will prompt you to:
    1. Confirm location if multiple matches found
    2. Select UV threshold for notifications (Low/Moderate/High/Very High)

- `$mylocation` - Display UV index for your saved location
  - Shows:
    - Current UV index
    - Risk level
    - Your notification threshold setting

### UV Index Risk Levels
- Low: UV index 0-2
- Moderate: UV index 3-5
- High: UV index 6-7
- Very High: UV index 8-10
- Extreme: UV index 11+

### Notification Thresholds
When setting up notifications, you can choose to be alerted when UV levels exceed:
1. Low (UV > 2)
2. Moderate (UV > 5)
3. High (UV > 7)
4. Very High (UV > 10)

Daily notifications will be sent at 9:00 AM if the UV index exceeds your chosen threshold.

### Docker Management Commands
```bash
# Start the bot
DISCORD_TOKEN=your_token WEATHER_API_KEY=your_key docker-compose up -d

# View live logs
docker-compose logs -f

# Stop the bot
docker-compose down

# Rebuild and restart (after code changes)
docker-compose up -d --build

# Check bot container status
docker-compose ps
```