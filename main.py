__author__ = 'Piotrek'

from tornado import autoreload
"""Simplified chat demo for websockets.
Authentication, error handling, etc are left as an exercise for the reader :)
"""

import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid
import pickle

from tornado.options import define, options
from datetime import datetime, date, time

define("port", default=8888, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/chatsocket", ChatSocketHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
        ]
        settings = dict(
            cookie_secret="super-tajne",
            login_url= "/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class LoginHandler(BaseHandler):
    def get(self):
        self.render("login.html")

    def post(self):
        self.set_secure_cookie("user", self.get_argument("name"))
        self.redirect("/")

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.write('Wylogowano. '
                   'Kliknij <a href="/">tutaj</a> żeby zalogować się ponownie.')

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("index.html", messages=ChatSocketHandler.cache)

class ChatSocketHandler(BaseHandler, tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200
    cache_file_name = "cache.dat"
    cache_file = None
    loaded = False

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        ChatSocketHandler.waiters.add(self)
        self.send_join_info(self)

    def on_close(self):
        ChatSocketHandler.waiters.remove(self)
        self.send_part_info(self)

    def send_join_info(self,user):
        chat = self.make_chat("dołączył do chatu","join.html","green")
        ChatSocketHandler.update_cache(chat)
        ChatSocketHandler.send_updates(chat)

    def send_part_info(self,user):
        chat = self.make_chat("odłączył się","join.html","blue")
        ChatSocketHandler.update_cache(chat)
        ChatSocketHandler.send_updates(chat)



    @classmethod
    def load_old(cls):
        if cls.loaded is False:
            if os.path.exists(cls.cache_file_name) is True:
                # print("Laduje")
                cls.cache_file=open(cls.cache_file_name,"rb")
                cls.cache = pickle.load(cls.cache_file)
                cls.cache_file.close()
                cls.loaded=True
        # cls.cache_file=open(cls.cache_file_name,"wb")

    @classmethod
    def update_cache(cls, chat):
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]
        with open('cache.dat', 'wb') as f:
            # Pickle the 'data' dictionary using the highest protocol available.
            pickle.dump(cls.cache, f, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def send_cache(cls, waiter):
        for message in cls.cache:
            waiter.write_message(message)


    @classmethod
    def send_updates(cls, chat):
        logging.info("Wysyłam wiadomosć do %d oczekujacych", len(cls.waiters))
        for waiter in cls.waiters:
            try:
                waiter.write_message(chat)
            except:
                logging.error("Błąd przy wysyłaniu wiadomosći", exc_info=True)

    def on_message(self, message):
        logging.info("Otrzymałem wiadomość %r", message)
        parsed = tornado.escape.json_decode(message)

        chat = self.make_chat(parsed["body"])

        ChatSocketHandler.update_cache(chat)
        ChatSocketHandler.send_updates(chat)

    def make_chat(self,body,template="message.html",col=None):
        chat = {
            "id": str(uuid.uuid4()),
            "time": datetime.now().strftime('%H:%M:%S'),
            "nick": tornado.escape.to_basestring(self.get_current_user().decode("utf-8")),
            "body": body,
            }
        if template=="message.html":
            chat["html"] = tornado.escape.to_basestring(
                self.render_string("message.html", message=chat))
        else:
            chat["html"] = tornado.escape.to_basestring(
            self.render_string(template, message=chat, color=col))
        return chat


def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    ChatSocketHandler.load_old()
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
