from hermes import Chatroom

import random, requests

class RandomImagesChatroom(Chatroom):
    command_patterns = (
        (r'^([a-zA-Z0-9_-]+)\.(jpg|png|gif)$', 'image'),
    )

    def image(self, sender, body, match):
        """If the message consists entirely of an image name such as "fail.jpg", make it a link to a (funny) image if it exists. Note that not all clients support HTML markup in messages. They will just receive the original message"""
        base_url = 'http://your.image.server.here'
        img_name = match.group(0)
        img_url = '%s/%s' % (base_url, img_name)

        try:
            meta_url = '%s/%s.txt' % (base_url, match.group(1))
            resp = requests.get(meta_url)
            urls = resp.text.strip().split('\n')
            img_url = random.choice(urls)
        except Exception: pass

        html_body = '[%s] <a href="%s">%s</a>' % (sender['NICK'], img_url, img_name,)
        self.broadcast(body, html_body=html_body, exclude=()) #not excluding sender so they can see result
