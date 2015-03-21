# -*- coding: utf-8 -*-
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

import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid

from tornado.options import define, options

define(u"port", default=8888, help=u"run on the given port", type=int)
define(u"debug", default=False, help=u"run in debug mode")


class Application(tornado.web.Application):
    def __init__(self):
        # URLの指定
        handlers = [
            (ur"/", MainHandler),
            (ur"/name/inputname", InputNameHandler),
            (ur"/name/signup", SignUpHandler),
            (ur"/name/signout", SignOutHandler),
            (ur"/chatsocket", ChatSocketHandler),
        ]
        settings = dict(
            cookie_secret=u"__pyladies_girls_tech_fes_demo_cookie__",
            template_path=os.path.join(os.path.dirname(__file__), u"templates"),
            static_path=os.path.join(os.path.dirname(__file__), u"static"),

            login_url=u"/name/inputname",
            autoescape=u"xhtml_escape",
            xsrf_cookies=True,
            debug=options.debug,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        username = self.get_secure_cookie(u"chatdemo_user")

        # cookieが値を返すとパスできる
        # 何もないとlogin_urlへリダイレクトされる → login_urlの指定がなければloginなしのシステムとなる
        if not username:
            return None
        return tornado.escape.utf8(username)


class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render(u"index.html", messages=ChatSocketHandler.cache)


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
        logging.info(u"sending message to %d waiters", len(cls.waiters))
        print chat
        for waiter in cls.waiters:
            try:
                waiter.write_message(chat)
            except:
                logging.error(u"Error sending message", exc_info=True)

    # 表示メッセージの整形
    def on_message(self, message):
        logging.info(u"got message %r", message)
        parsed = tornado.escape.json_decode(message)
        username = self.get_secure_cookie(u"chatdemo_user")

        chat = {
            u"id": unicode(uuid.uuid4()),
            u"from": unicode(username, encoding=u'utf-8'),  # html表示時文字化け対策実施
            u"body": parsed[u"body"],
            }
        chat[u"html"] = tornado.escape.to_basestring(
            self.render_string(u"message.html", message=chat))

        ChatSocketHandler.update_cache(chat)
        ChatSocketHandler.send_updates(chat)


# ログインの代わりに名前の入力してもらう
class InputNameHandler(BaseHandler):
    def get(self):
        self.render(u"inputname.html")

# 入力した名前をCookieにセット。チャットページで使えるようにする。
class SignUpHandler(BaseHandler):
    def get(self):
        self.render(u"login.html")

    # <form action="/name/setname" method="post"> の記述により
    # inputname.htmlから最初に呼ばれるdefはこちら。
    def post(self):
        logging.debug(u"xsrf_cookie:" + self.get_argument(u"_xsrf", None))

        self.check_xsrf_cookie()
        username = self.get_argument(u"username")
        logging.debug(u'サインアップメソッドで {0} の名前を受け取りました'.format(username))

        if username:
            self.set_secure_cookie(u"chatdemo_user", tornado.escape.utf8(username))
            self.redirect(u"/")
        else:
            self.set_status = 404
            self.set_header('Content-Type', 'text/html; charset="utf-8"')
            self.finish(
                '名前が入力されていません。最初からやり直して下さい。<br><a href=http://localhost:{port}>ログインページに戻る</a>'.format(port=options.port))


# テストのために必要性を感じたのでCookie削除処理をつけました。
# 本来今回のworkshopでは不要な処理です。。。
class SignOutHandler(BaseHandler):
    def get(self):
        self.clear_cookie(u"chatdemo_user")
        self.write(u"登録していたユーザ名を消去しました。もう一度はじめからやり直しをお願いします。")


def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    print u"サーバを起動します。"
    print u"http://localhost:" + str(options.port) + u" にアクセスしてください"
    print u"止めるときは Ctrl + c を押してください"
    tornado.ioloop.IOLoop.instance().start()


if __name__ == u"__main__":
    main()
