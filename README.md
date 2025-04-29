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