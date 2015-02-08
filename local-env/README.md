# ローカル開発環境の構築
## 仮想環境構築の動作テスト環境
Vagrant上に今回必要となる仮想環境をらくらく構築するためのスクリプト  
動作テスト環境は以下の通り

- Mac OSX 10.9.5 (Windowsはごめんなさい)
- Python 2.7.9
  - pip 6.0.7
    - ansible 1.8.2 (`pip install ansible`で導入可能)
- Vagrant 1.6.2
- VirtualBox 4.3.10 (VMWare等を利用されている場合は，適宜Vagrantfileを書き換えて下さい)

## 仮想環境構築手順
Private IPとかはよしなに書き換える  
`vagrant up`がうまく動いてくれない場合は，`vagrant provision`を試してみて下さい

```
$ vagrant up
```

無事に環境構築が終わったら，`vagrant ssh`で仮想環境にログインする  

### 仮想環境上でIPython Notebook Serverを動作させる手順
まず初めに，IPython Notebook Server用のパスワードを設定する  
`Enter password`が表示されたら，任意のパスワードを入力して設定する

```
$ ipython
In [1]: from IPython.lib import passwd
In [2]: passwd()
Enter password:
Verify password:
Out[2]: 'sha1:********'
```

`'sha1:********'`の形式で示される値をコピーする  
任意のエディタで`~/.ipython/profile_pyladies/ipython_notebook_config.py`を開き，`c.NotebookApp.password`の値
(* 'replace me!'で示される部分)をコピーした値で置き換える

全て終わったら，以下のコマンドでIPython Notebook Serverを起動出来る

```
$ ipython notebook --profile=pyladies
```

ローカルの適当なブラウザを立ち上げて，以下の通り打ち込むと，IPython Notebook Serverにアクセス出来る  
(ipやportを書き換えている場合は適宜変更して下さい)

```
http://192.168.33.10:9999
```

先ほど設定したパスワードを利用してログイン出来る