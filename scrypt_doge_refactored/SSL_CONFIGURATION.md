# SSL Configuration for Mining OS

The Mining OS supports HTTPS/SSL encryption for secure communication. This guide explains how to configure SSL for your mining operations.

## Enabling SSL

### Environment Variables

To enable SSL, you need to set the following environment variables:

- `SSL_CERTFILE`: Path to your SSL certificate file
- `SSL_KEYFILE`: Path to your SSL private key file

### Docker Configuration

When using Docker, you can enable SSL by:

1. Mounting your certificate and key files as volumes:
```yaml
volumes:
  - ./ssl/cert.pem:/app/ssl/cert.pem
  - ./ssl/key.pem:/app/ssl/key.pem
```

2. Setting the environment variables:
```yaml
environment:
  - SSL_CERTFILE=/app/ssl/cert.pem
  - SSL_KEYFILE=/app/ssl/key.pem
```

### Docker Run Example

```bash
docker run -d \
  --name mining-os \
  -p 31415:31415 \
  -e PAYOUT_ADDR=your_wallet_address \
  -e SSL_CERTFILE=/app/ssl/cert.pem \
  -e SSL_KEYFILE=/app/ssl/key.pem \
  -v /path/to/your/cert.pem:/app/ssl/cert.pem \
  -v /path/to/your/key.pem:/app/ssl/key.pem \
  mining-os
```

## Generating Self-Signed Certificates

For testing purposes, you can generate self-signed certificates:

```bash
# Generate private key
openssl genrsa -out key.pem 2048

# Generate certificate
openssl req -new -x509 -key key.pem -out cert.pem -days 365
```

## Production SSL Certificates

For production use, we recommend obtaining certificates from a trusted Certificate Authority such as:

- Let's Encrypt (free)
- DigiCert
- Comodo
- GlobalSign

## Security Considerations

1. **Private Key Protection**: Never share your private key file
2. **File Permissions**: Set appropriate file permissions (600) for your key file
3. **Certificate Expiry**: Monitor certificate expiration dates
4. **Regular Updates**: Update certificates before they expire

## Troubleshooting

### Common Issues

1. **Certificate Not Found**: Ensure the certificate files exist and are accessible
2. **Permission Denied**: Check file permissions on certificate and key files
3. **Invalid Certificate**: Verify the certificate format and validity

### Logs

Check the application logs for SSL-related errors:
```bash
docker logs mining-os
```

## Frontend Considerations

The frontend automatically detects whether to use HTTP or HTTPS based on the current protocol:

- In development: Uses HTTP
- In production with SSL: Uses HTTPS

WebSocket connections also automatically use the appropriate protocol:
- `ws://` for HTTP
- `wss://` for HTTPS

This ensures secure communication when SSL is enabled.