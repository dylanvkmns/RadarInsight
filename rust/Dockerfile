# Use the official Rust image as the build environment
FROM rust:1.78 as builder

# Create a new empty shell project
RUN USER=root cargo new --bin app
WORKDIR /app

# Copy your manifests
COPY ./Cargo.toml ./Cargo.toml
COPY ./Cargo.lock ./Cargo.lock

# This step caches your dependencies
RUN cargo build --release
RUN rm src/*.rs

# Now that the dependency is built, copy your actual source code
COPY ./src ./src

# Build your application with the dependencies cached
RUN touch src/main.rs
RUN cargo build --release

# The final stage/image
FROM debian:buster

# Install OpenSSL and other dependencies
RUN apt-get update && apt-get install -y \
    openssl \
    libssl1.1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the binary from the builder stage
COPY --from=builder /app/target/release/app /usr/local/bin/

# Set the binary as the container's entry point
ENTRYPOINT ["/usr/local/bin/app"]
