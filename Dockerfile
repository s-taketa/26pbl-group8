FROM alpine:3.19

WORKDIR /app

COPY . .

CMD ["sh", "-c", "echo 'Container is working' && sleep 3600"]