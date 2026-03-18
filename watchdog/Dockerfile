FROM alpine:latest

# Install required tools
RUN apk add --no-cache bash curl grep coreutils

# Create log directory
RUN mkdir -p /logs

# Copy watchdog script
COPY watchdog.sh /watchdog.sh
RUN chmod +x /watchdog.sh

# Run as daemon
CMD ["/watchdog.sh"]
