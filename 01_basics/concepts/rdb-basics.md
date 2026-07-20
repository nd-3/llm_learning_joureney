# RDB/SQLの基本

- 主キー

  **usersテーブル(利用者の表)**
  | user_id | name |
  |---|---|
  | 1 | 私 |
  | 2 | あなた |

- 外部キー

  **ordersテーブル(注文の表)**
  | order_id | user_id | item |
  |---|---|---|
  | 101 | 1 | ペン |
  | 102 | 1 | ノート |
  | 103 | 2 | 消しゴム |

# SQL基本文法

## RDBとは

- リレーショナルデータベース。
- 複数の表を共通のIDで繋げて管理すること。主キーと外部キーの構造。

## 主キーと外部キー

- usersテーブルの`user_id`が主キー、ordersテーブルの`user_id`が外部キーとなる。
- ordersテーブルの`user_id`で1の箇所はusersテーブルの`user_id`の1に設定している`私`になる。
- 同じ情報は1か所に持つ。

## なぜ表を分けるのか

- `私`や`あなた`をコードの至る箇所に書くと何の意味の`私`なのか`あなた`なのかわからなくなる
- `私`という名前をordersテーブルに直接何度も書くと、あとで名前を変えたときに全部の行を探して直す必要がある。IDだけ持たせておけば、名前はusersテーブルだけで管理できるので、そこだけ直せばいい。

## SELECT / WHERE / JOIN

**RDBからデータを取り出す**

```SQL
SELECT name FROM users;   -- usersという表からnameという列をとってくる
```

**条件を絞りたいとき**

```SQL
SELECT name FROM users WHERE user_id = 1;
```

**2つの表を繋げて取り出す**

```SQL
SELECT users.name, orders.item                -- くっつけた結果からnameとitemだけ選ぶ
FROM orders                                   -- まず注文の表を見る
JOIN users ON orders.user_id = users.user_id; -- orders側とusers側のuser_idが一致する行同士を横にくっつける
```

- JOINは双方に一致する行だけ残す←`INNER JOIN`
- どちらかにしかない場合、結果から消える。**存在してないから出てこない**
- ↑`LEFT JOIN`なら対応する情報がないところを空欄で出力する
