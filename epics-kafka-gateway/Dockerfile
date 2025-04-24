# syntax=docker/dockerfile:1

############################
# Builder stage            #
############################
FROM golang:1.22-alpine AS builder
WORKDIR /app

# Install git & certs (needed for go modules)
RUN apk add --no-cache git ca-certificates && update-ca-certificates

# Copy go.mod & go.sum first for better cache utilisation
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build statically linked binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o gateway ./server.go

############################
# Runtime stage            #
############################
FROM alpine:latest AS runtime
WORKDIR /app
COPY --from=builder /app/gateway ./gateway

# Expose REST/WebSocket port
EXPOSE 8080

ENTRYPOINT ["./gateway"]
