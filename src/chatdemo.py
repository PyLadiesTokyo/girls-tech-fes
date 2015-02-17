#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
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

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")


class Application(tornado.web.Application):
    def __init__(self):
        #URLの指定
        handlers = [
            (r"/", MainHandler),
            (r"/name/inputname", InputNameHandler),
            (r"/name/signup", SignUpHandler),
            (r"/name/signout", SignOutHandler),
            (r"/chatsocket", ChatSocketHandler),
        ]
        settings = dict(
            #本当はこんな簡素なcookie名にしちゃいけないよ
            cookie_secret="__pyladies_girls_tech_fes_demo_cookie__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            #Cookieデータが存在しない場合は下記へ強制リダイレクト
            login_url="/name/inputname",
            autoescape="xhtml_escape",
            xsrf_cookies=True,
            debug=options.debug,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        username = self.get_secure_cookie("chatdemo_user")

        # cookieが値を返すとパスできる
        # 何もないとlogin_urlへリダイレクトされる → login_urlの指定がなければloginなしのシステムとなる
        if not username:
            return None
        return tornado.escape.utf8(username)


class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("index.html", messages=ChatSocketHandler.cache)


class ChatSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        ChatSocketHandler.waiters.add(self)

    def on_close(self):
        ChatSocketHandler.waiters.remove(self)

    @classmethod
    def update_cache(cls, chat):
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]

    @classmethod
    def send_updates(cls, chat):
        logging.info("sending message to %d waiters", len(cls.waiters))
        print(chat)
        for waiter in cls.waiters:
            try:
                waiter.write_message(chat)
            except:
                logging.error("Error sending message", exc_info=True)

    # 表示メッセージの整形
    def on_message(self, message):
        logging.info("got message %r", message)
        parsed = tornado.escape.json_decode(message)
        username = self.get_secure_cookie("chatdemo_user")

        chat = {
            "id": str(uuid.uuid4()),
            "from": str(username, encoding='utf-8'),  # html表示時文字化け対策実施
            "body": parsed["body"],
            }
        chat["html"] = tornado.escape.to_basestring(
            self.render_string("message.html", message=chat))

        ChatSocketHandler.update_cache(chat)
        ChatSocketHandler.send_updates(chat)


# ログインの代わりに名前の入力してもらう
class InputNameHandler(BaseHandler):
    def get(self):
        self.render("inputname.html")

# 入力した名前をCookieにセット。チャットページで使えるようにする。
class SignUpHandler(BaseHandler):
    def get(self):
        self.render("login.html")

    # <form action="/name/setname" method="post"> の記述により
    # inputname.htmlから最初に呼ばれるdefはこちら。
    def post(self):
        logging.debug("xsrf_cookie:" + self.get_argument("_xsrf", None))

        self.check_xsrf_cookie()
        username = self.get_argument("username")
        logging.debug('サインアップメソッドで %s の名前を受け取りました' % username)

        if username:
            self.set_secure_cookie("chatdemo_user", tornado.escape.utf8(username))
            self.redirect("/")
        else:
            self.write_error(403)


# テストのために必要性を感じたのでCookie削除処理をつけました。
# 本来今回のworkshopでは不要な処理です。。。
class SignOutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("chatdemo_user")
        self.write("登録していたユーザ名を消去しました。もう一度はじめからやり直しをお願いします。")


def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
