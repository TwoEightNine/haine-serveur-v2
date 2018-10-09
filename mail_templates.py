MESSAGE_CODE = """<html>
<head>
    <title></title>
</head>
<body aria-readonly="false">
<p><span style="font-size:16px"><span style="font-family:arial,helvetica,sans-serif">You have successfully signed up!<br />
For activating your account open this link: <span style="color:#10d600"> <a href="%s">%s</a></span>.</span></span></p>
</body>
</html>
"""
MESSAGE_CODE_PLAIN = "You have successfully signed up!\nFor activating your account open this link: %s (%s)"

MESSAGE_PASSWORD = """<html>
<head>
    <title></title>
</head>
<body>
<pre>
<span style="font-size:16px"><span style="font-family:arial,helvetica,sans-serif">You have requested a new password and there is:
<strong>%s</strong>
Do not forget it again!</span></span></pre>
</body>
</html>
"""
MESSAGE_PASSWORD_PLAIN = "You have requested a new password and there is:\n%s\nDo not forget it again!"
