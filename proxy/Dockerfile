# Base image with fully functional 3proxy installation
FROM 3proxy/3proxy:latest

# Set the working directory (use a valid directory in the container)
WORKDIR /usr/local/3proxy

# Copy the configuration file to the appropriate location for chroot
COPY ./3proxy.cfg ./conf/3proxy.cfg

# Expose the proxy port
EXPOSE 3128

# Run 3proxy using the correct binary path
CMD ["/bin/3proxy", "./conf/3proxy.cfg"]
