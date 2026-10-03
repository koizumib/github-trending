# 0030 リポジトリ名と順位の数字を、Miller Text に近い新聞の書体（Gelasio）にする

- 日付：2026-10-03
- 状態：決定（0011 の「見出しも本文も BIZ UDPゴシック」のうち、英字の題名と数字だけを改める）

## 背景
本人から「リポジトリ名などは、もっと新聞っぽいフォントでいい。Miller Text のような」と。リポジトリ名はいつも英字なので、日本語の明朝体（0011 で細くて読みにくいとやめた）を使わずに、英字だけの書体で新聞らしくできる。

最初は Playfair Display（見出し向けの、線の太さの差が大きい書体）にして「アカウント名/」を斜体にしたが、本人が求めていたのは Miller Text のような新聞の本文・見出しの書体で、斜体ではなかった。

## 決定
- Miller Text は有料（Font Bureau）で Google Fonts にないため、近い無料の書体として Gelasio（太さ 400・700）を読み込む。Gelasio は Georgia と同じ寸法で作られた書体で、Georgia と Miller はどちらも Matthew Carter が Scotch Roman をもとに作った、新聞でよく使われる系統。Newsreader、Old Standard TT、Libre Caslon、Libre Baskerville、Source Serif とも並べて比べ、Miller に一番近いものを選んだ
- 読み込めないときの代わりは Georgia、Times New Roman
- 使うところ：一覧の題名と詳しいページの大きな題名（「アカウント名/」も同じ書体で、斜体にしない）、順位の数字、英字で始まる本文の大きな書き出し（0026）
- Gelasio の数字は既定で高さが不揃い（オールドスタイル）なので、高さを揃える（`lining-nums`）
- 「位」、日本語の書き出し、本文、そのほかの文字は BIZ UDPゴシックのまま
