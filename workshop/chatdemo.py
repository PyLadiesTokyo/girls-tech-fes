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
    """

    2. チャット機能を作ろう

    """


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
    """

    1. チャットページに遷移しよう

    """


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
