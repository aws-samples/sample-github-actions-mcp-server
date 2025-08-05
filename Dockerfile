FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -e .

HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=3 CMD python -c "import socket; socket.socket().connect(('localhost', 8080))" || exit 1

ENTRYPOINT ["python", "-m", "awslabs.github_actions_mcp_server.server"]
