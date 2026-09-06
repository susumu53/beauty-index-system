@echo off
chcp 65001 > nul
echo ======================================================
echo  🍳 料理・グルメブログ (syoshinsya2525) 自動投稿
echo ======================================================
cd /d %~dp0
python post_gourmet_article.py --type auto
echo ======================================================
echo 投稿処理が完了しました。
timeout /t 5 > nul
