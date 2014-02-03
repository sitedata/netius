# Examples

Here are some random examples on the netius usage.

```python
smtp_client = SMTPClient(auto_close = True)
smtp_client.message(
    [sender],
    [receiver],
    contents,
    host = "smtp.gmail.com",
    port = 587,
    username = "username@gmail.com",
    password = "password",
    stls = True
)
```

```python 
smtp_client = SMTPClient(auto_close = True)
smtp_client.message(
    [sender],
    [receiver],
    contents,
    host = "localhost",
    port = 25,
    stls = True
)
